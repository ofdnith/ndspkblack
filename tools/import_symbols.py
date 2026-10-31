#!/usr/bin/env python3
"""Sementes de função da decomp (third_party/pokeblack/ndsdisasm_config) -> configs do nds_recompile.

Um TOML por banco em --out: pkb_arm9_main, pkb_arm7_main, pkb_arm9_ovNNN.
Nomes de banco têm _arm9_/_arm7_ (o CMake do runner exige). Autoloads entram no banco
principal como [[code_copy]] (código que roda copiado em outro endereço).
Uso: tools/import_symbols.py --extracted local/extracted --out local/config
"""
import argparse, re, hashlib, json, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
CFG = R / "third_party/pokeblack/ndsdisasm_config"
LINE = re.compile(r"^(arm_func|thumb_func)\s+(0x[0-9A-Fa-f]+)(?:\s+(\S+))?")


def seeds(*names):
    out = {}
    for n in names:
        f = CFG / n
        if not f.exists():
            continue
        for ln in f.read_text(errors="replace").splitlines():
            m = LINE.match(ln.strip())
            if m:
                a = int(m.group(2), 16)
                out.setdefault(a, ("arm" if m.group(1) == "arm_func" else "thumb", m.group(3) or f"FUN_{a:08X}"))
    return out


COV = R / "config/seeds"
COVF = re.compile(r"^arm(9|7)_(arm9|arm7|overlay_(\d+))_([0-9a-f]{8})(?:\.\w+)?\.toml$")  # .r2 etc. = rodadas
EP = re.compile(r"addr\s*=\s*(0x[0-9A-Fa-f]+)\s*\nmode\s*=\s*\"(arm|thumb)\"")


def cov_seeds():
    """Sementes de cobertura (M3: tools/ingest_coverage_manifests.py -> config/seeds/).
    Retorna {"arm9": {...}, "arm7@<base>": {...}, <overlay id>: {...}}."""
    out = {}
    for f in sorted(COV.glob("*.toml")) if COV.is_dir() else []:
        m = COVF.match(f.name)
        if not m:
            continue
        key = int(m.group(3)) if m.group(3) else (
            "arm9" if m.group(2) == "arm9" else f"arm7@{int(m.group(4), 16):08X}")
        d = out.setdefault(key, {})
        for mm in EP.finditer(f.read_text()):
            a = int(mm.group(1), 16)
            d.setdefault(a, (mm.group(2), f"COV_{a:08X}"))
    return out


ASM = R / "third_party/pokeblack/asm"
FUNC = re.compile(r"^\s*(arm_func_start|thumb_func_start|non_word_aligned_thumb_func_start)\s+FUN_(?:\w*?_)?([0-9A-Fa-f]{8})\b", re.M)


def asm_seeds():
    """FUN_XXXXXXXX nos .s da decomp: o endereço está no nome. Retorna {"main": {...}, 93: {...}, ...}."""
    out = {}
    for f in sorted(ASM.rglob("*.s")):
        n = f.name
        m = re.match(r"overlay_(\d+)_", n)
        key = int(m.group(1)) if m else (93 if n.startswith("battle_") else "main")
        d = out.setdefault(key, {})
        for mm in FUNC.finditer(f.read_text(errors="replace")):
            a = int(mm.group(2), 16)
            d.setdefault(a, ("arm" if mm.group(1) == "arm_func_start" else "thumb", f"FUN_{a:08X}"))
    return out


def write(out, bank, title, cpu, isa, load, size, entry, sha, copies, funcs):
    ranges = [(load, load + size)] + [(c["runtime_start"], c["runtime_start"] + c["size"]) for c in copies]
    inside = {a: v for a, v in funcs.items() if any(s <= a < e for s, e in ranges)}
    L = ["# Gerado por tools/import_symbols.py. Não editar à mão.", "", "[program]",
         f'name = "{title}"', f'id = "{bank}"', f'cpu = "{cpu}"', f'isa = "{isa}"',
         f"load_address = 0x{load:08X}", f"size = 0x{size:08X}", f"entry_pc = 0x{entry:08X}", "",
         "[identity]", f'sha1 = "{sha}"', ""]
    for c in copies:
        L += ["[[code_copy]]", f"runtime_start = 0x{c['runtime_start']:08X}",
              f"source_start = 0x{c['source_start']:08X}", f"size = 0x{c['size']:08X}",
              f'name = "{c["name"]}"', ""]
    vistos = set()
    for a in sorted(inside):
        mode, name = inside[a]
        name = re.sub(r"[^A-Za-z0-9_]", "_", name)  # rótulos da decomp com "::" etc.
        if name in vistos:  # a decomp repete alguns nomes (ex.: thunk_FUN_020155ee); C não aceita
            name = f"{name}_{a:08X}"
        vistos.add(name)
        L += ["[[entry_point]]", f"addr = 0x{a:08X}", f'mode = "{mode}"', f'name = "{name}"', ""]
    alvo, novo = out / f"{bank}.toml", "\n".join(L)
    if not alvo.exists() or alvo.read_text() != novo:  # só regrava se mudou (senão o ninja refaz tudo)
        alvo.write_text(novo)
    return len(inside), len(funcs) - len(inside)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extracted", default=str(R / "local/extracted"))
    ap.add_argument("--out", default=str(R / "local/config"))
    a = ap.parse_args()
    ext, out = Path(a.extracted), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    man = json.loads((ext / "manifest.json").read_text())
    rep, fora = {}, {}
    asm = asm_seeds()
    cov = cov_seeds()

    def copies(mod, prefix):
        return [{"runtime_start": x["ram"], "source_start": mod["ram"] + x["offset"], "size": x["size"],
                 "name": f"{prefix}_autoload{i}"} for i, x in enumerate(mod["autoloads"]) if x["size"]]

    for cpu, isa, bank, title, cfgs in (
        ("arm9", "armv5te", "pkb_arm9_main", "Pokemon Black ARM9 principal",
         ["arm9_config.cfg"] + [f"arm9_autoload{i}.cfg" for i in range(4)]),
        ("arm7", "armv4t", "pkb_arm7_main", "Pokemon Black ARM7",
         ["arm7_static.cfg", "arm7_config.txt"] + [f"arm7_autoload{i}.cfg" for i in range(2)])):
        mod = man[cpu]
        data = (ext / f"{cpu}.bin").read_bytes()
        fs = seeds(*cfgs)
        if cpu == "arm9":
            for k2, v in asm.get("main", {}).items():
                fs.setdefault(k2, v)
        for k2, v in cov.get("arm9" if cpu == "arm9" else f"arm7@{mod['ram']:08X}", {}).items():
            fs.setdefault(k2, v)
        n, f = write(out, bank, title, cpu, isa, mod["ram"], len(data), mod["entry"],
                     hashlib.sha1(data).hexdigest(), copies(mod, cpu), fs)
        rep[bank], fora[bank] = n, f
        if cpu == "arm7":  # módulo ARM7 também roda copiado em outros endereços (aliases vistos na cobertura)
            for key, extra in cov.items():
                if not (isinstance(key, str) and key.startswith("arm7@")):
                    continue
                base = int(key[5:], 16)
                if base == mod["ram"]:
                    continue
                desloc = {a - mod["ram"] + base: v for a, v in fs.items()}
                for k2, v in extra.items():
                    desloc.setdefault(k2, v)
                ab = f"pkb_arm7_alias{base:08x}"
                n, f = write(out, ab, f"Pokemon Black ARM7 em 0x{base:08X}", cpu, isa, base, len(data),
                             base, hashlib.sha1(data).hexdigest(), [], desloc)
                rep[ab], fora[ab] = n, f

    total = len(man["overlay9"])
    for k, ov in enumerate(man["overlay9"]):
        i = ov["id"]
        data = (ext / "overlay9" / f"overlay_{i:04d}.bin").read_bytes()
        s = seeds(f"overlay_{i}.cfg", f"overlay_{i}_seeds.cfg")
        for k2, v in asm.get(i, {}).items():
            s.setdefault(k2, v)
        for k2, v in cov.get(i, {}).items():
            s.setdefault(k2, v)
        if not s:
            continue  # overlay sem funções conhecidas (provavelmente só dados): fica no interpretador
        bank = f"pkb_arm9_ov{i:03d}"
        n, f = write(out, bank, f"Pokemon Black overlay {i}", "arm9", "armv5te", ov["ram"], len(data),
                     ov["ram"], hashlib.sha1(data).hexdigest(), [], s)
        rep[bank], fora[bank] = n, f
        if k % 20 == 0:
            print(f"PROGRESSO {k}/{total}", flush=True)

    (out / "import_report.json").write_text(json.dumps({"entries": rep, "out_of_range": fora}, indent=1))
    ovs = [b for b in rep if "_ov" in b]
    print(f"OK: {len(rep)} bancos ({len(ovs)} overlays), {sum(rep.values())} funções "
          f"(ARM9 {rep['pkb_arm9_main']}, ARM7 {rep['pkb_arm7_main']}, overlays {sum(rep[b] for b in ovs)})")
    big = {b: v for b, v in fora.items() if v}
    if big:
        print("aviso: sementes fora do banco (descartadas):", dict(sorted(big.items(), key=lambda x: -x[1])[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
