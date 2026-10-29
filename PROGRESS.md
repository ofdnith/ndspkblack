# PROGRESS.md — diário

Formato: data · fase · o que mudou · evidência · o que quebrou · próximo passo.

## 2026-10-29 · Fase 0 → 1A (sessão 1)

**Ambiente testado.** Push no repo (privado, `main`); pasta do Mac conectada
(ler/escrever/mover ok; apagar bloqueado por padrão — arquivo de teste movido para
`_to_delete/`); cópia da ROM para o workspace; VM Linux aarch64 do Mac com rede, `pip`,
`g++` (sem sudo).

**Feito**
- Estrutura: CLAUDE.md, PLAN.md, PROGRESS.md, .gitignore; submódulos fixados:
  ndsrecomp `2d9f4f3` (v0.6.10), pokeblack `67d91a7`, recomp-ui `3f1d6f1`.
- `tools/verify_rom.sh`: dump confere — `IRBO`, SHA-1 `26ad0b99…99a5`, 268.435.456 bytes.
- Recompilador: build + **ctest 6/6** no workspace (x86-64) **e** na VM aarch64 do Mac
  (gcc 11). Ainda falta macOS nativo (precisa Xcode CLT/Homebrew no Mac).
- Patch `0001-freebios-only-build`: runner sem bancos da BIOS Nintendo; recusa rodar sem
  `--freebios --generated-firmware --boot direct` (testado: recusa sem flags).
- `tools/extract_rom.py`: ARM9 (BLZ, 0xA67C0), ARM7, **237 overlays (229 BLZ)**,
  247 arquivos, parâmetros de módulo e autoloads (ARM9: 4, ARM7: 2).
  **Conferido byte a byte contra o ndspy** (`tools/crosscheck_extract.py`) e com golden
  de hashes (`tests/golden/extract.json`, `tests/test_extract.py`).
- `tools/import_symbols.py`: 29.020 entradas de função da decomp → TOMLs em `local/config/`
  (ARM9 3.941, ARM7 301, overlays 24.778; overlay 93 vem de `asm/battle_*.s`).
- Primeira passada do `nds_recompile`: ARM9 principal **18.971 funções** (154 indefinidas),
  ARM7 **1.514** (5 indefinidas), sem erro; 48 + 4 shards.
- Oráculo melonDS 1.0rc compilado com patch próprio `0002-oracle-nodump-direct-boot`
  (+ `patches/melonds/0001-oracle-accessors`; ordem de patches upstream corrigida).
- `tools/probe_frames.py`: hashes de quadro pelo protocolo TCP (oráculo e nativo).

**Evidência de paridade (runner nativo SÓ com interpretador, sem bancos do título)**
vs oráculo, ambos FreeBIOS + firmware gerado + boot direto:
- Telas A e B **idênticas bit a bit** nos VBlanks 60, 120, 180, 300, 450, 600, 610
  (tela branca → logos The Pokémon Company/Nintendo → fade).
- Primeira tela diferente: **VBlank 612** (início da animação 3D da Game Freak).
- RAM principal já difere no VBlank 1 em 103 palavras: apelido do perfil do firmware
  gerado, CRC do perfil, **chip ID do cartucho** (`0x4000FFC2` melonDS × `0x0000FFC2`
  nativo, em 0x023FF800/0x023FFC00) e valores de pilha/tempo.

**M1 comprovado (tag `m1-build`)**
- `tools/bootstrap.sh` num **clone limpo** do repositório: exit 0 em 18 min (ROM → testes do
  recompilador 6/6 → extração conferida com ndspy e golden → 29.020 símbolos → C gerado →
  runner headless com bancos do título).
- C gerado **determinístico**: hash agregado `4ee04eafa7e1ee22…` igual nos dois builds;
  virou golden (`tests/golden/generated_c.sha1`, `tests/test_codegen.sh`, roda no bootstrap).

**Quebrado / atenção**
- `savestate_test` upstream não linka (`nds_performance_execution`); compilamos só `nds_runner`.
- O shim do oráculo upstream depende de patches do melonDS que nunca foram publicados;
  supridos pelo nosso `patches/melonds/0001`.
- O `ndsref` usado upstream para jogos é privado; usamos o `nds_oracle` com patch.
- 60 overlays sem rótulos na decomp (provavelmente só dados).
- **Runner com bancos do título**: o C gerado do ARM9/ARM7 **compila e linka** (164 alvos,
  20 min com 2 núcleos, binário de 65 MB) e os bancos são registrados para o SHA-1 certo.
  **Mas não executa corretamente**: fica preso antes do VBlank 60 num laço que lê o
  endereço inválido `0x600000D2` (ARM9). O mesmo jogo pelo interpretador chega a 610 VBlanks
  idênticos ao oráculo, então o defeito está no código recompilado (função mal delimitada,
  dado tratado como código, ou codegen). É o bug nº 1 da Fase 2.

**Próximo passo**
1. Resta da Fase 1A só o build no macOS nativo (você: Xcode CLT + Homebrew
   `cmake ninja python sdl3`; depois `tools/bootstrap.sh --sdl SDL3`).
2. Fase 2, primeiros alvos: (a) **laço em `0x600000D2` com bancos do título** — achar a
   função recompilada culpada (trace da PC + `dispatch_misses.log`), corrigir no TOML/importador;
   (b) alinhar firmware gerado e chip ID entre nativo e oráculo para zerar a diferença de RAM
   no VBlank 1; (c) primeira divergência de tela no 612.
3. Fase 1B: app mínimo de PS5 baseado na estrutura do ProsperoLight (o boilerplate
   original saiu do ar).
