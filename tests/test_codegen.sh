#!/usr/bin/env bash
# Regressão do C gerado: hash agregado de local/generated/{base,title}/*.{c,h}
# contra tests/golden/generated_c.sha1. Muda se o recompilador, os TOMLs/símbolos
# ou a ROM mudarem. --update regrava o golden.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cur=$(cd "$REPO/local/generated" && find . -type f \( -name '*.c' -o -name '*.h' \) | LC_ALL=C sort \
      | xargs sha1sum | sha1sum | cut -d' ' -f1)
if [ "${1:-}" = "--update" ]; then echo "$cur" > "$REPO/tests/golden/generated_c.sha1"; echo "golden atualizado: $cur"; exit 0; fi
want=$(cat "$REPO/tests/golden/generated_c.sha1")
[ "$cur" = "$want" ] && echo "OK C gerado bate com o golden ($cur)" || { echo "FALHOU: C gerado $cur ≠ golden $want"; exit 1; }
