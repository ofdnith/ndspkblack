#!/usr/bin/env python3
"""Regressão da extração: compara local/extracted/manifest.json com
tests/golden/extract.json (só hashes). --update regrava o golden."""
import hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "tests/golden/extract.json"

def summarize(m):
    ov = "".join(f"{o['id']}:{o['sha1']};" for o in m["overlay9"])
    return {"rom_sha1": m["rom_sha1"], "arm9_sha1": m["arm9"]["sha1"],
            "arm9_size": m["arm9"]["size"], "arm7_sha1": m["arm7"]["sha1"],
            "overlay9_count": len(m["overlay9"]),
            "overlay9_compressed": sum(o["compressed"] for o in m["overlay9"]),
            "overlay9_list_sha1": hashlib.sha1(ov.encode()).hexdigest(),
            "autoloads_arm9": len(m["arm9"]["module_params"]["autoloads"]),
            "autoloads_arm7": len(m["arm7"]["module_params"]["autoloads"]),
            "files": m["files"]["count"]}

cur = summarize(json.loads((REPO / "local/extracted/manifest.json").read_text()))
if "--update" in sys.argv:
    GOLD.write_text(json.dumps(cur, indent=1) + "\n"); print("golden atualizado"); sys.exit(0)
gold = json.loads(GOLD.read_text())
diff = {k: (gold.get(k), v) for k, v in cur.items() if gold.get(k) != v}
print("OK extração bate com o golden" if not diff else f"FALHOU: {diff}")
sys.exit(1 if diff else 0)
