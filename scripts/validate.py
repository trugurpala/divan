#!/usr/bin/env python3
"""Divan Teftis v5 — stdlib ile yerel on-denetim.

Resmi Agent Skills ve Claude Code dogrulayicilari CI'da ayrica calisir.
Bu betik hizli, bagimliliksiz ve vitrin tutarliligini da kapsayan ilk hattir.
"""

from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

try:
    from host_marketplaces import check as host_marketplaces_check
except ModuleNotFoundError:  # Imported as scripts.validate in unit tests.
    from scripts.host_marketplaces import check as host_marketplaces_check


KOK = pathlib.Path(__file__).resolve().parent.parent
AD_DESENI = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_DESENI = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
IZINLI_ALANLAR = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}


def frontmatter(metin: str) -> tuple[str, int] | None:
    """YAML frontmatter metnini ve govdenin basladigi indeksi dondur."""
    eslesme = re.match(r"^---\s*\n(.*?)\n---", metin, re.S)
    if not eslesme:
        return None
    return eslesme.group(1), eslesme.end()


def frontmatter_alani(fmt: str, alan: str) -> str | None:
    """Basit ve cok satirli YAML skalerini bagimliliksiz olarak oku.

    Tam YAML semasi resmi dogrulayiciya birakilir. Buradaki amac ozellikle
    ``description: |-`` gibi bloklarda gercek uzunlugu yanlis olcmemektir.
    """
    satirlar = fmt.splitlines()
    desen = re.compile(rf"^{re.escape(alan)}:\s*(.*)$")
    for indeks, satir in enumerate(satirlar):
        eslesme = desen.match(satir)
        if not eslesme:
            continue
        deger = eslesme.group(1).strip()
        if not deger:
            blok: list[str] = []
            for devam in satirlar[indeks + 1 :]:
                if devam and not devam[0].isspace():
                    break
                blok.append(devam)
            return " ".join(s.strip() for s in blok if s.strip()).strip()
        if deger not in {"|", "|-", "|+", ">", ">-", ">+"}:
            if len(deger) >= 2 and deger[0] == deger[-1] and deger[0] in {'"', "'"}:
                try:
                    return str(ast.literal_eval(deger))
                except (SyntaxError, ValueError):
                    pass
            return deger

        blok_satirlari: list[str] = []
        for devam in satirlar[indeks + 1 :]:
            if devam and not devam[0].isspace():
                break
            blok_satirlari.append(devam)
        dolu = [len(s) - len(s.lstrip()) for s in blok_satirlari if s.strip()]
        girinti = min(dolu) if dolu else 0
        parcalar = [s[girinti:] if len(s) >= girinti else "" for s in blok_satirlari]
        return "\n".join(parcalar).strip() if deger.startswith("|") else " ".join(
            s.strip() for s in parcalar
        ).strip()
    return None


def oku_json(yol: pathlib.Path, hatalar: list[str], etiket: str) -> dict:
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except Exception as hata:  # JSON ve dosya hatalarini tek raporda topla
        hatalar.append(f"{etiket} bozuk: {hata}")
        return {}
    if not isinstance(veri, dict):
        hatalar.append(f"{etiket}: kok nesne olmali")
        return {}
    return veri


def eval_sozlesmesini_denetle(
    skill_dizini: pathlib.Path, skill_adi: str, hatalar: list[str]
) -> None:
    """Varsa skill eval sozlesmesini yapisal ve yol-guvenli olarak denetle."""
    eval_yolu = skill_dizini / "evals" / "evals.json"
    if not eval_yolu.exists():
        return

    etiket = str(eval_yolu.relative_to(KOK)) if eval_yolu.is_relative_to(KOK) else str(eval_yolu)
    veri = oku_json(eval_yolu, hatalar, etiket)
    if veri.get("skill_name") != skill_adi:
        hatalar.append(
            f"{etiket}: skill_name ('{veri.get('skill_name')}') != '{skill_adi}'"
        )

    evalar = veri.get("evals")
    if not isinstance(evalar, list) or len(evalar) < 2:
        hatalar.append(f"{etiket}: en az 2 eval ornegi olmali")
        return

    gorulen_id: set[int] = set()
    kok = skill_dizini.resolve()
    for sira, eval_veri in enumerate(evalar, start=1):
        onek = f"{etiket}: eval[{sira}]"
        if not isinstance(eval_veri, dict):
            hatalar.append(f"{onek} nesne olmali")
            continue
        eval_id = eval_veri.get("id")
        if not isinstance(eval_id, int) or isinstance(eval_id, bool):
            hatalar.append(f"{onek}.id benzersiz tamsayi olmali")
        elif eval_id in gorulen_id:
            hatalar.append(f"{onek}.id tekrarli: {eval_id}")
        else:
            gorulen_id.add(eval_id)

        for alan in ["prompt", "expected_output"]:
            if not isinstance(eval_veri.get(alan), str) or not eval_veri[alan].strip():
                hatalar.append(f"{onek}.{alan} dolu metin olmali")

        beklentiler = eval_veri.get("expectations")
        if not isinstance(beklentiler, list) or not beklentiler or not all(
            isinstance(b, str) and b.strip() for b in beklentiler
        ):
            hatalar.append(f"{onek}.expectations en az bir dolu metin icermeli")

        dosyalar = eval_veri.get("files", [])
        if not isinstance(dosyalar, list) or not all(isinstance(d, str) for d in dosyalar):
            hatalar.append(f"{onek}.files metin yollarindan olusan dizi olmali")
            continue
        for dosya in dosyalar:
            hedef = (skill_dizini / dosya).resolve()
            if not hedef.is_relative_to(kok):
                hatalar.append(f"{onek}.files skill disina cikiyor: {dosya}")
            elif not hedef.is_file():
                hatalar.append(f"{onek}.files bulunamadi: {dosya}")


def surum_kayitlarini_denetle(
    kok: pathlib.Path, marketplace: dict, hatalar: list[str]
) -> None:
    """Tek sürüm kaynağını vitrin, plan ve yayın kayıtlarıyla karşılaştır."""
    version_yolu = kok / "VERSION"
    if not version_yolu.is_file():
        hatalar.append("VERSION eksik")
        return

    surum = version_yolu.read_text(encoding="utf-8").strip()
    if not SEMVER_DESENI.fullmatch(surum):
        hatalar.append(f"VERSION SemVer degil: '{surum}'")
        return

    if marketplace.get("version") != surum:
        hatalar.append(
            f"SURUM ESKI: marketplace ({marketplace.get('version')}) != VERSION ({surum})"
        )
    metadata_surumu = (marketplace.get("metadata") or {}).get("version")
    if metadata_surumu != surum:
        hatalar.append(
            f"SURUM ESKI: marketplace metadata ({metadata_surumu}) != VERSION ({surum})"
        )

    kayitlar = {
        "README": (kok / "README.md", f"v{surum}"),
        "README.en": (kok / "README.en.md", f"v{surum}"),
        "CHANGELOG": (kok / "CHANGELOG.md", f"## [{surum}]"),
        "BLUEPRINT": (kok / "BLUEPRINT.md", f"**v{surum} ✓**"),
        "Kurulum": (kok / "docs" / "Kurulum.md", f"DIVAN_REF=v{surum}"),
        "GitHub Pages": (kok / "docs" / "index.html", f"v{surum}"),
        "Site": (kok / "site" / "index.html", f"v{surum}"),
        "Eval rehberi": (kok / "evals" / "README.md", "python evals/run.py --check"),
        "Wiki ana sayfa": (kok / "docs" / "Home.md", f"v{surum}"),
        "Wiki durum": (kok / "docs" / "Durum-ve-Yol-Haritasi.md", f"v{surum}"),
        "Wiki manifest": (kok / "wiki-pages.json", "docs/Home.md"),
        "Aday Meclisi": (kok / "docs" / "Aday-Meclisi.md", "never-auto-install"),
        "Aday defteri": (kok / "registry" / "candidates.json", "never-auto-install"),
    }
    for ad, (yol, beklenen) in kayitlar.items():
        if not yol.is_file():
            hatalar.append(f"{yol.relative_to(kok)} eksik")
            continue
        if beklenen not in yol.read_text(encoding="utf-8"):
            hatalar.append(f"SURUM ESKI: {ad} '{beklenen}' kaydini icermiyor")

    ilerleme = kok / ".divan" / "progress.md"
    if not ilerleme.is_file():
        hatalar.append(".divan/progress.md eksik")
    elif "## Sıradaki kesin adım" not in ilerleme.read_text(encoding="utf-8"):
        hatalar.append("HAFIZA ESKI: progress.md siradaki kesin adimi icermiyor")


def marketplace_denetle(kok: pathlib.Path, hatalar: list[str]) -> tuple[dict, list]:
    """Marketplace ve plugin manifestlerinin ortak kimliğini doğrula."""
    mp_yol = kok / ".claude-plugin" / "marketplace.json"
    mp = oku_json(mp_yol, hatalar, "marketplace.json")
    if not mp.get("name"):
        hatalar.append("marketplace.json: 'name' zorunlu")
    if not (mp.get("owner") or {}).get("name"):
        hatalar.append("marketplace.json: owner.name zorunlu")

    eklentiler = mp.get("plugins", [])
    if not isinstance(eklentiler, list):
        hatalar.append("marketplace.json: plugins dizi olmali")
        eklentiler = []
    gorulen_eklentiler: set[str] = set()
    for eklenti in eklentiler:
        if not isinstance(eklenti, dict) or not eklenti.get("name") or not eklenti.get("source"):
            hatalar.append(f"marketplace girdisi eksik (name/source): {eklenti}")
            continue
        ad = eklenti["name"]
        if ad in gorulen_eklentiler:
            hatalar.append(f"marketplace eklenti adi tekrarli: {ad}")
        gorulen_eklentiler.add(ad)
        pj_yol = kok / eklenti["source"] / ".claude-plugin" / "plugin.json"
        if not pj_yol.exists():
            hatalar.append(f"{ad}: plugin.json eksik")
            continue
        pj = oku_json(pj_yol, hatalar, f"{ad}/plugin.json")
        if pj.get("name") != ad:
            hatalar.append(f"{ad}: plugin.json name uyusmuyor ({pj.get('name')})")
        if eklenti.get("version") and pj.get("version") and eklenti["version"] != pj["version"]:
            hatalar.append(
                f"{ad}: marketplace surumu ({eklenti['version']}) != plugin.json ({pj['version']})"
            )

    host_hatalari, host_paketleri, _host_skilleri = host_marketplaces_check(kok)
    hatalar.extend(f"HOST PAZARI: {hata}" for hata in host_hatalari)
    if host_paketleri != len(eklentiler):
        hatalar.append(
            f"HOST PAZARI: ortak paket sayisi ({host_paketleri}) != Claude paket sayisi ({len(eklentiler)})"
        )
    return mp, eklentiler


def skilleri_denetle(
    kok: pathlib.Path, hatalar: list[str], uyarilar: list[str]
) -> list[pathlib.Path]:
    """Agent Skills temel sözleşmesini ve eval bağlantılarını doğrula."""
    gorulen_adlar: dict[str, pathlib.Path] = {}
    skiller = sorted(kok.glob("plugins/*/skills/*/SKILL.md"))
    for skill in skiller:
        goreli = skill.relative_to(kok)
        metin = skill.read_text(encoding="utf-8", errors="strict")
        ayrilan = frontmatter(metin)
        if not ayrilan:
            hatalar.append(f"{goreli}: YAML frontmatter yok")
            continue
        fmt, govde_baslangici = ayrilan
        anahtarlar = set(re.findall(r"^([A-Za-z_-]+):", fmt, re.M))
        fazla = anahtarlar - IZINLI_ALANLAR
        if fazla:
            uyarilar.append(f"{goreli}: standart disi frontmatter alanlari: {sorted(fazla)}")

        ad = frontmatter_alani(fmt, "name")
        tarif = frontmatter_alani(fmt, "description")
        if not ad:
            hatalar.append(f"{goreli}: 'name' yok")
            continue
        if len(ad) > 64:
            hatalar.append(f"{goreli}: name > 64 karakter")
        if not AD_DESENI.fullmatch(ad):
            hatalar.append(
                f"{goreli}: name deseni gecersiz (kucuk harf/rakam/tire): '{ad}'"
            )
        if ad != skill.parent.name:
            hatalar.append(
                f"{goreli}: name ('{ad}') klasor adiyla ('{skill.parent.name}') ayni degil"
            )
        if ad in gorulen_adlar:
            hatalar.append(f"CAKISMA: '{ad}' hem {gorulen_adlar[ad]} hem {goreli} icinde")
        gorulen_adlar[ad] = goreli
        if not tarif:
            hatalar.append(f"{goreli}: 'description' yok veya bos")
        elif len(tarif) > 1024:
            hatalar.append(f"{goreli}: description {len(tarif)} karakter (>1024)")

        lisans = frontmatter_alani(fmt, "license") or ""
        if lisans.lower().startswith("proprietary"):
            hatalar.append(f"{goreli}: PROPRIETARY icerik")

        eval_sozlesmesini_denetle(skill.parent, ad, hatalar)

        govde_satir = metin[govde_baslangici:].count("\n")
        if govde_satir > 500:
            uyarilar.append(
                f"{goreli}: govde {govde_satir} satir (>500 onerisi; references/ altina bol)"
            )
    return skiller


def zorunlu_belgeleri_denetle(kok: pathlib.Path, hatalar: list[str]) -> None:
    """Yer tutucu, zorunlu belge ve Claude devralma zincirini doğrula."""
    for dosya in list(kok.glob("**/*.json")) + list(kok.glob("*.md")) + [kok / "LICENSE"]:
        if dosya.is_file() and "DEGISTIR" in dosya.read_text(encoding="utf-8", errors="strict"):
            hatalar.append(f"{dosya.relative_to(kok)}: 'DEGISTIR' kalmis")
    for gerekli in [
        "THIRD_PARTY_LICENSES.md",
        "LICENSE",
        "NOTICE.md",
        "README.md",
        "README.en.md",
        "CHANGELOG.md",
        "VERSION",
        "BLUEPRINT.md",
        "CLAUDE.md",
        "UPSTREAM.md",
        "registry/upstream-baselines.json",
        "CONTRIBUTING.md",
    ]:
        if not (kok / gerekli).exists():
            hatalar.append(f"{gerekli} eksik")

    claude_yolu = kok / "CLAUDE.md"
    if claude_yolu.is_file():
        claude = claude_yolu.read_text(encoding="utf-8")
        for devralma in ["AGENTS.md", "BLUEPRINT.md", ".divan/progress.md", "scripts/devral.py --check"]:
            if devralma not in claude:
                hatalar.append(f"CLAUDE DEVRALMA ESKI: CLAUDE.md '{devralma}' kaydini icermiyor")


def ajanlari_denetle(kok: pathlib.Path, hatalar: list[str]) -> None:
    """Subagent frontmatter ve hook JSON sözleşmelerini doğrula."""
    for ajan in kok.glob("plugins/*/agents/*.md"):
        metin = ajan.read_text(encoding="utf-8", errors="strict")
        ayrilan = frontmatter(metin)
        if not ayrilan:
            hatalar.append(f"{ajan.relative_to(kok)}: subagent frontmatter eksik")
            continue
        fmt, _ = ayrilan
        if not frontmatter_alani(fmt, "name") or not frontmatter_alani(fmt, "description"):
            hatalar.append(f"{ajan.relative_to(kok)}: subagent name/description eksik")
    for hook in kok.glob("plugins/*/hooks/hooks.json"):
        oku_json(hook, hatalar, str(hook.relative_to(kok)))


def vitrini_denetle(
    kok: pathlib.Path,
    marketplace: dict,
    eklentiler: list,
    skiller: list[pathlib.Path],
    hatalar: list[str],
) -> None:
    """Katalog, belge, komut ve sürüm yüzeylerinin aynı gerçeği taşımasını sağla."""
    gercek_sayi = len(skiller)
    katalog = kok / "docs" / "Vezir-Katalogu.md"
    if katalog.exists():
        katalog_sayi = katalog.read_text(encoding="utf-8").count("| **")
        if katalog_sayi != gercek_sayi:
            hatalar.append(
                f"VITRIN ESKI: katalog {katalog_sayi} vezir diyor, gercek {gercek_sayi}"
            )

    belgeler = {
        "README": (kok / "README.md").read_text(encoding="utf-8"),
        "Kurulum": (kok / "docs" / "Kurulum.md").read_text(encoding="utf-8"),
        "Kaldirma": (kok / "docs" / "Kaldirma.md").read_text(encoding="utf-8"),
        "Standartlar": (kok / "docs" / "Standartlar-ve-Limitler.md").read_text(
            encoding="utf-8"
        ),
    }
    for belge_adi in ["README", "Kurulum", "Standartlar"]:
        icerik = belgeler[belge_adi]
        if f"{gercek_sayi} vezir" not in icerik and f"{gercek_sayi} skill" not in icerik:
            hatalar.append(f"VITRIN ESKI: {belge_adi} guncel skill sayisini ({gercek_sayi}) anmiyor")
    for eklenti in eklentiler:
        ad = eklenti.get("name") if isinstance(eklenti, dict) else None
        if not ad:
            continue
        for belge_adi in ["README", "Kurulum", "Kaldirma"]:
            if ad not in belgeler[belge_adi]:
                hatalar.append(f"VITRIN ESKI: {belge_adi} '{ad}' paketini anmiyor")
    for komut in kok.glob("plugins/*/commands/*.md"):
        if f"/{komut.stem}" not in belgeler["README"]:
            hatalar.append(f"VITRIN ESKI: README /{komut.stem} komutunu anmiyor")

    surum_kayitlarini_denetle(kok, marketplace, hatalar)


def denetle(kok: pathlib.Path = KOK) -> tuple[list[str], list[str], int, int]:
    """Bağımsız denetçileri tek raporda birleştiren ince orkestratör."""
    hatalar: list[str] = []
    uyarilar: list[str] = []
    marketplace, eklentiler = marketplace_denetle(kok, hatalar)
    skiller = skilleri_denetle(kok, hatalar, uyarilar)
    zorunlu_belgeleri_denetle(kok, hatalar)
    ajanlari_denetle(kok, hatalar)
    vitrini_denetle(kok, marketplace, eklentiler, skiller, hatalar)

    return hatalar, uyarilar, len(eklentiler), len(skiller)


def main() -> int:
    hatalar, uyarilar, paket_sayisi, skill_sayisi = denetle()
    for uyari in uyarilar:
        print(f"UYARI: {uyari}")
    if hatalar:
        print("\nTEFTIS BASARISIZ:")
        for hata in hatalar:
            print(f"  X {hata}")
        return 1
    print(
        f"\nTEFTIS TEMIZ - {paket_sayisi} paket, {skill_sayisi} skill; "
        "ad cakismasi yok, surumler ve vitrin tutarli"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
