#!/usr/bin/env bash
# Abre o jogo na janela (runner SDL3 do Mac). Save em local/saves/.
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"; R="$RAIZ/local/build/runner-sdl3"
mkdir -p "$RAIZ/local/saves"
cd "$R" && NDS_DEEP_TRACE=0 NDS_BANK_DIR="$RAIZ/local/banks/$(uname -s | tr A-Z a-z)" ./nds_runner "$R" --interactive --rom "$(ls "$RAIZ"/rom/*.nds | head -1)" \
  --config "$RAIZ/config/pokeblack.toml" --save-path "$RAIZ/local/saves/pokeblack.sav" \
  --freebios --generated-firmware --boot direct --player-name "${PKB_NOME:-$(id -un | cut -c1-10)}" --startup-mode automatic \
  2>&1 | tee "$RAIZ/local/logs/jogar.log" | tail -20
