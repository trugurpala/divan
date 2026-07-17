#!/usr/bin/env python3
"""Aylik nobet: upstream repolari taze klonlayip vendored icerikle kiyaslar.
Degisim varsa rapor basar (CI bunu issue'ya cevirir)."""
import re, hashlib, pathlib, subprocess, tempfile, sys

REPOLAR = ["obra/superpowers", "anthropics/skills", "vercel-labs/agent-skills", "nextlevelbuilder/ui-ux-pro-max-skill"]
OZGUN = {"sadrazam", "vezir-yetistirme", "defterdar", "musavir", "temkin", "kural-hazinesi"}
KOK = pathlib.Path(__file__).resolve().parent.parent

def harita(kok):
    h = {}
    for sk in pathlib.Path(kok).rglob("SKILL.md"):
        m = re.search(r"^name:\s*(.+)$", sk.read_text(errors="ignore")[:2000], re.M)
        if m: h[m.group(1).strip()] = sk.parent
    return h

def imza(d):
    return {str(f.relative_to(d)): hashlib.md5(f.read_bytes()).hexdigest()
            for f in sorted(pathlib.Path(d).rglob("*"))
            if f.is_file() and ".git" not in f.parts}

with tempfile.TemporaryDirectory() as tmp:
    ust = {}
    for r in REPOLAR:
        hedef = pathlib.Path(tmp) / r.split("/")[1]
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"https://github.com/{r}", str(hedef)], check=True)
        ust.update(harita(hedef))
    degisen = []
    for sk in sorted(KOK.glob("plugins/*/skills/*/SKILL.md")):
        ad = re.search(r"^name:\s*(.+)$", sk.read_text(errors="ignore")[:2000], re.M).group(1).strip()
        if ad in OZGUN or ad not in ust: continue
        b, u = imza(sk.parent), imza(ust[ad])
        fark = sorted((set(u) - set(b)) | {f for f in set(b) & set(u) if b[f] != u[f]})
        # bilincli yamalar UPSTREAM.md tablosunda; SKILL.md tek-satir farklari orada kontrol edilir
        if fark:
            degisen.append(f"- **{ad}**: {', '.join(fark[:5])}")
    if degisen:
        print("UPSTREAM DEGISIMI VAR:\n" + "\n".join(degisen))
        print("\nKurasyon geregi: farki incele, deger katiyorsa tasi, yama ise UPSTREAM.md tablosuyla kiyasla.")
        sys.exit(2)
    print("Nobet temiz: tum vendored vezirler upstream ile uyumlu.")
