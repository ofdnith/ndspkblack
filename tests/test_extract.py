#!/usr/bin/env python3
"""Confere a extração (local/extracted/manifest.json) contra tests/golden/extract.json."""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
m = json.loads((R / "local/extracted/manifest.json").read_text())
g = json.loads((R / "tests/golden/extract.json").read_text())
got = {"rom_sha1": m["rom_sha1"], "arm9_sha1": m["arm9"]["sha1"], "arm9_size": m["arm9"]["size"],
       "arm7_sha1": m["arm7"]["sha1"], "overlay9_count": len(m["overlay9"]),
       "overlay9_compressed": sum(o["compressed"] for o in m["overlay9"]),
       "overlay9_list_sha1": m["overlay9_list_sha1"], "autoloads_arm9": len(m["arm9"]["autoloads"]),
       "autoloads_arm7": len(m["arm7"]["autoloads"]), "files": m["files"]}
if "--update" in sys.argv:
    (R / "tests/golden/extract.json").write_text(json.dumps(got, indent=1) + "\n"); print("golden atualizado"); sys.exit(0)
bad = {k: (got.get(k), v) for k, v in g.items() if got.get(k) != v}
if bad:
    print("FALHOU extração ≠ golden:", bad); sys.exit(1)
print("OK extração bate com o golden")
