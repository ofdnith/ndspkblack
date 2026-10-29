#!/usr/bin/env python3
"""Sonda de quadros pelo protocolo TCP do ndsrecomp (TCP.md).

Funciona contra o oráculo (nds_oracle, porta 19843) e contra o runner nativo
(nds_runner --serve, porta 19842). Avança até cada VBlank do ARM9 pedido e
imprime, para as duas telas (motores A e B), o SHA-1 dos pixels RGB e a
quantidade de pixels não pretos. Opcionalmente salva PNGs em local/captures/
(fora do git) para olhar.

Uso:
  tools/probe_frames.py --port 19843 --at 60,120,180,300 [--png local/captures/oracle]
  tools/probe_frames.py --port 19842 --at 60,120 --reset
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import struct
import sys
import zlib
from pathlib import Path


class Client:
    def __init__(self, port: int, timeout: float = 600.0):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        self.f = self.s.makefile("rw")

    def cmd(self, **kw):
        self.f.write(json.dumps(kw) + "\n")
        self.f.flush()
        line = self.f.readline()
        if not line:
            raise RuntimeError("conexão fechada")
        return json.loads(line)


def write_png(path: Path, w: int, h: int, rgb: bytes) -> None:
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--at", required=True, help="lista de VBlanks do ARM9, ex. 60,120,180")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--png", help="prefixo para salvar PNGs (use local/...)")
    ap.add_argument("--stall", type=int, default=300000)
    a = ap.parse_args()
    c = Client(a.port)
    if a.reset:
        c.cmd(cmd="reset")
    for n in [int(x) for x in a.at.split(",")]:
        r = c.cmd(cmd="run_to_event", event="vblank9", count=n, stall=a.stall)
        if not r.get("reached", False):
            print(f"vblank9={n}: NÃO ALCANÇADO {json.dumps(r)[:200]}")
            return 1
        parts = []
        for eng in ("A", "B"):
            fb = c.cmd(cmd="framebuffer", engine=eng)
            rgb = bytes.fromhex(fb["rgb"])
            lit = sum(1 for i in range(0, len(rgb), 3) if rgb[i] | rgb[i + 1] | rgb[i + 2])
            parts.append(f"{eng} sha1={hashlib.sha1(rgb).hexdigest()[:16]} acesos={lit:5d}")
            if a.png:
                write_png(Path(f"{a.png}_v{n:05d}_{eng}.png"), fb["w"], fb["h"], rgb)
        print(f"vblank9={n:5d}  " + "  ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
