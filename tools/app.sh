#!/usr/bin/env bash
# M6: monta local/app/Pokemon Black.app (só no Mac). Dados do cartucho embutidos (cartucho.pkb),
# 179 bancos nativos, SDL3 dentro do app, saves em ~/Library/Application Support/PokemonBlack.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"; cd "$RAIZ"
APP="local/app/Pokemon Black.app"; C="$APP/Contents"
rm -rf "$APP"; mkdir -p "$C/MacOS" "$C/Resources/banks" "$C/Frameworks"
echo "PROGRESSO 1/6"; python3 tools/empacotar.py rom/*.nds "$C/Resources/cartucho.pkb"
echo "PROGRESSO 2/6"; cp local/build/runner-sdl3/nds_runner "$C/MacOS/"; cp config/pokeblack.toml "$C/Resources/"
cp local/banks/darwin/*.dylib "$C/Resources/banks/"
SDL=$(otool -L "$C/MacOS/nds_runner" | awk '/libSDL3/{print $1}')
cp "$(realpath "$SDL")" "$C/Frameworks/libSDL3.0.dylib"
install_name_tool -id @rpath/libSDL3.0.dylib "$C/Frameworks/libSDL3.0.dylib"
install_name_tool -change "$SDL" @executable_path/../Frameworks/libSDL3.0.dylib "$C/MacOS/nds_runner"
echo "PROGRESSO 3/6"; python3 tools/icone.py "$C/Resources/cartucho.pkb" local/app/AppIcon.iconset
iconutil -c icns -o "$C/Resources/AppIcon.icns" local/app/AppIcon.iconset
cat > "$C/MacOS/PokemonBlack" <<'SH'
#!/bin/zsh
# Abre o jogo. Teclas: setas, Z=A, X=B, A=Y, S=X, Q=L, W=R, Enter=Start, Backspace=Select, mouse=toque.
# Menu de configurações: Esc (ou Guide / L3 no controle). Qualidade gráfica vale ao reabrir.
R="$(cd "$(dirname "$0")/.." && pwd)"
D="${PKB_DATA:-$HOME/Library/Application Support/PokemonBlack}"; mkdir -p "$D"; cd "$D"
export NDS_DEEP_TRACE=0 NDS_BANK_DIR="$R/Resources/banks"
while true; do
  rm -f "$D/reiniciar"
  Q=${PKB_QUALIDADE:-$(grep -s '^pkb_quality=' "$D/settings.ini" | tail -1 | cut -d= -f2)}
  case "$Q" in
    1) G=auto;    RES=2; AA=0 ;;   # baixo: 3D 2x
    2) G=auto;    RES=3; AA=4 ;;   # medio: 3D 3x + suavização 4
    3) G=auto;    RES=4; AA=8 ;;   # alto:  3D 4x + suavização 8
    *) G=soft;    RES=1; AA=0 ;;   # original: igual ao DS
  esac
  NDS_3D_RENDERER=$G "$R/MacOS/nds_runner" "$D" --interactive --rom "$R/Resources/cartucho.pkb" \
    --config "$R/Resources/pokeblack.toml" --save-path "$D/pokeblack.sav" \
    --runtime-settings-path "$D/settings.ini" --no-coverage-manifest \
    --internal-resolution $RES --antialiasing $AA \
    --freebios --generated-firmware --boot direct --player-name "${PKB_NOME:-$(id -un | cut -c1-10)}" --startup-mode automatic \
    2> "$D/ultimo.log"
  [ -f "$D/reiniciar" ] || break
done
SH
chmod +x "$C/MacOS/PokemonBlack"
cat > "$C/Info.plist" <<'PL'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
 <key>CFBundleName</key><string>Pokemon Black</string>
 <key>CFBundleDisplayName</key><string>Pokemon Black</string>
 <key>CFBundleIdentifier</key><string>local.ndspkblack.app</string>
 <key>CFBundleExecutable</key><string>PokemonBlack</string>
 <key>CFBundleIconFile</key><string>AppIcon</string>
 <key>CFBundlePackageType</key><string>APPL</string>
 <key>CFBundleShortVersionString</key><string>0.6</string>
 <key>CFBundleVersion</key><string>6</string>
 <key>LSMinimumSystemVersion</key><string>13.0</string>
 <key>NSHighResolutionCapable</key><true/>
 <key>LSApplicationCategoryType</key><string>public.app-category.games</string>
</dict></plist>
PL
echo "PROGRESSO 4/6"; codesign --force -s - "$C/Frameworks/libSDL3.0.dylib"; codesign --force -s - "$C/MacOS/nds_runner"
echo "PROGRESSO 5/6"; codesign --force -s - "$APP"
echo "PROGRESSO 6/6"; codesign --verify --verbose=1 "$APP" && du -sh "$APP"
echo "OK: $APP"
