#!/usr/bin/env python3
"""Divan yayın kontrol düzlemi: hazırla, sapmayı denetle, release notu üret."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

KOK = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = pathlib.Path("release-manifest.json")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def manifesti_oku(kok: pathlib.Path = KOK) -> dict:
    veri = json.loads((kok / MANIFEST).read_text(encoding="utf-8"))
    if veri.get("schema_version") != 1 or veri.get("version_source") != "VERSION":
        raise ValueError("release-manifest.json şeması geçersiz")
    yuzeyler = veri.get("public_surfaces")
    if not isinstance(yuzeyler, list) or not yuzeyler:
        raise ValueError("release manifesti public_surfaces içermeli")
    return veri


def surum(kok: pathlib.Path = KOK) -> str:
    deger = (kok / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(deger):
        raise ValueError(f"VERSION SemVer değil: {deger!r}")
    return deger


def changelog_bolumu(kok: pathlib.Path = KOK, version: str | None = None) -> str:
    version = version or surum(kok)
    metin = (kok / "CHANGELOG.md").read_text(encoding="utf-8")
    eslesme = re.search(
        rf"^## \[{re.escape(version)}\](?:\s+-\s+[^\n]+)?\n(?P<body>.*?)(?=^## \[|\Z)",
        metin,
        re.MULTILINE | re.DOTALL,
    )
    if not eslesme:
        raise ValueError(f"CHANGELOG.md içinde [{version}] bölümü yok")
    govde = eslesme.group("body").strip()
    if not govde:
        raise ValueError(f"CHANGELOG [{version}] bölümü boş")
    return govde


def release_notu(kok: pathlib.Path = KOK) -> str:
    version = surum(kok)
    govde = changelog_bolumu(kok, version)
    return (
        f"# Divan v{version}\n\n{govde}\n\n"
        "## Sabitlenmiş kurulum\n\n"
        f"- Claude Code: marketplace'i ekledikten sonra paketleri `divan` kaynağından kurun.\n"
        f"- Codex/macOS/Linux: `DIVAN_REF=v{version}` ile `scripts/kur-codex.sh` kullanın.\n"
        f"- Codex/Windows: `$env:DIVAN_REF = \"v{version}\"` ile `scripts/kur-codex.ps1` kullanın.\n\n"
        "Yükseltmeden önce [kurulum](https://github.com/trugurpala/divan/wiki/Kurulum) ve "
        "[kaldırma/geri alma](https://github.com/trugurpala/divan/wiki/Kaldirma) rehberlerini okuyun.\n"
    )


def denetle(kok: pathlib.Path = KOK) -> dict:
    veri = manifesti_oku(kok)
    version = surum(kok)
    hatalar: list[str] = []
    kimlikler: set[str] = set()
    for yuzey in veri["public_surfaces"]:
        if not isinstance(yuzey, dict):
            hatalar.append("public surface girdisi nesne olmalı")
            continue
        kimlik = yuzey.get("id")
        yol_metni = yuzey.get("path")
        marker = yuzey.get("marker")
        if not all(
            isinstance(x, str) and bool(x) for x in (kimlik, yol_metni, marker)
        ):
            hatalar.append(f"eksik public surface alanı: {yuzey}")
            continue
        assert isinstance(kimlik, str)
        assert isinstance(yol_metni, str)
        assert isinstance(marker, str)
        if kimlik in kimlikler:
            hatalar.append(f"yinelenen public surface id: {kimlik}")
        kimlikler.add(kimlik)
        yol = (kok / yol_metni).resolve()
        if not yol.is_relative_to(kok.resolve()) or not yol.is_file():
            hatalar.append(f"{kimlik}: dosya bulunamadı: {yol_metni}")
            continue
        beklenen = marker.format(version=version)
        if beklenen not in yol.read_text(encoding="utf-8"):
            hatalar.append(f"{kimlik}: beklenen işaret yok: {beklenen}")

    try:
        changelog_bolumu(kok, version)
    except ValueError as hata:
        hatalar.append(str(hata))

    pazar = json.loads((kok / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    if pazar.get("version") != version or (pazar.get("metadata") or {}).get("version") != version:
        hatalar.append("marketplace version/metadata VERSION ile eşleşmiyor")

    if hatalar:
        raise ValueError("Yayın yüzeyleri farklı:\n- " + "\n- ".join(hatalar))
    return {"status": "valid", "version": version, "surface_count": len(kimlikler)}


def hazirla(yeni: str, kok: pathlib.Path = KOK) -> None:
    if not SEMVER.fullmatch(yeni):
        raise ValueError(f"Yeni sürüm SemVer değil: {yeni!r}")
    eski = surum(kok)
    if yeni == eski:
        raise ValueError(f"VERSION zaten {yeni}")
    veri = manifesti_oku(kok)
    pazar_yolu = kok / ".claude-plugin/marketplace.json"
    pazar = json.loads(pazar_yolu.read_text(encoding="utf-8"))
    pazar["version"] = yeni
    pazar.setdefault("metadata", {})["version"] = yeni
    guncellemeler: list[tuple[pathlib.Path, str]] = []
    for yuzey in veri["public_surfaces"]:
        if not yuzey.get("replace_version"):
            continue
        yol = (kok / yuzey["path"]).resolve()
        if not yol.is_relative_to(kok.resolve()) or not yol.is_file():
            raise ValueError(f"Hazırlanacak yüzey bulunamadı: {yuzey['path']}")
        metin = yol.read_text(encoding="utf-8")
        eski_metin = f"v{eski}"
        eski_rozet = f"version-{eski}"
        if eski_metin not in metin and eski_rozet not in metin:
            raise ValueError(f"{yuzey['path']}: {eski_metin} bulunamadı; sessiz geçilmedi")
        metin = metin.replace(eski_metin, f"v{yeni}")
        metin = metin.replace(eski_rozet, f"version-{yeni}")
        guncellemeler.append((yol, metin))

    # Bütün yüzeyler önce okunup doğrulandı; ancak bundan sonra diske yazılır.
    # Böylece eksik bir işaret yarım sürüm hazırlığı bırakmaz.
    (kok / "VERSION").write_text(yeni + "\n", encoding="utf-8")
    pazar_yolu.write_text(json.dumps(pazar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for yol, metin in guncellemeler:
        yol.write_text(metin, encoding="utf-8")
    print(
        f"v{eski} → v{yeni}: deterministik yüzeyler hazırlandı. "
        "Şimdi CHANGELOG ve BLUEPRINT anlatısını yaz; sonra --check çalıştır."
    )


def main() -> int:
    ayrac = argparse.ArgumentParser()
    kip = ayrac.add_mutually_exclusive_group(required=True)
    kip.add_argument("--check", action="store_true")
    kip.add_argument("--prepare", metavar="SEMVER")
    kip.add_argument("--notes", type=pathlib.Path, metavar="DOSYA")
    kip.add_argument("--status", action="store_true")
    secim = ayrac.parse_args()
    try:
        if secim.prepare:
            hazirla(secim.prepare)
        elif secim.notes:
            secim.notes.write_text(release_notu(), encoding="utf-8")
            print(secim.notes)
        else:
            print(json.dumps(denetle(), ensure_ascii=False))
    except (OSError, ValueError, json.JSONDecodeError) as hata:
        print(f"HATA: {hata}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
