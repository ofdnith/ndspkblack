#!/usr/bin/env bash
# Build do port. Uso: tools/build.sh [--sdl NONE|SDL3] [--jobs N]
#   Padrão: SDL3 (janela) no macOS, NONE (sem janela, para rotas) no Linux.
# Etapas com barra de progresso; logs em local/logs/. Rodar de novo só refaz o que mudou.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"; export RAIZ
[ -d "$HOME/.local/bin" ] && export PATH="$HOME/.local/bin:$PATH"
for b in /opt/homebrew/bin /usr/local/bin; do [ -d $b ] && export PATH="$b:$PATH"; done
if [ "$(uname -s)" = Darwin ]; then SDL=SDL3; OVL=1; else SDL=NONE; OVL=0; fi  # VM: overlays só com --overlays (lento)
JOBS="$( (command -v nproc >/dev/null && nproc) || sysctl -n hw.ncpu 2>/dev/null || echo 4)"
while [ $# -gt 0 ]; do case "$1" in
  --sdl) SDL="$2"; shift 2;;
  --overlays) OVL=1; shift;; --sem-overlays) OVL=0; shift;; --jobs) JOBS="$2"; shift 2;;
  *) echo "argumento desconhecido: $1" >&2; exit 2;; esac; done

bash "$RAIZ/tools/setup.sh"
source "$RAIZ/tools/progresso.sh"
SHA1=26ad0b9967aa279c4a266ee69f52b9b2332399a5
TP="$RAIZ/third_party"; NDSR="$TP/ndsrecomp"; L="$RAIZ/local"
RECOMP="$L/build/$(uname -s | tr A-Z a-z)/recompiler/nds_recompile"
ROM="$(ls "$RAIZ"/rom/*.nds | head -1)"
GEN="$L/generated"; NOVO="$GEN/.novo"
PY="${PYTHON:-python3}"
APP=0; [ "$(uname -s)" = Darwin ] && APP=1
TOTAL=$((5 + OVL + APP))

extrair() { "$PY" -I "$RAIZ/tools/extract_rom.py" --rom "$ROM" --out "$L/extracted" && "$PY" -I "$RAIZ/tests/test_extract.py"; }
rotulos() { "$PY" -I "$RAIZ/tools/import_symbols.py" --extracted "$L/extracted" --out "$L/config"; }
sync_dir() {  # troca só arquivos que mudaram, para não recompilar à toa
  mkdir -p "$2"
  for f in "$1"/*; do cmp -s "$f" "$2/$(basename "$f")" || cp "$f" "$2/"; done
  for f in "$2"/*; do [ -e "$1/$(basename "$f")" ] || rm -f "$f"; done
}
gerar_c() {
  rm -rf "$NOVO"; mkdir -p "$NOVO/base" "$NOVO/title"
  echo "PROGRESSO 0/4"
  "$RECOMP" --config "$NDSR/bios/freebios9.toml" --bin "$NDSR/third_party/freebios/drastic_bios_arm9.bin" --out "$NOVO/base" --bank freebios_arm9
  echo "PROGRESSO 1/4"
  "$RECOMP" --config "$NDSR/bios/freebios7.toml" --bin "$NDSR/third_party/freebios/drastic_bios_arm7.bin" --out "$NOVO/base" --bank freebios_arm7
  echo "PROGRESSO 2/4"
  "$RECOMP" --config "$L/config/pkb_arm9_main.toml" --bin "$L/extracted/arm9.bin" --out "$NOVO/title" \
    --bank pkb_arm9_main --shards 48 --validate-live-bytes
  echo "PROGRESSO 3/4"
  "$RECOMP" --config "$L/config/pkb_arm7_main.toml" --bin "$L/extracted/arm7.bin" --out "$NOVO/title" \
    --bank pkb_arm7_main --shards 4 --validate-live-bytes
  sync_dir "$NOVO/base" "$GEN/base"; sync_dir "$NOVO/title" "$GEN/title"; rm -rf "$NOVO"
  echo "PROGRESSO 4/4"
}
RB="$L/build/runner-$(echo "$SDL" | tr 'A-Z' 'a-z')"
runner_cfg() {
  build_no_lugar "$RB"
  cmake -G Ninja -S "$NDSR/runner" -B "$RB" -DCMAKE_BUILD_TYPE=Release \
    -DNDS_SDL_BACKEND="$SDL" -DNDS_BOOTSTRAP_FIRMWARE=ON -DNDS_FREEBIOS_ONLY=ON \
    $( [ "$SDL" = SDL3 ] && echo "-DNDS_ENABLE_COMPUTE_RENDERER=ON -DNDS_ACCELERATED_RENDERER=OPENGL" \
                         || echo "-DNDS_ENABLE_COMPUTE_RENDERER=OFF" ) \
    -DNDS_GENERATED_DIR="$GEN/base" \
    -DNDS_RECOMP_UI_ROOT="$TP/recomp-ui" -DNDS_TITLE_BANK_DIR="$GEN/title" -DNDS_TITLE_ROM_SHA1="$SHA1"
}
runner() { cmake --build "$RB" -j "$JOBS" --target nds_runner; }
checar_bancos() {  # nenhuma biblioteca pode ter símbolo do próprio banco indefinido (dlopen falharia)
  local ruins=0 f
  for f in "$RAIZ"/local/banks/"$(uname -s | tr A-Z a-z)"/pkb_*; do
    if nm -u "$f" | grep -qE ' _?pkb_'; then echo "símbolo indefinido em $(basename "$f")"; ruins=$((ruins+1)); fi
  done
  echo "bancos checados: $(ls "$RAIZ"/local/banks/"$(uname -s | tr A-Z a-z)" | wc -l | tr -d ' '), com problema: $ruins"; [ "$ruins" = 0 ]
}
overlays() {  # M2: uma biblioteca por overlay em local/banks/<sistema>/ (carregadas pelo runner, patch 0005)
  local B="local/build/overlays-$(uname -s | tr A-Z a-z)"
  cd "$RAIZ" && "$PY" tools/overlays.py --fase c && ninja -f "$B/c.ninja" -j "$JOBS" &&
    "$PY" tools/overlays.py --fase lib && ninja -f "$B/lib.ninja" -j "$JOBS" && checar_bancos
}

etapa 1 "Extrair ROM"            extrair
etapa 2 "Rótulos da decomp"      rotulos
etapa 3 "Gerar C (ARM9+ARM7)"    gerar_c
etapa 4 "Configurar runner"      runner_cfg
etapa 5 "Compilar runner ($SDL)" runner
if [ "$OVL" = 1 ]; then etapa 6 "Overlays (177 módulos)" overlays; fi
if [ "$APP" = 1 ]; then etapa $((6 + OVL)) "App (Pokemon Black.app)" bash "$RAIZ/tools/app.sh"; fi
echo; echo "OK: runner em $RB/nds_runner"
