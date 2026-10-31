#!/usr/bin/env bash
# Barra de progresso para builds longos. Uso, dentro de outro script:
#   source tools/progresso.sh
#   TOTAL=8
#   etapa 1 "Baixando ferramentas"  comando args...
# Mostra: [1/8] título  ████████░░░░  45%  03:12  <última linha do log>
# O % vem das linhas do ninja (NINJA_STATUS) ou de "PROGRESSO n/t" impressas pelo comando.
# Log completo de cada etapa em local/logs/.
RAIZ="${RAIZ:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOGS="$RAIZ/local/logs"; mkdir -p "$LOGS"
export NINJA_STATUS="[%p %f/%t] "
[ -d "$HOME/.local/bin" ] && export PATH="$HOME/.local/bin:$PATH"
# Na VM cada sessão monta o projeto num caminho diferente (/sessions/<id>/...). Pastas de build do
# CMake guardam caminho absoluto: se o projeto "mudou de lugar", apaga a pasta de build (só em local/).
build_no_lugar() {  # build_no_lugar <pasta-de-build>
  local c="$1/CMakeCache.txt"
  if [ -f "$c" ] && ! grep -qF "$RAIZ/" "$c"; then echo "projeto mudou de caminho: refazendo $1"; rm -rf "$1"; fi
}
TOTAL="${TOTAL:-?}"
_barra() { local p=$1 n=$(( $1 / 5 )) s=""; for ((i=0;i<20;i++)); do ((i<n)) && s+="█" || s+="░"; done; printf '%s' "$s"; }
_tempo() { printf '%02d:%02d' $(( $1 / 60 )) $(( $1 % 60 )); }
etapa() {
  local n=$1 titulo=$2; shift 2
  set +e +o pipefail   # o laço da barra não pode derrubar o script
  local log="$LOGS/$(printf '%02d' "$n")-$(echo "$titulo" | tr ' A-Z' '-a-z' | tr -cd 'a-z0-9-').log"
  local t0=$SECONDS
  "$@" >"$log" 2>&1 & local pid=$!
  local largura=$(( $(tput cols 2>/dev/null || echo 100) - 60 )); (( largura < 10 )) && largura=10
  while kill -0 "$pid" 2>/dev/null; do
    local pct
    pct=$(grep -aoE '^\[ *[0-9]+%|PROGRESSO [0-9]+/[0-9]+' "$log" 2>/dev/null | tail -1 |
          awk '/PROGRESSO/{split($2,a,"/"); printf "%d", a[1]*100/a[2]; next} {gsub(/[^0-9]/,""); print}')
    local ult; ult=$(tail -1 "$log" 2>/dev/null | tr -d '\r' | cut -c1-"$largura")
    printf '\r\033[K[%s/%s] %-26.26s %s %4s  %s  %s' "$n" "$TOTAL" "$titulo" \
      "$(_barra "${pct:-0}")" "${pct:-…}%" "$(_tempo $((SECONDS - t0)))" "$ult"
    sleep 1
  done
  wait "$pid"; local rc=$?
  if (( rc == 0 )); then
    printf '\r\033[K[%s/%s] %-26.26s %s 100%%  %s  ok\n' "$n" "$TOTAL" "$titulo" "$(_barra 100)" "$(_tempo $((SECONDS - t0)))"
  else
    printf '\r\033[K[%s/%s] %-26.26s FALHOU (código %s) em %s — últimas linhas de %s:\n' \
      "$n" "$TOTAL" "$titulo" "$rc" "$(_tempo $((SECONDS - t0)))" "$log"
    tail -15 "$log"; exit "$rc"
  fi
  set -e -o pipefail
}
