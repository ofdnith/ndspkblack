#!/usr/bin/env bash
# Na VM nada roda em segundo plano depois que a chamada do shell termina. Este script avança um
# build do ninja por até N segundos (padrão 165) e para; rodar de novo continua de onde parou.
# Uso: tools/fatia.sh <pasta-de-build> [alvo] [segundos]
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"; export PATH="$HOME/.local/bin:$PATH"
export NINJA_STATUS="[%p %f/%t] "
timeout "${3:-165}" ninja -C "$1" -j "$(nproc)" ${2:-nds_runner} >> "$RAIZ/local/logs/fatia.log" 2>&1; rc=$?
grep -aE '^\[' "$RAIZ/local/logs/fatia.log" | tail -1 | cut -c1-40
grep -aE 'error:|FAILED' "$RAIZ/local/logs/fatia.log" | tail -3 | cut -c1-200
case $rc in 0) echo "PRONTO";; 124) echo "continua (fatia acabou)";; *) echo "ERRO rc=$rc";; esac
