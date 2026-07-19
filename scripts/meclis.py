#!/usr/bin/env python3
"""Divan Aday Meclisi defterini doğrula ve insan-okunur kataloğu üret."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parent.parent
DEFTER = KOK / "registry" / "candidates.json"
KATALOG = KOK / "docs" / "Aday-Meclisi.md"
ID_DESENI = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GITHUB_DESENI = re.compile(r"^https://github\.com/[^/\s]+/[^/\s]+$")
TIPLER = {"skill-plugin", "registry-index", "framework-library", "app-template", "standard-research"}
KARARLAR = {"PENDING", "ADOPT", "ADAPT", "REFERENCE", "REJECT"}
DURUMLAR = {"new", "triage", "audit", "accepted", "adapted", "reference", "rejected"}
SON_KARAR_DURUMU = {
    "ADOPT": "accepted",
    "ADAPT": "adapted",
    "REFERENCE": "reference",
    "REJECT": "rejected",
}


def tarih(deger: object, etiket: str) -> str:
    if not isinstance(deger, str):
        raise ValueError(f"{etiket} ISO tarih olmalı")
    try:
        dt.date.fromisoformat(deger)
    except ValueError as hata:
        raise ValueError(f"{etiket} ISO tarih değil: {deger}") from hata
    return deger


def oku(kok: pathlib.Path = KOK) -> dict:
    veri = json.loads((kok / "registry" / "candidates.json").read_text(encoding="utf-8"))
    if veri.get("schema_version") != 1:
        raise ValueError("schema_version 1 olmalı")
    if veri.get("autonomy") != "never-auto-install":
        raise ValueError("Meclis hiçbir adayı otomatik kuramaz")
    adaylar = veri.get("candidates")
    if not isinstance(adaylar, list):
        raise ValueError("candidates dizi olmalı")
    return veri


def denetle(veri: dict) -> list[dict]:
    adaylar = veri["candidates"]
    kimlikler: set[str] = set()
    adresler: set[str] = set()
    for sira, aday in enumerate(adaylar, start=1):
        onek = f"candidates[{sira}]"
        if not isinstance(aday, dict):
            raise ValueError(f"{onek} nesne olmalı")
        for alan in ("id", "name", "canonical_url", "type", "status", "decision", "user_gap", "execution_review", "risk_notes", "rationale"):
            if not isinstance(aday.get(alan), str) or not aday[alan].strip():
                raise ValueError(f"{onek}.{alan} dolu metin olmalı")
        if not ID_DESENI.fullmatch(aday["id"]):
            raise ValueError(f"{onek}.id tireli küçük harf biçiminde olmalı")
        if aday["id"] in kimlikler:
            raise ValueError(f"yinelenen aday id: {aday['id']}")
        kimlikler.add(aday["id"])
        if not GITHUB_DESENI.fullmatch(aday["canonical_url"]):
            raise ValueError(f"{onek}.canonical_url kanonik GitHub repo adresi olmalı")
        adres = aday["canonical_url"].lower()
        if adres in adresler:
            raise ValueError(f"yinelenen aday URL: {aday['canonical_url']}")
        adresler.add(adres)
        if aday["type"] not in TIPLER:
            raise ValueError(f"{onek}.type geçersiz: {aday['type']}")
        if aday["status"] not in DURUMLAR or aday["decision"] not in KARARLAR:
            raise ValueError(f"{onek} durum/karar geçersiz")
        if aday["decision"] == "PENDING":
            if aday["status"] not in {"new", "triage", "audit"}:
                raise ValueError(f"{onek}: PENDING yalnız açık durumlarda olabilir")
        elif SON_KARAR_DURUMU[aday["decision"]] != aday["status"]:
            raise ValueError(f"{onek}: karar ile durum uyuşmuyor")
        if aday["execution_review"] not in {"not-executed", "metadata-only", "reviewed"}:
            raise ValueError(f"{onek}.execution_review geçersiz")

        lisans = aday.get("license")
        if not isinstance(lisans, dict):
            raise ValueError(f"{onek}.license nesne olmalı")
        for alan in ("spdx", "evidence_url", "scope_note"):
            if not isinstance(lisans.get(alan), str) or not lisans[alan].strip():
                raise ValueError(f"{onek}.license.{alan} dolu metin olmalı")
        if aday["decision"] in {"ADOPT", "ADAPT"} and lisans["spdx"] == "UNKNOWN":
            raise ValueError(f"{onek}: lisansı belirsiz aday alınamaz/uyarlanamaz")

        kanitlar = aday.get("evidence")
        if not isinstance(kanitlar, list) or not all(isinstance(k, str) and k.startswith("https://") for k in kanitlar):
            raise ValueError(f"{onek}.evidence HTTPS adresleri dizisi olmalı")
        if aday["decision"] != "PENDING" and len(set(kanitlar)) < 2:
            raise ValueError(f"{onek}: son karar en az iki kanıt ister")
        if lisans["evidence_url"] not in kanitlar:
            raise ValueError(f"{onek}: lisans kanıtı evidence içinde olmalı")
        tarih(aday.get("observed_at"), f"{onek}.observed_at")
        tarih(aday.get("next_review"), f"{onek}.next_review")
    return adaylar


def katalog_uret(veri: dict) -> str:
    adaylar = denetle(veri)
    karar_sayilari = {karar: sum(a["decision"] == karar for a in adaylar) for karar in sorted(KARARLAR)}
    satirlar = [
        "# Aday Meclisi",
        "",
        "> Tek doğru kaynak: `registry/candidates.json`. Bu sayfa otomatik üretilir;",
        "> bir adayın burada görünmesi kurulduğu veya onaylandığı anlamına gelmez.",
        "> Otonomi sınırı: `never-auto-install`.",
        "",
        "## Durum",
        "",
        f"Toplam **{len(adaylar)}** aday · " + " · ".join(f"{k}: {v}" for k, v in karar_sayilari.items()),
        "",
        "| Aday | Tür | Lisans | Karar | Sonraki inceleme | Gerekçe |",
        "|---|---|---|---|---|---|",
    ]
    for aday in sorted(adaylar, key=lambda a: a["name"].lower()):
        satirlar.append(
            f"| [{aday['name']}]({aday['canonical_url']}) | `{aday['type']}` | "
            f"{aday['license']['spdx']} | **{aday['decision']}** | {aday['next_review']} | {aday['rationale']} |"
        )
    satirlar.extend(
        [
            "",
            "## Yaşam döngüsü",
            "",
            "1. **Keşif:** GitHub araması veya topluluk formu yalnız aday üretir.",
            "2. **Triage:** Kimlik, tür, mükerrerlik ve kullanıcı boşluğu belirlenir.",
            "3. **Audit:** Lisans, köken, script/hook/araç yetkileri ve bakım kanıtı incelenir.",
            "4. **Karar:** `ADOPT`, `ADAPT`, `REFERENCE` veya `REJECT` gerekçesiyle kaydedilir.",
            "5. **İcra:** Yalnız `ADOPT/ADAPT`; pin, atıf, eval ve tüm teftiş kapılarından sonra ayrı PR ile yapılır.",
            "",
            "Haftalık keşif workflow'u aday kodu indirmez veya çalıştırmaz. Yıldız ve güncellik yalnız keşif sinyalidir; lisans, güvenlik veya kalite kanıtı değildir.",
            "",
        ]
    )
    return "\n".join(satirlar)


def ana() -> int:
    ayrac = argparse.ArgumentParser()
    kip = ayrac.add_mutually_exclusive_group(required=True)
    kip.add_argument("--check", action="store_true")
    kip.add_argument("--render", action="store_true")
    secim = ayrac.parse_args()
    veri = oku()
    beklenen = katalog_uret(veri)
    if secim.render:
        KATALOG.write_text(beklenen, encoding="utf-8")
        print(f"{KATALOG.relative_to(KOK)} güncellendi")
        return 0
    gercek = KATALOG.read_text(encoding="utf-8") if KATALOG.exists() else ""
    if gercek != beklenen:
        raise SystemExit("Aday Meclisi kataloğu eski; python scripts/meclis.py --render çalıştır")
    print(json.dumps({"status": "valid", "candidate_count": len(veri["candidates"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
