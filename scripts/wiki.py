#!/usr/bin/env python3
"""Divan Wiki sayfalarını sürümlü docs kaynaklarından derle ve denetle."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import tempfile


KOK = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = KOK / "wiki-pages.json"
SLUG = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
WIKI_LINK = re.compile(r"\[\[(?:[^]|]+\|)?([^]]+)\]\]")


def manifesti_oku(kok: pathlib.Path = KOK) -> list[dict[str, str]]:
    yol = kok / MANIFEST.name
    veri = json.loads(yol.read_text(encoding="utf-8"))
    sayfalar = veri.get("pages")
    if not isinstance(sayfalar, list) or not sayfalar:
        raise ValueError("wiki-pages.json en az bir sayfa içermeli")

    kaynaklar: set[str] = set()
    sluglar: set[str] = set()
    basliklar: set[str] = set()
    for sira, sayfa in enumerate(sayfalar, start=1):
        if not isinstance(sayfa, dict):
            raise ValueError(f"pages[{sira}] nesne olmalı")
        for alan in ("source", "slug", "title"):
            if not isinstance(sayfa.get(alan), str) or not sayfa[alan].strip():
                raise ValueError(f"pages[{sira}].{alan} dolu metin olmalı")
        kaynak = sayfa["source"]
        slug = sayfa["slug"]
        baslik = sayfa["title"]
        if pathlib.PurePosixPath(kaynak).is_absolute() or ".." in pathlib.PurePosixPath(kaynak).parts:
            raise ValueError(f"wiki kaynağı repo dışına çıkamaz: {kaynak}")
        if not SLUG.fullmatch(slug):
            raise ValueError(f"geçersiz Wiki slug: {slug}")
        if kaynak in kaynaklar or slug in sluglar or baslik in basliklar:
            raise ValueError(f"yinelenen Wiki kaydı: {sayfa}")
        kaynaklar.add(kaynak)
        sluglar.add(slug)
        basliklar.add(baslik)
    if sayfalar[0]["slug"] != "Home":
        raise ValueError("ilk Wiki sayfası Home olmalı")
    return sayfalar


def derle(cikti: pathlib.Path, kok: pathlib.Path = KOK) -> list[pathlib.Path]:
    sayfalar = manifesti_oku(kok)
    cikti.mkdir(parents=True, exist_ok=True)
    for eski in cikti.glob("*.md"):
        eski.unlink()

    uretilen: list[pathlib.Path] = []
    for sayfa in sayfalar:
        kaynak = (kok / sayfa["source"]).resolve()
        if not kaynak.is_relative_to(kok.resolve()) or not kaynak.is_file():
            raise FileNotFoundError(f"Wiki kaynağı bulunamadı: {sayfa['source']}")
        hedef = cikti / f"{sayfa['slug']}.md"
        shutil.copyfile(kaynak, hedef)
        uretilen.append(hedef)

    kenar = cikti / "_Sidebar.md"
    satirlar = ["## Divan Wiki", ""]
    satirlar.extend(f"- [[{s['title']}|{s['slug']}]]" for s in sayfalar)
    kenar.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    uretilen.append(kenar)
    return uretilen


def denetle(kok: pathlib.Path = KOK) -> dict[str, object]:
    surum = (kok / "VERSION").read_text(encoding="utf-8").strip()
    with tempfile.TemporaryDirectory(prefix="divan-wiki-") as gecici:
        cikti = pathlib.Path(gecici)
        dosyalar = derle(cikti, kok)
        sluglar = {p.stem for p in dosyalar}
        if "Home" not in sluglar or "_Sidebar" not in sluglar:
            raise ValueError("Home veya _Sidebar üretilmedi")

        for zorunlu in ("Home.md", "Durum-ve-Yol-Haritasi.md"):
            metin = (cikti / zorunlu).read_text(encoding="utf-8")
            if f"v{surum}" not in metin:
                raise ValueError(f"{zorunlu} v{surum} sürümünü anmıyor")

        izinli_hedefler = sluglar | {
            s["title"] for s in manifesti_oku(kok)
        }
        for dosya in dosyalar:
            metin = dosya.read_text(encoding="utf-8")
            for hedef in WIKI_LINK.findall(metin):
                if hedef not in izinli_hedefler:
                    raise ValueError(f"{dosya.name}: kırık Wiki bağlantısı [[{hedef}]]")

    return {"status": "valid", "version": surum, "page_count": len(dosyalar)}


def main() -> int:
    ayrac = argparse.ArgumentParser()
    kip = ayrac.add_mutually_exclusive_group(required=True)
    kip.add_argument("--check", action="store_true")
    kip.add_argument("--build", type=pathlib.Path)
    secim = ayrac.parse_args()

    if secim.check:
        print(json.dumps(denetle(), ensure_ascii=False))
    else:
        dosyalar = derle(secim.build)
        print(json.dumps({"status": "built", "page_count": len(dosyalar)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
