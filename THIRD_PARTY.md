# Third-party components and licenses

**None of the components below is included in this repository.** `tools/setup.sh` downloads them
at build time, at pinned commits, into `third_party/` (ignored by git). They keep their own
licenses; nothing here relicenses them.

| Component | Source (pinned commit) | License | How it is used |
|---|---|---|---|
| ndsrecomp | github.com/RetroPortingToolKit/ndsrecomp (`2d9f4f3`) | Own code: **PolyForm Noncommercial 1.0.0**. `runner/src/`, `recompiler/armv4t/`, `recompiler/support/`, `oracle/`: **MIT**. `runner/vendor/melonds/`, `runner/src/melonds_compute/`, `runner/src/frontend.cpp`, `oracle/patches/`: **GPL-3.0-or-later** | recompiler and runtime; patched by `patches/ndsrecomp/` |
| melonDS (vendored inside ndsrecomp) | github.com/melonDS-emu/melonDS | GPL-3.0-or-later | hardware runtime and OpenGL renderer |
| FreeBIOS (submodule of ndsrecomp) | github.com/mstan/freebios (mirror of melonDS `freebios/`, DraStic BIOS replacement by Gilead Kutnick) | BSD-2-Clause | open replacement for the DS BIOS |
| arm-recomp-core (submodule of ndsrecomp) | github.com/mstan/arm-recomp-core | its own license | recompiler core |
| recomp-ui | github.com/RetroPortingToolKit/recomp-ui (`3f1d6f1`) | MIT | runtime UI |
| pokeblack decompilation | github.com/squiddonaut/pokeblack (`67d91a7`) | no license file | read at build time for function labels and boundaries only; nothing from it is redistributed |
| SDL3 | installed by Homebrew | zlib | window, input, audio |

License texts: [`LICENSE`](LICENSE) and [`LICENSES/GPL-3.0.txt`](LICENSES/GPL-3.0.txt) (GPL-3.0),
[`LICENSES/MIT-ndsrecomp.txt`](LICENSES/MIT-ndsrecomp.txt) (MIT, ndsrecomp) and
[`LICENSES/PolyForm-Noncommercial-1.0.0.txt`](LICENSES/PolyForm-Noncommercial-1.0.0.txt)
(PolyForm Noncommercial 1.0.0, including ndsrecomp's scope notes).

## What this means for you

- **Noncommercial only.** ndsrecomp's own code is under PolyForm Noncommercial 1.0.0
  (<https://polyformproject.org/licenses/noncommercial/1.0.0>), Copyright (c) 2026 Matthew
  Stanley. Personal, hobby, study and other noncommercial uses are allowed; commercial use needs
  a separate license from its author.
- **The built runner is GPL-3.0-or-later.** `nds_runner` links melonDS code, so the binary inside
  `Pokemon Black.app` is a GPL-3.0-or-later combined work. That matters only if you distribute
  it — and the app must not be distributed anyway, because it also contains game data
  ([LEGAL.md](LEGAL.md)).

## This project's own files

Tools, configuration, seeds, test routes and hashes, and documentation written for this project
are under the **GPL-3.0** ([`LICENSE`](LICENSE)). Patches follow the license of the file they
modify: see [`patches/LICENSES.md`](patches/LICENSES.md).
