#!/usr/bin/env python3
"""M2: cada overlay do jogo vira uma biblioteca nativa (local/banks/<sistema>/<banco>.so|.dylib).

Duas fases, cada uma um build.ninja com caminhos relativos à raiz (sobrevive à troca de caminho da VM):
  --fase c    overlay (toml+bin) --recompilador--> C em local/generated/overlays/<banco>/  (marca <banco>.ok)
  --fase lib  lê os .c que o recompilador realmente gerou --cc--> .o --link--> biblioteca
O recompilador decide quantos shards gera (1 shard = <banco>.c; N = <banco>_NN.c), por isso a fase lib
é montada depois da fase c. O runner (patch 0005) abre as bibliotecas via NDS_BANK_DIR.
Uso: tools/overlays.py --fase c|lib [--so ov093,ov094]
"""
import argparse, platform, re
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SIS = platform.system().lower()
EXT = ".dylib" if SIS == "darwin" else ".so"
LINK = "-dynamiclib -undefined dynamic_lookup" if SIS == "darwin" else "-shared"


def bancos(so):
    cfgs = sorted((R / "local/config").glob("pkb_arm9_ov*.toml")) + \
        sorted((R / "local/config").glob("pkb_arm7_alias*.toml"))  # ARM7 copiado em outro endereço (M3)
    for cfg in cfgs:
        if not so or cfg.stem in so:
            yield cfg


def binario(bank):
    if "_arm7_" in bank:
        return "local/extracted/arm7.bin"
    num = int(re.search(r"ov(\d+)", bank).group(1))
    return f"local/extracted/overlay9/overlay_{num:04d}.bin"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=["c", "lib"], required=True)
    ap.add_argument("--so", default="")
    a = ap.parse_args()
    so = {x.strip() if x.strip().startswith("arm") else f"arm9_{x.strip()}" for x in a.so.split(",") if x.strip()}
    so = {f"pkb_{x}" for x in so}
    bd = Path(f"local/build/overlays-{SIS}")
    (R / bd).mkdir(parents=True, exist_ok=True)
    recomp = f"local/build/{SIS}/recompiler/nds_recompile"
    if a.fase == "c":
        L = [f"builddir = {bd}/c", f"recomp = {recomp}", "",
             "rule recomp",
             "  command = rm -rf $dir && mkdir -p $dir && $recomp --config $cfg --bin $bin --out $dir "
             "--bank $bank --shards $n --validate-live-bytes > $dir.log 2>&1 && touch $out",
             "  description = C $bank", ""]
        oks = []
        for cfg in bancos(so):
            bank = cfg.stem
            # shards pelo tamanho do código: o finder acha muito mais funções que os rótulos (ex.: ov009 com
            # 3 shards virou 3 arquivos de 34 MB, >2 min cada na VM). ~6 KB de binário por shard, máx. 64.
            n = max(1, min(64, (R / binario(bank)).stat().st_size // 6000))
            d = f"local/generated/overlays/{bank}"
            binp = binario(bank)
            L += [f"build {d}.ok: recomp local/config/{bank}.toml {binp} | $recomp",
                  f"  cfg = local/config/{bank}.toml", f"  bin = {binp}", f"  dir = {d}",
                  f"  bank = {bank}", f"  n = {n}"]
            oks.append(f"{d}.ok")
        L += [f"build tudo: phony {' '.join(oks)}", "default tudo", ""]
        (R / bd / "c.ninja").write_text("\n".join(L))
        print(f"OK fase c: {len(oks)} overlays ({bd}/c.ninja)")
        return
    inc = ("-Ithird_party/ndsrecomp/recompiler/armv4t "
           "-Ithird_party/ndsrecomp/external/arm-recomp-core/common")
    L = [f"builddir = {bd}/lib",
         "cflags = -O2 -g0 -w -std=gnu11 -fPIC -DNDEBUG " + inc, "",
         "rule cc", "  command = cc $cflags -DNDS_STATIC_CPU=$cpu -I$dir -MD -MF $out.d -c $in -o $out", "  depfile = $out.d",
         "  deps = gcc", "  description = CC $in", "",
         "rule link", f"  command = cc {LINK} -o $out $in", "  description = LINK $out", ""]
    libs = []
    for cfg in bancos(so):
        bank = cfg.stem
        d = R / f"local/generated/overlays/{bank}"
        cs = sorted(p for p in d.glob("*.c")) if d.is_dir() else []
        if not cs:
            print(f"aviso: {bank} sem C gerado (rodar a fase c)")
            continue
        objs = []
        for c in cs:
            rel = c.relative_to(R).as_posix()
            o = f"{bd}/obj/{bank}/{c.stem}.o"
            objs.append(o)
            L += [f"build {o}: cc {rel} | local/generated/overlays/{bank}.ok", f"  dir = local/generated/overlays/{bank}",
                  f"  cpu = {1 if '_arm7_' in bank else 0}"]
        lib = f"local/banks/{SIS}/{bank}{EXT}"
        L += [f"build {lib}: link {' '.join(objs)}", ""]
        libs.append(lib)
    L += [f"build tudo: phony {' '.join(libs)}", "default tudo", ""]
    (R / bd / "lib.ninja").write_text("\n".join(L))
    print(f"OK fase lib: {len(libs)} bibliotecas ({bd}/lib.ninja -> local/banks/{SIS}/)")


if __name__ == "__main__":
    main()
