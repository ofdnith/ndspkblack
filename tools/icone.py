#!/usr/bin/env python3
"""Ícone do app a partir do banner do cartucho (32x32, 4bpp) -> pasta .iconset (PNG puro, sem Pillow).
Uso: tools/icone.py <rom.nds|cartucho.pkb> <saida.iconset>"""
import struct, sys, zlib
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2])
data = src.read_bytes()
if data[:8] == b"PKBCART1":
    data = zlib.decompress(data[44:])
ban = struct.unpack_from("<I", data, 0x68)[0]
bmp, pal = data[ban + 0x20: ban + 0x220], data[ban + 0x220: ban + 0x240]
cores = []
for i in range(16):
    c = struct.unpack_from("<H", pal, i * 2)[0]
    cores.append(((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31, 0 if i == 0 else 255))
px = [[None] * 32 for _ in range(32)]
for t in range(16):
    tx, ty = (t % 4) * 8, (t // 4) * 8
    for y in range(8):
        for x in range(8):
            b = bmp[t * 32 + y * 4 + x // 2]
            px[ty + y][tx + x] = cores[(b >> 4) if x & 1 else (b & 15)]
def png(n, path):
    raw = b"".join(b"\x00" + b"".join(bytes(px[y * 32 // n][x * 32 // n]) for x in range(n)) for y in range(n))
    blk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + blk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0)) + blk(b"IDAT", zlib.compress(raw, 9)) + blk(b"IEND", b""))
out.mkdir(parents=True, exist_ok=True)
for s in (16, 32, 128, 256, 512):
    png(s, out / f"icon_{s}x{s}.png"); png(s * 2, out / f"icon_{s}x{s}@2x.png")
print("OK ícone:", out)
