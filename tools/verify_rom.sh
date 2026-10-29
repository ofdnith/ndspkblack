#!/usr/bin/env bash
# Confere o dump de Pokémon Black contra o SHA-1 fixado do projeto.
# Uso: tools/verify_rom.sh [caminho.nds]   (padrão: local/rom/pokeblack.nds)
set -euo pipefail
EXPECTED_SHA1="26ad0b9967aa279c4a266ee69f52b9b2332399a5"
EXPECTED_SIZE=268435456
ROM="${1:-$(dirname "$0")/../local/rom/pokeblack.nds}"
[ -f "$ROM" ] || { echo "ERRO: ROM não encontrada: $ROM" >&2; exit 2; }
size=$(wc -c < "$ROM" | tr -d ' ')
if command -v sha1sum >/dev/null; then sha=$(sha1sum "$ROM" | cut -d' ' -f1)
else sha=$(shasum -a 1 "$ROM" | cut -d' ' -f1); fi
code=$(dd if="$ROM" bs=1 skip=12 count=4 2>/dev/null)
if [ "$sha" != "$EXPECTED_SHA1" ] || [ "$size" != "$EXPECTED_SIZE" ] || [ "$code" != "IRBO" ]; then
  echo "ERRO: dump não confere (sha1=$sha tamanho=$size código=$code)" >&2; exit 1
fi
echo "OK: IRBO $sha $size bytes"
