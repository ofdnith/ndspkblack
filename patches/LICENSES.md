# Patch licenses

Each patch modifies files of an upstream project. The changes in a patch are offered under the
**same license as the upstream file they modify** (see [`../THIRD_PARTY.md`](../THIRD_PARTY.md)).
The diff context lines are upstream code, under upstream's license.

| Patch | Upstream files | License |
|---|---|---|
| `melonds/0001-oracle-accessors.patch` | melonDS `src/NDS.h` | GPL-3.0-or-later |
| `ndsrecomp/0001-freebios-only-build.patch` | `runner/CMakeLists.txt` · `runner/src/main.cpp` | PolyForm Noncommercial 1.0.0 · MIT |
| `ndsrecomp/0002-oracle-nodump-direct-boot.patch` | `oracle/shim/nds_oracle.cpp` | MIT |
| `ndsrecomp/0003-cart-chip-id-dsi-bit.patch` | `runner/src/io.cpp` | MIT |
| `ndsrecomp/0004-macos-live-overlay-toolchain.patch` | `runner/src/live_overlay_platform.cpp` | MIT |
| `ndsrecomp/0005-pkb-overlay-banks-dlopen.patch` | `runner/CMakeLists.txt` · `runner/src/main.cpp`, `runner/src/pkb_overlay_banks.{cpp,h}` (new) | PolyForm Noncommercial 1.0.0 · MIT |
| `ndsrecomp/0006-pkb-cartucho-embutido.patch` | `runner/CMakeLists.txt` · `runner/src/main.cpp`, `runner/src/pkb_overlay_banks.{cpp,h}` | PolyForm Noncommercial 1.0.0 · MIT |
| `ndsrecomp/0007-pkb-opengl41-menu-controle.patch` | `runner/src/frontend.cpp`, `runner/src/melonds_compute/*` | GPL-3.0-or-later |
| `ndsrecomp/0008-pkb-layouts-tela-cheia-hd-janela-unica.patch` | `runner/src/frontend.cpp`, `runner/src/melonds_compute/*` | GPL-3.0-or-later |

## Upstream notices

- **ndsrecomp** — Copyright (c) 2026 Matthew Stanley. Own code licensed under the PolyForm
  Noncommercial License 1.0.0, <https://polyformproject.org/licenses/noncommercial/1.0.0>
  (full text: [`../LICENSES/PolyForm-Noncommercial-1.0.0.txt`](../LICENSES/PolyForm-Noncommercial-1.0.0.txt));
  runner and oracle trees under the MIT License
  ([`../LICENSES/MIT-ndsrecomp.txt`](../LICENSES/MIT-ndsrecomp.txt)); melonDS-derived files under
  GPL-3.0-or-later ([`../LICENSES/GPL-3.0.txt`](../LICENSES/GPL-3.0.txt)).
- **melonDS** — Copyright the melonDS team, GPL-3.0-or-later.
