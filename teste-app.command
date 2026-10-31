#!/bin/zsh
# Abre o app com dados de teste em local/teste-app (log no projeto). Qualidade: argumento ou ALTO (3).
cd "$(dirname "$0")"
open -n --env PKB_DATA="$PWD/local/teste-app" --env PKB_QUALIDADE="${1:-3}" "local/app/Pokemon Black.app"
exit 0
