#!/usr/bin/env python3
"""Divan Teftis — repo butunluk denetimi. CI'da her push'ta calisir."""
import json, re, sys, pathlib

KOK = pathlib.Path(__file__).resolve().parent.parent
hatalar, uyarilar = [], []

# 1) marketplace.json ve plugin.json'lar gecerli mi, kaynaklar yerinde mi
mp = KOK / ".claude-plugin/marketplace.json"
try:
    m = json.loads(mp.read_text(encoding="utf-8"))
except Exception as e:
    hatalar.append(f"marketplace.json bozuk: {e}")
    m = {"plugins": []}
for pl in m.get("plugins", []):
    kaynak = KOK / pl["source"]
    pj = kaynak / ".claude-plugin/plugin.json"
    if not pj.exists():
        hatalar.append(f"{pl['name']}: plugin.json eksik")
    else:
        try:
            json.loads(pj.read_text(encoding="utf-8"))
        except Exception as e:
            hatalar.append(f"{pl['name']}/plugin.json bozuk: {e}")
    if not list((kaynak / "skills").glob("*/SKILL.md")):
        hatalar.append(f"{pl['name']}: skills/ altinda SKILL.md yok")

# 2) Agent Skills spec: frontmatter + name/description sinirlari
for sk in sorted(KOK.glob("plugins/*/skills/*/SKILL.md")):
    metin = sk.read_text(encoding="utf-8", errors="ignore")
    fm = re.match(r"^---\s*\n(.*?)\n---", metin, re.S)
    rel = sk.relative_to(KOK)
    if not fm:
        hatalar.append(f"{rel}: YAML frontmatter yok")
        continue
    govde = fm.group(1)
    if not re.search(r"^name\s*:", govde, re.M):
        hatalar.append(f"{rel}: 'name' alani yok")
    if not re.search(r"^description\s*:", govde, re.M):
        hatalar.append(f"{rel}: 'description' alani yok")
    ad = re.search(r"^name\s*:\s*(.+)$", govde, re.M)
    if ad and len(ad.group(1).strip()) > 64:
        uyarilar.append(f"{rel}: name 64 karakteri asiyor")
    tarif = re.search(r"^description\s*:\s*(.+)$", govde, re.M)
    if tarif and len(tarif.group(1).strip()) > 1024:
        uyarilar.append(f"{rel}: description 1024 karakteri asiyor")

# 3) Yasaklilar: proprietary icerik ve unutulmus placeholder
for sk in KOK.glob("plugins/**/SKILL.md"):
    if "license: Proprietary" in sk.read_text(encoding="utf-8", errors="ignore"):
        hatalar.append(f"{sk.relative_to(KOK)}: PROPRIETARY icerik — dagitilamaz!")
for dosya in list(KOK.glob("**/*.json")) + [KOK / "LICENSE", KOK / "README.md"]:
    if dosya.exists() and "DEGISTIR" in dosya.read_text(encoding="utf-8", errors="ignore"):
        hatalar.append(f"{dosya.relative_to(KOK)}: 'DEGISTIR' placeholder kalmis")

# 4) Zorunlu belgeler
for gerekli in ["THIRD_PARTY_LICENSES.md", "LICENSE", "README.md", "BLUEPRINT.md"]:
    if not (KOK / gerekli).exists():
        hatalar.append(f"{gerekli} eksik")

for u in uyarilar:
    print(f"UYARI: {u}")
if hatalar:
    print("TEFTIS BASARISIZ:")
    for h in hatalar:
        print(f"  ✗ {h}")
    sys.exit(1)
paket = len(m.get("plugins", []))
skill = len(list(KOK.glob("plugins/*/skills/*/SKILL.md")))
print(f"TEFTIS TEMIZ ✓ — {paket} paket, {skill} skill dogrulandi")
