#!/usr/bin/env python3
"""Divan Aday Meclisi defterini doğrula ve insan-okunur kataloğu üret."""

# English canonical implementation.
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import urllib.error
import urllib.request

KOK = pathlib.Path(__file__).resolve().parent.parent
DEFTER = KOK / "registry" / "candidates.json"
KATALOG = KOK / "docs" / "Aday-Meclisi.md"
ID_DESENI = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GITHUB_DESENI = re.compile(r"^https://github\.com/[^/\s]+/[^/\s]+$")
SHA_DESENI = re.compile(r"^[0-9a-f]{40}$")
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


ADAY_METIN_ALANLARI = (
    "id", "name", "canonical_url", "type", "status", "decision", "user_gap",
    "execution_review", "risk_notes", "rationale",
)


def _metin_alanlarini_denetle(aday: object, onek: str) -> dict:
    if not isinstance(aday, dict):
        raise ValueError(f"{onek} nesne olmalı")
    for alan in ADAY_METIN_ALANLARI:
        if not isinstance(aday.get(alan), str) or not aday[alan].strip():
            raise ValueError(f"{onek}.{alan} dolu metin olmalı")
    return aday


def _karar_durumunu_denetle(aday: dict, onek: str) -> None:
    if aday["status"] not in DURUMLAR or aday["decision"] not in KARARLAR:
        raise ValueError(f"{onek} durum/karar geçersiz")
    if aday["decision"] == "PENDING":
        if aday["status"] not in {"new", "triage", "audit"}:
            raise ValueError(f"{onek}: PENDING yalnız açık durumlarda olabilir")
    elif SON_KARAR_DURUMU[aday["decision"]] != aday["status"]:
        raise ValueError(f"{onek}: karar ile durum uyuşmuyor")
    if aday["execution_review"] not in {"not-executed", "metadata-only", "reviewed"}:
        raise ValueError(f"{onek}.execution_review geçersiz")


def _immutable_kaniti_denetle(aday: dict, kanitlar: list[str], onek: str) -> None:
    if aday["decision"] == "PENDING":
        return
    reviewed_head = aday.get("reviewed_head")
    if not isinstance(reviewed_head, str) or not SHA_DESENI.fullmatch(reviewed_head):
        raise ValueError(f"{onek}.reviewed_head 40 haneli commit olmalı")
    if not any(reviewed_head in kanit for kanit in kanitlar):
        raise ValueError(f"{onek}.reviewed_head immutable kanıtlara bağlanmalı")


def _lisans_ve_kanitlari_denetle(aday: dict, onek: str) -> None:
    lisans = aday.get("license")
    if not isinstance(lisans, dict):
        raise ValueError(f"{onek}.license nesne olmalı")
    for alan in ("spdx", "evidence_url", "scope_note"):
        if not isinstance(lisans.get(alan), str) or not lisans[alan].strip():
            raise ValueError(f"{onek}.license.{alan} dolu metin olmalı")
    if aday["decision"] in {"ADOPT", "ADAPT"} and lisans["spdx"] == "UNKNOWN":
        raise ValueError(f"{onek}: lisansı belirsiz aday alınamaz/uyarlanamaz")
    kanitlar = aday.get("evidence")
    if not isinstance(kanitlar, list) or not all(
        isinstance(k, str) and k.startswith("https://") for k in kanitlar
    ):
        raise ValueError(f"{onek}.evidence HTTPS adresleri dizisi olmalı")
    if aday["decision"] != "PENDING" and len(set(kanitlar)) < 2:
        raise ValueError(f"{onek}: son karar en az iki kanıt ister")
    if lisans["evidence_url"] not in kanitlar:
        raise ValueError(f"{onek}: lisans kanıtı evidence içinde olmalı")
    _immutable_kaniti_denetle(aday, kanitlar, onek)


def denetle(veri: dict) -> list[dict]:
    adaylar = veri["candidates"]
    kimlikler: set[str] = set()
    adresler: set[str] = set()
    for sira, ham_aday in enumerate(adaylar, start=1):
        onek = f"candidates[{sira}]"
        aday = _metin_alanlarini_denetle(ham_aday, onek)
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
        _karar_durumunu_denetle(aday, onek)
        _lisans_ve_kanitlari_denetle(aday, onek)
        tarih(aday.get("observed_at"), f"{onek}.observed_at")
        tarih(aday.get("next_review"), f"{onek}.next_review")
    return adaylar


def _github_istegi(url: str) -> urllib.request.Request:
    basliklar = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "divan-candidate-review/1",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        basliklar["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=basliklar)


def uzak_kanitlari_denetle(
    veri: dict,
    *,
    opener=urllib.request.urlopen,
    timeout: int = 15,
) -> int:
    """Final Meclis kararlarının commit ve lisans URL'lerini GitHub'da çöz."""
    adaylar = denetle(veri)
    sayi = 0
    for aday in adaylar:
        if aday["decision"] == "PENDING":
            continue
        repo_yolu = aday["canonical_url"].removeprefix("https://github.com/")
        commit_url = (
            f"https://api.github.com/repos/{repo_yolu}/commits/"
            f"{aday['reviewed_head']}"
        )
        for etiket, url in (
            ("GitHub commit", commit_url),
            ("lisans URL", aday["license"]["evidence_url"]),
        ):
            try:
                with opener(_github_istegi(url), timeout=timeout) as yanit:
                    if getattr(yanit, "status", 200) != 200:
                        raise ValueError(f"HTTP {yanit.status}")
            except (OSError, urllib.error.URLError, ValueError) as hata:
                raise ValueError(
                    f"{aday['id']}: {etiket} kanıtı çözümlenemedi: {url}"
                ) from hata
        sayi += 1
    return sayi


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
    kip.add_argument("--resolve", action="store_true")
    secim = ayrac.parse_args()
    veri = oku()
    if secim.resolve:
        sayi = uzak_kanitlari_denetle(veri)
        print(json.dumps({"status": "resolved", "candidate_count": sayi}, ensure_ascii=False))
        return 0
    beklenen = katalog_uret(veri)
    if secim.render:
        KATALOG.write_text(beklenen, encoding="utf-8", newline="\n")
        print(f"{KATALOG.relative_to(KOK)} güncellendi")
        return 0
    gercek = KATALOG.read_text(encoding="utf-8") if KATALOG.exists() else ""
    if gercek != beklenen:
        raise SystemExit("Aday Meclisi kataloğu eski; python scripts/candidate_review.py --render çalıştır")
    print(json.dumps({"status": "valid", "candidate_count": len(veri["candidates"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
