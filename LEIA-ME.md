# Pokémon Black — port nativo para Mac

Projeto pessoal: fazer **Pokémon Black (Nintendo DS)** virar um **app nativo de Mac**
(Apple Silicon, MacBook Air M2): `Pokemon Black.app`, duplo clique, jogo inteiro do começo aos
créditos, com save, **sem precisar do arquivo `.nds`** depois de pronto.

## Como funciona (em uma página)

O código-fonte do jogo nunca foi publicado. Tudo o que o jogo é está dentro da ROM (`rom/`),
em código de máquina ARM do DS. O port não reescreve o jogo: ele **traduz**.

```
ROM (.nds) ──► extração ──► ARM9, ARM7, 237 overlays, arquivos
                  │
                  ▼
          recompilador (ndsrecomp) ──► C, uma função C por função do jogo
                  │
                  ▼
          clang do Mac ──► código nativo ARM64
                  │
                  ▼
          runtime ──► reimplementa o hardware do DS: vídeo 2D/3D, som, toque, botões, save
                  │
                  ▼
          janela no Mac (SDL3)
```

- **ARM9**: o processador principal (jogo, gráficos). **ARM7**: o secundário (som, toque, Wi-Fi).
- **Overlays**: pedaços do código do ARM9 que o jogo carrega sob demanda (intro, mapa, batalha…).
  São 237 e concentram a maior parte das funções (~24,8 mil de ~29 mil com rótulo).
- **Port total** = ARM9, ARM7 e **todos os overlays** rodando como código nativo. O interpretador
  do runtime fica só como rede de segurança.
- Os dados do jogo (sprites, mapas, textos, música) não são convertidos: são extraídos da ROM
  **uma vez, no build**, e embutidos no `.app`. A ROM é matéria-prima do build; o app pronto roda
  sem ela. O app contém dados da Nintendo: é para uso pessoal, não para distribuir.

## Marcos
M0 ferramentas → M1 núcleo nativo (ARM9+ARM7) → M2 código recompilado (overlays em módulos)
→ M3 velocidade (só se precisar) → M4 novo jogo e saves → M5 zerável → M6 app independente.
Detalhes e critérios de pronto em `PLANO.md`.

## Ferramentas (só da comunidade)
- [ndsrecomp](https://github.com/RetroPortingToolKit/ndsrecomp): recompilador + runtime (núcleo
  derivado do melonDS) + oráculo para comparar.
- [decomp pokeblack](https://github.com/squiddonaut/pokeblack): só para saber onde começa e termina
  cada função.
- [recomp-ui](https://github.com/RetroPortingToolKit/recomp-ui): interface do runtime.
- FreeBIOS e firmware sintetizado. Nada da Nintendo além do dump do cartucho.

## Pastas
| Pasta | O quê |
|---|---|
| `rom/` | o dump do cartucho (não mexer) |
| `CLAUDE.md` | instruções para a IA que trabalha no projeto |
| `PLANO.md` | fases, critério de pronto de cada uma |
| `PROGRESSO.md` | diário: o que foi feito, prova, próximo passo |
| `docs/APRENDIZADOS.md` | o que a primeira tentativa descobriu (não repetir erros) |
| `tools/` | scripts: `setup.sh` (baixa ferramentas), `progresso.sh` (barra de progresso) |
| `patches/` | nossos patches sobre o ndsrecomp e o melonDS |
| `config/` | config do título |
| `tests/routes`, `tests/golden` | rotas de teste (botões por quadro) e hashes esperados das telas |
| `third_party/` | ferramentas baixadas pelo `setup.sh` |
| `local/` | tudo que é gerado (C, builds, saves, logs). Pode apagar e refazer |

## Como rodar
- **Jogar:** `local/app/Pokemon Black.app` (duplo clique). Teclas: setas, Z=A, X=B, A=Y, S=X, Q=L, W=R,
  Enter=Start, Backspace=Select, mouse=toque. Saves em `~/Library/Application Support/PokemonBlack`.
  Pode arrastar o app para Aplicativos; ele não precisa do `.nds`.
- **Reconstruir tudo:** `build.command` (duplo clique): ferramentas → C → runner → 177 overlays → app →
  rotas de teste. `rota.command` roda só as rotas (lista em `local/rotas.txt`).
