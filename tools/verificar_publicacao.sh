#!/usr/bin/env bash
# Confere o que seria publicado: nada derivado do cartucho, nada binário, nada grande.
# Uso: tools/verificar_publicacao.sh   (opcional: PKB_PRIVADO='palavra1|palavra2' para barrar
# nomes ou e-mails pessoais). Funciona com ou sem git; compatível com o bash 3.2 do macOS.
set -euo pipefail
cd "$(dirname "$0")/.."
erros=0
falha() { echo "  ✗ $1: $2"; erros=$((erros + 1)); }

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  lista() { git ls-files -co --exclude-standard; }
else  # pasta sem git: mesma regra do .gitignore
  lista() { find . -type f ! -path './.git/*' ! -path './rom/*' ! -path './local/*' \
    ! -path './third_party/*' ! -path '*/__pycache__/*' ! -name .DS_Store | sed 's|^\./||'; }
fi

n=0
while IFS= read -r f; do
  n=$((n + 1))
  case "$f" in
    rom/LEIA.txt) ;;
    rom/*|local/*|third_party/*) falha "pasta proibida" "$f"; continue ;;
  esac
  m=$(printf '%s' "$f" | tr 'A-Z' 'a-z')
  case "$m" in
    *.nds|*.srl|*.dsi|*.sav|*.dsv|*.pkb|*.bin|*.narc|*.sdat|*.dylib|*.so|*.o|*.a|*.app/*|*.dmg|\
    *.zip|*.7z|*.rar|*.png|*.jpg|*.jpeg|*.gif|*.bmp|*.mp4|*.mov|*.wav|*.mp3|*.ogg|*.icns)
      falha "tipo proibido" "$f"; continue ;;
  esac
  [ -f "$f" ] || continue
  [ "$(wc -c <"$f")" -le 1048576 ] || falha "maior que 1 MB" "$f"
  tr -d '\000' <"$f" | cmp -s - "$f" || falha "conteúdo binário" "$f"
  if [ -n "${PKB_PRIVADO:-}" ] && grep -qiE "$PKB_PRIVADO" "$f"; then falha "dado pessoal" "$f"; fi
done < <(lista)

if [ "$erros" -eq 0 ]; then echo "OK: $n arquivos conferidos, nada proibido."
else echo "BARRADO: $erros problema(s) em $n arquivos. Nada disso pode ser publicado."; exit 1; fi
