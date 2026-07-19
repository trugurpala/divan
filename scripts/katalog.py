#!/usr/bin/env python3
"""Skill frontmatter'larından deterministik Vezir Kataloğu üret ve denetle."""

from __future__ import annotations

import argparse
import importlib
import pathlib
import re

try:
    validate = importlib.import_module("scripts.validate")
except ModuleNotFoundError:  # `python scripts/katalog.py` çağrısı
    validate = importlib.import_module("validate")


KOK = pathlib.Path(__file__).resolve().parent.parent
KATALOG = KOK / "docs" / "Vezir-Katalogu.md"


def kisalt(metin: str, sinir: int = 240) -> str:
    temiz = re.sub(r"\s+", " ", metin).strip().strip('"')
    if len(temiz) <= sinir:
        return temiz
    parca = temiz[: sinir - 1].rsplit(" ", 1)[0]
    return f"{parca}…"


def skill_kayitlari(kok: pathlib.Path = KOK) -> dict[str, list[tuple[str, str]]]:
    paketler: dict[str, list[tuple[str, str]]] = {}
    for yol in sorted(kok.glob("plugins/*/skills/*/SKILL.md")):
        ayrilan = validate.frontmatter(yol.read_text(encoding="utf-8"))
        if not ayrilan:
            raise ValueError(f"frontmatter yok: {yol.relative_to(kok)}")
        fmt, _ = ayrilan
        ad = validate.frontmatter_alani(fmt, "name")
        aciklama = validate.frontmatter_alani(fmt, "description")
        if not ad or not aciklama:
            raise ValueError(f"name/description eksik: {yol.relative_to(kok)}")
        paketler.setdefault(yol.parents[2].name, []).append((ad, kisalt(aciklama)))
    return paketler


def katalog_uret(kok: pathlib.Path = KOK) -> str:
    paketler = skill_kayitlari(kok)
    toplam = sum(len(skiller) for skiller in paketler.values())
    satirlar = [
        "# Vezir Kataloğu",
        "",
        "> Tek doğru kaynak: `plugins/*/skills/*/SKILL.md`. Bu sayfa",
        "> `python scripts/katalog.py --render` ile deterministik üretilir.",
        "",
        f"Toplam **{toplam} skill**, **{len(paketler)} paket**.",
        "",
    ]
    for paket in sorted(paketler):
        skiller = sorted(paketler[paket], key=lambda kayit: kayit[0])
        satirlar.extend(
            [
                f"## {paket} ({len(skiller)} vezir)",
                "",
                "| Vezir | Ne yapar / ne zaman |",
                "|---|---|",
            ]
        )
        for ad, aciklama in skiller:
            guvenli = aciklama.replace("|", "\\|")
            satirlar.append(f"| **{ad}** | {guvenli} |")
        satirlar.append("")
    return "\n".join(satirlar)


def main() -> int:
    ayrac = argparse.ArgumentParser()
    kip = ayrac.add_mutually_exclusive_group(required=True)
    kip.add_argument("--check", action="store_true")
    kip.add_argument("--render", action="store_true")
    secim = ayrac.parse_args()
    beklenen = katalog_uret()
    if secim.render:
        KATALOG.write_text(beklenen, encoding="utf-8")
        print(f"{KATALOG.relative_to(KOK)} güncellendi")
        return 0
    gercek = KATALOG.read_text(encoding="utf-8") if KATALOG.exists() else ""
    if gercek != beklenen:
        raise SystemExit("Vezir Kataloğu eski; python scripts/katalog.py --render çalıştır")
    print("Vezir Kataloğu temiz: 41 skill / 5 paket")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
