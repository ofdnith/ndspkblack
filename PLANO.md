# PLANO.md — port total de Pokémon Black para Mac

**Objetivo final:** um **`Pokemon Black.app`** que abre com duplo clique no Mac (M2) e roda o jogo
inteiro **nativo**, do começo aos créditos, com save, **sem precisar do arquivo `.nds`**.
Todo o código do jogo (ARM9, ARM7, 237 overlays) é recompilado para ARM64; os dados do jogo
(gráficos, mapas, textos, sons) são extraídos da ROM **uma vez, no build**, e embutidos no `.app`.

**Caminho escolhido (30/10/2026):** recompilação estática com o ndsrecomp. A ROM é matéria-prima do
build, não do jogo pronto. (Descartados: port pela decomp, que levaria anos; remake do zero, que
deixaria de ser o Pokémon Black.)

**Regra de ouro:** terminar > perfeito. O que importa é o jogo **zerável** e jogável em velocidade
normal (≥ 60 quadros/s). Porcentagem de código nativo é meio, não meta. Cada marco fecha com prova
(rota de teste ou medição).

**Lição da 1ª tentativa:** gerar e compilar C para tudo funciona (1,5 GB de C em ~6 min no M2), mas
ligar tudo num **executável único** (~417 MB) trava o linker. Por isso o jogo é montado **em
módulos**: executável pequeno + uma biblioteca por overlay.

## Marcos
| Marco | Pronto quando (prova) |
|---|---|
| **M0 — Ferramentas** | `tools/setup.sh` baixa e compila tudo com barra de progresso; recompilador passa nos testes (6/6); extração bate com `tests/golden/extract.json` |
| **M1 — Núcleo nativo** | ARM9 principal + ARM7 recompilados; rotas `boot_logos`, `title_screen`, `primeira_batalha` passam com os hashes de `tests/golden/`; jogo abre na janela do Mac |
| **M2 — Código recompilado** | todos os overlays como bibliotecas próprias, carregadas pelo runtime; `primeira_batalha` passa; `measure` registrado; rebuild de um overlay em segundos |
| **M3 — Velocidade (só se precisar)** | se algum trecho ficar abaixo de 60 quadros/s ou travar no interpretador, usar sementes de cobertura nesse trecho. Sem meta de % |
| **M4 — Novo jogo e saves** | rota da intro até a 1ª batalha; salvar → fechar → abrir com o mesmo estado (rota + hash) |
| **M5 — Zerável** | rotas por trecho (ginásios, Liga, créditos) a partir de saves, sem crash; áudio e 3D aprovados pelo mantenedor jogando |
| **M6 — App independente** | `Pokemon Black.app` com duplo clique; dados do jogo embutidos (`.nds` não é lido); saves em `~/Library/Application Support`; controle/teclado; rotas continuam passando |

## Detalhe por marco

### M0 — Ferramentas
- [x] `tools/setup.sh`: ndsrecomp `2d9f4f3`, pokeblack `67d91a7`, recomp-ui `3f1d6f1`, `patches/`, recompilador, `ctest`
- [x] Extrator da ROM (ARM9 BLZ, ARM7, overlays, arquivos, parâmetros de módulo, autoloads) + golden
- [x] Importador de rótulos da decomp → config por banco (nomes com `_arm9_`/`_arm7_`)
- [x] `tools/build.sh` + `build.command` com `tools/progresso.sh`

### M1 — Núcleo nativo
- [x] C do ARM9 principal e ARM7 (`--validate-live-bytes`, shards 48/4), runner sem janela na VM
- [x] Rotas com golden; runner SDL3 no macOS (`build.command`)

### M2 — Código recompilado (o coração do port)
- [x] (pulado: Fallback 1 direto) Estudar o banco carregável do runner (`live_overlay`: ABI `NdsLiveBankInfo`, cache de
      shards, `live_overlay_register_cached_banks`) e pré-preencher esse cache **no build**
- [x] Uma biblioteca por overlay, compiladas em paralelo; o runtime escolhe pelo conteúdo vivo
- **Fallback 1** (~1 h sem avanço): patch no runner que faz `dlopen` de `local/banks/*.dylib` e
  registra a tabela de despacho de cada uma.
- **Fallback 2:** agrupar overlays em poucos bancos estáticos (≤ 100 MB cada).

### M3 — Velocidade (só se precisar)
- [x] Onde estiver lento ou travado: `run_route --coverage` → `ingest_coverage_manifests.py` →
      `config/seeds/` → regenerar. Pular este marco se o jogo já roda a ≥ 60 quadros/s

### M4 — Novo jogo e saves
- [x] Save FLASH 512 KB em arquivo; rota de save/load (hash das duas telas idêntico)
- [ ] Teclado de toque (mouse) para o nome

### M5 — Zerável
- [ ] Rotas por trecho a partir de saves; Musical, Metrô de Batalha, PC, Pokédex, dia/estação
- [ ] Wi-Fi/online desligados com segurança

### M6 — App independente
- [x] Build extrai os dados do cartucho (cabeçalho, sistema de arquivos, overlays, ícone) para um
      pacote embutido no `.app`; o runtime lê o "cartucho" desse pacote em vez do `.nds`
- [x] `.app` assinado localmente (ad-hoc), ícone, saves em `~/Library/Application Support/PokemonBlack`
- [ ] Controle (gamepad) e teclado remapeáveis, layouts de tela, resolução 3D alta
- [x] (rotas com o cartucho embutido do app) Teste final: mover o `.nds` para fora da pasta e o jogo continuar abrindo e passando nas rotas

Fora de escopo: online (GTS, Global Link, Dream World), multiplayer local, outras plataformas.
O `.app` contém dados do jogo: é para uso pessoal, não para distribuir.
