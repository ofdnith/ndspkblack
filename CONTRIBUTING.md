# Contributing

Thanks for your interest! Bug reports and patches are welcome, under one strict rule:

## Never post anything from the game

Do **not** attach, paste or link — in issues, pull requests, commits or discussions:
- ROMs, dumps or links to them (and do not ask for them);
- extracted files, generated C code, libraries, the built `.app` or `cartucho.pkb`;
- save files;
- screenshots or recordings of the game.

Text logs (`~/Library/Application Support/PokemonBlack/ultimo.log`), frame numbers, hashes and
descriptions of what you saw are fine. Anything that breaks this rule will be deleted.

## Before opening a pull request

1. Run `tools/verificar_publicacao.sh` and make sure it ends with `OK`.
2. Prove the change with a test route (`tools/rota.py`) when it affects the game.
3. Your contribution is licensed like the files it touches: GPL-3.0 for this project's own files;
   for patches, the license of the upstream file ([`patches/LICENSES.md`](patches/LICENSES.md)).
4. This is a noncommercial project ([LEGAL.md](LEGAL.md)).

---

**Português:** contribuições são bem-vindas, mas **nunca** anexe, cole ou indique ROMs, arquivos
extraídos, C gerado, o app, saves ou capturas de tela do jogo. Logs de texto, números de quadro e
hashes podem. Rode `tools/verificar_publicacao.sh` antes de enviar.
