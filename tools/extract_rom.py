#!/usr/bin/env python3
"""Extrai a ROM do DS: ARM9 e ARM7 (descomprimidos), overlays ARM9, arquivos, manifesto.

Uso: tools/extract_rom.py --rom rom/X.nds --out local/extracted
Saída: arm9.bin, arm7.bin, overlay9/overlay_NNNN.bin, files/NNNN.bin, manifest.json.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path


def grava(caminho, dados):
    """Só regrava se o conteúdo mudou: a data do arquivo é o que o ninja olha para recompilar."""
    if not caminho.exists() or caminho.stat().st_size != len(dados) or caminho.read_bytes() != dados:
        caminho.write_bytes(dados)

SIG = struct.pack("<II", 0xDEC00621, 0x2106C0DE)


def u32(b, o): return struct.unpack_from("<I", b, o)[0]


def blz_decompress(data: bytes) -> bytes:
    """Compressão BLZ (LZ de trás para frente) usada no ARM9 e nos overlays."""
    buf = bytes(data)
    if len(buf) < 8:
        return buf
    hdr_len = buf[-5]
    enc_len = u32(buf, len(buf) - 8) & 0xFFFFFF
    inc = u32(buf, len(buf) - 4)
    if hdr_len < 8 or enc_len > len(buf):
        raise ValueError("cabeçalho BLZ inválido")
    end = len(buf)
    out = bytearray(end + inc)
    out[:end] = buf
    src, dst, stop = end - hdr_len, end + inc, end - enc_len
    while src > stop:
        src -= 1
        flags = buf[src]
        for _ in range(8):
            if src <= stop:
                break
            if flags & 0x80:
                b1, b2 = buf[src - 1], buf[src - 2]
                src -= 2
                disp = (((b1 & 0x0F) << 8) | b2) + 3
                for _ in range((b1 >> 4) + 3):
                    dst -= 1
                    out[dst] = out[dst + disp]
            else:
                src -= 1
                dst -= 1
                out[dst] = buf[src]
            flags = (flags << 1) & 0xFF
    return bytes(out)


def module_params(code: bytes, ram: int):
    i = code.find(SIG)
    if i < 0:
        return None
    o = i - 0x1C  # struct: autoload_list_start/end, autoload_start, bss start/end, compressed_end, sdk
    names = ["autoload_list_start", "autoload_list_end", "autoload_start", "static_bss_start",
             "static_bss_end", "compressed_static_end", "sdk_version"]
    p = {n: u32(code, o + 4 * k) for k, n in enumerate(names)}
    p["offset"] = o
    return p


def autoloads(code: bytes, ram: int, p):
    if not p:
        return []
    lst = []
    data_at = p["autoload_start"] - ram
    for a in range(p["autoload_list_start"] - ram, p["autoload_list_end"] - ram, 16):
        addr, size, sinit, bss = struct.unpack_from("<IIII", code, a)
        lst.append({"ram": addr, "size": size, "sinit": sinit, "bss": bss, "offset": data_at})
        data_at += size
    return lst


def sha1(b): return hashlib.sha1(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rom = Path(a.rom).read_bytes()
    out = Path(a.out)
    (out / "overlay9").mkdir(parents=True, exist_ok=True)
    (out / "files").mkdir(parents=True, exist_ok=True)
    print("PROGRESSO 0/4")

    code_id = rom[0x0C:0x10].decode("ascii", "replace")
    a9o, a9e, a9r, a9s = struct.unpack_from("<IIII", rom, 0x20)
    a7o, a7e, a7r, a7s = struct.unpack_from("<IIII", rom, 0x30)
    fnto, fnts, fato, fats, ov9o, ov9s = struct.unpack_from("<IIIIII", rom, 0x40)
    fat = [struct.unpack_from("<II", rom, fato + 8 * k) for k in range(fats // 8)]

    arm9 = rom[a9o:a9o + a9s]
    p9 = module_params(arm9, a9r)
    blz9 = bool(p9 and p9["compressed_static_end"])
    if blz9:
        cut = p9["compressed_static_end"] - a9r
        arm9 = blz_decompress(arm9[:cut]) + arm9[cut:]  # marcador fica como na ROM (igual ao ndspy)
    arm7 = rom[a7o:a7o + a7s]
    p7 = module_params(arm7, a7r)
    grava(out / "arm9.bin", arm9)
    grava(out / "arm7.bin", arm7)
    print("PROGRESSO 1/4")

    ovs, comp = [], 0
    for k in range(ov9s // 32):
        oid, ram, size, bss, s0, s1, fid, fl = struct.unpack_from("<8I", rom, ov9o + 32 * k)
        st, en = fat[fid]
        data = rom[st:en]
        c = bool(fl & 0x01000000)
        if c:
            data = blz_decompress(data)
            comp += 1
        grava(out / "overlay9" / f"overlay_{oid:04d}.bin", data)
        ovs.append({"id": oid, "ram": ram, "size": size, "bss": bss, "sinit": [s0, s1],
                    "file_id": fid, "compressed": c, "sha1": sha1(data), "len": len(data)})
    print("PROGRESSO 2/4")

    for fid, (st, en) in enumerate(fat):
        grava(out / "files" / f"{fid:04d}.bin", rom[st:en])
    print("PROGRESSO 3/4")

    man = {
        "rom_sha1": sha1(rom), "code": code_id,
        "arm9": {"rom_offset": a9o, "entry": a9e, "ram": a9r, "rom_size": a9s, "size": len(arm9),
                 "sha1": sha1(arm9), "blz": blz9, "module_params": p9,
                 "autoloads": autoloads(arm9, a9r, p9)},
        "arm7": {"rom_offset": a7o, "entry": a7e, "ram": a7r, "size": len(arm7), "sha1": sha1(arm7),
                 "module_params": p7, "autoloads": autoloads(arm7, a7r, p7)},
        "fnt": [fnto, fnts], "fat": [fato, fats], "fat_entries": len(fat),
        "files": len(fat) - len(ovs), "overlay9": ovs,
        "overlay9_list_sha1": sha1("\n".join(o["sha1"] for o in ovs).encode()),
    }
    grava(out / "manifest.json", json.dumps(man, indent=1).encode())
    print(f"OK {code_id}: ARM9 {len(arm9):#x} (blz={'sim' if blz9 else 'não'}), ARM7 {len(arm7):#x}, "
          f"overlays {len(ovs)} ({comp} BLZ), arquivos {len(fat) - len(ovs)}, autoloads "
          f"{len(man['arm9']['autoloads'])}/{len(man['arm7']['autoloads'])}")
    print("PROGRESSO 4/4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
