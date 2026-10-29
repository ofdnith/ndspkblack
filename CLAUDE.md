# CLAUDE.md — ndspkblack

Recompilação estática de **Pokémon Black (DS)** com o [ndsrecomp](https://github.com/RetroPortingToolKit/ndsrecomp),
para rodar nativo no Mac (Apple Silicon) e como app homebrew no PS5 base (13.60, etaHEN).

Plano completo: `PLAN.md` (espelho do doc https://claude.ai/artifact/XveGmhFWxeXsn1wcAdyfQa).
Diário: `PROGRESS.md`. Idioma do projeto: **português**.

## Ritual de cada sessão
1. Testar as permissões necessárias (repo, pasta do Mac, rede).
2. Ler `CLAUDE.md`, `PLAN.md`, `PROGRESS.md`.
3. Copiar a ROM para o workspace e conferir o SHA-1 (`tools/fetch_rom.md`, `tools/verify_rom.sh`).
4. Dizer em uma linha a fase atual e a próxima tarefa.
5. Ao terminar: atualizar `PROGRESS.md` (e caixas do `PLAN.md`), commit e push.

## Regras inegociáveis
1. **Só ferramentas da comunidade.** Nenhum SDK, BIOS, firmware ou ferramenta da Sony
   ou da Nintendo. BIOS = FreeBIOS; firmware = imagem sintetizada pelo ndsrecomp
   (`--freebios --generated-firmware --boot direct`). O único material da Nintendo é o dump
   do cartucho do usuário, como dado de entrada.
   - Consequência: as capturas de bancos de firmware (`bios/firmware_banks/`) do ndsrecomp,
     que exigem firmware Nintendo, **não** são usadas.
2. **Nada derivado da ROM entra no git**: `.nds`, BIOS, firmware, ARM9/ARM7/overlays
   extraídos, C gerado, binários compilados, `.sav`, savestates, screenshots/vídeos do jogo.
   Testes guardam só hashes e logs de texto.
3. **Nada é "funcionando" sem rota de teste ou hash que comprove.**
4. Repositório **privado**. Mudar visibilidade só com autorização do Quevin.

## ROM-alvo
Pokémon Black USA/EUR v1.0 (NDSi Enhanced), código `IRBO`,
SHA-1 `26ad0b9967aa279c4a266ee69f52b9b2332399a5`, 268.435.456 bytes.
Toda config de título é fixada a esse SHA-1; build com outro dump falha cedo.

## Onde as coisas ficam
| Lugar | Conteúdo |
|---|---|
| `third_party/ndsrecomp` | submódulo fixado (recompilador, runner, oráculo) |
| `third_party/pokeblack` | submódulo fixado (decomp, só leitura de rótulos/limites de função) |
| `config/` | TOMLs do título (nossos) |
| `patches/` | patches nossos sobre o ndsrecomp, isolados |
| `tools/` | scripts nossos (verificação, extração, build, suíte) |
| `tests/routes/*.inp`, `tests/golden/` | rotas de input e hashes esperados |
| `ps5/` | app homebrew (Fase 1B/7) |
| `local/` | **ignorado**: ROM (`local/rom/`), extraídos, gerados, builds, saves |

Mac: `~/Documents/pokeblack-recomp` (dump na raiz por enquanto; destino planejado `local/rom/`).
Obs.: o shell remoto do Mac (`device_bash`) é uma VM Linux aarch64 dentro do Mac, não o macOS;
build nativo macOS/SDL3 continua sendo feito por você no Terminal.

## Autonomia
Sem pedir: builds, testes, branches, commits e push neste repo, escrever rotas e patches.
Sempre perguntar: apagar coisas no Mac, mexer fora da pasta do projeto, mudar visibilidade
do repo, qualquer ação no PS5.

## Comandos (atualizar conforme surgirem)
```sh
git submodule update --init --recursive        # submódulos fixados
tools/verify_rom.sh local/rom/pokeblack.nds    # confere SHA-1
tools/bootstrap.sh                             # build do zero (Fase 1A)
```

## Commits e tags
Commits pequenos por tarefa, mensagens em português. Cada fase fecha com tag
(`m1-build`, `m2-titulo`, …).
