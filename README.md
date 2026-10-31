# ndspkblack — static recompilation of Pokémon Black (DS) for macOS

**English** · [Português](README.pt-BR.md)

Tools that turn **your own Pokémon Black cartridge (Nintendo DS)** into a **native macOS app**
for Apple Silicon: `Pokemon Black.app`, launched with a double click, with saves, gamepad
support and high-resolution 3D.

> **This repository contains nothing from Nintendo, The Pokémon Company or Game Freak.** There is
> no ROM, no game code (original or translated), no graphics, music, text, BIOS, firmware or
> encryption keys here — only scripts, patches, configuration and documentation written for this
> project. The game is assembled **on your own machine** from a dump of **your own** cartridge.
> The resulting app contains game data: it is for **personal use only**. Do not distribute the
> app, the ROM or anything generated from it. Read [LEGAL.md](LEGAL.md) before using this project.

---

## Contents
1. [How it works](#how-it-works)
2. [Requirements](#requirements)
3. [Step-by-step setup](#step-by-step-setup)
4. [Playing](#playing)
5. [Settings menu](#settings-menu)
6. [Gamepads](#gamepads)
7. [Graphics and screen layouts](#graphics-and-screen-layouts)
8. [Saves](#saves)
9. [Tests (routes)](#tests-routes)
10. [Repository layout](#repository-layout)
11. [Project status](#project-status)
12. [Troubleshooting](#troubleshooting)
13. [Credits and licensing](#credits-and-licensing)

---

## How it works

The game's source code was never published; everything the game is lives inside the cartridge
as DS ARM machine code. Instead of emulating that code, this project **translates it ahead of
time** (static recompilation):

```
your cartridge (.nds) ──► extraction ──► ARM9, ARM7, 237 overlays, files
                              │
                              ▼
                  ndsrecomp (recompiler) ──► C (one C function per game function)
                              │
                              ▼
                  Apple clang ──► native ARM64 code (+ 179 libraries, one per overlay)
                              │
                              ▼
                  runtime ──► reimplements the DS hardware: 2D/3D video, sound, touch, save
                              │
                              ▼
                  Pokemon Black.app (SDL3, OpenGL)
```

- **ARM9** (main CPU) and **ARM7** (sound, touch) become native code. The ARM7 module runs
  copied to two RAM addresses; the build produces one bank for each.
- **Overlays** (code loaded on demand: overworld, battle, menus…) become separate libraries
  (`.dylib`) that the app loads at startup. The runtime picks the right function by checking
  the bytes currently in memory.
- Anything static analysis misses runs in a fallback interpreter. With the coverage seeds in
  `config/seeds/` that is well under 1% of what runs on the test route (~5 million ARM9
  instructions over 31,000 frames, down from ~750 million before the seeds).
- Video, sound, touch and save are **not** game code: the runtime reimplements them (derived
  from [melonDS](https://melonds.kuribo64.net/)).
- Community tools only: **FreeBIOS** and a synthesized firmware. No Nintendo SDK, BIOS or
  firmware is used or needed.

## Requirements

| What | Details |
|---|---|
| Mac | **Apple Silicon** (M1/M2/M3/M4), **macOS 13** or newer. Tested on a MacBook Air M2 |
| Disk space | ~10 GB free (generated C, objects and libraries in `local/`) |
| Apple tools | **Xcode Command Line Tools** (clang, git, python3): `xcode-select --install` |
| Homebrew | [brew.sh](https://brew.sh). The build installs `cmake`, `ninja` and `sdl3` by itself |
| Internet | The first time, to download the community tools (ndsrecomp, decomp, recomp-ui) |
| **Cartridge** | A dump of **your own** cartridge: Pokémon Black **USA/EUR v1.0** (NDSi Enhanced), code `IRBO`, 268,435,456 bytes, **SHA-1 `26ad0b9967aa279c4a266ee69f52b9b2332399a5`** |

The build checks the SHA-1 and refuses any other dump (other versions and languages have
different code, and the configuration here does not apply to them). This project does not
provide, link to or help you obtain a ROM. See [LEGAL.md](LEGAL.md).

To check your file in Terminal:
```sh
shasum -a 1 "path/to/your/PokemonBlack.nds"
```

## Step-by-step setup

1. **Clone** the repository (preferably in `~/Documents`, with no spaces in the path):
   ```sh
   cd ~/Documents
   git clone https://github.com/ofdnith/ndspkblack.git pokeblack-recomp
   cd pokeblack-recomp
   ```
2. **Put your cartridge dump** in the `rom/` folder (any name ending in `.nds`):
   ```sh
   cp "path/to/your/PokemonBlack.nds" rom/
   ```
3. **Run the build**: double-click `build.command` in Finder (or `./build.command` in Terminal).
   It shows every stage with a progress bar and a timer:

   | Stage | What it does | Time on an M2 (first run) |
   |---|---|---|
   | Tools | installs cmake/ninja/SDL3, downloads ndsrecomp/decomp/recomp-ui, applies `patches/`, builds and tests the recompiler | 2–5 min |
   | Extract ROM | splits ARM9, ARM7, overlays and files; checks them against `tests/golden/extract.json` | seconds |
   | Labels + seeds | writes each bank's configuration (decomp labels + `config/seeds/`) | seconds |
   | Generate C, build runner | ARM9 + ARM7 to C, then the runtime with SDL3/OpenGL | 2–5 min |
   | Overlays | 177 overlays + 2 ARM7 banks become 179 libraries | 10–15 min |
   | App | assembles `local/app/Pokemon Black.app` (embedded cartridge, icon, local signature) | ~1 min |
   | Test routes | plays by itself up to the first battle and checks the screens | 4–5 min |

   It should end with `primeira_batalha: PASSOU` ("first battle: passed"). Running the build
   again only redoes what changed.
4. **Open the game**: `local/app/Pokemon Black.app`. You can drag it to **Applications**; it no
   longer needs the `.nds` (the cartridge is embedded, compressed, inside the app).

> If macOS says `build.command` cannot be opened because of missing permissions, run
> `chmod +x *.command tools/*.sh tools/*.py` inside the folder.

## Playing

| DS | Keyboard |
|---|---|
| D-pad | arrow keys |
| A / B | Z / X |
| X / Y | S / A |
| L / R | Q / W |
| Start / Select | Enter / Backspace |
| Touch (bottom screen) | mouse |
| **Settings menu** | **Esc** |

The window title shows frames per second (60 = real DS speed).

## Settings menu

Open it with **Esc** (on a gamepad: the **Guide/Home** button or **left stick click, L3**; Start
stays free for the game). Navigate with the arrow keys; Enter confirms, Backspace goes back.
The menu labels are in Portuguese.

| Section | Option | Effect |
|---|---|---|
| **Gráficos** (Graphics) | Graphics quality | Original / Low / Medium / High (see below) |
| | Restart to apply | closes and reopens the game with the new quality (**save in-game first**) |
| **Tela** (Screen) | Layout | Stacked / Side by side / Large main screen — applies immediately |
| | Fullscreen | No / Yes — applies immediately |
| **Controle** (Gamepad) | DS A, DS B, … DS RIGHT | which gamepad button presses each DS button |
| | Restore defaults | resets the mapping |
| **Sistema** (System) | Back to game / Quit | |

Choices are stored in `~/Library/Application Support/PokemonBlack/settings.ini`.

## Gamepads

1. Pair the gamepad in **macOS Bluetooth settings** (System Settings → Bluetooth) or plug it in.
   Any gamepad SDL3 recognizes works: Xbox, PlayStation (DualShock 4 / DualSense), Switch Pro,
   8BitDo, etc.
2. Open the game — the gamepad is detected even if connected while the game is running.
3. Default mapping (by button position, Xbox layout):

   | Gamepad | DS |
   |---|---|
   | bottom face button (A on Xbox / ✕ on PS) | A |
   | right face button (B on Xbox / ○ on PS) | B |
   | left face button (X / □) | X |
   | top face button (Y / △) | Y |
   | LB / L1, RB / R1 | L, R |
   | Start/Menu/Options, Back/View/Share | Start, Select |
   | D-pad | D-pad |

4. To change it: **Esc → Controle**, pick the DS button and use ←/→ to choose which gamepad
   button presses it. If you prefer "A" on the right (Nintendo-style pads), swap DS A ↔ DS B.

## Graphics and screen layouts

> 🧪 The Low/Medium/High qualities, layouts and fullscreen are recent and still being tested.
> OpenGL has been confirmed on an M2 ("OpenGL 4.1 Metal / Apple M2", internal 3D at 1024×768);
> **Original** is the path proven by the test routes.

| Quality | What it does |
|---|---|
| **Original** | exactly like the DS: 256×192 per screen, software 3D |
| **Low** | 3D drawn at 2× (512×384) with OpenGL |
| **Medium** | 3D at 3× with anti-aliasing (4 samples) |
| **High** | 3D at 4× (1024×768) with maximum anti-aliasing (8 samples) |

2D (menus, text, sprites) is pixel art and stays at its original resolution; no option invents
texture detail the game does not have. macOS only offers OpenGL 4.1, and patch `0007` adapts
melonDS's OpenGL renderer to it; if OpenGL fails, the game falls back to software 3D.

| Layout | Use |
|---|---|
| **Stacked** | like the DS (top screen above the bottom one) |
| **Side by side** | both screens horizontally; better on wide monitors |
| **Large main screen** | top screen at 3× and the bottom one small on the right (16:9); best in fullscreen |

The mouse keeps touching the bottom screen in every layout.

## Saves

- Save normally through the game's own menu (X button → SAVE). The cartridge save (512 KB
  FLASH) lives at `~/Library/Application Support/PokemonBlack/pokeblack.sav`.
- **Back that file up** from time to time. The runtime's savestates (save anywhere) **do not
  work** with this game; use the in-game save.
- The app also keeps `settings.ini`, the console identity (`generated-identity.bin`) and the
  last session's log (`ultimo.log`) there, which is useful when reporting problems.

## Tests (routes)

Nothing counts as "working" without a test route: a list of button presses per frame that the
runner executes by itself, headless, comparing the SHA-1 of the screens with `tests/golden/`.
Only hashes are stored — never screenshots.

| Route | Proves |
|---|---|
| `boot_logos` | identical boot logos (13 checkpoints) |
| `title_screen` | title screen |
| `primeira_batalha` | intro, naming, starter Pokémon, the first two battles, back to the bedroom |
| `salvar_m4` | continues `primeira_batalha` and saves through the in-game menu |
| `carregar_m4` | starts from that save, Continue, and checks the screens match bit for bit |

```sh
python3 tools/rota.py primeira_batalha --runner "local/app/Pokemon Black.app/Contents/MacOS/nds_runner" \
  --rom "local/app/Pokemon Black.app/Contents/Resources/cartucho.pkb" \
  --bancos "local/app/Pokemon Black.app/Contents/Resources/banks"
```
Or double-click `rota.command` (runs the routes listed in `local/rotas.txt`).
Important details: routes pin the console MAC address (`--identity-mac`) because the game uses
it to seed its RNG (Pokémon stats), and they force software 3D, which is deterministic.

## Repository layout

| Path | Contents |
|---|---|
| `build.command` | full build + routes (double-click) |
| `rota.command`, `jogar.command`, `teste-app.command` | routes; play through the build's runner; app with test data |
| `tools/setup.sh` | downloads the pinned tools (ndsrecomp `2d9f4f3`, pokeblack decomp `67d91a7`, recomp-ui `3f1d6f1`), applies patches, builds and tests the recompiler |
| `tools/build.sh` | extraction → labels/seeds → C → runner → overlays → app |
| `tools/extract_rom.py`, `tools/import_symbols.py`, `tools/overlays.py` | extraction, bank configuration, building the 179 modules |
| `tools/empacotar.py`, `tools/icone.py`, `tools/app.sh` | embedded cartridge, icon (from the cartridge banner), `.app` assembly |
| `tools/rota.py`, `tools/mosaico.py` | route runner; contact sheet of a route's screenshots |
| `tools/verificar_publicacao.sh` | pre-publish check: refuses ROMs, saves, binaries, images and large files |
| `patches/ndsrecomp/0001–0008`, `patches/melonds/` | our runtime changes (list below; licenses in [`patches/LICENSES.md`](patches/LICENSES.md)) |
| `config/pokeblack.toml` | title configuration (512 KB FLASH save) |
| `config/seeds/` | coverage seeds (addresses of functions observed in the interpreter) |
| `tests/` | routes, expected hashes, extraction test |
| `docs/APRENDIZADOS.md` | pitfalls found so far (Portuguese) |
| `PLANO.md`, `PROGRESSO.md`, `LEIA-ME.md` | milestones, project log, quick overview (Portuguese) |
| `CLAUDE.md` | instructions for the AI assistant that works on the project (Portuguese) |
| `LEGAL.md`, `THIRD_PARTY.md`, `LICENSE`, `LICENSES/` | legal notice, third-party components, license texts |
| `rom/` | **your** `.nds` (ignored by git) |
| `local/` | everything generated: extraction, C, builds, libraries, app (ignored by git) |
| `third_party/` | tools downloaded by `setup.sh` (ignored by git) |

Patches on top of ndsrecomp:

| Patch | What it does |
|---|---|
| 0001 | FreeBIOS-only runner (no Nintendo BIOS banks) |
| 0002 | melonDS oracle without dumps (debugging) |
| 0003 | cartridge chip ID with the DSi bit |
| 0004 | runner builds on macOS |
| 0005 | loads overlay banks as libraries (`dlopen`) |
| 0006 | reads the embedded cartridge (`cartucho.pkb`) |
| 0007 | macOS OpenGL 4.1, Portuguese menu, gamepad mapping |
| 0008 | both screens in one OpenGL window, layouts, fullscreen |

## Project status

| Milestone | Status |
|---|---|
| M0 Tools | ✅ |
| M1 Native core (ARM9 + ARM7) | ✅ |
| M2 Overlays as modules | ✅ 177 native overlays |
| M3 Coverage | ✅ interpreter < 1% on the test route |
| M4 New game and saves | ✅ save → quit → reopen with the same state |
| M5 Beatable | ⏳ proven up to the first battle; the rest depends on playing |
| M6 Standalone app | ✅ `.app` without the `.nds` |
| HD graphics, layouts, fullscreen, gamepad | 🧪 implemented; being tested |

Out of scope: online play (GTS, Global Link, Dream World) and local multiplayer.

## Troubleshooting

- **"ROM errada"** (wrong ROM) during the build: the SHA-1 does not match. Only the USA/EUR
  v1.0 dump (`IRBO`) is supported.
- **Build fails at "cmake e ninja"**: install Homebrew and the Command Line Tools, then run it again.
- **"You do not have permission"** when opening a `.command`: `chmod +x *.command tools/*.sh`.
- **The game is slow or froze**: attach `~/Library/Application Support/PokemonBlack/ultimo.log`
  to your report — but never attach saves, ROMs or screenshots of copyrighted content.
- **Changed the quality and nothing happened**: use "Reiniciar para aplicar" (restart to apply)
  in the menu.

## Credits and licensing

Built only with community tools, **downloaded at build time and not included here**:
- [ndsrecomp](https://github.com/RetroPortingToolKit/ndsrecomp) — DS static recompiler and runtime
  (PolyForm Noncommercial 1.0.0 / MIT / GPL-3.0-or-later, depending on the part)
- [melonDS](https://github.com/melonDS-emu/melonDS) — basis of the hardware runtime and the OpenGL
  renderer (GPL-3.0-or-later)
- [pokeblack](https://github.com/squiddonaut/pokeblack) — community decompilation (only function
  labels and boundaries are used, at build time)
- [recomp-ui](https://github.com/RetroPortingToolKit/recomp-ui) — runtime UI (MIT)
- FreeBIOS (BSD-2-Clause), [SDL3](https://libsdl.org) (zlib)

**Licensing in short** (details in [THIRD_PARTY.md](THIRD_PARTY.md)):
- This project's own files (tools, configuration, tests, documentation) are under the
  **GPL-3.0** ([`LICENSE`](LICENSE)).
- Each patch in `patches/` is offered under the license of the upstream file it modifies
  (MIT, GPL-3.0-or-later or PolyForm Noncommercial 1.0.0); see
  [`patches/LICENSES.md`](patches/LICENSES.md).
- Because ndsrecomp is noncommercial, **this project as a whole may only be used for
  noncommercial purposes.**

Pokémon and Nintendo DS are trademarks of their respective owners. This project is not
affiliated with, endorsed by or sponsored by Nintendo, The Pokémon Company, Game Freak or
Creatures Inc. Trademarks are used only to identify the game the tools are compatible with.
