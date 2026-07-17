#!/usr/bin/env python3
"""Aylik nobet: vendored skill'leri taze upstream klonlariyla karsilastir.

Cikis kodlari: 0 temiz, 2 kurasyon gerektiren fark, 1 denetim calismadi.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile


REPOLAR = [
    "obra/superpowers",
    "anthropics/skills",
    "vercel-labs/agent-skills",
    "nextlevelbuilder/ui-ux-pro-max-skill",
]
OZGUN = {
    "sadrazam",
    "vezir-yetistirme",
    "defterdar",
    "musavir",
    "ordu-nizami",
    "temkin",
    "kural-hazinesi",
}
KURASYON_KAYNAKLARI = {
    "PatrickJS/awesome-cursorrules": "b044f956f021b6e8877f16781bcfc466a6a120e9",
}
# Bilincli farklarda upstream dosyasinin bilinen taban imzasi da sabitlenir.
# Boylece upstream ayni dosyayi degistirirse izin listesi bu degisimi gizlemez.
YAMALAR = {
    ("claude-api", "SKILL.md"): "1d08b3be1c02b6bd2d8c966b1645e234fbb36454d2dd4cbd39802d2f321bd0f4",
    ("vercel-react-best-practices", "AGENTS.md"): "fc93e7421177bbf869cce892bc60a6c83a4517d974bc3bf65c4e2c1e58a6ccf6",
}
KOK = pathlib.Path(__file__).resolve().parent.parent


def sha256(dosya: pathlib.Path) -> str:
    return hashlib.sha256(dosya.read_bytes()).hexdigest()


def harita(kok: pathlib.Path) -> dict[str, pathlib.Path]:
    sonuc: dict[str, pathlib.Path] = {}
    for skill in kok.rglob("SKILL.md"):
        eslesme = re.search(
            r"^name:\s*(.+)$", skill.read_text(errors="ignore")[:4000], re.M
        )
        if eslesme:
            sonuc[eslesme.group(1).strip()] = skill.parent
    return sonuc


def imza(dizin: pathlib.Path) -> dict[str, str]:
    return {
        str(dosya.relative_to(dizin)): sha256(dosya)
        for dosya in sorted(dizin.rglob("*"))
        if dosya.is_file()
        and ".git" not in dosya.parts
        and "__pycache__" not in dosya.parts
        and dosya.suffix != ".pyc"
    }


def klonla(repo: str, hedef: pathlib.Path) -> str:
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"https://github.com/{repo}", str(hedef)],
        check=True,
        timeout=120,
    )
    return subprocess.check_output(
        ["git", "-C", str(hedef), "rev-parse", "HEAD"], text=True, timeout=15
    ).strip()


def denetle() -> list[str]:
    degisen: list[str] = []
    with tempfile.TemporaryDirectory(prefix="divan-nobet-") as gecici:
        tmp = pathlib.Path(gecici)
        upstream: dict[str, pathlib.Path] = {}

        for sira, repo in enumerate(REPOLAR):
            hedef = tmp / f"upstream-{sira}"
            klonla(repo, hedef)
            upstream.update(harita(hedef))

        for sira, (repo, taban_commit) in enumerate(KURASYON_KAYNAKLARI.items()):
            guncel = klonla(repo, tmp / f"curated-{sira}")
            if guncel != taban_commit:
                degisen.append(
                    f"- **{repo}**: kure edilen kaynak ilerledi "
                    f"({taban_commit[:12]} -> {guncel[:12]})"
                )

        for skill_md in sorted(KOK.glob("plugins/*/skills/*/SKILL.md")):
            eslesme = re.search(
                r"^name:\s*(.+)$", skill_md.read_text(errors="ignore")[:4000], re.M
            )
            if not eslesme:
                continue
            ad = eslesme.group(1).strip()
            if ad in OZGUN:
                continue
            if ad not in upstream:
                degisen.append(f"- **{ad}**: upstream skill artik bulunamadi")
                continue

            yerel, ust = imza(skill_md.parent), imza(upstream[ad])
            tum_dosyalar = set(yerel) | set(ust)
            farklar = sorted(dosya for dosya in tum_dosyalar if yerel.get(dosya) != ust.get(dosya))
            beklenmeyen: list[str] = []
            for dosya in farklar:
                taban_imza = YAMALAR.get((ad, dosya))
                upstream_imza = ust.get(dosya)
                if taban_imza and upstream_imza == taban_imza:
                    continue
                beklenmeyen.append(dosya)
            if beklenmeyen:
                ozet = ", ".join(beklenmeyen[:8])
                if len(beklenmeyen) > 8:
                    ozet += f" (+{len(beklenmeyen) - 8})"
                degisen.append(f"- **{ad}**: {ozet}")

    return degisen


def main() -> int:
    try:
        degisen = denetle()
    except (OSError, subprocess.SubprocessError) as hata:
        print(f"NOBET CALISMADI: {hata}", file=sys.stderr)
        return 1
    if degisen:
        print("UPSTREAM DEGISIMI VAR:\n" + "\n".join(degisen))
        print("\nFarki lisans ve urun degeri acisindan inceleyip kurasyon karari verin.")
        return 2
    print("Nobet temiz: vendored vezirler ve kure edilen kaynaklar izlenen tabanla uyumlu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
