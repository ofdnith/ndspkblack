#!/bin/zsh
# M7: recompila (runner com o patch 0009), confere que o app normal continua passando e roda o jogo
# com o cartucho de TESTE (todas as falas = "Teste PKB çãé"). Resultado em local/rotas/traducao-*.txt
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
bash tools/build.sh || { echo; echo "O build falhou. Deixe esta janela aberta e avise o Claude."; exit 1; }
A="local/app/Pokemon Black.app/Contents"
echo; echo "== 1/2 App normal: primeira_batalha (tem que PASSAR) =="
python3 tools/rota.py primeira_batalha --runner "$A/MacOS/nds_runner" --rom "$A/Resources/cartucho.pkb" \
  --bancos "$A/Resources/banks" 2>&1 | tee local/rotas/traducao-app-normal.txt
echo; echo "== 2/2 Cartucho de teste da tradução (hashes vão diferir: é texto novo) =="
python3 tools/rota.py primeira_batalha --ate 16700 --runner "$A/MacOS/nds_runner" --rom local/traducao/cartucho-teste.pkb \
  --bancos "$A/Resources/banks" --saida local/rotas/traducao-teste 2>&1 | tee local/rotas/traducao-teste.txt
echo; echo "Terminado."; exit 0
