#!/usr/bin/env bash
# Build do zero do ndspkblack (Fase 1A): verifica a ROM, aplica patches,
# compila o recompilador, gera FreeBIOS e bancos do título, compila o runner.
#
# Uso: tools/bootstrap.sh [--rom caminho.nds] [--sdl NONE|SDL3|SDL2] [--jobs N]
#   Padrão: ROM em local/rom/pokeblack.nds, runner headless (NONE).
# Tudo que é gerado fica em local/ (ignorado pelo git).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ROM="$REPO/local/rom/pokeblack.nds"
SDL=NONE
JOBS="$( (command -v nproc >/dev/null && nproc) || sysctl -n hw.ncpu 2>/dev/null || echo 2)"
while [ $# -gt 0 ]; do
  case "$1" in
    --rom) ROM="$2"; shift 2;;
    --sdl) SDL="$2"; shift 2;;
    --jobs) JOBS="$2"; shift 2;;
    *) echo "argumento desconhecido: $1" >&2; exit 2;;
  esac
done

SHA1=26ad0b9967aa279c4a266ee69f52b9b2332399a5
NDSR="$REPO/third_party/ndsrecomp"
LOCAL="$REPO/local"
BUILD="$LOCAL/build"
GEN_BASE="$LOCAL/generated/base"
GEN_TITLE="$LOCAL/generated/title"
PY="${PYTHON:-python3}"
step() { printf '\n==> %s\n' "$*"; }

step "1/8 ROM"
"$REPO/tools/verify_rom.sh" "$ROM"
if [ "$ROM" != "$LOCAL/rom/pokeblack.nds" ]; then
  mkdir -p "$LOCAL/rom" && cp "$ROM" "$LOCAL/rom/pokeblack.nds"
fi

step "2/8 Submódulos"
git -C "$REPO" submodule update --init --recursive --depth 1

step "3/8 Patches sobre o ndsrecomp"
for p in "$REPO"/patches/ndsrecomp/*.patch; do
  [ -e "$p" ] || continue
  if git -C "$NDSR" apply --check "$p" 2>/dev/null; then
    git -C "$NDSR" apply "$p"; echo "aplicado: $(basename "$p")"
  elif git -C "$NDSR" apply --reverse --check "$p" 2>/dev/null; then
    echo "já aplicado: $(basename "$p")"
  else
    echo "ERRO: patch não aplica: $p" >&2; exit 1
  fi
done

step "4/8 Recompilador + testes"
cmake -G Ninja -S "$NDSR/recompiler" -B "$BUILD/recompiler" -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$BUILD/recompiler" -j "$JOBS"
(cd "$BUILD/recompiler" && ctest --output-on-failure)
RECOMP="$BUILD/recompiler/nds_recompile"

step "5/8 Extração da ROM (+ conferência com ndspy, se instalado)"
"$PY" -I "$REPO/tools/extract_rom.py" --rom "$LOCAL/rom/pokeblack.nds" --out "$LOCAL/extracted"
if "$PY" -c "import ndspy" 2>/dev/null; then
  "$PY" "$REPO/tools/crosscheck_extract.py" --rom "$LOCAL/rom/pokeblack.nds" --out "$LOCAL/extracted"
else
  echo "ndspy ausente: pulei a conferência (pip install ndspy)"
fi
"$PY" -I "$REPO/tests/test_extract.py"

step "6/8 Símbolos da decomp -> TOMLs"
"$PY" -I "$REPO/tools/import_symbols.py" --extracted "$LOCAL/extracted" --out "$LOCAL/config"

step "7/8 Geração de C (FreeBIOS + ARM9/ARM7 do jogo)"
rm -rf "$GEN_BASE" "$GEN_TITLE"; mkdir -p "$GEN_BASE" "$GEN_TITLE"
"$RECOMP" --config "$NDSR/bios/freebios9.toml" --bin "$NDSR/third_party/freebios/drastic_bios_arm9.bin" \
  --out "$GEN_BASE" --bank freebios_arm9
"$RECOMP" --config "$NDSR/bios/freebios7.toml" --bin "$NDSR/third_party/freebios/drastic_bios_arm7.bin" \
  --out "$GEN_BASE" --bank freebios_arm7
"$RECOMP" --config "$LOCAL/config/pkb_arm9_main.toml" --bin "$LOCAL/extracted/arm9.bin" \
  --out "$GEN_TITLE" --bank pkb_arm9_main --shards 48
"$RECOMP" --config "$LOCAL/config/pkb_arm7_main.toml" --bin "$LOCAL/extracted/arm7.bin" \
  --out "$GEN_TITLE" --bank pkb_arm7_main --shards 4

step "8/8 Runner (SDL=$SDL) com bancos do título"
RB="$BUILD/runner-title-$(echo "$SDL" | tr 'A-Z' 'a-z')"
cmake -G Ninja -S "$NDSR/runner" -B "$RB" -DCMAKE_BUILD_TYPE=Release \
  -DNDS_SDL_BACKEND="$SDL" -DNDS_BOOTSTRAP_FIRMWARE=ON -DNDS_FREEBIOS_ONLY=ON \
  -DNDS_ENABLE_COMPUTE_RENDERER=OFF \
  -DNDS_GENERATED_DIR="$GEN_BASE" -DNDS_RECOMP_UI_ROOT="$REPO/third_party/recomp-ui" \
  -DNDS_TITLE_BANK_DIR="$GEN_TITLE" -DNDS_TITLE_ROM_SHA1="$SHA1" >/dev/null
cmake --build "$RB" -j "$JOBS" --target nds_runner

echo
echo "OK: runner em $RB/nds_runner"
echo "Rodar: $RB/nds_runner local/run 200000000 --rom local/rom/pokeblack.nds --no-save \\"
echo "         --freebios --generated-firmware --boot direct"
