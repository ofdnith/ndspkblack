# ndspkblack — recompilação estática do Pokémon Black (DS) para Mac

[English](README.md) · **Português**

Ferramentas para transformar o **seu próprio cartucho de Pokémon Black (Nintendo DS)** num
**app nativo de Mac** (Apple Silicon): `Pokemon Black.app`, com duplo clique, save, controle e
gráficos em alta resolução.

> **Este repositório não contém nada da Nintendo.** Não há ROM, código do jogo (nem traduzido),
> gráficos, músicas, textos, BIOS ou firmware aqui. Ele traz só scripts, patches e configuração.
> O jogo é montado **na sua máquina**, a partir de um dump do **seu** cartucho, e o app gerado
> contém dados do jogo: é para **uso pessoal**, não distribua o app nem a ROM. Leia o
> [LEGAL.md](LEGAL.md) antes de usar.

---

## Índice
1. [Como funciona](#como-funciona)
2. [Requisitos](#requisitos)
3. [Instalação passo a passo](#instalação-passo-a-passo)
4. [Jogando](#jogando)
5. [Menu de configurações](#menu-de-configurações)
6. [Controles externos (gamepad)](#controles-externos-gamepad)
7. [Gráficos e layouts de tela](#gráficos-e-layouts-de-tela)
8. [Saves](#saves)
9. [Testes (rotas)](#testes-rotas)
10. [Estrutura do repositório](#estrutura-do-repositório)
11. [Estado do projeto](#estado-do-projeto)
12. [Problemas comuns](#problemas-comuns)
13. [Créditos e licença](#créditos-e-licença)

---

## Como funciona

O código-fonte do jogo nunca foi publicado; tudo o que o jogo é está dentro do cartucho, em
código de máquina ARM do DS. Em vez de emular esse código, este projeto o **traduz antes de rodar**
(recompilação estática):

```
seu cartucho (.nds) ──► extração ──► ARM9, ARM7, 237 overlays, arquivos
                            │
                            ▼
                ndsrecomp (recompilador) ──► C (uma função C por função do jogo)
                            │
                            ▼
                clang do Mac ──► código nativo ARM64 (+ 179 bibliotecas, uma por overlay)
                            │
                            ▼
                runtime ──► reimplementa o hardware do DS: vídeo 2D/3D, som, toque, save
                            │
                            ▼
                Pokemon Black.app (SDL3, OpenGL)
```

- **ARM9** (processador principal) e **ARM7** (som, toque) viram código nativo. O módulo ARM7
  roda copiado em dois endereços de RAM; o build gera um banco para cada um.
- **Overlays** (pedaços de código carregados sob demanda: campo, batalha, menus…) viram
  bibliotecas próprias (`.dylib`) que o app carrega ao abrir. O runtime escolhe a função certa
  conferindo os bytes que estão na memória naquele momento.
- O que a análise estática não encontra roda num interpretador de reserva. Com as sementes de
  cobertura em `config/seeds/`, isso é bem menos de 1% do que roda na rota de teste
  (~5 milhões de instruções do ARM9 em 31.000 quadros; eram ~750 milhões antes das sementes).
- Vídeo, som, toque e save **não** são código do jogo: são reimplementados pelo runtime
  (derivado do [melonDS](https://melonds.kuribo64.net/)).
- Só ferramentas da comunidade: **FreeBIOS** e firmware sintetizado; nada de SDK, BIOS ou
  firmware da Nintendo.

## Requisitos

| O quê | Detalhe |
|---|---|
| Mac | **Apple Silicon** (M1/M2/M3/M4), **macOS 13** ou mais novo. Testado num MacBook Air M2 |
| Espaço em disco | ~10 GB livres (C gerado, objetos e bibliotecas em `local/`) |
| Ferramentas da Apple | **Command Line Tools do Xcode** (clang, git, python3): `xcode-select --install` |
| Homebrew | [brew.sh](https://brew.sh). O build instala sozinho `cmake`, `ninja` e `sdl3` |
| Internet | Na primeira vez, para baixar as ferramentas da comunidade (ndsrecomp, decomp, recomp-ui) |
| **Cartucho** | Dump do **seu** cartucho: Pokémon Black **USA/EUR v1.0** (NDSi Enhanced), código `IRBO`, 268.435.456 bytes, **SHA-1 `26ad0b9967aa279c4a266ee69f52b9b2332399a5`** |

O build confere o SHA-1 e recusa qualquer outro dump (outras versões ou idiomas têm código
diferente e as configurações daqui não valem para eles).

Para conferir o seu arquivo no Terminal:
```sh
shasum -a 1 "caminho/do/seu/PokemonBlack.nds"
```

## Instalação passo a passo

1. **Clone** o repositório (de preferência em `~/Documents`, sem espaços no caminho):
   ```sh
   cd ~/Documents
   git clone https://github.com/ofdnith/ndspkblack.git pokeblack-recomp
   cd pokeblack-recomp
   ```
2. **Coloque o dump do seu cartucho** na pasta `rom/` (qualquer nome terminado em `.nds`):
   ```sh
   cp "caminho/do/seu/PokemonBlack.nds" rom/
   ```
3. **Rode o build**: dê duplo clique em `build.command` no Finder (ou `./build.command` no
   Terminal). Ele mostra cada etapa com barra de progresso e tempo:

   | Etapa | O que faz | Tempo no M2 (1ª vez) |
   |---|---|---|
   | Ferramentas | instala cmake/ninja/SDL3, baixa ndsrecomp/decomp/recomp-ui, aplica `patches/`, compila e testa o recompilador | 2–5 min |
   | Extrair ROM | separa ARM9, ARM7, overlays e arquivos; confere com `tests/golden/extract.json` | segundos |
   | Rótulos + sementes | gera a configuração de cada banco (rótulos da decomp + `config/seeds/`) | segundos |
   | Gerar C e compilar runner | ARM9 + ARM7 em C, depois o runtime com SDL3/OpenGL | 2–5 min |
   | Overlays | 177 overlays + 2 bancos do ARM7 viram 179 bibliotecas | 10–15 min |
   | App | monta `local/app/Pokemon Black.app` (cartucho embutido, ícone, assinatura local) | ~1 min |
   | Rotas de teste | joga sozinho até a primeira batalha e confere as telas | 4–5 min |

   No fim deve aparecer `primeira_batalha: PASSOU`. Rodar o build de novo só refaz o que mudou.
4. **Abra o jogo**: `local/app/Pokemon Black.app`. Pode arrastá-lo para **Aplicativos**; ele não
   precisa mais do `.nds` (o cartucho vai embutido, comprimido, dentro do app).

> Se o macOS disser que o `build.command` não pode ser aberto por falta de permissão, rode
> `chmod +x *.command tools/*.sh tools/*.py` dentro da pasta.

## Jogando

| DS | Teclado |
|---|---|
| Direcional | setas |
| A / B | Z / X |
| X / Y | S / A |
| L / R | Q / W |
| Start / Select | Enter / Backspace |
| Toque (tela de baixo) | mouse |
| **Menu de configurações** | **Esc** |

O título da janela mostra os quadros por segundo (60 = velocidade real do DS).

## Menu de configurações

Abra com **Esc** (no controle: botão central **Guide/Home** ou clique do **analógico esquerdo, L3**;
o Start fica livre para o jogo). Navegue com as setas, Enter confirma, Backspace volta.

| Seção | Opção | Efeito |
|---|---|---|
| **Gráficos** | Qualidade gráfica | Original / Baixo / Médio / Alto (veja abaixo) |
| | Reiniciar para aplicar | fecha e reabre o jogo com a nova qualidade (**salve no jogo antes**) |
| **Tela** | Layout | Empilhado / Lado a lado / Tela principal grande — aplica na hora |
| | Tela cheia | Não / Sim — aplica na hora |
| **Controle** | DS A, DS B, … DS DIREITA | qual botão do controle aperta cada botão do DS |
| | Restaurar padrão | volta o mapeamento original |
| **Sistema** | Voltar ao jogo / Sair | |

As escolhas ficam em `~/Library/Application Support/PokemonBlack/settings.ini`.

## Controles externos (gamepad)

1. Pareie o controle no **Bluetooth do macOS** (Ajustes do Sistema → Bluetooth) ou ligue por cabo.
   Funciona com controles reconhecidos pelo SDL3: Xbox, PlayStation (DualShock 4 / DualSense),
   Nintendo Switch Pro, 8BitDo etc.
2. Abra o jogo — o controle é reconhecido mesmo se conectado com o jogo já aberto.
3. Mapeamento padrão (posição dos botões, padrão Xbox):

   | Controle | DS |
   |---|---|
   | botão de baixo (A no Xbox / ✕ no PS) | A |
   | botão da direita (B no Xbox / ○ no PS) | B |
   | botão da esquerda (X / □) | X |
   | botão de cima (Y / △) | Y |
   | LB / L1, RB / R1 | L, R |
   | Start/Menu/Options, Back/View/Share | Start, Select |
   | direcional | direcional |

4. Para mudar: **Esc → Controle**, escolha o botão do DS e troque com ←/→ qual botão do controle
   o aperta. Quem usa controle da Nintendo e prefere o "A" à direita: troque DS A ↔ DS B.

## Gráficos e layouts de tela

> 🧪 Qualidades Baixo/Médio/Alto, layouts e tela cheia são recentes e ainda estão em teste. O OpenGL já
> foi confirmado num M2 ("OpenGL 4.1 Metal / Apple M2", 3D interno em 1024×768); o nível **Original**
> é o caminho provado pelas rotas.

| Qualidade | O que faz |
|---|---|
| **Original** | exatamente como o DS: 256×192 por tela, 3D por software |
| **Baixo** | 3D desenhado em 2× (512×384) pelo OpenGL |
| **Médio** | 3D em 3× com suavização (4 amostras) |
| **Alto** | 3D em 4× (1024×768) com suavização máxima (8 amostras) |

O 2D (menus, textos, sprites) é arte em pixels e continua na resolução original; nenhuma opção
cria detalhe de textura que o jogo não tem. O macOS só oferece OpenGL 4.1, e o patch
`0007` adapta o renderizador OpenGL do melonDS a ele; se o OpenGL falhar, o jogo volta sozinho
ao 3D por software.

| Layout | Uso |
|---|---|
| **Empilhado** | como o DS (tela de cima sobre a de baixo) |
| **Lado a lado** | as duas telas na horizontal; ocupa melhor monitores largos |
| **Tela principal grande** | tela de cima em 3× e a de baixo pequena à direita (16:9); ideal em tela cheia |

O mouse continua tocando a tela de baixo em qualquer layout.

## Saves

- O jogo salva normalmente pelo menu do próprio Pokémon (botão X → SAVE). O save do cartucho
  (FLASH de 512 KB) fica em `~/Library/Application Support/PokemonBlack/pokeblack.sav`.
- **Faça backup** desse arquivo de vez em quando. Os savestates do runtime (salvar em qualquer
  ponto) **não funcionam** neste jogo; use o save do jogo.
- O app também guarda ali `settings.ini`, a identidade do console (`generated-identity.bin`) e o
  log da última sessão (`ultimo.log`), útil para relatar problemas.

## Testes (rotas)

Nada é considerado "funcionando" sem uma rota de teste: uma lista de botões por quadro que o
runner executa sozinho, sem janela, comparando o SHA-1 das telas com `tests/golden/`.

| Rota | Prova |
|---|---|
| `boot_logos` | logos iniciais idênticos (13 pontos) |
| `title_screen` | tela-título |
| `primeira_batalha` | intro, nome, Pokémon inicial, batalhas contra Cheren e Bianca, volta ao quarto |
| `salvar_m4` | continua `primeira_batalha` e salva pelo menu do jogo |
| `carregar_m4` | abre com aquele save, Continue, e confere que as telas batem bit a bit |

```sh
python3 tools/rota.py primeira_batalha --runner "local/app/Pokemon Black.app/Contents/MacOS/nds_runner" \
  --rom "local/app/Pokemon Black.app/Contents/Resources/cartucho.pkb" \
  --bancos "local/app/Pokemon Black.app/Contents/Resources/banks"
```
Ou duplo clique em `rota.command` (roda as rotas listadas em `local/rotas.txt`).
Detalhes importantes: as rotas fixam o MAC do console (`--identity-mac`), porque o jogo usa o MAC
na semente do sorteio (atributos dos Pokémon); e forçam o 3D por software, que é o determinístico.

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `build.command` | build completo + rotas (duplo clique) |
| `rota.command`, `jogar.command`, `teste-app.command` | rotas; jogo pelo runner do build; app com dados de teste |
| `tools/setup.sh` | baixa as ferramentas fixadas (ndsrecomp `2d9f4f3`, decomp pokeblack `67d91a7`, recomp-ui `3f1d6f1`), aplica patches, compila e testa o recompilador |
| `tools/build.sh` | extração → rótulos/sementes → C → runner → overlays → app |
| `tools/extract_rom.py`, `tools/import_symbols.py`, `tools/overlays.py` | extração, configuração dos bancos, build dos 179 módulos |
| `tools/empacotar.py`, `tools/icone.py`, `tools/app.sh` | cartucho embutido, ícone (do banner do cartucho), montagem do `.app` |
| `tools/rota.py`, `tools/mosaico.py` | executor de rotas; mosaico das fotos de uma rota |
| `tools/verificar_publicacao.sh` | conferência antes de publicar: barra ROM, saves, binários, imagens e arquivos grandes |
| `patches/ndsrecomp/0001–0008`, `patches/melonds/` | nossas mudanças no runtime (lista abaixo; licenças em [`patches/LICENSES.md`](patches/LICENSES.md)) |
| `config/pokeblack.toml` | configuração do título (save FLASH 512 KB) |
| `config/seeds/` | sementes de cobertura (endereços de funções observadas no interpretador) |
| `tests/` | rotas, hashes esperados, teste da extração |
| `docs/APRENDIZADOS.md` | armadilhas encontradas (leia antes de mexer) |
| `PLANO.md`, `PROGRESSO.md` | marcos e diário do projeto |
| `CLAUDE.md` | instruções para o assistente de IA que trabalha no projeto |
| `LEGAL.md`, `THIRD_PARTY.md`, `LICENSE`, `LICENSES/` | aviso legal, componentes de terceiros, textos das licenças |
| `rom/` | **seu** `.nds` (ignorado pelo git) |
| `local/` | tudo o que é gerado: extração, C, builds, bibliotecas, app (ignorado pelo git) |
| `third_party/` | ferramentas baixadas pelo `setup.sh` (ignorado pelo git) |

Patches sobre o ndsrecomp:

| Patch | O que faz |
|---|---|
| 0001 | runner só com FreeBIOS (sem bancos da BIOS da Nintendo) |
| 0002 | oráculo melonDS sem dumps (depuração) |
| 0003 | chip ID do cartucho com o bit de DSi |
| 0004 | runner compila no macOS |
| 0005 | carrega os bancos de overlay como bibliotecas (`dlopen`) |
| 0006 | lê o cartucho embutido (`cartucho.pkb`) |
| 0007 | OpenGL 4.1 do macOS, menu em português, mapeamento de controle |
| 0008 | as duas telas numa janela OpenGL, layouts, tela cheia |

## Estado do projeto

| Marco | Situação |
|---|---|
| M0 Ferramentas | ✅ |
| M1 Núcleo nativo (ARM9 + ARM7) | ✅ |
| M2 Overlays em módulos | ✅ 177 overlays nativos |
| M3 Cobertura | ✅ interpretador < 1% na rota de teste |
| M4 Novo jogo e saves | ✅ salvar → fechar → abrir com o mesmo estado |
| M5 Zerável | ⏳ provado só até a primeira batalha; o resto depende de jogar |
| M6 App independente | ✅ `.app` sem `.nds` |
| Gráficos HD, layouts, tela cheia, controle | 🧪 implementados; em teste |

Fora do escopo: jogo online (GTS, Global Link, Dream World), multiplayer local.

## Problemas comuns

- **"ROM errada"** no build: o SHA-1 não bate. Só o dump USA/EUR v1.0 (`IRBO`) é suportado.
- **Build falha em "cmake e ninja"**: instale o Homebrew e as Command Line Tools e rode de novo.
- **"não possui os privilégios de acesso"** ao abrir um `.command`: `chmod +x *.command tools/*.sh`.
- **O jogo abriu lento ou travou**: anexe `~/Library/Application Support/PokemonBlack/ultimo.log`
  ao relatar.
- **Mudei a qualidade e nada mudou**: use "Reiniciar para aplicar" no menu.

## Créditos e licença

Construído só com ferramentas da comunidade, **baixadas no build e não incluídas aqui**:
- [ndsrecomp](https://github.com/RetroPortingToolKit/ndsrecomp) — recompilador estático de DS e runtime
  (PolyForm Noncommercial 1.0.0 / MIT / GPL-3.0-or-later, conforme a parte)
- [melonDS](https://github.com/melonDS-emu/melonDS) — base do runtime de hardware e do renderizador OpenGL (GPL-3.0-or-later)
- [pokeblack](https://github.com/squiddonaut/pokeblack) — decomp da comunidade (só rótulos e limites de função, lidos no build)
- [recomp-ui](https://github.com/RetroPortingToolKit/recomp-ui) — interface do runtime (MIT)
- FreeBIOS (BSD-2-Clause), [SDL3](https://libsdl.org) (zlib)

**Licenças em resumo** (detalhes em [THIRD_PARTY.md](THIRD_PARTY.md)):
- Os arquivos próprios do projeto (ferramentas, configuração, testes, documentação) estão sob a
  **GPL-3.0** ([`LICENSE`](LICENSE)).
- Cada patch em `patches/` segue a licença do arquivo que modifica (MIT, GPL-3.0-or-later ou
  PolyForm Noncommercial 1.0.0); veja [`patches/LICENSES.md`](patches/LICENSES.md).
- Como o ndsrecomp é não comercial, **o projeto inteiro só pode ser usado sem fins comerciais.**

Pokémon e Nintendo DS são marcas de seus donos. Este projeto não tem relação com a Nintendo, a
The Pokémon Company, a Game Freak ou a Creatures Inc., nem é endossado por elas, e não inclui
nenhum material delas. As marcas são citadas só para dizer com qual jogo as ferramentas funcionam.
