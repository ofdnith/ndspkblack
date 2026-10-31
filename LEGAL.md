# Legal notice

**English** · [Português](#aviso-legal-português)

## No affiliation, trademarks

This is an independent, noncommercial hobby project. It is **not affiliated with, endorsed by or
sponsored by** Nintendo, The Pokémon Company, Game Freak or Creatures Inc. "Pokémon", "Pokémon
Black" and "Nintendo DS" are trademarks of their respective owners and are used here only to say
which game the tools work with.

## What this repository contains — and what it does not

It contains only material written for this project: scripts, patches to open-source
community tools, configuration, test routes, hash values and documentation.

It does **not** contain, and never will:
- ROMs, cartridge dumps or any part of one (code, graphics, sound, text, maps, data files);
- game code in any form — original, disassembled, decompiled or recompiled to C or native code;
- screenshots, recordings or any other images or sounds from the game;
- Nintendo BIOS, firmware, SDK files, encryption keys or anything that defeats copy protection;
- save files or built apps.

The files in `config/seeds/` list memory addresses where the game's functions start (facts about
the program, the same kind of information community decompilation projects publish).
`tests/golden/` holds SHA-1 hashes, which cannot be turned back into images or data.

## Your responsibility

- The tools only work with a dump of a cartridge **you own and dumped yourself**. Whether making
  and using such a personal copy is allowed depends on the law where you live; it is your
  responsibility to check it.
- This project does not provide, link to or help anyone obtain ROMs. Requests for ROMs, links to
  them or uploads of game data in issues, pull requests or discussions will be deleted.
- The app the build produces contains data from your cartridge. **It is for your personal use
  only. Do not share, upload, sell or distribute it**, nor the ROM, the extracted files, the
  generated C code or the libraries.
- One of the required tools (ndsrecomp) is licensed for **noncommercial use only**, so this
  project may only be used for noncommercial purposes. See [THIRD_PARTY.md](THIRD_PARTY.md).

## No warranty

This software is provided "as is", without warranty of any kind, as stated in sections 15 and 16
of the GPL-3.0 ([`LICENSE`](LICENSE)) and in the licenses of each third-party component. Back up
your saves.

## Rights holders

If you represent a rights holder and believe something in this repository infringes your rights,
please open an issue in this repository (or contact the maintainer through GitHub) describing the
material. It will be reviewed and, if appropriate, removed promptly. GitHub's DMCA process is also
available.

---

## Aviso legal (Português)

- **Sem vínculo.** Projeto independente, sem fins comerciais, sem relação com a Nintendo, a The
  Pokémon Company, a Game Freak ou a Creatures Inc. "Pokémon", "Pokémon Black" e "Nintendo DS" são
  marcas de seus donos, citadas só para dizer com qual jogo as ferramentas funcionam.
- **O que há aqui.** Só scripts, patches de ferramentas da comunidade, configuração, rotas de
  teste, hashes e documentação escritos para este projeto. **Não há** ROM, código do jogo (nem
  traduzido para C), imagens, sons, textos, BIOS, firmware, SDK, chaves, saves nem o app pronto.
- **Sua responsabilidade.** As ferramentas só funcionam com o dump de um cartucho **seu**, feito
  por você; se essa cópia pessoal é permitida depende da lei do seu país. O projeto não fornece
  nem indica onde obter ROMs, e pedidos ou links desse tipo serão apagados. O app gerado contém
  dados do jogo: **uso pessoal, não distribua** (nem a ROM, os arquivos extraídos, o C gerado ou
  as bibliotecas).
- **Uso não comercial.** O ndsrecomp, necessário para o build, só pode ser usado sem fins
  comerciais; portanto o projeto inteiro também.
- **Sem garantia**, conforme as seções 15 e 16 da GPL-3.0 e as licenças de cada componente.
- **Titulares de direitos:** abra uma issue ou contate o mantenedor pelo GitHub; o material será
  revisto e, se for o caso, retirado prontamente.
