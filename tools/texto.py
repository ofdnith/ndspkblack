#!/usr/bin/env python3
"""M7 (tradução): extrai e reinjeta o texto do jogo (5ª geração) — só a ferramenta, sem texto do jogo.

Arquivos de texto: NARCs a/0/0/2 (sistema) e a/0/0/3 (história). Cada entrada do NARC é uma tabela
de linhas em UTF-16, cifradas por XOR: chave da linha j = 0x7C89 + j*0x2983, e a chave gira 3 bits à
esquerda a cada caractere. 0xFFFE = quebra de linha, 0xFFFF = fim, 0xF000 cmd n p1..pn = comando.

Formato dos .txt (um por entrada do NARC):  NNNN<TAB>texto   — uma linha do jogo por linha do arquivo.
  \\n = quebra de linha; {F000 cmd p1 ...} = comando (hex, NÃO mexer); \\uXXXX = caractere especial;
  \\\\, \\{ = barra e chave literais. Na tradução basta escrever as linhas que mudam (as que faltarem
  ficam como no original).

Uso:
  tools/texto.py extrair  [--rom R] [--saida local/traducao/original]
  tools/texto.py teste    [--rom R]          # ida e volta byte a byte dos dois NARCs (prova)
  tools/texto.py checar   [--trad local/traducao/ptbr]   # comandos preservados, caracteres suportados
  tools/texto.py aplicar  [--rom R] [--trad local/traducao/ptbr] [--saida local/traducao/rom-ptbr.nds]
"""
import argparse, glob, os, re, struct, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NARCS = {"002": "a/0/0/2", "003": "a/0/0/3"}
u16 = lambda b, o: struct.unpack_from("<H", b, o)[0]
u32 = lambda b, o: struct.unpack_from("<I", b, o)[0]

# ---------------- ROM / NARC ----------------
def rom_padrao():
    r = glob.glob(str(RAIZ / "rom" / "*.nds")); assert r, "ROM não encontrada em rom/"; return r[0]

def fnt_paths(rom):
    fnt = u32(rom, 0x40); out = {}
    def walk(d, prefix):
        base = fnt + 8 * (d & 0xFFF); p = fnt + u32(rom, base); fid = u16(rom, base + 4)
        while True:
            t = rom[p]; p += 1
            if t == 0: break
            n = t & 0x7F; name = rom[p:p + n].decode("latin1"); p += n
            if t & 0x80: sub = u16(rom, p); p += 2; walk(sub, prefix + name + "/")
            else: out[prefix + name] = fid; fid += 1
    walk(0xF000, ""); return out

def fat(rom, fid):
    o = u32(rom, 0x48) + 8 * fid; return u32(rom, o), u32(rom, o + 4)

def narc_unpack(b):
    assert b[:4] == b"NARC", "não é NARC"
    p = u16(b, 0xC); assert b[p:p+4] == b"BTAF"; n = u32(b, p + 8)
    ents = [(u32(b, p + 12 + 8*i), u32(b, p + 16 + 8*i)) for i in range(n)]
    btaf_len = u32(b, p + 4); p += btaf_len
    assert b[p:p+4] == b"BTNF"; btnf = b[p:p + u32(b, p + 4)]; p += u32(b, p + 4)
    assert b[p:p+4] == b"GMIF"; g = p + 8
    return [b[g+s:g+e] for s, e in ents], dict(hdr=b[:p], btnf=btnf, pad=b[g+ents[0][1]:g+ents[1][0]][:1] if n > 1 and ents[1][0] > ents[0][1] else b"\xff")

def narc_pack(files, info):
    pad = info["pad"] or b"\xff"; ents = []; gm = bytearray()
    for f in files:
        s = len(gm); gm += f; ents.append((s, len(gm)))
        while len(gm) % 4: gm += pad
    btaf = b"BTAF" + struct.pack("<IHH", 12 + 8*len(ents), len(ents), 0) + b"".join(struct.pack("<II", s, e) for s, e in ents)
    gmif = b"GMIF" + struct.pack("<I", 8 + len(gm)) + bytes(gm)
    body = btaf + info["btnf"] + gmif
    hdr = bytearray(info["hdr"][:0x10]); struct.pack_into("<I", hdr, 8, 0x10 + len(body))
    return bytes(hdr) + body

# ---------------- texto da 5ª geração ----------------
rol3 = lambda k: ((k << 3) | (k >> 13)) & 0xFFFF

def txt_decode(b):
    """-> (linhas: lista de listas de u16 SEM o 0xFFFF final, extras por linha (u16 desconhecido))"""
    nsec, nl = u16(b, 0), u16(b, 2); assert nsec == 1, f"{nsec} seções"
    so = u32(b, 12); linhas = []; extras = []
    for j in range(nl):
        o, n, x = u32(b, so + 4 + 8*j), u16(b, so + 8 + 8*j), u16(b, so + 10 + 8*j)
        key = (0x7C89 + j * 0x2983) & 0xFFFF; cs = []
        for i in range(n):
            cs.append(u16(b, so + o + 2*i) ^ key); key = rol3(key)
        assert cs and cs[-1] == 0xFFFF, f"linha {j} sem terminador"
        linhas.append(cs[:-1]); extras.append(x); fim = o + 2 * n
    # enchimento final até múltiplo de 4 (bytes sem significado; guardados para a prova byte a byte)
    return linhas, extras, (b[8:12], b[so + fim:so + u32(b, so)] if nl else b"")

def txt_encode(linhas, extras, meta):
    unk8, ench = meta
    nl = len(linhas); tab = bytearray(); dados = bytearray(); base = 4 + 8 * nl
    for j, cs in enumerate(linhas):
        cs = list(cs) + [0xFFFF]; key = (0x7C89 + j * 0x2983) & 0xFFFF
        tab += struct.pack("<IHH", base + len(dados), len(cs), extras[j])
        for c in cs: dados += struct.pack("<H", c ^ key); key = rol3(key)
    falta = (-(4 + len(tab) + len(dados))) % 4
    dados += ench if len(ench) == falta else b"\0" * falta
    sec = struct.pack("<I", 4 + len(tab) + len(dados)) + tab + dados
    return struct.pack("<HHI", 1, nl, len(sec)) + unk8 + struct.pack("<I", 16) + sec

# ------------- texto <-> linha editável -------------
def chars_to_str(cs):
    s = []; i = 0
    while i < len(cs):
        c = cs[i]
        if c == 0xF000 and i + 2 < len(cs) + 1:
            cmd, n = cs[i+1], cs[i+2]; ps = cs[i+3:i+3+n]
            s.append("{F000 " + " ".join(f"{x:04X}" for x in [cmd, n, *ps]) + "}"); i += 3 + n; continue
        if c == 0xFFFE: s.append("\\n")
        elif c == 0x5C: s.append("\\\\")
        elif c == 0x7B: s.append("\\{")
        elif 0x20 <= c < 0x7F or (0xA0 <= c < 0x2000 and chr(c).isprintable()): s.append(chr(c))
        else: s.append(f"\\u{c:04X}")
        i += 1
    return "".join(s)

def str_to_chars(s):
    out = []; i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            nx = s[i+1]
            if nx == "n": out.append(0xFFFE); i += 2
            elif nx == "u": out.append(int(s[i+2:i+6], 16)); i += 6
            else: out.append(ord(nx)); i += 2
        elif ch == "{":
            j = s.index("}", i); out += [0xF000] + [int(x, 16) for x in s[i+1:j].split()[1:]]; i = j + 1
        else: out.append(ord(ch)); i += 1
    return out

COMANDO = re.compile(r"\{F000[^}]*\}")

def ler_txt(p):
    d = {}
    for ln in Path(p).read_text(encoding="utf-8").split("\n"):
        if not ln.strip(): continue
        k, _, v = ln.partition("\t"); d[int(k)] = v
    return d

def narcs_da_rom(rom):
    P = fnt_paths(rom); out = {}
    for nome, caminho in NARCS.items():
        fid = P[caminho]; s, e = fat(rom, fid); out[nome] = (fid, rom[s:e])
    return out

# ---------------- comandos ----------------
def cmd_extrair(a):
    rom = Path(a.rom).read_bytes(); saida = Path(a.saida); total = 0
    for nome, (fid, narc) in narcs_da_rom(rom).items():
        files, _ = narc_unpack(narc); d = saida / nome; d.mkdir(parents=True, exist_ok=True)
        for k, f in enumerate(files):
            linhas, _, _ = txt_decode(f); total += len(linhas)
            (d / f"{k:04d}.txt").write_text("".join(f"{j:04d}\t{chars_to_str(cs)}\n" for j, cs in enumerate(linhas)), encoding="utf-8")
    print(f"OK: {total} linhas em {saida}")

def cmd_teste(a):
    rom = Path(a.rom).read_bytes(); n = 0
    for nome, (fid, narc) in narcs_da_rom(rom).items():
        files, info = narc_unpack(narc); novos = []
        for k, f in enumerate(files):
            linhas, extras, unk = txt_decode(f)
            linhas2 = [str_to_chars(chars_to_str(cs)) for cs in linhas]
            assert linhas2 == linhas, f"{nome}/{k}: ida e volta do texto difere"
            g = txt_encode(linhas2, extras, unk)
            assert g == f, f"{nome}/{k}: recodificação difere ({len(g)} vs {len(f)})"
            novos.append(g); n += 1
        assert narc_pack(novos, info) == narc, f"NARC {nome} remontado difere"
    print(f"OK: {n} arquivos de texto e 2 NARCs idênticos byte a byte após decodificar → texto → recodificar")

def carregar_traducao(trad, nome, k):
    p = Path(trad) / nome / f"{k:04d}.txt"
    return ler_txt(p) if p.exists() else {}

def cmd_checar(a, fonte_ok=None):
    rom = Path(a.rom).read_bytes(); erros = 0; mudadas = 0; novos_chars = set()
    orig_chars = set()
    narcs = narcs_da_rom(rom)
    for nome, (fid, narc) in narcs.items():
        for f in narc_unpack(narc)[0]:
            for cs in txt_decode(f)[0]: orig_chars.update(cs)
    for nome, (fid, narc) in narcs.items():
        files, _ = narc_unpack(narc)
        for k, f in enumerate(files):
            tr = carregar_traducao(a.trad, nome, k)
            if not tr: continue
            linhas = txt_decode(f)[0]
            for j, v in tr.items():
                if j >= len(linhas): print(f"ERRO {nome}/{k:04d}:{j:04d} linha não existe"); erros += 1; continue
                o = chars_to_str(linhas[j])
                if v == o: continue
                mudadas += 1
                from collections import Counter   # ordem de nome/número pode mudar; "rola" (BE00) extra é permitido
                sem_rola = lambda x: Counter(c for c in COMANDO.findall(x) if not c.startswith("{F000 BE00 "))
                if sem_rola(v) != sem_rola(o):
                    print(f"ERRO {nome}/{k:04d}:{j:04d} comandos {{F000 ...}} diferentes do original"); erros += 1
                try: cs = str_to_chars(v)
                except Exception as e: print(f"ERRO {nome}/{k:04d}:{j:04d} escape inválido ({e})"); erros += 1; continue
                novos_chars.update(c for c in cs if c not in orig_chars and c < 0xF000)
    if novos_chars:
        print("AVISO: caracteres que o jogo original não usa (a fonte pode não ter): " + " ".join(chr(c) for c in sorted(novos_chars)))
    print(f"{'OK' if not erros else 'FALHOU'}: {mudadas} linhas traduzidas, {erros} erros")
    return erros

A200 = lambda x: (x + 0x1FF) & ~0x1FF

def substituir_arquivos(rom, trocas):
    """trocas: {fid: bytes}. Os arquivos trocados são gravados em sequência a partir do lugar original (os dois
    NARCs de texto são vizinhos); arquivos do cartucho que ficariam por baixo são movidos para a área livre no
    fim da região DS (NTR). Nada passa do fim da região NTR (cabeçalho 0x90): em modo DS, cartuchos
    DSi-enhanced não deixam ler além dela — arquivo lá some (menu vazio, jogo trava)."""
    tab = u32(rom, 0x48); n = u32(rom, 0x4C) // 8
    ntr_fim = u16(rom, 0x90) * 0x80000 or len(rom)
    cauda = A200(len(bytes(rom[:ntr_fim]).rstrip(b"\xff")))       # depois do último byte usado da região NTR
    ent = {i: fat(rom, i) for i in range(n)}
    ordem = sorted(trocas, key=lambda f: ent[f][0]); pos = ent[ordem[0]][0]; novo_lugar = {}
    for fid in ordem:
        ini = pos                                                    # empacota em sequência, sem buracos
        novo_lugar[fid] = (ini, ini + len(trocas[fid])); pos = A200(ini + len(trocas[fid]))
    sobrepoe = lambda a, b: a[0] < b[1] and b[0] < a[1]
    despejar = sorted((i for i, (s, e) in ent.items() if i not in trocas and e > s
                       and any(sobrepoe((s, e), r) for r in novo_lugar.values())), key=lambda i: ent[i][0])
    fim = cauda
    for i in despejar: fim = A200(fim + ent[i][1] - ent[i][0])
    if fim > ntr_fim or max(e for _, e in novo_lugar.values()) > ntr_fim:   # confere antes de mexer na ROM
        raise SystemExit(f"não cabe na região DS: faltam {fim - ntr_fim} bytes para realocar {len(despejar)} arquivo(s)")
    dados = {i: bytes(rom[ent[i][0]:ent[i][1]]) for i in despejar}
    for i in list(trocas) + despejar:                                # apaga os lugares antigos
        s, e = ent[i]; rom[s:e] = b"\xff" * (e - s)
    for fid, (s, e) in novo_lugar.items():
        assert e <= ntr_fim
        rom[s:e] = trocas[fid]; struct.pack_into("<II", rom, tab + 8 * fid, s, e)
    for i in despejar:
        s = cauda; e = s + len(dados[i]); cauda = A200(e)
        if e > ntr_fim: raise SystemExit(f"sem espaço na região DS para realocar o arquivo {i}")
        rom[s:e] = dados[i]; struct.pack_into("<II", rom, tab + 8 * i, s, e)
    return despejar

# Entradas da Pokédex em outros idiomas (só aparecem para Pokémon de 4ª geração vindos de jogos estrangeiros).
# Se o texto traduzido não couber na região DS do cartucho, estas são esvaziadas, uma a uma, até caber.
SACRIFICAVEIS = [("002", 242, "Pokédex em japonês (kanji)"), ("002", 241, "Pokédex em japonês (kana)"),
                 ("002", 239, "Pokédex em alemão"), ("002", 240, "Pokédex em italiano"),
                 ("002", 238, "Pokédex em francês"), ("002", 243, "Pokédex em espanhol")]

def cmd_aplicar(a):
    if cmd_checar(a): sys.exit("checagem falhou: nada aplicado")
    base = Path(a.rom).read_bytes(); narcs = narcs_da_rom(base); total = 0; textos = {}
    for nome, (fid, narc) in narcs.items():
        files, info = narc_unpack(narc); novos = []
        for k, f in enumerate(files):
            tr = carregar_traducao(a.trad, nome, k)
            if not tr: novos.append(f); continue
            linhas, extras, unk = txt_decode(f)
            for j, v in tr.items(): linhas[j] = str_to_chars(v)
            novos.append(txt_encode(linhas, extras, unk)); total += 1
        textos[nome] = (fid, novos, info)
    vazios = []
    while True:
        rom = bytearray(base)
        trocas = {fid: narc_pack(novos, info) for fid, novos, info in textos.values()}
        try:
            movidos = substituir_arquivos(rom, trocas); break
        except SystemExit:
            if len(vazios) == len(SACRIFICAVEIS): raise
            nome, k, desc = SACRIFICAVEIS[len(vazios)]; vazios.append(desc)
            fid, novos, info = textos[nome]; linhas, extras, unk = txt_decode(novos[k])
            novos[k] = txt_encode([[] for _ in linhas], extras, unk)
    for d in vazios: print(f"AVISO: sem espaço no cartucho — esvaziada: {d}")
    if movidos: print(f"{len(movidos)} arquivo(s) do cartucho realocado(s) dentro da região DS")
    Path(a.saida).parent.mkdir(parents=True, exist_ok=True); Path(a.saida).write_bytes(rom)
    print(f"OK: {total} arquivos de texto traduzidos → {a.saida}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["extrair", "teste", "checar", "aplicar"])
    ap.add_argument("--rom", default=None)
    ap.add_argument("--trad", default=str(RAIZ / "local/traducao/ptbr"))
    ap.add_argument("--saida", default=None)
    a = ap.parse_args(); a.rom = a.rom or rom_padrao()
    if a.acao == "extrair": a.saida = a.saida or str(RAIZ / "local/traducao/original"); cmd_extrair(a)
    elif a.acao == "teste": cmd_teste(a)
    elif a.acao == "checar": sys.exit(1 if cmd_checar(a) else 0)
    else: a.saida = a.saida or str(RAIZ / "local/traducao/rom-ptbr.nds"); cmd_aplicar(a)
