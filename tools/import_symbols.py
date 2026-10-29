#!/usr/bin/env python3
"""Importa rótulos de função da decomp pokeblack (third_party/pokeblack) e
gera os TOMLs de recompilação do ndsrecomp para o ARM9 principal, o ARM7 e
cada overlay do ARM9.

Fonte dos rótulos: as macros `arm_func_start` / `thumb_func_start` /
`non_word_aligned_thumb_func_start` nos .s da decomp, seguidas da linha
`Nome: ; 0xENDERECO`. Só lemos rótulos e endereços; nada é montado.

Os TOMLs carregam o SHA-1 dos binários extraídos, então são derivados do
dump e vão para local/config/ (fora do git). Regenere com este script.

Uso: tools/import_symbols.py [--extracted local/extracted] [--out local/config]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DECOMP = REPO / "third_party" / "pokeblack"

MACRO = re.compile(r"^\s*(arm_func_start|thumb_func_start|non_word_aligned_thumb_func_start)\s+(\S+)")
LABEL = re.compile(r"^(\S+):\s*;\s*0x([0-9A-Fa-f]{8})")
OVERLAY_FILE = re.compile(r"overlay_(\d+)_[0-9A-Fa-f]{8}\.s$")
# A decomp dividiu o overlay 93 (batalha) em arquivos battle_*.s sem prefixo.
BATTLE_OVERLAY = 93


def scan(path: Path) -> list[tuple[int, str, str]]:
    """Devolve [(endereço, modo, nome)] de um arquivo .s."""
    out = []
    pending: tuple[str, str] | None = None
    for line in path.read_text(errors="replace").splitlines():
        m = MACRO.match(line)
        if m:
            pending = ("arm" if m.group(1) == "arm_func_start" else "thumb", m.group(2))
            continue
        if pending:
            lm = LABEL.match(line)
            if lm and lm.group(1) == pending[1]:
                out.append((int(lm.group(2), 16), pending[0], pending[1]))
                pending = None
            elif line.strip() and not line.strip().startswith(("@", ";", ".")):
                pending = None  # macro sem rótulo com endereço: ignora
    return out


def collect() -> dict[str, list[tuple[int, str, str]]]:
    banks: dict[str, list] = defaultdict(list)
    for f in sorted((DECOMP / "asm").rglob("*.s")):
        if "macros" in f.parts or "nonmatchings" in f.parts:
            continue
        m = OVERLAY_FILE.search(f.name)
        if m:
            key = f"ov9_{int(m.group(1)):03d}"
        elif f.name.startswith("battle_"):
            key = f"ov9_{BATTLE_OVERLAY:03d}"
        else:
            key = "arm9"
        banks[key].extend(scan(f))
    for f in sorted((DECOMP / "sub" / "asm").rglob("*.s")):
        banks["arm7"].extend(scan(f))
    return banks


def toml_header(name: str, bid: str, cpu: str, isa: str, load: int, size: int,
                entry: int, sha1: str) -> list[str]:
    return [
        f"# {bid}.toml — gerado por tools/import_symbols.py; não editar à mão.",
        "# Rótulos: decomp pokeblack (third_party/pokeblack). Arquivo fora do git.",
        "",
        "[program]",
        f'name         = "{name}"',
        f'id           = "{bid}"',
        f'cpu          = "{cpu}"',
        f'isa          = "{isa}"',
        f"load_address = 0x{load:08X}",
        f"size         = 0x{size:08X}",
        f"entry_pc     = 0x{entry:08X}",
        "",
        "[identity]",
        f'sha1 = "{sha1}"',
        "",
    ]


def entries(funcs, in_range) -> tuple[list[str], int]:
    lines, seen, n = [], set(), 0
    for addr, mode, name in sorted(funcs):
        if addr in seen or not in_range(addr):
            continue
        seen.add(addr)
        n += 1
        lines += ["[[entry_point]]", f"addr = 0x{addr:08X}", f'mode = "{mode}"',
                  f'name = "{name}"', ""]
    return lines, n


def code_copies(mp: dict) -> list[str]:
    out = []
    for i, a in enumerate(mp["autoloads"]):
        out += ["[[code_copy]]", f"runtime_start = 0x{a['ram']:08X}",
                f"source_start  = 0x{a['source']:08X}", f"size          = 0x{a['size']:08X}",
                f'name          = "autoload{i}"', ""]
    return out


def in_autoload(mp: dict, addr: int) -> bool:
    return any(a["ram"] <= addr < a["ram"] + a["size"] for a in mp["autoloads"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extracted", default=str(REPO / "local/extracted"))
    ap.add_argument("--out", default=str(REPO / "local/config"))
    a = ap.parse_args()
    ext, out = Path(a.extracted), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    man = json.loads((ext / "manifest.json").read_text())
    banks = collect()
    report = {}

    for cpu, isa, label in (("arm9", "armv5te", "ARM9 principal"), ("arm7", "armv4t", "ARM7")):
        info = man[cpu]
        mp = info["module_params"]
        static_end = mp["autoload_start"]
        load = info["load"]

        def ok(addr, load=load, static_end=static_end, mp=mp):
            return load <= addr < static_end or in_autoload(mp, addr)

        body, n = entries(banks[cpu], ok)
        skipped = len({x[0] for x in banks[cpu]}) - n
        text = toml_header(f"Pokemon Black {label}", f"pkb_{cpu}_main", cpu, isa, load,
                           info["size"], info["entry"], info["sha1"]) + code_copies(mp) + body
        (out / f"pkb_{cpu}_main.toml").write_text("\n".join(text))
        report[f"pkb_{cpu}_main"] = {"entries": n, "fora_do_intervalo": skipped}

    for ov in man["overlay9"]:
        key = f"ov9_{ov['id']:03d}"
        lo, hi = ov["ram"], ov["ram"] + ov["ram_size"]
        body, n = entries(banks.get(key, []), lambda x, lo=lo, hi=hi: lo <= x < hi)
        text = toml_header(f"Pokemon Black overlay {ov['id']}", f"pkb_{key}", "arm9", "armv5te",
                           lo, ov["ram_size"], lo, ov["sha1"]) + body
        (out / f"pkb_{key}.toml").write_text("\n".join(text))
        report[f"pkb_{key}"] = {"entries": n,
                                "fora_do_intervalo": len({x[0] for x in banks.get(key, [])}) - n}

    (out / "import_report.json").write_text(json.dumps(report, indent=1))
    tot = sum(r["entries"] for r in report.values())
    bad = {k: v["fora_do_intervalo"] for k, v in report.items() if v["fora_do_intervalo"]}
    print(f"OK: {len(report)} configs, {tot} entradas de função "
          f"(ARM9 {report['pkb_arm9_main']['entries']}, ARM7 {report['pkb_arm7_main']['entries']}, "
          f"overlays {tot - report['pkb_arm9_main']['entries'] - report['pkb_arm7_main']['entries']})")
    if bad:
        print(f"AVISO: rótulos fora do intervalo do banco: {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
