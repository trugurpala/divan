#!/usr/bin/env python3
"""Divan Teftis — repo butunluk denetimi. CI'da her push'ta calisir."""
import json, re, sys, pathlib

KOK = pathlib.Path(__file__).resolve().parent.parent
hatalar, uyarilar = [], []

# 1) marketplace.json ve plugin.json'lar
mp_yol = KOK / ".claude-plugin" / "marketplace.json"
try:
    mp = json.loads(mp_yol.read_text(encoding="utf-8"))
except Exception as e:
    hatalar.append(f"marketplace.json bozuk: {e}"); mp = {"plugins": []}
for pl in mp.get("plugins", []):
    pj = KOK / pl["source"] / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        hatalar.append(f"{pl['name']}: plugin.json eksik"); continue
    try: json.loads(pj.read_text(encoding="utf-8"))
    except Exception as e: hatalar.append(f"{pl['name']}/plugin.json bozuk: {e}")

# 2) SKILL.md frontmatter — Agent Skills standardi (agentskills.io)
skiller = sorted(KOK.glob("plugins/*/skills/*/SKILL.md"))
for sk in skiller:
    metin = sk.read_text(encoding="utf-8", errors="ignore")
    fm = re.match(r"^---\s*\n(.*?)\n---", metin, re.S)
    goreli = sk.relative_to(KOK)
    if not fm:
        hatalar.append(f"{goreli}: YAML frontmatter yok"); continue
    if not re.search(r"^name:", fm.group(1), re.M):
        hatalar.append(f"{goreli}: 'name' alani yok")
    if not re.search(r"^description:", fm.group(1), re.M):
        hatalar.append(f"{goreli}: 'description' alani yok")
    ad = re.search(r"^name:\s*(.+)$", fm.group(1), re.M)
    tarif = re.search(r"^description:\s*(.+)$", fm.group(1), re.M)
    if ad and len(ad.group(1).strip()) > 64:
        uyarilar.append(f"{goreli}: name > 64 karakter (standart siniri)")
    if tarif and len(tarif.group(1).strip()) > 1024:
        uyarilar.append(f"{goreli}: description > 1024 karakter (standart siniri)")

# 3) Yasaklilar: proprietary icerik + unutulmus placeholder
for sk in skiller:
    if re.search(r"^license:\s*Proprietary", sk.read_text(errors="ignore"), re.M):
        hatalar.append(f"{sk.relative_to(KOK)}: PROPRIETARY icerik — dagitilamaz!")
for dosya in list(KOK.glob("**/*.json")) + list(KOK.glob("*.md")) + [KOK / "LICENSE"]:
    if dosya.is_file() and "DEGISTIR" in dosya.read_text(errors="ignore"):
        hatalar.append(f"{dosya.relative_to(KOK)}: 'DEGISTIR' placeholder kalmis")

# 4) Zorunlu belgeler
for gerekli in ["THIRD_PARTY_LICENSES.md", "LICENSE", "README.md", "BLUEPRINT.md"]:
    if not (KOK / gerekli).exists():
        hatalar.append(f"{gerekli} eksik")

for u in uyarilar: print(f"UYARI: {u}")
if hatalar:
    print("\nTEFTIS BASARISIZ:")
    for h in hatalar: print(f"  X {h}")
    sys.exit(1)
print(f"\nTEFTIS TEMIZ - {len(mp.get('plugins', []))} paket, {len(skiller)} skill dogrulandi")
