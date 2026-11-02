#!/usr/bin/env python3
"""M7: gera uma "tradução" sintética para testar o pipeline sem texto real: toda linha vira
"Teste PKB çãé" mantendo os comandos {F000 ...} do original. Saída em local/traducao/teste/."""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import texto as t
rom = Path(t.rom_padrao()).read_bytes(); saida = t.RAIZ / "local/traducao/teste"; n = 0
for nome, (fid, narc) in t.narcs_da_rom(rom).items():
    d = saida / nome; d.mkdir(parents=True, exist_ok=True)
    for k, f in enumerate(t.narc_unpack(narc)[0]):
        out = []
        for j, cs in enumerate(t.txt_decode(f)[0]):
            if not cs: continue
            cmds = "".join(t.COMANDO.findall(t.chars_to_str(cs)))
            out.append(f"{j:04d}\tTeste PKB çãé{cmds}\n"); n += 1
        (d / f"{k:04d}.txt").write_text("".join(out), encoding="utf-8")
print(f"OK: {n} linhas de teste em {saida}")
