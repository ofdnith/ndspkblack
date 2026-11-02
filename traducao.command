#!/bin/zsh
# M7: 1) baixa o modelo de tradução open source (Argos Translate en→pt-BR) para local/argos (a VM não
# alcança o site); 2) recompila e testa (app normal + cartucho de teste da tradução).
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ ! -d local/argos/model ] && ! ls -d local/argos/*/model >/dev/null 2>&1; then
  echo "== Baixando modelo Argos en→pt-BR =="
  mkdir -p local/argos && curl -fL --progress-bar https://argos-net.com/v1/translate-en_pb-1_9.argosmodel -o local/argos/en_pb.zip \
    && (cd local/argos && unzip -o -q en_pb.zip && rm en_pb.zip) && echo "modelo ok" || echo "FALHOU o download do modelo"
fi
exec ./traducao-teste.command
