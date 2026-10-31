#!/usr/bin/env python3
"""M6: ROM -> cartucho.pkb (o "cartucho" embutido no app; o runner lê com o patch 0006).
"PKBCART1" | u64 tamanho original | u64 tamanho útil | SHA-1 | zlib(bytes úteis); o enchimento 0xFF
final não é guardado. Uso: tools/empacotar.py <rom.nds> <saida.pkb>"""
import hashlib, struct, sys, zlib
from pathlib import Path
rom = Path(sys.argv[1]).read_bytes(); out = Path(sys.argv[2])
util = len(rom.rstrip(b"\xff"))
sha = hashlib.sha1(rom).digest()
assert sha.hex() == "26ad0b9967aa279c4a266ee69f52b9b2332399a5", "ROM errada"
z = zlib.compress(rom[:util], 6)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(b"PKBCART1" + struct.pack("<QQ", len(rom), util) + sha + z)
print(f"OK: {out.name} — {len(rom)} bytes no cartucho, {util} úteis, {len(z)} comprimidos")
