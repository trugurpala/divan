#!/usr/bin/env python3
"""Makine-okunur v1 kapılarını insan/Wiki sayfasına deterministik aktar."""

from __future__ import annotations

import argparse
import json
import pathlib


KOK = pathlib.Path(__file__).resolve().parent.parent
KAYNAK = pathlib.Path("registry/v1-gates.json")
HEDEF = pathlib.Path("docs/V1-Hazirlik.md")
DURUMLAR = {
    "passed": "✅ Geçti",
    "ready": "🟡 Hazır; canlı kanıt bekliyor",
    "pending": "⬜ Bekliyor",
}


def oku(kok: pathlib.Path = KOK) -> dict:
    veri = json.loads((kok / KAYNAK).read_text(encoding="utf-8"))
    if veri.get("schema_version") != 1 or veri.get("target") != "1.0.0":
        raise ValueError("v1 kapı defteri şema/target alanı geçersiz")
    kapilar = veri.get("gates")
    if not isinstance(kapilar, list) or not kapilar:
        raise ValueError("v1 kapı defteri boş olamaz")
    gorulen: set[str] = set()
    for sira, kapi in enumerate(kapilar, start=1):
        if not isinstance(kapi, dict):
            raise ValueError(f"gates[{sira}] nesne olmalı")
        kimlik = kapi.get("id")
        if not isinstance(kimlik, str) or not kimlik or kimlik in gorulen:
            raise ValueError(f"gates[{sira}].id eksik veya yineleniyor")
        gorulen.add(kimlik)
        if kapi.get("status") not in DURUMLAR:
            raise ValueError(f"{kimlik}: geçersiz status")
        if not isinstance(kapi.get("title"), str) or not kapi["title"].strip():
            raise ValueError(f"{kimlik}: title zorunlu")
        kanitlar = kapi.get("evidence")
        if not isinstance(kanitlar, list) or not kanitlar:
            raise ValueError(f"{kimlik}: en az bir evidence zorunlu")
        for kanit in kanitlar:
            if not isinstance(kanit, str) or not kanit.strip():
                raise ValueError(f"{kimlik}: boş evidence")
            if kanit.startswith(("http://", "https://")):
                continue
            yol = (kok / kanit).resolve()
            if not yol.is_relative_to(kok.resolve()) or not yol.exists():
                raise ValueError(f"{kimlik}: kanıt bulunamadı: {kanit}")
    return veri


def uret(kok: pathlib.Path = KOK) -> str:
    veri = oku(kok)
    kapilar = veri["gates"]
    gecen = sum(k["status"] == "passed" for k in kapilar)
    hazir = sum(k["status"] == "ready" for k in kapilar)
    satirlar = [
        "# v1 Hazırlık Karnesi",
        "",
        "Hedef sürüm: v1.0.0",
        "",
        f"> **Bugünkü sonuç:** {gecen}/{len(kapilar)} kapı kanıtla geçti; "
        f"{hazir} kapının otomasyonu hazır fakat canlı kanıtı henüz kaydedilmedi. "
        "Bütün kapılar geçmeden Divan v1 veya ‘dünya standardı’ ilan edilmez.",
        "",
        "| Kapı | Durum | Kanıt |",
        "|---|---|---|",
    ]
    for kapi in kapilar:
        kanit = "<br>".join(f"`{k}`" if not k.startswith("http") else f"[{k}]({k})" for k in kapi["evidence"])
        satirlar.append(f"| {kapi['title']} | {DURUMLAR[kapi['status']]} | {kanit} |")
    satirlar.extend(
        [
            "",
            "## Durumların anlamı",
            "",
            "- **Geçti:** kanıt üretildi ve tekrar denetlenebilir.",
            "- **Hazır:** uygulama/CI kapısı yazıldı; `main` veya Release üstünde başarılı koşu bekleniyor.",
            "- **Bekliyor:** ürünün kendi kendine uyduramayacağı gerçek dış kanıt gerekiyor.",
            "",
            "## v1 için kalan gerçek işler",
            "",
            "1. Gerçek bir ajan adaptörü ve bağımsız hakemle aynı vakaları baseline/skill olarak koşup sonucu yayımlamak.",
            "2. Proje sahibi dışındaki en az bir kullanıcının sabitlenmiş release üzerinden kurulum ve görev kanıtını kabul formuyla göndermesi.",
            "",
            "Bu sayfa elle güncellenmez. Kaynak `registry/v1-gates.json`; üretim "
            "`python scripts/v1.py --render`, sapma teftişi `python scripts/v1.py --check` komutudur.",
            "",
        ]
    )
    return "\n".join(satirlar)


def yaz(kok: pathlib.Path = KOK) -> None:
    (kok / HEDEF).write_text(uret(kok), encoding="utf-8")


def denetle(kok: pathlib.Path = KOK) -> None:
    beklenen = uret(kok)
    gercek = (kok / HEDEF).read_text(encoding="utf-8") if (kok / HEDEF).is_file() else ""
    if gercek != beklenen:
        raise ValueError("docs/V1-Hazirlik.md kapı defterinden farklı; python scripts/v1.py --render çalıştır")


def main() -> int:
    ayrac = argparse.ArgumentParser()
    kip = ayrac.add_mutually_exclusive_group(required=True)
    kip.add_argument("--render", action="store_true")
    kip.add_argument("--check", action="store_true")
    secim = ayrac.parse_args()
    if secim.render:
        yaz()
        print(f"{HEDEF} üretildi")
    else:
        denetle()
        print(json.dumps({"status": "valid", "target": "1.0.0"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
