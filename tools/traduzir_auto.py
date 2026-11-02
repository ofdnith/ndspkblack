#!/usr/bin/env python3
"""M7: tradução automática EN→PT-BR do texto do jogo com o Argos Translate (modelo en_pb, open source,
offline, via CTranslate2 + SentencePiece) e revisão automática de cada linha. Só a ferramenta vai
para o git; texto e resultado ficam em local/traducao/.

  entrada:  local/traducao/original/{002,003}/NNNN.txt   (tools/texto.py extrair)
  saída:    local/traducao/ptbr/{002,003}/NNNN.txt       (lida por tools/texto.py aplicar / tools/app.sh)
            local/traducao/revisao.tsv                    (linhas sinalizadas: arquivo, linha, motivo)
  modelo:   local/argos/  (pasta do .argosmodel descompactado; baixado no Mac por traducao.command)
  glossário: local/traducao/glossario.tsv  (EN<TAB>PT; criado com termos básicos se não existir)

Proteções (cada linha):
  - comandos {F000 ...} viram marcadores e voltam no mesmo lugar e ordem;
  - nomes de Pokémon, golpes, itens e habilidades (tirados das listas do próprio jogo) não são traduzidos;
    termos do glossário viram a forma PT fixada;
  - arquivos que são listas de nomes não passam pelo tradutor (só o glossário se aplica);
  - quebras de linha \\n refeitas pela largura da linha original;
  - caracteres sem glifo na fonte do jogo são trocados pelo mais próximo (até a fonte ganhar os glifos).
Revisão automática (vai para revisao.tsv): marcador perdido/duplicado (linha fica em inglês), linha que
voltou igual ao inglês, mais linhas que o original +2, palavra repetida 3x seguidas, texto vazio.

Retomável: cache em local/traducao/cache-mt.json; roda em fatias (--segundos, padrão 160).
Uso: tools/traduzir_auto.py [--segundos N] [--so-montar]
"""
import argparse, glob, json, re, sys, time, textwrap
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import texto as texto_mod
RAIZ = Path(__file__).resolve().parent.parent
T = RAIZ / "local/traducao"; ORIG = T / "original"; SAIDA = T / "ptbr"
CACHE = T / "cache-mt.json"; GLOS = T / "glossario.tsv"; MODELO = RAIZ / "local/argos"
CMD = re.compile(r"\{F000[^}]*\}")
ANCORAS = {"Bulbasaur", "Pound", "Master Ball", "Stench"}   # identificam as listas de nomes do jogo
# fonte do jogo: estes não existem no texto original (sem glifo garantido) → substituto provisório
SEM_GLIFO = str.maketrans({"õ": "o", "Õ": "O", "Â": "A", "Ã": "A", "Ê": "E", "Í": "I", "Ó": "O",
                           "Ô": "O", "Ú": "U", "Ç": "C", "“": '"', "”": '"', "‘": "'", "’": "'", "—": "-", "–": "-"})
GLOSSARIO_INICIAL = """# EN<TAB>PT — termos fixos (edite à vontade; linhas com # são ignoradas)
Poké Ball\tPoké Bola
Poké Balls\tPoké Bolas
Pokémon Center\tCentro Pokémon
Pokémon Centers\tCentros Pokémon
Poké Mart\tPoké Mart
Pokédex\tPokédex
Pokémon\tPokémon
Gym Leader\tLíder de Ginásio
Gym Leaders\tLíderes de Ginásio
Gym\tGinásio
Badge\tInsígnia
Badges\tInsígnias
Elite Four\tElite dos Quatro
Champion\tCampeão
Trainer\tTreinador
Trainers\tTreinadores
Professor Juniper\tProfessora Juniper
Potion\tPoção
Super Potion\tSuper Poção
Hyper Potion\tHiper Poção
Max Potion\tPoção Máxima
Full Restore\tRestauração Total
Revive\tReviver
Antidote\tAntídoto
Repel\tRepelente
Escape Rope\tCorda de Fuga
PC\tPC
Xtransceiver\tXtransceiver
C-Gear\tC-Gear
Team Plasma\tEquipe Plasma
Musical\tMusical
Battle Subway\tMetrô de Batalha
HP\tPS
PP\tPP
EXP. Points\tPontos de EXP.
Exp. Points\tPontos de Exp.
Fainted\tDesmaiou
fainted\tdesmaiou
"""

def ler(p):
    d = {}
    for ln in Path(p).read_text(encoding="utf-8").split("\n"):
        if "\t" in ln: k, v = ln.split("\t", 1); d[int(k)] = v
    return d

def glossario():
    if not GLOS.exists(): GLOS.write_text(GLOSSARIO_INICIAL, encoding="utf-8")
    g = {}
    for ln in GLOS.read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#") and "\t" in ln:
            en, pt = ln.split("\t", 1); g[en.strip()] = pt.strip()
    return g

def arquivos():
    return sorted(glob.glob(str(ORIG / "*" / "*.txt")))

_EN = set("the you to is a of and i it your this for that be are what with have can my me will on in do not was so".split())
_OUTRAS = set("le la les de des et vous je est un une pour pas que qui dans der die das und ich du ist nicht ein eine mit zu "
              "den el los las y en es no por con para tu il di che e per non sono è ti".split())

def outro_idioma(d):
    """Arquivos com texto de outros idiomas (o jogo guarda nomes/frases FR/DE/IT/ES/JP/KR para trocas)
    ou listas grandes de nomes: não passam pelo tradutor."""
    vals = [v for v in d.values() if v.strip()]
    if not vals: return False
    ws = re.findall(r"[a-zà-ÿ']+", " ".join(vals).lower())
    en = sum(w in _EN for w in ws) / max(1, len(ws)); ou = sum(w in _OUTRAS for w in ws) / max(1, len(ws))
    if len(ws) >= 30 and ou >= 0.06 and en <= 0.02: return True
    curtas = sum(1 for v in vals if len(v) <= 16 and " " not in v.strip()) / len(vals)
    return len(vals) >= 200 and curtas >= 0.9

def pular_linha(v):
    return v.count("\\u") >= 2          # japonês/coreano (sem glifos latinos)

def listas_de_nomes():
    nomes, arqs = set(), set()
    for p in arquivos():
        d = ler(p)
        if ANCORAS & set(d.values()):
            arqs.add(p); nomes.update(v for v in d.values() if 4 <= len(v) <= 16 and "{" not in v and "\\" not in v)
        elif outro_idioma(d): arqs.add(p)
    # nomes que também são palavras comuns ("Rest", "Return", "Protect"…) não são protegidos no diálogo:
    # se a forma minúscula aparece em alguma fala, deixa o tradutor cuidar.
    falas = " ".join(" ".join(ler(p).values()) for p in arquivos() if p not in arqs)
    minusc = set(re.findall(r"\b[a-z][a-z'-]+\b", falas))
    nomes = {n for n in nomes if n.lower() not in minusc}
    return nomes, arqs

class Protetor:
    """Troca comandos, nomes e termos do glossário por marcadores que o tradutor preserva."""
    def __init__(self, nomes, glos):
        termos = {t: t for t in nomes}; termos.update(glos)
        self.termos = termos
        alts = sorted(termos, key=len, reverse=True)
        self.re_termo = re.compile(r"(?<![\w'])(" + "|".join(map(re.escape, alts)) + r")(?![\w'])") if alts else None
    def proteger(self, s):
        tok = []
        def m(x, valor):
            tok.append(valor); return f" XZ{len(tok)-1}Q "
        s = CMD.sub(lambda x: m(x, x.group(0)), s)
        if self.re_termo: s = self.re_termo.sub(lambda x: m(x, self.termos[x.group(0)]), s)
        return re.sub(r"\s+", " ", s).strip(), tok
    @staticmethod
    def restaurar(s, tok):
        num = lambda t: int(t.replace("O", "0").replace("o", "0"))   # o modelo às vezes troca 0 por O
        achados = [num(n) for n in re.findall(r"XZ\s?([\dOo]+)\s?Q", s)]
        if sorted(achados) != list(range(len(tok))): return None
        s = re.sub(r"XZ\s?([\dOo]+)\s?Q", lambda x: "\0" + str(num(x.group(1))) + "\0", s)
        s = re.sub(r"\0(\d+)\0", lambda x: tok[int(x.group(1))], s)
        s = re.sub(r" +", " ", s).strip()
        return re.sub(r" ([,.!?;:…])", r"\1", s)

def quebrar(s, largura):
    """Refaz \\n pela largura em caracteres (comandos {…} não contam e nunca são cortados)."""
    s = CMD.sub(lambda m: m.group(0).replace(" ", "\x01"), s)
    palavras = s.split(" "); linhas = []; atual = ""; vis = 0
    for w in palavras:
        lw = len(CMD.sub("", w.replace("\x01", " ")))
        if atual and vis + 1 + lw > largura: linhas.append(atual); atual, vis = w, lw
        else: atual = (atual + " " + w) if atual else w; vis += (1 if vis else 0) + lw
    if atual: linhas.append(atual)
    return "\\n".join(linhas).replace("\x01", " ")

class Tradutor:
    def __init__(self):
        import ctranslate2, sentencepiece as spm
        mdir = next(MODELO.glob("**/model"), None)
        sp = next(MODELO.glob("**/sentencepiece.model"), None)
        if not mdir or not sp: sys.exit(f"modelo não encontrado em {MODELO} (rode traducao.command no Mac)")
        self.t = ctranslate2.Translator(str(mdir), device="cpu", inter_threads=1, intra_threads=int(__import__("os").environ.get("PKB_THREADS", "4")))
        self.sp = spm.SentencePieceProcessor(model_file=str(sp))
    def __call__(self, frases):
        # o modelo traduz uma sentença por vez (com várias, costuma perder a primeira): divide e junta
        partes = [re.split(r"(?<=[.!?…])\s+", f) for f in frases]
        planas = [x for ps in partes for x in ps]
        src = [self.sp.encode(f, out_type=str) for f in planas]
        res = self.t.translate_batch(src, beam_size=2, max_batch_size=32, max_decoding_length=160, repetition_penalty=1.1)
        out = ["".join(r.hypotheses[0]).replace("\u2581", " ").strip() for r in res]
        it = iter(out); return [" ".join(next(it) for _ in ps) for ps in partes]

def segmento_para_mt(v):
    v = re.sub(r"\\u([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16)), v)   # aspas curvas etc.
    return re.sub(r"\s+", " ", v.replace("\\n", " ")).strip()

PAG = re.compile(r"(\{F000 BE0[0-9] [^}]*\})")       # BE01 = espera botão e limpa; BE00 = rola uma linha
ROLA = "{F000 BE00 0000}"
LARG_DIALOGO = 42                                  # p95 das linhas de diálogo do jogo = 45 caracteres
ORDEM_FIXA = re.compile(r"\{F000 (?:FF|BD)")         # cor/alinhamento: a ordem importa

def unidades(v):
    """Divide a linha em caixas: [(texto, separador)]. Linhas sem BE0x = uma unidade só."""
    partes = PAG.split(v); out = []
    for k in range(0, len(partes), 2):
        out.append((partes[k], partes[k + 1] if k + 1 < len(partes) else ""))
    return out

def tem_letras(t):
    return re.search(r"[A-Za-z]{2}", CMD.sub("", t).replace("\\n", " ")) is not None

def montar_caixa(r, larg, dialogo):
    linhas = quebrar(r, larg).split("\\n")
    if not dialogo: return "\\n".join(linhas), len(linhas)
    txt = linhas[0] + ("\\n" + linhas[1] if len(linhas) > 1 else "")
    return txt + "".join(ROLA + "\\n" + l for l in linhas[2:]), len(linhas)

def mesmos_comandos(a, b):
    from collections import Counter
    if Counter(CMD.findall(a)) != Counter(CMD.findall(b)): return False
    return [c for c in CMD.findall(a) if ORDEM_FIXA.match(c)] == [c for c in CMD.findall(b) if ORDEM_FIXA.match(c)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--segundos", type=int, default=160)
    ap.add_argument("--so-montar", action="store_true"); a = ap.parse_args()
    t0 = time.time(); glos = glossario(); nomes, arqs_nomes = listas_de_nomes()
    prot = Protetor(nomes, glos)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    def chaves(v):
        for txt, _ in unidades(v):
            if tem_letras(txt): yield prot.proteger(segmento_para_mt(txt))
    # 1) frases únicas a traduzir (já protegidas), caixa por caixa
    alvo = []
    for p in arquivos():
        if p in arqs_nomes: continue
        for j, v in ler(p).items():
            if pular_linha(v): continue
            alvo += [s for s, _ in chaves(v)]
    alvo = list(dict.fromkeys(alvo)); pend = [s for s in alvo if s not in cache]
    if pend and not a.so_montar:
        mt = Tradutor(); feitos = 0
        for i in range(0, len(pend), 64):
            if time.time() - t0 > a.segundos: break
            lote = pend[i:i+64]
            for s, r in zip(lote, mt(lote)): cache[s] = r
            feitos += len(lote)
            CACHE.write_text(json.dumps(cache, ensure_ascii=False))
        print(f"PROGRESSO {len(alvo) - len(pend) + feitos}/{len(alvo)} frases únicas ({feitos} nesta fatia)")
        if feitos < len(pend): print("continua (rode de novo)"); return
    elif pend: print(f"faltam {len(pend)} frases; montando com o que há")
    # 2) montar arquivos + revisão automática
    revis = []; n = 0
    for p in arquivos():
        rel = Path(p).relative_to(ORIG); out = []
        for j, v in ler(p).items():
            if p in arqs_nomes:
                if v in glos: out.append(f"{j:04d}\t{glos[v].translate(SEM_GLIFO)}")
                continue
            if pular_linha(v) or not tem_letras(v): continue
            n_orig = v.count("\\n") + 1
            # caixa de diálogo: tem BE0x, ou tem exatamente 2 linhas (uma caixa só). Campos de 1 linha não quebram;
            # campos de 3+ linhas (descrições) quebram na largura original.
            dialogo = PAG.search(v) is not None or n_orig == 2
            larg = LARG_DIALOGO if dialogo else max(20, max(len(CMD.sub("", x)) for x in v.split("\\n")))
            nova = ""; motivo = None; avisos = []
            for txt, sep in unidades(v):
                pre = "\\n" if txt.startswith("\\n") else ""
                if not tem_letras(txt): nova += txt + sep; continue
                s, tok = prot.proteger(segmento_para_mt(txt))
                if s not in cache: motivo = "sem tradução ainda"; break
                r = prot.restaurar(cache[s], tok)
                if r is None: motivo = "marcador perdido (mantido em inglês)"; break
                if not r.strip(): motivo = "tradução vazia (mantido em inglês)"; break
                if not mesmos_comandos(r, txt): motivo = "comandos de cor/alinhamento fora de ordem (mantido em inglês)"; break
                if dialogo or n_orig >= 3:
                    caixa, nl = montar_caixa(r, larg, dialogo)
                else:
                    caixa, nl = r, 1
                    if len(CMD.sub("", r)) > max(len(CMD.sub("", txt)) + 4, int(len(CMD.sub("", txt)) * 1.3)):
                        avisos.append("campo de 1 linha bem mais longo (pode cortar)")
                if not dialogo and n_orig >= 3 and nl > n_orig: avisos.append("mais linhas que o campo original (pode cortar)")
                if dialogo and nl > 4: avisos.append("caixa longa (rola 3+ vezes)")
                if segmento_para_mt(r) == segmento_para_mt(txt) and len(CMD.sub("", r).split()) > 2: avisos.append("igual ao inglês")
                if re.search(r"\b(\w+)( \1\b){2,}", r, re.I): avisos.append("palavra repetida")
                nova += pre + caixa + sep
            if motivo:
                if motivo != "sem tradução ainda": revis.append((str(rel), j, motivo))
                continue
            nova = nova.translate(SEM_GLIFO)
            try: texto_mod.str_to_chars(nova)
            except Exception: revis.append((str(rel), j, "escape inválido (mantido em inglês)")); continue
            for m in dict.fromkeys(avisos): revis.append((str(rel), j, m))
            out.append(f"{j:04d}\t{nova}"); n += 1
        d = SAIDA / rel; d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
    (T / "revisao.tsv").write_text("arquivo\tlinha\tmotivo\n" + "".join(f"{a}\t{b:04d}\t{c}\n" for a, b, c in revis), encoding="utf-8")
    from collections import Counter
    print(f"OK: {n} linhas traduzidas; {len(revis)} sinalizadas em local/traducao/revisao.tsv")
    for m, c in Counter(x[2] for x in revis).most_common(): print(f"  {c:6d}  {m}")

if __name__ == "__main__": main()
