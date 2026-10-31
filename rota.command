#!/bin/zsh
# Roda no Mac (sem janela) as rotas listadas em local/rotas.txt (uma por linha; padrão primeira_batalha).
# Resultado em local/rotas/mac-<rota>.txt
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
[ -f local/rotas.txt ] || echo primeira_batalha > local/rotas.txt
A="local/app/Pokemon Black.app/Contents"   # usa o runner, o cartucho e os bancos de dentro do app
for r in $(cat local/rotas.txt); do
  echo "== Rota $r =="; python3 tools/rota.py $r --runner "$A/MacOS/nds_runner" --rom "$A/Resources/cartucho.pkb" --bancos "$A/Resources/banks" $(grep -q "^$r " local/rotas-args.txt 2>/dev/null && grep "^$r " local/rotas-args.txt | cut -d" " -f2-) 2>&1 | tee local/rotas/mac-$r.txt
done
echo; echo "Terminado."; exit 0
