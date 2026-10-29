#!/usr/bin/env python3
"""Confere a saída do extract_rom.py contra o ndspy (implementação independente
da comunidade): ARM9 descomprimido, ARM7, cada overlay e cada arquivo.
Uso: tools/crosscheck_extract.py [--rom ...] [--out local/extracted]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import ndspy.code
import ndspy.codeCompression
import ndspy.rom

REPO = Path(__file__).resolve().parent.parent


def h(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default=str(REPO / "local/rom/pokeblack.nds"))
    ap.add_argument("--out", default=str(REPO / "local/extracted"))
    a = ap.parse_args()
    out = Path(a.out)
    man = json.loads((out / "manifest.json").read_text())
    rom = ndspy.rom.NintendoDSRom.fromFile(a.rom)
    bad = 0

    arm9 = ndspy.codeCompression.decompress(rom.arm9)
    if h(arm9) != man["arm9"]["sha1"]:
        print(f"DIVERGE arm9: ndspy {h(arm9)} vs nosso {man['arm9']['sha1']}"); bad += 1
    if h(rom.arm7) != man["arm7"]["sha1"]:
        print("DIVERGE arm7"); bad += 1

    ovs = rom.loadArm9Overlays()
    if len(ovs) != len(man["overlay9"]):
        print(f"DIVERGE contagem overlays {len(ovs)} vs {len(man['overlay9'])}"); bad += 1
    for o in man["overlay9"]:
        theirs = h(ovs[o["id"]].data)
        if theirs != o["sha1"]:
            print(f"DIVERGE overlay {o['id']}"); bad += 1

    n = 0
    for fid, data in enumerate(rom.files):
        path = rom.filenames.filenameOf(fid)
        if path is None:
            continue
        mine = (out / "data" / path)
        if not mine.exists() or h(mine.read_bytes()) != h(data):
            print(f"DIVERGE arquivo {fid} {path}"); bad += 1
        n += 1

    print(("OK" if bad == 0 else f"FALHOU ({bad})") +
          f": arm9, arm7, {len(man['overlay9'])} overlays, {n} arquivos conferidos com ndspy")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
