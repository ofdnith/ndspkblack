# APRENDIZADOS — o que a 1ª tentativa (29–30/10/2026) descobriu

## Resultados que já foram alcançados (e devem ser alcançados de novo rápido)
- Jogo rodou **na janela do Mac**: logos → título → Start → intro → nome → caixa (Tepig) →
  batalhas do Cheren e da Bianca → volta ao quarto. Caminho em `tests/routes/primeira_batalha.json`.
- Medição (rota primeira_batalha, Mac M2), com ARM9 principal + ARM7 recompilados + sementes:
  ARM9 71–99% nativo, **ARM7 100%**, **128–145 VBlanks/s** (60 = velocidade real).
  O que faltava no ARM9 eram os overlays.
- Com todos os overlays como bancos estáticos: C gerado (177 bancos, 1,5 GB) e compilado em ~6 min
  no M2, mas o **link do executável único não terminou em 25+ min**. Daí o plano em módulos.

## Números da ROM
`IRBO`, SHA-1 `26ad0b9967aa279c4a266ee69f52b9b2332399a5`. ARM9 BLZ (0xA67C0, carga 0x02004000,
entrada 0x02004800), ARM7 0x28F84 em 0x02380000, 237 overlays (229 BLZ), 247 arquivos.
Rótulos da decomp: ARM9 9.751, ARM7 914, overlays 24.778 (overlay 93 = `asm/battle_*.s` → `ov9_093`;
60 overlays sem rótulo, provavelmente só dados). Funções achadas pelo recompilador: ARM9 principal
28.679, ARM7 3.224.

## Patches (`patches/`)
- `ndsrecomp/0001-freebios-only-build`: runner sem bancos da BIOS Nintendo; exige
  `--freebios --generated-firmware --boot direct` e `-DNDS_BOOTSTRAP_FIRMWARE=ON -DNDS_FREEBIOS_ONLY=ON`.
- `ndsrecomp/0002-oracle-nodump-direct-boot` + `melonds/0001-oracle-accessors`: oráculo melonDS sem dumps
  (só para depurar; melonDS 1.0rc, patches upstream na ordem 0003 0001 0002 0004 0005).
- `ndsrecomp/0003-cart-chip-id-dsi-bit`: chip ID `0x4000FFC2`.
- `ndsrecomp/0004-macos-live-overlay-toolchain`: sem ele o runner **não compila no macOS**.

## Armadilhas (não repetir)
1. **`--validate-live-bytes` é obrigatório** em todo banco. Sem ele o jogo trava antes do VBlank 60:
   o crt0 do ARM7 copia código para `0x03800000`, região que o autoload sobrescreve depois.
2. **Teclas = máscara de 12 bits, ativa em 0**, X/Y nos bits 10–11 (solto `0xFFF`, Start `0xFF7`,
   A `0xFFE`). Uma tabela de 10 bits apertava X+Y junto e fez o Start "não funcionar". Rotas usam
   nomes de tecla (`["start"]`).
3. Parâmetros de módulo do SDK: procurar a assinatura `DEC00621 2106C0DE` (sem rodapé de 12 bytes
   neste dump). Autoload: entradas de 16 bytes (ARM9: 4, ARM7: 2).
4. C em shards: `--shards 48` ARM9, `--shards 4` ARM7, overlays `max(1, funções/800)`. O runner
   espera arquivos `*_NN.c`. Nome de banco **precisa ter `_arm9_` ou `_arm7_`** (CMake recusa).
5. Compilar só `--target nds_runner` (`savestate_test` upstream não linka).
6. Savestates do runtime não funcionam neste jogo. Save em bateria: FLASH 512 KB.
7. Oráculo melonDS muda de resultado conforme as paradas: reset antes de cada ponto.
   Nativo é ~2,5% mais rápido em ciclos que o melonDS → transições adiantadas: **não é bug**.
8. A 1ª sessão gastou tempo com precisão de emulador. Foco: o jogo chegar mais longe.
9. Nunca `pkill -f` com nome que aparece na própria linha (mata o shell): `pkill -x nds_runner`.
10. Teclado do runner: setas, Z=A, X=B, A=Y, S=X, Q=L, W=R, Enter=Start, Backspace=Select, mouse=toque.
11. Ferramentas úteis do ndsrecomp: protocolo TCP de teste do runner (hash de quadro, máscara de teclas,
    `coverage_manifest`), contadores `emu_attrib` (`NDS_PROFILE_EMU=1`) e `tier3_coverage` para medir
    % nativo; `tools/ingest_coverage_manifests.py` transforma cobertura em sementes.
12. Rodar com `NDS_DEEP_TRACE=0` para medir velocidade honesta.
13. **VM: nada sobrevive ao fim da chamada do shell** (nohup, setsid, tmux, systemd-run: todos morrem).
    Trabalho longo = fatias ≤ 170 s que retomam (`tools/fatia.sh`). Cada sessão monta o projeto num
    caminho novo (`/sessions/<id>/mnt/...`): pastas de build do CMake precisam ser refeitas.
15. `sed -i` na VM recria o arquivo **sem bit de execução**: depois de editar um `.command`/`.sh`, `chmod +x`.
    Sem isso o Terminal do Mac recusa ("não possui os privilégios de acesso").
16. Recompilador: com 1 shard ele grava `<banco>.c` (sem número); com N pode gerar menos que o pedido.
    Nunca presuma os nomes: gerar o C primeiro e listar os arquivos (overlays.py em duas fases).
17. Com `--shards` > 1, rótulos com `::` (switch tables da decomp) quebram o C: sanitizar nomes.
18. Com sementes, ~99,9% do código do jogo roda nativo e a velocidade passa a ser limitada pela
    emulação do hardware (~185 VBlanks/s na VM). Savestates do runtime seguem quebrados.
19. O módulo ARM7 roda copiado em 0x037F79BC e 0x02FCE5A8: precisa de bancos alias (import_symbols).
20. **O MAC do firmware entra na semente do RNG do jogo.** Runner novo = MAC novo = outro Tepig.
    Rotas sempre com `--identity-mac 00:09:BF:DF:B1:33`.
21. Fechar um Terminal com processo rodando abre a pergunta "Finalizar?" (botão Finalizar).
14. A decomp tem nome de função repetido (`thunk_FUN_020155ee`): o importador desambigua.

## Rotas e golden (`tests/`)
`boot_logos` (13 pontos até o VBlank 610, idênticos ao melonDS), `title_screen` (tela título ~5901),
`title_start` (sem golden), `primeira_batalha` (sequencial, pontos 7000…31000). Os golden foram
gravados com config FLASH 512 KB e perfil de firmware `--player-name melonDS`.
