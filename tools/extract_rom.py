#!/usr/bin/env python3
"""Extrai cabeçalho, ARM9, ARM7, overlays (BLZ descomprimido) e o sistema de
arquivos de um dump de Pokémon Black verificado.

Toda a saída vai para um diretório fora do git (padrão: local/extracted/).
O manifesto (manifest.json) só guarda metadados e SHA-1, nunca bytes da ROM.

Uso: tools/extract_rom.py [--rom local/rom/pokeblack.nds] [--out local/extracted] [--no-files]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

EXPECTED_SHA1 = "26ad0b9967aa279c4a266ee69f52b9b2332399a5"
NITROCODE = 0xDEC00621
REPO = Path(__file__).resolve().parent.parent


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def blz_decompress(data: bytes) -> bytes:
    """Descompressão "backwards LZ" (BLZ) usada no ARM9 e overlays do DS.

    Rodapé de 8 bytes: u32 (tamanho_comprimido | header_len << 24),
    u32 tamanho_extra. Os dados são lidos e escritos do fim para o começo.
    """
    if len(data) < 8:
        raise ValueError("BLZ: dados curtos demais")
    w0, extra = struct.unpack_from("<II", data, len(data) - 8)
    comp_len = w0 & 0xFFFFFF
    hdr_len = w0 >> 24
    if extra == 0:
        return data
    if hdr_len < 8 or comp_len > len(data):
        raise ValueError(f"BLZ: rodapé inválido comp={comp_len:#x} hdr={hdr_len}")
    base = len(data) - comp_len           # prefixo não comprimido
    out = bytearray(data) + bytearray(extra)
    src = len(data) - hdr_len             # fim dos dados comprimidos
    dst = len(out)
    while src > base:
        src -= 1
        flags = data[src]
        for _ in range(8):
            if src <= base:
                break
            if flags & 0x80:
                src -= 2
                pair = data[src] | (data[src + 1] << 8)
                disp = (pair & 0x0FFF) + 3
                n = (pair >> 12) + 3
                for _ in range(n):
                    dst -= 1
                    if dst < base:
                        raise ValueError("BLZ: escrita antes do início")
                    out[dst] = out[dst + disp]
            else:
                src -= 1
                dst -= 1
                out[dst] = data[src]
            flags = (flags << 1) & 0xFF
    if dst != base:
        raise ValueError(f"BLZ: terminou em {dst:#x}, esperado {base:#x}")
    return bytes(out)  # tamanho = len(data) + extra


def module_params(code: bytes, load: int) -> dict | None:
    """Lê os parâmetros de módulo do SDK (assinatura nitrocode) e a lista de
    autoload: entradas de 16 bytes (ram, size, sinit, bss), dados contíguos a
    partir de autoload_start."""
    pos = code.find(struct.pack("<II", NITROCODE, 0x2106C0DE))
    if pos < 0:
        return None
    p = pos - 0x1C
    ls, le, ast, bss_s, bss_e, comp_end, sdk = struct.unpack_from("<7I", code, p)
    autoloads = []
    src = ast
    for i in range((le - ls) // 16):
        ram, size, sinit, bss = struct.unpack_from("<4I", code, ls - load + i * 16)
        autoloads.append({"ram": ram, "size": size, "sinit": sinit, "bss": bss,
                          "source": src})
        src += size
    if src != ls:
        raise ValueError(f"autoload: dados terminam em {src:#x}, tabela começa em {ls:#x}")
    return {"params_addr": load + p, "autoload_list": [ls, le], "autoload_start": ast,
            "static_bss": [bss_s, bss_e], "compressed_static_end": comp_end,
            "sdk_version": sdk, "autoloads": autoloads}


def parse_fnt(fnt: bytes) -> dict[int, str]:
    """Mapeia file_id -> caminho a partir da File Name Table."""
    paths: dict[int, str] = {}

    def walk(dir_id: int, prefix: str) -> None:
        off, first_file, _ = struct.unpack_from("<IHH", fnt, (dir_id & 0xFFF) * 8)
        fid = first_file
        p = off
        while True:
            t = fnt[p]
            p += 1
            if t == 0:
                break
            ln = t & 0x7F
            name = fnt[p : p + ln].decode("latin-1")
            p += ln
            if t & 0x80:
                sub = struct.unpack_from("<H", fnt, p)[0]
                p += 2
                walk(sub, f"{prefix}{name}/")
            else:
                paths[fid] = prefix + name
                fid += 1

    walk(0xF000, "")
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default=str(REPO / "local/rom/pokeblack.nds"))
    ap.add_argument("--out", default=str(REPO / "local/extracted"))
    ap.add_argument("--no-files", action="store_true", help="não extrai o sistema de arquivos")
    a = ap.parse_args()

    rom = Path(a.rom).read_bytes()
    if sha1(rom) != EXPECTED_SHA1:
        print(f"ERRO: SHA-1 {sha1(rom)} não é o dump esperado", file=sys.stderr)
        return 1
    out = Path(a.out)
    (out / "overlay9").mkdir(parents=True, exist_ok=True)
    (out / "overlay7").mkdir(parents=True, exist_ok=True)

    h = rom[:0x200]
    hdr = {
        "title": h[0:12].rstrip(b"\0").decode(),
        "game_code": h[12:16].decode(),
        "unit_code": h[0x12],
        "rom_version": h[0x1E],
    }
    (out / "header.bin").write_bytes(rom[:0x4000])
    (a9_off, a9_entry, a9_load, a9_size,
     a7_off, a7_entry, a7_load, a7_size) = struct.unpack_from("<8I", h, 0x20)
    fnt_off, fnt_size, fat_off, fat_size = struct.unpack_from("<4I", h, 0x40)
    y9_off, y9_size, y7_off, y7_size = struct.unpack_from("<4I", h, 0x50)

    man: dict = {"rom_sha1": EXPECTED_SHA1, "header": hdr, "overlay9": [], "overlay7": []}

    # ARM9: secure area já vem decriptada em dumps limpos (0x4000..0x4800).
    arm9_raw = rom[a9_off : a9_off + a9_size]
    # Module params: achados pela assinatura (nitrocode, 0x2106C0DE) dentro do
    # binário; o rodapé de 12 bytes após o ARM9 não existe neste dump.
    arm9 = arm9_raw
    comp_info = None
    sig = struct.pack("<II", NITROCODE, 0x2106C0DE)
    pos = arm9_raw.find(sig)
    if pos >= 0:
        params_off = pos - 0x1C
        comp_end = struct.unpack_from("<I", arm9_raw, params_off + 0x14)[0]
        if comp_end:
            clen = comp_end - a9_load
            arm9 = blz_decompress(arm9_raw[:clen]) + arm9_raw[clen:]
            comp_info = {"params_off": params_off, "compressed_end": comp_end}
    mp9 = module_params(arm9, a9_load)
    (out / "arm9.bin").write_bytes(arm9)
    (out / "arm9_raw.bin").write_bytes(arm9_raw)
    man["arm9"] = {"rom_off": a9_off, "entry": a9_entry, "load": a9_load,
                   "size_raw": a9_size, "size": len(arm9),
                   "blz": comp_info, "module_params": mp9,
                   "sha1": sha1(arm9), "sha1_raw": sha1(arm9_raw)}

    arm7 = rom[a7_off : a7_off + a7_size]
    (out / "arm7.bin").write_bytes(arm7)
    man["arm7"] = {"rom_off": a7_off, "entry": a7_entry, "load": a7_load,
                   "size": a7_size, "module_params": module_params(arm7, a7_load),
                   "sha1": sha1(arm7)}

    fat = [struct.unpack_from("<II", rom, fat_off + i * 8) for i in range(fat_size // 8)]

    def overlays(tab_off: int, tab_size: int, kind: str) -> None:
        for i in range(tab_size // 32):
            (ov_id, ram, ram_size, bss, sinit_s, sinit_e,
             file_id, flags) = struct.unpack_from("<8I", rom, tab_off + i * 32)
            start, end = fat[file_id]
            raw = rom[start:end]
            compressed = bool(flags & 0x01000000)
            data = blz_decompress(raw) if compressed else raw
            if compressed and len(data) != ram_size:
                raise ValueError(f"{kind} {ov_id}: {len(data):#x} != ram_size {ram_size:#x}")
            (out / kind / f"overlay_{ov_id:04d}.bin").write_bytes(data)
            man[kind].append({"id": ov_id, "ram": ram, "ram_size": ram_size, "bss": bss,
                              "sinit": [sinit_s, sinit_e], "file_id": file_id,
                              "compressed": compressed, "size_raw": len(raw),
                              "sha1": sha1(data)})

    overlays(y9_off, y9_size, "overlay9")
    overlays(y7_off, y7_size, "overlay7")
    (out / "y9.bin").write_bytes(rom[y9_off : y9_off + y9_size])
    (out / "y7.bin").write_bytes(rom[y7_off : y7_off + y7_size])

    names = parse_fnt(rom[fnt_off : fnt_off + fnt_size])
    man["files"] = {"count": len(names), "fat_entries": len(fat)}
    if not a.no_files:
        for fid, path in names.items():
            s, e = fat[fid]
            dst = out / "data" / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(rom[s:e])

    # DSi (NDSi Enhanced): só registra; o projeto roda em modo DS.
    if hdr["unit_code"] & 2:
        a9i_off, _, a9i_load, a9i_size, a7i_off, _, a7i_load, a7i_size = \
            struct.unpack_from("<8I", rom, 0x1C0)
        man["dsi"] = {"arm9i": {"rom_off": a9i_off, "load": a9i_load, "size": a9i_size},
                      "arm7i": {"rom_off": a7i_off, "load": a7i_load, "size": a7i_size}}

    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    n9, n7 = len(man["overlay9"]), len(man["overlay7"])
    c9 = sum(o["compressed"] for o in man["overlay9"])
    print(f"OK {hdr['game_code']}: ARM9 {len(arm9):#x} (blz={'sim' if comp_info else 'não'}), "
          f"ARM7 {a7_size:#x}, overlays ARM9 {n9} ({c9} BLZ), ARM7 {n7}, "
          f"arquivos {len(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
