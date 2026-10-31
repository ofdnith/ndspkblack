#!/usr/bin/env python3
"""Roda uma rota de teste (tests/routes/<nome>.json) no runner sem janela e compara com o golden.

Uso: tools/rota.py <nome> [--runner local/build/runner-none/nds_runner] [--gravar]
- Rota não sequencial: reset antes de cada ponto (como o golden foi gravado).
- Rota sequencial: um boot só; aplica "inputs" [[vblank, [teclas]], ...] e confere os pontos.
Hash de tela = SHA-1 dos bytes RGB do framebuffer (motor A = tela de cima, B = de baixo).
Grava PNG de cada ponto em local/rotas/<nome>/ para olhar. Saída 0 = passou.
"""
import argparse, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TECLAS = {"a": 0, "b": 1, "select": 2, "start": 3, "right": 4, "left": 5,
          "up": 6, "down": 7, "r": 8, "l": 9, "x": 10, "y": 11}
SOLTO = 0x0FFF  # 12 bits, ativo em 0 (APRENDIZADOS #2)


def mascara(nomes):
    m = SOLTO
    for n in nomes:
        m &= ~(1 << TECLAS[n])
    return m


class Cliente:
    def __init__(s, porta):
        s.sock = socket.create_connection(("127.0.0.1", porta), timeout=3600); s.buf = b""

    def cmd(s, nome, **a):
        a["cmd"] = nome
        s.sock.sendall((json.dumps(a) + "\n").encode())
        while b"\n" not in s.buf:
            c = s.sock.recv(1 << 20)
            if not c:
                raise RuntimeError("runner fechou a conexão")
            s.buf += c
        linha, s.buf = s.buf.split(b"\n", 1)
        r = json.loads(linha)
        if isinstance(r, dict) and "error" in r:
            raise RuntimeError(f"{nome}: {r['error']}")
        return r

    def vb(s):
        return int(s.cmd("event_counts")["vblank9"])

    def ate(s, alvo):
        for _ in range(1000):
            r = s.cmd("run_to_event", event="vblank9", count=alvo, max_rounds=50_000_000)
            if r.get("terminal"):
                raise RuntimeError(f"PAROU: arm9={r.get('reason9')!r} arm7={r.get('reason7')!r}")
            if r.get("stalled"):
                raise RuntimeError(f"travou antes do vblank9 {alvo}")
            if s.vb() >= alvo:
                return
        raise RuntimeError(f"não chegou ao vblank9 {alvo}")

    def telas(s):
        out = {}
        for e in ("A", "B"):
            fb = s.cmd("framebuffer", engine=e)
            out[e] = (fb["w"], fb["h"], bytes.fromhex(fb["rgb"]))
        return out


def png(telas, caminho):
    """PNG das duas telas empilhadas, sem depender do Pillow."""
    import struct, zlib
    w, h, _ = telas["A"]
    linhas = b"".join(b"\x00" + telas[e][2][y * w * 3:(y + 1) * w * 3] for e in "AB" for y in range(h))
    def bloco(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    caminho.write_bytes(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", w, h * 2, 8, 2, 0, 0, 0))
                        + bloco(b"IDAT", zlib.compress(linhas, 6)) + bloco(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nome")
    ap.add_argument("--runner", default=str(RAIZ / "local/build/runner-none/nds_runner"))
    ap.add_argument("--porta", type=int, default=19870)
    ap.add_argument("--ate", type=int, default=0, help="só os pontos até este vblank (VM tem limite de 3 min)")
    ap.add_argument("--bancos", default="", help="pasta das bibliotecas de overlay (padrão local/banks/<sistema>)")
    ap.add_argument("--rom", default="", help="cartucho a usar (ex.: local/cartucho.pkb); padrão rom/*.nds")
    ap.add_argument("--save", default="", help="arquivo de save FLASH (padrão: sem save)")
    ap.add_argument("--cobertura", action="store_true", help="grava local/rotas/<rota>/cobertura.json no fim")
    ap.add_argument("--diag", action="store_true", help="salva tier3_coverage e a RAM no fim")
    ap.add_argument("--sem-reset", action="store_true", help="não reinicia entre pontos (mais rápido)")
    ap.add_argument("--gravar", action="store_true", help="grava o golden em vez de comparar")
    a = ap.parse_args()

    rota = json.loads((RAIZ / f"tests/routes/{a.nome}.json").read_text())
    gpath = RAIZ / f"tests/golden/{a.nome}.json"  # um golden só: com o MAC fixo, VM e Mac dão o mesmo
    golden = json.loads(gpath.read_text())["frames"] if gpath.exists() else {}
    out = RAIZ / f"local/rotas/{a.nome}"; out.mkdir(parents=True, exist_ok=True)
    rom = Path(a.rom).resolve() if a.rom else sorted((RAIZ / "rom").glob("*.nds"))[0]
    runner = Path(a.runner).resolve()
    cmd = [str(runner), str(runner.parent), "--serve", "--port", str(a.porta),
           "--rom", str(rom)] + (["--save-path", str(Path(a.save).resolve())] if a.save else ["--no-save"]) + [ "--config", str(RAIZ / "config/pokeblack.toml"),
           "--freebios", "--generated-firmware", "--boot", "direct",
           # MAC fixo: a semente do RNG do jogo usa o MAC (atributos do Tepig etc.). É o MAC com que os
           # goldens do Mac foram gravados; --identity-mac não grava nada na pasta do runner.
           "--identity-mac", "00:09:BF:DF:B1:33",
           "--player-name", "melonDS", "--startup-mode", "automatic"]
    proc = subprocess.Popen(cmd, cwd=str(runner.parent), stdout=open(out / "runner.out.log", "wb"),
                            stderr=subprocess.STDOUT,
                            env=dict(os.environ, NDS_DEEP_TRACE=os.environ.get("NDS_DEEP_TRACE", "0"),
                                     NDS_3D_RENDERER="soft",  # rotas comparam o 3D por software (o OpenGL difere nas bordas)
                                     NDS_BANK_DIR=(str(Path(a.bancos).resolve()) if a.bancos else None) or os.environ.get("NDS_BANK_DIR", str(RAIZ / "local/banks" / os.uname().sysname.lower()))))
    res = {"rota": a.nome, "pontos": {}, "falhas": []}
    t0 = time.time()
    try:
        c = None
        for _ in range(240):
            if proc.poll() is not None:
                raise RuntimeError(f"runner saiu cedo (código {proc.returncode}); veja {out}/runner.out.log")
            try:
                c = Cliente(a.porta); break
            except OSError:
                time.sleep(0.5)
        if c is None:
            raise RuntimeError("servidor de teste não abriu")
        entradas = sorted(rota.get("inputs", []), key=lambda x: x[0])
        seq = rota.get("sequencial", False)
        c.cmd("reset"); c.cmd("keys", mask=SOLTO)
        pontos = [p for p in rota["checkpoints"] if not a.ate or p["vblank9"] <= a.ate]
        if a.ate and all(p["vblank9"] != a.ate for p in pontos):
            pontos.append({"vblank9": a.ate})
        for p in pontos:
            alvo = p["vblank9"]
            if not seq and not a.sem_reset:
                c.cmd("reset"); c.cmd("keys", mask=SOLTO)
            pend = [e for e in entradas if e[0] < alvo and (not seq or e[0] >= c.vb())]
            for vb, teclas in pend:
                if c.vb() < vb:
                    c.ate(vb)
                c.cmd("keys", mask=mascara(teclas))
            c.ate(alvo)
            t = c.telas()
            png(t, out / f"{alvo:06d}.png")
            hs = {e: hashlib.sha1(t[e][2]).hexdigest() for e in "AB"}
            g = golden.get(str(alvo))
            ok = (g == hs) if g else None
            res["pontos"][str(alvo)] = {"hash": hs, "ok": ok}
            print(f"vblank {alvo:>6}  A {hs['A'][:10]} B {hs['B'][:10]}  "
                  f"{'ok' if ok else ('DIFERENTE' if ok is False else 'sem golden')}  "
                  f"({time.time()-t0:.0f}s)", flush=True)
        if a.save:
            try: res["save_flush"] = c.cmd("cart_save_flush")
            except RuntimeError as e: res["save_flush"] = str(e)
        try:
            res["cobertura"] = c.cmd("static_coverage")
            res["despacho"] = c.cmd("dispatch_stats")
            if a.cobertura:  # manifesto de cobertura do interpretador (M3: vira sementes)
                res["cobertura_manifest"] = c.cmd("coverage_manifest", path=str((out / "cobertura.json").resolve()))
            if a.diag:  # onde o interpretador rodou + bytes vivos da RAM principal (para cruzar com overlays)
                (out / "tier3.json").write_text(json.dumps(c.cmd("tier3_coverage", max=262144)))
                (out / "mainram.hex").write_text(c.cmd("read_region", region="mainram").get("hex", ""))
        except RuntimeError as e:
            res["cobertura"] = str(e)
    except Exception as e:
        res["falhas"].append(str(e)); print("FALHA:", e)
    finally:
        proc.terminate()
        try: proc.wait(timeout=20)
        except subprocess.TimeoutExpired: proc.kill()
    res["segundos"] = round(time.time() - t0, 1)
    if a.gravar and not res["falhas"]:
        gpath.write_text(json.dumps({"route": a.nome, "frames": {k: v["hash"] for k, v in res["pontos"].items()}}, indent=1))
    passou = not res["falhas"] and all(v["ok"] for v in res["pontos"].values())
    res["passou"] = passou
    (out / "resultado.json").write_text(json.dumps(res, indent=1))
    print(f"\n{a.nome}: {'PASSOU' if passou else 'NÃO PASSOU'} em {res['segundos']}s  (PNG em {out})")
    return 0 if passou else 1


if __name__ == "__main__":
    sys.exit(main())
