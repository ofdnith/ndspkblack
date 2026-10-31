#!/usr/bin/env python3
"""Junta os PNG de uma rota (local/rotas/<rota>/) num mosaico com o número do quadro. Uso: tools/mosaico.py <rota> [de] [até]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parent.parent
rota = sys.argv[1]; de = int(sys.argv[2]) if len(sys.argv) > 2 else 0; ate = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
fs = [f for f in sorted((R / "local/rotas" / rota).glob("0*.png")) if de <= int(f.stem) <= ate]
W, H, cols = 170, 255, 7
img = Image.new("RGB", (cols * W, max(1, (len(fs) + cols - 1) // cols) * (H + 12)), "white"); d = ImageDraw.Draw(img)
for i, f in enumerate(fs):
    x, y = (i % cols) * W, (i // cols) * (H + 12)
    img.paste(Image.open(f).resize((W, H)), (x, y + 12)); d.text((x + 2, y), f.stem, fill="black")
out = R / "local/rotas" / rota / "mosaico.png"; img.save(out); print(len(fs), "quadros ->", out)
