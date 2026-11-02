#!/bin/zsh
# M7: monta o app COM a tradução (local/traducao/ptbr) e roda a rota primeira_batalha só para tirar as telas
# (hashes vão diferir: o texto é outro). Telas a cada 400 quadros em local/rotas/traducao-ptbr/
# (local/traducao_debug.json = primeira_batalha com mais pontos; se não existir, usa a rota normal)
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
bash tools/build.sh || { echo; echo "O build falhou. Deixe esta janela aberta e avise o Claude."; exit 1; }
A="local/app/Pokemon Black.app/Contents"
[ -f local/traducao_debug.json ] || cp tests/routes/primeira_batalha.json local/traducao_debug.json
python3 tools/rota.py local/traducao_debug.json --runner "$A/MacOS/nds_runner" --rom "$A/Resources/cartucho.pkb" \
  --bancos "$A/Resources/banks" --saida local/rotas/traducao-ptbr 2>&1 | tee local/rotas/traducao-ptbr.txt
echo; echo "Terminado."; exit 0
