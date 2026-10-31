# CLAUDE.md — instruções para a IA

## Missão
Terminar o **port total** de Pokémon Black (DS) para Mac (M2): `Pokemon Black.app` de duplo clique,
com ARM9, ARM7 e todos os overlays recompilados para nativo, jogável do começo aos créditos, com
save, e **sem precisar do `.nds`** (dados do jogo extraídos no build e embutidos no app). Marcos
M0–M6 no `PLANO.md`: trabalhe sempre no primeiro marco ainda não provado. Leia `LEIA-ME.md`,
`PLANO.md`, `PROGRESSO.md` e `docs/APRENDIZADOS.md` no início de cada sessão.

## Você é independente. Termine, não aperfeiçoe.
- **Autonomia total.** Não peça permissão nem confirmação. Decida, faça, registre a decisão em uma
  linha no `PROGRESSO.md` e siga. O mantenedor quer o jogo rodando, não perguntas.
- **Pare só** para: apagar algo fora de `local/`, mexer fora de `~/Documents/pokeblack-recomp/`,
  gastar dinheiro, ou quando precisar de uma ação física dele (ex.: duplo clique no `build.command`
  ou jogar e dizer o que viu). Nesse caso peça uma coisa só, clara, e continue o que der enquanto isso.
- **Bom o bastante vence perfeito.** A pergunta é sempre: *isso faz o jogo chegar mais longe ou
  rodar em velocidade normal?* Se não, não faça. **Meta = zerável**, não % de código nativo.
  - Diferenças de tempo em relação ao melonDS (alguns quadros) **não são bugs**.
  - Não refatore, não embeleze código, não otimize antes de medir, não escreva testes além da rota
    que prova a fase.
  - Se um caminho travar por mais de ~1 hora de trabalho, troque de caminho (fallback do `PLANO.md`)
    em vez de insistir.
  - Gambiarra que funciona e está anotada é aceitável. Polimento é a última fase.
- **Fase a fase.** Feche o critério de pronto da fase atual antes de abrir a próxima.

## Regras (essas não se negociam)
1. **Só ferramentas da comunidade.** Nada de SDK, BIOS, firmware ou ferramenta da Nintendo/Sony.
   BIOS = FreeBIOS; firmware sintetizado (`--freebios --generated-firmware --boot direct`).
2. **Prova antes de "funciona".** Toda fase fecha com rota de teste (hash das telas) ou medição
   (`measure`). Escreva a prova no `PROGRESSO.md`.
3. **Nada derivado do cartucho é publicado.** O projeto vive em `~/Documents/pokeblack-recomp/`
   (é lá que se trabalha). O repositório público `github.com/ofdnith/ndspkblack` recebe só
   ferramentas, patches, config, sementes, rotas/hashes e documentação — nunca `rom/`, `local/`,
   `third_party/`, C gerado, bibliotecas, o `.app`, saves ou imagens do jogo (veja `.gitignore`).
   Publicar = conferir a lista de arquivos antes de cada envio.

## Ambiente
- Shell remoto (`device_bash`) = **VM Linux aarch64 dentro do Mac**, com rede. Serve para quase
  tudo: baixar ferramentas, gerar C, compilar e rodar o runner **sem janela** (rotas e medição).
  Trabalhe aqui por padrão; é onde você é independente. A VM é fraca (4 núcleos, 3 GB de RAM):
  compilar o C do jogo inteiro nela é lento; prefira gerar e testar por partes, e deixe o build
  completo para o Mac (8 núcleos). Chamadas duram até 3 min e **nada sobrevive em segundo plano**
  (nohup/setsid/tmux morrem): trabalho longo na VM = fatias que retomam (`tools/fatia.sh`).
- **macOS de verdade** (janela SDL3, build com clang da Apple) só pelo Terminal do Mac:
  `build.command` com duplo clique. O Claude abre os `.command` sozinho pelo Finder (menu Ir → Documentos → pokeblack-recomp →
  duplo clique); o Terminal só pode ser observado. O mantenedor não quer fazer nada à mão.
- Apagar arquivos pela VM exige pedir permissão uma vez por sessão (`device_request_delete_permission`).
- Builds longos: use sempre `tools/progresso.sh` (etapa N/T, % da compilação, cronômetro, log em
  `local/logs/`). O mantenedor precisa ver que está andando.

## Janelas: abriu, fechou
- **Toda janela que o Claude abrir no Mac (Terminal, Finder, jogo) tem que ser fechada por ele** antes de
  encerrar o trabalho. Os `.command` terminam com `exit`; janela do Terminal que sobrar → botão fechar
  (e "Encerrar" se perguntar). O jogo (`tools/jogar.sh`) só é aberto quando for para o mantenedor jogar.
- Não pare no meio: depois de fechar algo provado, siga para a próxima tarefa do plano.

## Ritual de cada sessão
1. Ler os 4 documentos. 2. Dizer em uma linha a fase e a próxima tarefa. 3. Trabalhar até fechar
algo provado. 4. Atualizar `PROGRESSO.md` (o que mudou, prova, próximo passo).

## ROM
Pokémon Black USA/EUR v1.0 (NDSi Enhanced), `IRBO`, SHA-1
`26ad0b9967aa279c4a266ee69f52b9b2332399a5`, 268.435.456 bytes, em `rom/`. Nunca altere a ROM.
