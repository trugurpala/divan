#!/usr/bin/env python3
"""Bir ajanın Divan'ı sohbet geçmişi olmadan devralabildiğini denetle."""

# English canonical implementation.
from __future__ import annotations

import argparse
import pathlib
import sys

KOK = pathlib.Path(__file__).resolve().parent.parent
ZORUNLU = {
    "Claude sözleşmesi": "CLAUDE.md",
    "ajan sözleşmesi": "AGENTS.md",
    "ürün hafızası": "BLUEPRINT.md",
    "ilerleme defteri": ".divan/progress.md",
    "sürüm kaynağı": "VERSION",
    "yayın manifestosu": "release-manifest.json",
    "v1 kapıları": "registry/v1-gates.json",
}


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
    if progress.is_file() and "## Sıradaki kesin adım" not in progress.read_text(encoding="utf-8"):
        hatalar.append(".divan/progress.md sıradaki kesin adımı içermiyor")
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
