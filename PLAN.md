# PLAN.md — Pokémon Black Recomp

Espelho do plano em https://claude.ai/artifact/XveGmhFWxeXsn1wcAdyfQa (o doc tem a versão
completa, com justificativas, riscos e divisão de papéis). Aqui ficam as **caixas marcadas**.

## Marcos
| Marco | Critério de pronto | Tag |
|---|---|---|
| M1 — Build reproduzível | ROM verificada por SHA-1, ARM9/ARM7/overlays extraídos, recompilador gera C sem erro | `m1-build` |
| M2 — Tela título | Boot até a tela título no Mac, quadro idêntico ao melonDS | `m2-titulo` |
| M3 — Novo jogo | Intro completa, escolha do inicial, primeira batalha vencida | `m3-novo-jogo` |
| M4 — Saves | Salvar, fechar, carregar com mesmo estado; `.sav` compatível com melonDS | `m4-saves` |
| M5 — Jogo zerável | Liga e créditos sem crash, em rota documentada | `m5-zeravel` |
| M6 — Melhorias | Resolução alta, layouts, controle remapeável | `m6-melhorias` |
| M7 — PS5 | Pasta homebrew no PS5 13.60 via etaHEN, jogo até o M4 | `m7-ps5` |

Fora de escopo: online (GTS, Global Link, Dream World), multiplayer local, distribuir
qualquer arquivo derivado da ROM.

## Fase 0 — Preparação (Quevin)
- [x] Dump verificado: SHA-1 `26ad0b9967aa279c4a266ee69f52b9b2332399a5`, 268.435.456 bytes, `IRBO` (reconferido pelo Claude em 29/10)
- [x] Pasta `~/Documents/pokeblack-recomp/` no Mac, conectada à sessão
- [ ] Mover o dump para `local/rom/` dentro da pasta (hoje está na raiz)
- [x] Repositório privado criado e acesso de escrita ao Claude (`souzaq001/ndspkblack`)
- [x] Projeto no app com as instruções
- [ ] Ativar a memória em Settings
- [ ] Mac: Xcode Command Line Tools e Homebrew (`cmake ninja python sdl3`)
- [ ] PS5: FTP do etaHEN aceita conexão a partir do Mac

## Fase 1A — Fundação do build (M1)
- [x] Submódulos ndsrecomp e pokeblack fixados num commit
- [ ] Compilar recompilador e testes no workspace
- [ ] Compilar recompilador e testes no Mac (valida Apple Silicon)
- [ ] Compilar o oráculo melonDS
- [ ] Boot `--freebios --generated-firmware --boot direct`, headless, como padrão
- [ ] Extrator: cabeçalho, ARM9, ARM7, overlays (BLZ), sistema de arquivos
- [ ] Importador de símbolos: rótulos do asm/ da decomp → entradas de função nos TOMLs
- [ ] Primeira passada do `nds_recompile` no ARM9 principal e no ARM7
- [ ] **Pronto quando:** o C gerado compila e o build roda do zero com um único script

## Fase 1B — Teste de fumaça no PS5 (paralela)
- [ ] App mínimo do boilerplate nativo: janela SDL2 com padrão de teste, DualSense, gravação em `/download0`
- [ ] Instalar via FTP em `/data/homebrew/PPSA99xxx` e abrir no 13.60 com etaHEN
- [ ] **Pronto quando:** abre, responde ao controle e grava um arquivo

## Fase 2 — Até a tela título (M2)
- [ ] Runner com bancos do título (`NDS_TITLE_BANK_DIR` + SHA-1)
- [ ] Rodar em modo DS
- [ ] Overlays pelo interpretador de fallback, depois recompilados um a um
- [ ] Ciclo de divergência com `find_first_diverge`
- [ ] Investigar checagens antipirataria do protocolo de cartucho
- [ ] **Pronto quando:** tela título aparece e o quadro bate com o melonDS

## Fase 3 — Novo jogo e primeira batalha (M3)
- [ ] Intro, teclado de toque, overworld 3D, menus
- [ ] Overlays de batalha, áudio (ARM7)
- [ ] Cobertura guiando funções e jump tables
- [ ] Rotas `intro_ate_inicial.inp` e `primeira_batalha.inp` com golden hashes

## Fase 4 — Saves (M4)
- [ ] Tipo e tamanho do save no `game.toml`
- [ ] Salvar/fechar/carregar; `.sav` trocado com melonDS nos dois sentidos

## Fase 5 — Jogo zerável (M5)
- [ ] Rotas por trecho a partir de savestates
- [ ] Musical, Metrô de Batalha, PC, Pokédex, dia/estação
- [ ] Sem fio/online desativados com segurança
- [ ] Trechos quentes fora do interpretador
- [ ] Sessão longa no Mac

## Fase 6 — Melhorias (M6)
- [ ] Layouts de tela, resolução 3D, texturas
- [ ] Controle remapeável, cursor de toque, acelerar

## Fase 7 — Port PS5 (M7)
- [ ] App em `ps5/`, runner com backend SDL2 do SDK
- [ ] Todos os overlays pré-compilados (sem compilador no console)
- [ ] DualSense, touchpad/cursor, saves e logs em `/download0`, 1080p/4K
- [ ] Empacotar e instalar via FTP

## Fase 8 — Polimento
- [ ] Desempenho e estabilidade no PS5
- [ ] Atualizar submódulo e reenviar patches upstream
- [ ] Revisar o que pode ser publicado
