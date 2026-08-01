#!/usr/bin/env python3
"""Bir ajanın Divan'ı sohbet geçmişi olmadan devralabildiğini denetle."""

# English canonical implementation.
from __future__ import annotations

import argparse
import pathlib
import re
import sys

KOK = pathlib.Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
REPUBLICATION = re.compile(
    r"\bpush\b|\bpublish\b|\bopen\b.{0,40}\b(?:pull request|pr)\b",
    re.IGNORECASE | re.DOTALL,
)
ZORUNLU = {
    "Claude sözleşmesi": "CLAUDE.md",
    "ajan sözleşmesi": "AGENTS.md",
    "ürün hafızası": "BLUEPRINT.md",
    "ilerleme defteri": ".divan/progress.md",
    "sürüm kaynağı": "VERSION",
    "yayın manifestosu": "release-manifest.json",
    "v1 kapıları": "registry/v1-gates.json",
}


def _bolum(metin: str, baslik: str) -> str | None:
    eslesme = re.search(
        rf"^## {re.escape(baslik)}\s*\n(?P<body>.*?)(?=^## |\Z)",
        metin,
        re.MULTILINE | re.DOTALL,
    )
    return eslesme.group("body").strip() if eslesme else None


def _alan(bolum: str, etiket: str) -> str | None:
    eslesme = re.search(
        rf"^- {re.escape(etiket)}:\s*(?P<value>\S.*?)\s*$",
        bolum,
        re.MULTILINE,
    )
    return eslesme.group("value").strip() if eslesme else None


def _semver_tuple(deger: str) -> tuple[int, int, int] | None:
    eslesme = SEMVER.fullmatch(deger)
    if not eslesme:
        return None
    return (int(eslesme.group(1)), int(eslesme.group(2)), int(eslesme.group(3)))


def _yayin_alanlarini_oku(bolum: str) -> tuple[tuple[str, str, str] | None, list[str]]:
    hatalar: list[str] = []
    yayin_surum = _alan(bolum, "Latest published release")
    commit = _alan(bolum, "Published commit")
    evidence_goreli = _alan(bolum, "Publication evidence")
    if yayin_surum is None or not yayin_surum.startswith("v"):
        hatalar.append("yayın durumu geçerli Latest published release içermiyor")
    if commit is None or not COMMIT.fullmatch(commit):
        hatalar.append("yayın durumu 40 karakterli küçük harf commit SHA içermiyor")
    if evidence_goreli is None:
        hatalar.append("yayın durumu Publication evidence yolu içermiyor")
    if hatalar:
        return None, hatalar
    assert yayin_surum is not None and commit is not None and evidence_goreli is not None
    return (yayin_surum, commit, evidence_goreli), []


def _surum_hatalari(yayin_surum: str, mevcut_surum: str) -> list[str]:
    hatalar: list[str] = []
    yayin_semver = _semver_tuple(yayin_surum[1:])
    mevcut_semver = _semver_tuple(mevcut_surum)
    if yayin_semver is None:
        hatalar.append(f"yayın durumu SemVer değil: {yayin_surum!r}")
    if mevcut_semver is None:
        hatalar.append(f"VERSION SemVer değil: {mevcut_surum!r}")
    if yayin_semver is not None and mevcut_semver is not None and yayin_semver > mevcut_semver:
        hatalar.append("son yayımlanmış sürüm VERSION değerinden yeni olamaz")
    return hatalar


def _evidence_hatalari(
    kok: pathlib.Path,
    evidence_goreli: str,
    yayin_surum: str,
    commit: str,
) -> list[str]:
    evidence_posix = pathlib.PurePosixPath(evidence_goreli)
    evidence_yolu = (kok / evidence_posix).resolve()
    if (
        evidence_posix.is_absolute()
        or ".." in evidence_posix.parts
        or evidence_posix.parts[:2] != (".divan", "evidence")
        or evidence_posix.suffix != ".md"
        or not evidence_yolu.is_relative_to(kok.resolve())
    ):
        return ["Publication evidence repo içinde göreli bir .divan/evidence/*.md olmalı"]
    if not evidence_yolu.is_file():
        return [f"Publication evidence eksik veya dosya değil: {evidence_goreli}"]
    evidence = evidence_yolu.read_text(encoding="utf-8")
    hatalar: list[str] = []
    if f"- Version: {yayin_surum}" not in evidence:
        hatalar.append("yayın kanıtı sürümü progress kaydıyla eşleşmiyor")
    if f"- Source commit: {commit}" not in evidence:
        hatalar.append("yayın kanıtı commit'i progress kaydıyla eşleşmiyor")
    return hatalar


def _sonraki_adim_hatalari(progress_metin: str, yayin_surum: str) -> list[str]:
    sonraki = _bolum(progress_metin, "Sıradaki kesin iş")
    if (
        sonraki is not None
        and yayin_surum.casefold() in sonraki.casefold()
        and REPUBLICATION.search(sonraki)
    ):
        return ["sıradaki adım zaten yayımlanmış sürümü yeniden yayımlamaya çalışıyor"]
    return []


def _yayin_durumunu_denetle(
    kok: pathlib.Path,
    progress_metin: str,
    mevcut_surum: str,
) -> list[str]:
    yayin = _bolum(progress_metin, "Yayın durumu")
    if yayin is None:
        return [".divan/progress.md yayın durumu sözleşmesini içermiyor"]
    alanlar, hatalar = _yayin_alanlarini_oku(yayin)
    if alanlar is None:
        return hatalar
    yayin_surum, commit, evidence_goreli = alanlar
    hatalar.extend(_surum_hatalari(yayin_surum, mevcut_surum))
    hatalar.extend(_evidence_hatalari(kok, evidence_goreli, yayin_surum, commit))
    hatalar.extend(_sonraki_adim_hatalari(progress_metin, yayin_surum))
    return hatalar


def denetle(kok: pathlib.Path = KOK) -> list[str]:
    hatalar: list[str] = []
    for etiket, goreli in ZORUNLU.items():
        yol = kok / goreli
        if not yol.is_file() or not yol.read_text(encoding="utf-8").strip():
            hatalar.append(f"{etiket} eksik veya boş: {goreli}")
    claude_yolu = kok / "CLAUDE.md"
    claude = claude_yolu.read_text(encoding="utf-8") if claude_yolu.is_file() else ""
    for goreli in ("AGENTS.md", "BLUEPRINT.md", ".divan/progress.md"):
        if goreli not in claude:
            hatalar.append(f"CLAUDE.md devralmada {goreli} dosyasını okumuyor")
    progress = kok / ".divan/progress.md"
    version = kok / "VERSION"
    if progress.is_file():
        progress_metin = progress.read_text(encoding="utf-8")
        if progress_metin.count("## Sıradaki kesin iş") != 1:
            hatalar.append(".divan/progress.md tek bir sıradaki kesin iş içermeli")
        if version.is_file():
            hatalar.extend(
                _yayin_durumunu_denetle(
                    kok,
                    progress_metin,
                    version.read_text(encoding="utf-8").strip(),
                )
            )
    return hatalar


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    hatalar = denetle()
    if hatalar:
        for hata in hatalar:
            print(f"HATA: {hata}", file=sys.stderr)
        return 1
    print("DEVRAL TEMİZ — Claude Code sözleşme, yön, durum ve yayın kayıtlarını buldu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
