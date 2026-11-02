#!/usr/bin/env python3
"""M6: ROM -> cartucho.pkb (o "cartucho" embutido no app; o runner lê com o patch 0006).
"PKBCART1" | u64 tamanho original | u64 tamanho útil | SHA-1 do ORIGINAL | zlib(bytes úteis); o
enchimento 0xFF final não é guardado.
M7: --dados <rom-ptbr.nds> embute uma imagem com dados trocados (tools/texto.py aplicar). O cabeçalho
continua com o SHA-1 do original: o runner (patch 0009) usa essa identidade, então módulos nativos e
config do título continuam valendo.
Uso: tools/empacotar.py <rom.nds> <saida.pkb> [--dados <imagem.nds>]"""
import hashlib, struct, sys, zlib
from pathlib import Path
args = sys.argv[1:]; dados = None
if "--dados" in args: i = args.index("--dados"); dados = Path(args[i + 1]); del args[i:i + 2]
rom = Path(args[0]).read_bytes(); out = Path(args[1])
sha = hashlib.sha1(rom).digest()
assert sha.hex() == "26ad0b9967aa279c4a266ee69f52b9b2332399a5", "ROM errada"
if dados:
    img = dados.read_bytes()
    assert len(img) == len(rom), "imagem com dados trocados tem tamanho diferente do cartucho"
    assert img[:0x200] == rom[:0x200], "cabeçalho mudou: só dados (arquivos/FAT) podem mudar"
    rom = img
util = len(rom.rstrip(b"\xff"))
z = zlib.compress(rom[:util], 6)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(b"PKBCART1" + struct.pack("<QQ", len(rom), util) + sha + z)
print(f"OK: {out.name} — {len(rom)} bytes no cartucho, {util} úteis, {len(z)} comprimidos"
      + (f" (dados de {dados.name})" if dados else ""))
