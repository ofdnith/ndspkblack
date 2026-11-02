#!/bin/zsh
# M7: tradução automática EN→PT-BR (Argos/CTranslate2) no Mac, retomável. Resultado em local/traducao/ptbr,
# revisão automática em local/traducao/revisao.tsv. Depois: build.command embute no app.
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH" PKB_THREADS=8
V=local/venv-traducao   # Python próprio (o do Homebrew não aceita pip install)
[ -x $V/bin/python3 ] || python3 -m venv $V
$V/bin/python3 -c "import ctranslate2, sentencepiece" 2>/dev/null || $V/bin/python3 -m pip install -q ctranslate2 sentencepiece
while true; do
  out=$($V/bin/python3 tools/traduzir_auto.py --segundos 600 2>&1); echo "$out" | tail -12
  echo "$out" | grep -q "continua" || break
done
echo; echo "Terminado."; exit 0
