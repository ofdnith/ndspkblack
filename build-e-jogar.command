#!/bin/zsh
# Reconstrói tudo (com a tradução de local/traducao/ptbr, se existir) e abre o Pokemon Black.app para jogar.
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
bash tools/build.sh || { echo; echo "O build falhou. Deixe esta janela aberta e avise o Claude."; exit 1; }
echo; echo "== Abrindo o jogo =="; open "local/app/Pokemon Black.app"
echo "Terminado."; exit 0
