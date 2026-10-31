#!/usr/bin/env bash
# Fase 0: baixa as ferramentas fixadas, aplica nossos patches e compila o recompilador.
# Funciona no macOS e na VM Linux. Rodar de novo é seguro (pula o que já existe).
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"; export RAIZ
source "$RAIZ/tools/progresso.sh"
TP="$RAIZ/third_party"; NDSR="$TP/ndsrecomp"; BUILD="$RAIZ/local/build/$(uname -s | tr A-Z a-z)"  # recompilador: um por sistema (Linux na VM, Darwin no Mac)
JOBS="$( (command -v nproc >/dev/null && nproc) || sysctl -n hw.ncpu 2>/dev/null || echo 4)"
TOTAL=6

baixar() {  # baixar <pasta> <url> <commit>
  local dir="$TP/$1"
  if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD)" = "$(git -C "$dir" rev-parse "$3^{commit}" 2>/dev/null)" ]; then
    echo "já no commit $3"; return; fi
  rm -rf "$dir"; git init -q "$dir"; git -C "$dir" remote add origin "$2"
  git -C "$dir" fetch -q --depth 1 origin "$3"; git -C "$dir" checkout -q FETCH_HEAD
  git -C "$dir" submodule update --init --recursive --depth 1 2>&1 | tail -3 || true
  echo "ok $1 @ $3"
}
ferramentas() {
  mkdir -p "$TP"
  echo "PROGRESSO 0/3"; baixar ndsrecomp https://github.com/RetroPortingToolKit/ndsrecomp 2d9f4f3cb33daa78a724a1c17fdbcc2048580c2c
  echo "PROGRESSO 1/3"; baixar recomp-ui https://github.com/RetroPortingToolKit/recomp-ui 3f1d6f122a58823614abce14f5b86f4d165a629c
  echo "PROGRESSO 2/3"; baixar pokeblack https://github.com/squiddonaut/pokeblack 67d91a78b16caccbd4fbecdddf8a74c823d208a6
  echo "PROGRESSO 3/3"
}
patches() {
  for p in "$RAIZ"/patches/ndsrecomp/*.patch; do
    if git -C "$NDSR" apply --reverse --check "$p" 2>/dev/null; then echo "já aplicado: $(basename "$p")"
    else git -C "$NDSR" apply "$p" && echo "aplicado: $(basename "$p")"; fi
  done
}
rom() {
  local rom; rom=$(ls "$RAIZ"/rom/*.nds | head -1)
  local sha; sha=$( (command -v sha1sum >/dev/null && sha1sum "$rom") || shasum -a 1 "$rom"); sha=${sha%% *}
  [ "$sha" = 26ad0b9967aa279c4a266ee69f52b9b2332399a5 ] || { echo "ROM errada: $sha"; exit 1; }
  echo "ROM ok: $sha"
}
ferramentas_vm() {  # cmake/ninja na VM Linux via pip (o Mac usa os do Homebrew)
  if [ "$(uname -s)" = Darwin ]; then for b in /opt/homebrew/bin /usr/local/bin; do [ -d $b ] && PATH="$b:$PATH"; done
    command -v cmake >/dev/null && command -v ninja >/dev/null && brew list sdl3 >/dev/null 2>&1 && { echo "cmake, ninja e SDL3 ok"; return; }
  else command -v cmake >/dev/null && command -v ninja >/dev/null && { echo "cmake e ninja ok"; return; }; fi
  if [ "$(uname -s)" = Darwin ]; then
    command -v brew >/dev/null || { echo "falta o Homebrew (https://brew.sh)"; exit 1; }
    brew install cmake ninja sdl3; return; fi
  pip install --user --break-system-packages -q cmake ninja || pip install --user -q cmake ninja
}
recompilador() {
  build_no_lugar "$BUILD/recompiler"
  cmake -G Ninja -S "$NDSR/recompiler" -B "$BUILD/recompiler" -DCMAKE_BUILD_TYPE=Release
  cmake --build "$BUILD/recompiler" -j "$JOBS"
}
testes() { (cd "$BUILD/recompiler" && ctest --output-on-failure); }

etapa 1 "ROM (SHA-1)"            rom
etapa 2 "cmake e ninja"          ferramentas_vm
etapa 3 "Baixar ferramentas"     ferramentas
etapa 4 "Aplicar patches"        patches
etapa 5 "Compilar recompilador"  recompilador
etapa 6 "Testes do recompilador" testes
echo; echo "Fase 0 (ferramentas) ok. Recompilador: $BUILD/recompiler/nds_recompile"
