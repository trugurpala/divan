#!/usr/bin/env python3
"""Divan Teftis v2 — Agent Skills spec (agentskills.io) + Claude Code marketplace semasina gore tam denetim."""
import json, re, sys, pathlib

KOK = pathlib.Path(__file__).resolve().parent.parent
hatalar, uyarilar = [], []
AD_DESENI = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
IZINLI_ALANLAR = {"name", "description", "license", "allowed-tools", "metadata", "compatibility", "version"}

# 1) marketplace.json + plugin.json'lar + surum tutarliligi
mp_yol = KOK / ".claude-plugin" / "marketplace.json"
try:
    mp = json.loads(mp_yol.read_text(encoding="utf-8"))
except Exception as e:
    hatalar.append(f"marketplace.json bozuk: {e}"); mp = {"plugins": []}
if not mp.get("name"): hatalar.append("marketplace.json: 'name' zorunlu")
if not (mp.get("owner") or {}).get("name"): hatalar.append("marketplace.json: owner.name zorunlu")
for pl in mp.get("plugins", []):
    if not pl.get("name") or not pl.get("source"):
        hatalar.append(f"marketplace girdisi eksik (name/source): {pl}")
        continue
    pj_yol = KOK / pl["source"] / ".claude-plugin" / "plugin.json"
    if not pj_yol.exists():
        hatalar.append(f"{pl['name']}: plugin.json eksik"); continue
    try:
        pj = json.loads(pj_yol.read_text(encoding="utf-8"))
    except Exception as e:
        hatalar.append(f"{pl['name']}/plugin.json bozuk: {e}"); continue
    if pj.get("name") != pl["name"]:
        hatalar.append(f"{pl['name']}: plugin.json name uyusmuyor ({pj.get('name')})")
    if pl.get("version") and pj.get("version") and pl["version"] != pj["version"]:
        uyarilar.append(f"{pl['name']}: marketplace surumu ({pl['version']}) != plugin.json ({pj['version']})")

# 2) SKILL.md — spec denetimi
gorulen_adlar = {}
skiller = sorted(KOK.glob("plugins/*/skills/*/SKILL.md"))
for sk in skiller:
    goreli = sk.relative_to(KOK)
    metin = sk.read_text(encoding="utf-8", errors="ignore")
    fm = re.match(r"^---\s*\n(.*?)\n---", metin, re.S)
    if not fm:
        hatalar.append(f"{goreli}: YAML frontmatter yok"); continue
    fmt = fm.group(1)
    # koseli ayrac guvenligi
    if "<" in fmt or ">" in fmt:
        hatalar.append(f"{goreli}: frontmatter'da < > karakteri (prompt injection riski, spec yasagi)")
    # alan denetimi
    anahtarlar = set(re.findall(r"^([A-Za-z_-]+):", fmt, re.M))
    fazla = anahtarlar - IZINLI_ALANLAR
    if fazla:
        uyarilar.append(f"{goreli}: standart disi frontmatter alanlari: {sorted(fazla)}")
    ad = re.search(r"^name:\s*(.+)$", fmt, re.M)
    tarif = re.search(r"^description:\s*(.+)$", fmt, re.M)
    if not ad:
        hatalar.append(f"{goreli}: 'name' yok"); continue
    ad_deger = ad.group(1).strip()
    if len(ad_deger) > 64: hatalar.append(f"{goreli}: name > 64 karakter")
    if not AD_DESENI.match(ad_deger):
        hatalar.append(f"{goreli}: name deseni gecersiz (kucuk harf/rakam/tire): '{ad_deger}'")
    if ad_deger != sk.parent.name:
        hatalar.append(f"{goreli}: name ('{ad_deger}') klasor adiyla ('{sk.parent.name}') AYNI DEGIL — skill yuklenmez!")
    if ad_deger in gorulen_adlar:
        hatalar.append(f"CAKISMA: '{ad_deger}' hem {gorulen_adlar[ad_deger]} hem {goreli} icinde")
    gorulen_adlar[ad_deger] = goreli
    if not tarif:
        hatalar.append(f"{goreli}: 'description' yok")
    elif len(tarif.group(1).strip()) > 1024:
        hatalar.append(f"{goreli}: description > 1024 karakter")
    govde_satir = metin[fm.end():].count("\n")
    if govde_satir > 500:
        uyarilar.append(f"{goreli}: govde {govde_satir} satir (>500 onerisi — references/ dosyalarina bol)")

# 3) Yasaklilar
for sk in skiller:
    if re.search(r"^license:\s*Proprietary", sk.read_text(errors="ignore"), re.M):
        hatalar.append(f"{sk.relative_to(KOK)}: PROPRIETARY icerik!")
for dosya in list(KOK.glob("**/*.json")) + list(KOK.glob("*.md")) + [KOK / "LICENSE"]:
    if dosya.is_file() and "DEGISTIR" in dosya.read_text(errors="ignore"):
        hatalar.append(f"{dosya.relative_to(KOK)}: 'DEGISTIR' kalmis")

# 4) Zorunlu belgeler
for g in ["THIRD_PARTY_LICENSES.md", "LICENSE", "README.md", "BLUEPRINT.md", "UPSTREAM.md", "CONTRIBUTING.md"]:
    if not (KOK / g).exists(): hatalar.append(f"{g} eksik")


# 5) Subagent ve hook denetimi
for aj in KOK.glob("plugins/*/agents/*.md"):
    metin = aj.read_text(encoding="utf-8", errors="ignore")
    fm = re.match(r"^---\s*\n(.*?)\n---", metin, re.S)
    if not fm or not re.search(r"^name:", fm.group(1), re.M) or not re.search(r"^description:", fm.group(1), re.M):
        hatalar.append(f"{aj.relative_to(KOK)}: subagent frontmatter eksik (name/description)")
for hk in KOK.glob("plugins/*/hooks/hooks.json"):
    try: json.loads(hk.read_text(encoding="utf-8"))
    except Exception as e: hatalar.append(f"{hk.relative_to(KOK)}: hooks.json bozuk: {e}")


# 6) Vitrin tutarliligi: belgeler urunle esit olmak zorunda (eskime = hata)
gercek_sayi = len(list(KOK.glob("plugins/*/skills/*/SKILL.md")))
katalog = (KOK / "docs" / "Vezir-Katalogu.md")
if katalog.exists():
    katalog_sayi = katalog.read_text(encoding="utf-8", errors="ignore").count("| **")
    if katalog_sayi != gercek_sayi:
        hatalar.append(f"VITRIN ESKI: katalog {katalog_sayi} vezir diyor, gercek {gercek_sayi} — docs/Vezir-Katalogu.md yeniden uret")
readme = (KOK / "README.md").read_text(encoding="utf-8", errors="ignore")
if f"{gercek_sayi} vezir" not in readme and f"{gercek_sayi} skill" not in readme:
    hatalar.append(f"VITRIN ESKI: README guncel vezir sayisini ({gercek_sayi}) anmiyor")
for pl in mp.get("plugins", []):
    if pl["name"] not in readme:
        hatalar.append(f"VITRIN ESKI: README '{pl['name']}' paketini anmiyor")
for komut in KOK.glob("plugins/*/commands/*.md"):
    if f"/{komut.stem}" not in readme:
        hatalar.append(f"VITRIN ESKI: README /{komut.stem} komutunu anmiyor")

for u in uyarilar: print(f"UYARI: {u}")
if hatalar:
    print("\nTEFTIS BASARISIZ:")
    for h in hatalar: print(f"  X {h}")
    sys.exit(1)
print(f"\nTEFTIS TEMIZ - {len(mp.get('plugins', []))} paket, {len(skiller)} skill; ad cakismasi yok, klasor=name esles­mesi tam")
