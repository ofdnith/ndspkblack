#!/bin/zsh
# Ponto de entrada no Mac: duplo clique no Finder. Mostra cada etapa com barra de progresso.
# 1) instala o que faltar (Homebrew: cmake, ninja, SDL3)  2) gera e compila o jogo
# 3) monta local/app/Pokemon Black.app  4) roda as rotas de teste com o app. Para jogar: abrir o app
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
bash tools/build.sh "$@" || { echo; echo "O build falhou. Deixe esta janela aberta e avise o Claude."; exit 1; }
mkdir -p local/rotas
A="local/app/Pokemon Black.app/Contents"
echo; echo "== Rota primeira_batalha com o runner, o cartucho e os bancos de DENTRO do app (sem o .nds) =="
python3 tools/rota.py primeira_batalha --runner "$A/MacOS/nds_runner" --rom "$A/Resources/cartucho.pkb" \
  --bancos "$A/Resources/banks" 2>&1 | tee local/rotas/mac-app-primeira_batalha.txt
for r in $(cat local/rotas.txt 2>/dev/null); do
  python3 tools/rota.py $r --runner "$A/MacOS/nds_runner" --rom "$A/Resources/cartucho.pkb" --bancos "$A/Resources/banks" \
    $(grep "^$r " local/rotas-args.txt 2>/dev/null | cut -d" " -f2-) 2>&1 | tee local/rotas/mac-app-$r.txt
done
echo; echo "Terminado."; exit 0
