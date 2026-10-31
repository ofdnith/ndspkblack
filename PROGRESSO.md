# PROGRESSO.md — diário

Formato: data · fase · o que mudou · prova · próximo passo. Decisões em uma linha.

## 2026-10-30 · Recomeço do zero
- Tudo apagado menos a ROM. Mantidos (texto, poucos KB, caros de refazer): os 4 patches do
  ndsrecomp + 1 do melonDS (`patches/`), rotas e hashes de tela (`tests/`), config do título.
- Resumo da 1ª tentativa em `docs/APRENDIZADOS.md`. Repositório GitHub antigo: o mantenedor apaga na web.
- Pasta organizada; plano novo (módulos por overlay em vez de executável único).
- **Próximo passo:** Fase 0 — escrever e rodar `tools/setup.sh` na VM.

## 2026-10-30 · Objetivo e marcos definidos
- Decisão do mantenedor: seguir pela recompilação estática; objetivo final = `.app` independente
  (dados do jogo embutidos, sem o `.nds`). Marcos M0–M6 no `PLANO.md`; docs atualizadas.
- `tools/setup.sh` e `tools/progresso.sh` escritos; **ainda não rodados** (VM ganhou cmake/ninja
  via `pip install --user`; ficam em `~/.local/bin`, pôr no PATH).
- **Próximo passo:** M0 — rodar `tools/setup.sh` na VM (em segundo plano, log em `local/`).
- Decisão do mantenedor: meta é o jogo zerável; % de cobertura não é critério. M3 virou "velocidade, só se precisar".

## 2026-10-30 (noite) · M0 fechado, M1 quase
- **M0 provado na VM:** `tools/setup.sh` 6/6 etapas ok; recompilador `ctest` 6/6; extração bate com
  `tests/golden/extract.json` (`tests/test_extract.py`). Rótulos: 179 bancos, 75.022 funções.
- Corrigido `tools/import_symbols.py`: a decomp repete o nome `thunk_FUN_020155ee` em dois endereços →
  C não compilava (redefinição). Nomes repetidos ganham sufixo `_<endereço>`.
- Decisão: recompilador em `local/build/<sistema>/recompiler` (linux na VM, darwin no Mac); pastas de
  build do CMake se refazem sozinhas se o projeto mudou de caminho (`build_no_lugar` em `progresso.sh`).
- Decisão: na VM, processos em segundo plano morrem ao fim de cada chamada (nem `setsid`/`tmux`
  sobrevivem). Builds longos na VM: `tools/fatia.sh <pasta-build>` em fatias de 165 s.
- Novo `tools/rota.py <rota> [--ate N] [--sem-reset] [--gravar]`: roda a rota no runner sem janela,
  compara hash SHA-1 do RGB de cada tela com `tests/golden/`, salva PNG em `local/rotas/<rota>/`.
- **Prova M1 (VM, runner NONE, ARM9 principal + ARM7 recompilados, overlays no interpretador):**
  - `boot_logos`: **13/13 pontos iguais ao golden** (50 s).
  - `title_screen --sem-reset`: **3/3 iguais** (54 s).
  - `primeira_batalha --ate 16700`: **2/2 iguais** (7000 e 16700: quarto com Bianca/Cheren e a caixa).
    Ritmo ~110–150 VBlanks/s na VM; os 31.000 não cabem no limite de 3 min por chamada.
- `build.command` agora: instala cmake/ninja/SDL3 pelo Homebrew se faltar → build SDL3 → rota
  `primeira_batalha` inteira (resultado em `local/rotas/mac-primeira_batalha.txt`) → abre o jogo
  (`tools/jogar.sh`, save em `local/saves/`).
- **Próximo passo:** o mantenedor dá duplo clique no `build.command` (fecha o M1: rota inteira + janela).
  Depois: M2 — estudar `live_overlay` / bancos carregáveis por overlay.

## 2026-10-30 (noite, 2) · **M1 fechado**
- `build.command` aberto pelo Claude (Finder): build SDL3 no Mac ok; **jogo abriu na janela do Mac**
  (`tools/jogar.sh`, save em `local/saves/pokeblack.sav`).
- Rota `primeira_batalha` inteira no Mac (`rota.command`, 298 s, sem janela): 7000/16700/17300 iguais ao
  golden antigo; 21000/29000/31000 diferentes, mas **iguais em duas rodadas** e conferidos a olho:
  batalha do Snivy (Cheren), batalha do Oshawott (Bianca), volta ao quarto bagunçado. Diferença = tempo
  (golden antigo veio de outra build, com sementes). Decisão: golden regravado com esta build;
  o antigo ficou em `tests/golden/primeira_batalha.1a-tentativa.json`.
- `tools/rota.py`: PNG sem Pillow (o Python do Mac não tem); caminho do runner resolvido.
- Novo `rota.command` (duplo clique) roda a rota no Mac. O Claude abre `.command` pelo Finder
  (Ir → Documentos → duplo clique); o Terminal só é observado.
- **Próximo passo:** M2 — estudar `live_overlay` (banco carregável por overlay) e montar o primeiro
  overlay como biblioteca própria.

## 2026-10-30/31 (madrugada) · **M2 fechado — 177 overlays em módulos nativos**
- Caminho: Fallback 1 do PLANO direto (sem o cache `live_overlay`, que compila páginas a partir de
  cobertura ao vivo). Decisão: bancos estáticos por overlay como bibliotecas + `dlopen`.
- Patch `patches/ndsrecomp/0005-pkb-overlay-banks-dlopen.patch`: `runner/src/pkb_overlay_banks.cpp`
  abre `$NDS_BANK_DIR/pkb_arm*.{so,dylib}`, pega `g_dispatch_<banco>` e registra (ARM9, exc 0xFFFF0000).
  O runtime escolhe pelo conteúdo vivo (`--validate-live-bytes`), então overlays no mesmo endereço convivem.
- `tools/overlays.py` em duas fases (`--fase c`: recompila; `--fase lib`: compila o que foi gerado — o
  recompilador decide os shards; 1 shard = `<banco>.c`). Etapa 6 do `tools/build.sh` (padrão no Mac,
  `--overlays` na VM) + checagem `nm` de símbolos do banco indefinidos.
- `tools/import_symbols.py`: rótulos com `::` viram `_` (C não aceita).
- **Provas:**
  - Mac: 177 bibliotecas (300 MB) em 10:45; `[pkb] 177 carregados, 0 falhas, 1.033.247 entradas`.
  - `primeira_batalha` no Mac **com os 177 módulos: PASSOU 6/6** (mesmos hashes do golden).
    Tempo da rota 287 s contra 334 s sem módulos (−14%); trecho das batalhas 17300→29000: 80 s contra 121 s (−34%).
  - VM, rota até 19500 com ov010+ov021 nativos: instruções interpretadas no ARM9 504M → 454M (−10%);
    parte do ov021 no interpretador 10,3% → 2,7%, ov010 4,2% → 1,0%; tela idêntica.
  - Rebuild de 1 overlay (toml alterado): 4,1 s na VM.
- O que ainda roda no interpretador: sobretudo funções do **ARM9 principal** não descobertas (85% do
  tier3 ARM9 no campo) e muito do ARM7 (tier3_insns7 796M na rota). É o M3 (sementes de cobertura).
- Velocidade: a rota sem janela no Mac faz 31.000 VBlanks em 287 s ≈ 108/s (> 60). M3 não é obrigatório.
- Pendente: fechar a janela do Terminal do último build (a tela do Mac bloqueou antes).
- **Próximo passo:** M4 — save FLASH em arquivo + rota de salvar/fechar/abrir com o mesmo estado.

## 2026-10-31 (madrugada) · **M3 feito (sementes de cobertura)**
- `tools/rota.py --cobertura` grava o manifesto de cobertura; `local/images/` = imagens da ROM no formato
  do `ingest_coverage_manifests.py`; sementes em `config/seeds/*.toml` (texto, no projeto; rodadas
  seguintes como `*.r2.toml`, nunca sobrescrever — o ingest só devolve o "resto" ainda não coberto).
- `tools/import_symbols.py` junta as sementes aos bancos e cria **bancos alias do ARM7**
  (`pkb_arm7_alias037f79bc`, `pkb_arm7_alias02fce5a8`): o módulo ARM7 roda copiado nesses endereços,
  então o banco em 0x02380000 nunca era usado. Eles viram bibliotecas como os overlays.
- `tools/overlays.py`: shards pelo tamanho do binário (~6 KB/shard, máx. 64). Com sementes o finder
  acha muito mais funções (ov009: 3 shards de 34 MB → >2 min cada na VM).
- **Provas (VM, mesma rota, mesmas telas):**
  | até 19500 | tempo | instr. interpretadas ARM9 | ARM7 |
  |---|---|---|---|
  | sem sementes/módulos | 158,8 s | 504 M | 497 M |
  | + bancos alias ARM7 | 131,6 s | 494 M | **4.110** |
  | + sementes ARM9 principal | 109,1 s | **51 M** | 4.110 |
  - Rota **inteira** `primeira_batalha` na VM com 14 módulos: 168 s (antes não cabia em 3 min);
    ARM9 interpretado 48,8 M instr. (Mac sem sementes: 746 M); ARM7 5,6 mil.
    Golden próprio do Linux `tests/golden/primeira_batalha.linux.json` (tempo difere do Mac; telas
    conferidas); 2ª rodada **PASSOU** contra ele (determinístico).
- 2ª rodada de sementes (cobertura da rota inteira: overlays de batalha 93/94/95) já em
  `config/seeds/*.r2.toml`: entra no próximo build do Mac.
- Savestates seguem quebrados ("IO core scalar is invalid"): não dá para encadear chamadas na VM.
- **Próximo passo:** build do Mac (tudo com sementes) + rota; depois M4 no Mac (rota que salva no menu,
  fecha, abre e confere). A tela do Mac estava bloqueada; janela do Terminal do build anterior pendente.
- 2ª rodada de sementes compilada na VM (runner + 16 módulos, incl. overlays de batalha 93/94/95):
  `primeira_batalha` inteira **PASSOU** (golden Linux) em 169,8 s; ARM9 interpretado **5,1 M instr.**
  (era 48,8 M; antes das sementes ~750 M), ARM7 4.110. O tempo não caiu: o gargalo agora é a emulação
  do hardware, não o código do jogo. Na VM não dá para passar de ~31.000 VBlanks numa chamada.
- **Próximo passo (precisa do Mac desbloqueado):** `build.command` (177 overlays + alias ARM7 com
  sementes) → rota no Mac; depois M4 no Mac: estender a rota após o 31.000 até salvar no menu,
  fechar, abrir com o save e conferir (tela/RAM). Fechar a janela do Terminal que ficou aberta.

## 2026-10-31 (manhã) · M3 no Mac + **M4 fechado (salvar e carregar)**
- Build no Mac com todas as sementes: 179 bibliotecas (177 overlays + 2 alias ARM7), 0 com problema;
  `[pkb] 179 carregados, 1.075.578 entradas`. `primeira_batalha` **PASSOU 6/6** em 226 s
  (era 287 s com módulos sem sementes, 334 s sem módulos).
- `tools/rota.py --save <arquivo>`: usa save FLASH em arquivo e faz `cart_save_flush` no fim.
  `rota.command` lê `local/rotas.txt` (rotas) e `local/rotas-args.txt` (argumentos por rota).
  `tools/mosaico.py <rota>`: mosaico das fotos para conferir de uma vez.
- Exploração: depois do 31.000, A até o quarto ficar livre (~31.450). Menu (X) na tela de baixo:
  POKÉMON | BAG / AAAAAAA | SAVE / OPTIONS; cursor começa sem seleção.
- **Prova M4 (Mac):**
  - `salvar_m4` (golden novo): X → baixo, baixo, direita (SAVE) → A → "Saving... Don't turn off the
    power" → "AAAAAAA saved the game." (Nuvema Town, tempo 0:05). Save em `local/saves/m4.sav`.
  - `carregar_m4` (golden novo): processo novo com o mesmo save → tela-título → CONTINUE (AAAAAAA,
    Nuvema Town, 0 insígnias, 0:05) → "Spring" → quarto. **Telas de cima e de baixo idênticas, bit a
    bit, às do fim de `salvar_m4`** (A 356585ce…, B 16d6db41…).
- Decisão: M6 (app independente) antes de M5. M5 ("zerável") depende do mantenedor jogando (áudio/3D
  aprovados por ele) e de corrigir o que aparecer; para isso ele precisa do `.app` de duplo clique.
  Rotas automáticas por ginásio a partir de saves ficam como complemento.
- **Próximo passo:** M6 — `Pokemon Black.app` com os dados do cartucho embutidos (sem ler o `.nds`),
  saves em `~/Library/Application Support/PokemonBlack`.

## 2026-10-31 (manhã) · **M6 fechado — `Pokemon Black.app`**
- Patch `0006-pkb-cartucho-embutido`: o runner lê `cartucho.pkb` (zlib, sem o enchimento 0xFF; 111 MB
  em vez de 268 MB) e confere o SHA-1 pelo registro dos bancos. `tools/empacotar.py` gera o pacote.
- `tools/app.sh` (etapa 7 do build no Mac) monta `local/app/Pokemon Black.app`: runner + SDL3 em
  Frameworks (install_name_tool) + `cartucho.pkb` + 179 bancos + ícone tirado do banner do cartucho
  (`tools/icone.py`) + lançador; assinatura ad-hoc (`codesign --verify` ok); 799 MB.
  Saves/identidade/configurações em `~/Library/Application Support/PokemonBlack` (nada é escrito no app).
- Descoberta: **o MAC do console entra na semente do RNG** (atributos do Tepig etc.). O runner gera um
  MAC por pasta (`generated-identity.bin`), por isso a VM "diferia" do Mac. `tools/rota.py` agora passa
  `--identity-mac 00:09:BF:DF:B1:33` (o dos goldens): VM e Mac dão os mesmos hashes; um golden só.
  (`tests/golden/primeira_batalha.linux.json` ficou obsoleto — não usado.)
- **Prova M6:** com runner, cartucho e bancos de DENTRO do app (sem `.nds`): `primeira_batalha` PASSOU
  6/6, `salvar_m4` PASSOU, `carregar_m4` PASSOU. Duplo clique no app pelo Finder: tela-título com
  Reshiram, **60,1 quadros/s**; fechado em seguida.
- `tools/import_symbols.py` só regrava `.toml` que mudou (antes forçava recompilar os 177 overlays).
- Pendências do M6 (polimento, não bloqueiam): título da janela ("ndsrecomp firmware preview"),
  remapear controle/teclado, layouts de tela, resolução 3D alta.
- **Próximo passo:** M5 — o mantenedor joga com o app; eu corrijo travamentos/erros que aparecerem
  (log em `~/Library/Application Support/PokemonBlack/ultimo.log`). Rotas por trecho a partir de saves.

## 2026-10-31 (meio-dia) · Qualidade gráfica + menu + controle (em teste)
- Patch `0007-pkb-opengl41-menu-controle`:
  - Renderizador OpenGL do melonDS (`-DNDS_ACCELERATED_RENDERER=OPENGL`) portado para o **OpenGL 4.1
    do macOS**: contexto 4.1 core no Apple, shaders do apresentador `#version 410` (sem
    `layout(binding/location)`: unidades e posições definidas por código), `glMemoryBarrier` vira no-op
    e `glTexStorage3D` vira `glTexImage3D` quando faltam. Se o OpenGL falhar, cai para o software.
  - Menu do jogo (Esc; no controle Guide ou L3 — o Start fica para o jogo): título "Pokemon Black";
    **Gráficos** (Qualidade: ORIGINAL/BAIXO/MÉDIO/ALTO + "Reiniciar para aplicar"); **Controle**
    (cada botão do DS escolhe um botão do controle; "Restaurar padrão"); **Sistema** (voltar, sair).
    Tudo em `settings.ini` (`pkb_quality`, `pkb_pad_N`). Controle conectado com o jogo aberto já era
    reconhecido (SDL3: Xbox, PlayStation, Switch Pro etc. pareados no Bluetooth do macOS).
  - Título da janela "Pokemon Black - N FPS (Esc: menu)".
- Lançador do app lê `pkb_quality`: Original = software 1x; Baixo = OpenGL 2x; Médio = 3x + AA 4;
  Alto = 4x + AA 8. "Reiniciar para aplicar" grava `reiniciar` e o lançador reabre o jogo.
  `PKB_DATA` troca a pasta de dados (testes). Rotas forçam `NDS_3D_RENDERER=soft`.
- Build Mac com OpenGL: runner compilou sem erro; `primeira_batalha` com o app **PASSOU 6/6**.
  (`salvar_m4`/`carregar_m4` interrompidas — janela do build fechada no meio.)
- Teste manual (mantenedor + Claude): menu abre, "MÉDIO" salvo, **reinício pelo menu funcionou**, 60,1 FPS.
  Observado: na introdução com MÉDIO a tela de cima pareceu cortada/ampliada e a de baixo preta —
  falta confirmar se é defeito da apresentação HD. O log do app fica em ~/Library (pasta protegida
  para o Claude): próximo passo é testar com `teste-app.command` (dados em local/teste-app).
- `tools/extract_rom.py` só regrava arquivos que mudaram (antes forçava recompilar os 177 overlays).

## 2026-10-31 (tarde) · Repositório público
- Decisão do mantenedor: publicar o projeto **só com ferramentas** em `github.com/ofdnith/ndspkblack`
  (reusado, histórico novo e limpo; público). Entram `tools/`, `patches/`, `config/` (+ sementes),
  `tests/` (rotas e hashes), `docs/`, os `.command` e a documentação; ficam fora `rom/`, `local/`,
  `third_party/` (`.gitignore`). Licença GPL-3.0 (patches sobre ndsrecomp/melonDS).
- `README.md` novo: guia completo (requisitos, instalação, jogo, menu, controle, gráficos, saves,
  rotas, estrutura, estado, problemas comuns, créditos).
- Nome do jogador no firmware: `PKB_NOME` ou o usuário do Mac (antes era um nome fixo no código).
- Regra 3 do `CLAUDE.md` atualizada (git permitido; nada derivado do cartucho).
- Pendente do trabalho de gráficos: conferir na tela o HD no Alto, layouts e tela cheia
  (OpenGL 4.1 Metal/M2 e 3D interno 1024×768 já confirmados pelo log).

## 2026-10-31 (fim da tarde) · Preparação para público
- Nome e e-mail pessoais removidos de todos os arquivos e do histórico (commit único refeito com
  autor `ofdnith <ofdnith@users.noreply.github.com>`). Bundle ID do app: `local.ndspkblack.app`.
- Achado: o ndsrecomp **não é só GPL**. Código próprio = PolyForm Noncommercial 1.0.0;
  `runner/src`, `oracle/` = MIT; partes do melonDS = GPL-3.0-or-later. Cada patch agora segue a
  licença do arquivo que modifica (`patches/LICENSES.md`); o projeto inteiro é **só não comercial**.
- Novos: `README.md` em inglês (o português virou `README.pt-BR.md`), `LEGAL.md`, `THIRD_PARTY.md`,
  `LICENSES/` (GPL-3.0, MIT, PolyForm), `CONTRIBUTING.md`, modelos de issue/PR em `.github/`.
- `tools/verificar_publicacao.sh`: barra `rom/`, `local/`, `third_party/`, ROM/save/binários/imagens,
  arquivos > 1 MB e (com `PKB_PRIVADO`) dados pessoais. Provado: barra `.NDS` e arquivo com byte nulo;
  passa os 88 arquivos do repositório. **Rodar antes de cada publicação.**
