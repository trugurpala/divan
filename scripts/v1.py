#!/usr/bin/env python3
"""Makine-okunur v1 kapılarını insan/Wiki sayfasına deterministik aktar."""

from __future__ import annotations

import argparse
import json
import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parent.parent
KAYNAK = pathlib.Path("registry/v1-gates.json")
HEDEF = pathlib.Path("docs/V1-Hazirlik.md")
DURUMLAR = {
    "passed": "✅ Geçti",
    "ready": "🟡 Hazır; canlı kanıt bekliyor",
    "pending": "⬜ Bekliyor",
}


def _validate_real_agent_evidence(veri: dict, yol: pathlib.Path) -> None:
    """Fail closed when the published blinded run is incomplete or deanonymized."""
    if veri.get("schema_version") != 1 or veri.get("status") != "completed":
        raise ValueError(f"{yol}: real-agent evidence schema/status geçersiz")
    vakalar = veri.get("cases")
    vaka_sayisi = veri.get("case_count")
    hukum_sayisi = veri.get("judged_count")
    if (
        not isinstance(vakalar, list)
        or not isinstance(vaka_sayisi, int)
        or isinstance(vaka_sayisi, bool)
        or vaka_sayisi <= 0
        or vaka_sayisi != len(vakalar)
        or hukum_sayisi != vaka_sayisi
    ):
        raise ValueError(f"{yol}: case/judgement sayıları geçersiz")

    yasak_anahtarlar = {"mapping", "winner", "winner_label", "winner_condition"}

    def ozel_anahtar_ara(deger: object) -> None:
        if isinstance(deger, dict):
            sizan = yasak_anahtarlar & set(deger)
            if sizan:
                raise ValueError(f"{yol}: public evidence private key içeriyor: {sorted(sizan)}")
            for alt in deger.values():
                ozel_anahtar_ara(alt)
        elif isinstance(deger, list):
            for alt in deger:
                ozel_anahtar_ara(alt)

    ozel_anahtar_ara(vakalar)
    for vaka in vakalar:
        if not isinstance(vaka, dict):
            raise ValueError(f"{yol}: case nesne olmalı")
        adaylar = vaka.get("candidates")
        hukum = vaka.get("judgement")
        if not isinstance(adaylar, dict) or list(adaylar) != ["A", "B"]:
            raise ValueError(f"{yol}: public candidates sabit A/B sırasını kullanmalı")
        if not isinstance(hukum, dict) or set(hukum) != {"expectation_scores"}:
            raise ValueError(f"{yol}: public judgement yalnız rubrik skorları içermeli")

    ozet = veri.get("summary")
    if not isinstance(ozet, dict):
        raise ValueError(f"{yol}: summary eksik")
    sayaclar: list[int] = []
    for alan in ("skill_wins", "baseline_wins", "ties"):
        deger = ozet.get(alan)
        if not isinstance(deger, int) or isinstance(deger, bool) or deger < 0:
            raise ValueError(f"{yol}: summary.{alan} geçersiz")
        sayaclar.append(deger)
    if sum(sayaclar) != hukum_sayisi:
        raise ValueError(f"{yol}: summary toplamı judged_count ile eşleşmiyor")
    kararli = sayaclar[0] + sayaclar[1]
    beklenen_oran = sayaclar[0] / kararli if kararli else None
    if ozet.get("skill_win_rate") != beklenen_oran:
        raise ValueError(f"{yol}: skill_win_rate sayaçlarla eşleşmiyor")

    provenance = veri.get("provenance")
    zorunlu = (
        "agent",
        "agent_version",
        "agent_model",
        "judge",
        "judge_version",
        "judge_model",
        "source_commit",
        "divan_version",
        "environment",
        "blind_seed_sha256",
        "blind_seed_entropy_bits",
        "blinding_method",
        "selected_skills",
        "timeout_seconds",
        "minimum_skill_win_rate",
        "run_command",
    )
    if not isinstance(provenance, dict):
        raise ValueError(f"{yol}: provenance eksik")
    if "blind_seed" in provenance:
        raise ValueError(f"{yol}: public evidence private key içeriyor: blind_seed")
    for alan in zorunlu:
        deger = provenance.get(alan)
        if not isinstance(deger, str) or not deger.strip():
            raise ValueError(f"{yol}: provenance.{alan} eksik veya geçersiz")
    if not re.fullmatch(r"[0-9a-f]{40}", provenance["source_commit"]):
        raise ValueError(f"{yol}: provenance.source_commit tam Git SHA olmalı")
    if not re.fullmatch(r"[0-9a-f]{64}", provenance["blind_seed_sha256"]):
        raise ValueError(f"{yol}: provenance.blind_seed_sha256 geçersiz")
    try:
        seed_bitleri = int(provenance["blind_seed_entropy_bits"])
    except ValueError as hata:
        raise ValueError(f"{yol}: provenance.blind_seed_entropy_bits geçersiz") from hata
    if seed_bitleri < 128:
        raise ValueError(f"{yol}: provenance.blind_seed_entropy_bits en az 128 olmalı")
    if provenance["blinding_method"] != "secrets.token_bytes(32)":
        raise ValueError(f"{yol}: provenance.blinding_method geçersiz")
    if "--seed" in provenance["run_command"]:
        raise ValueError(f"{yol}: publishable run_command dışarıdan seed alamaz")


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
        if kimlik == "real-agent-comparison" and kapi["status"] == "passed":
            eval_yollari = [
                (kok / kanit).resolve()
                for kanit in kanitlar
                if kanit.startswith("evals/results/") and kanit.endswith(".json")
            ]
            if len(eval_yollari) != 1:
                raise ValueError(f"{kimlik}: tek yayımlanmış JSON kanıtı gerekli")
            try:
                eval_verisi = json.loads(eval_yollari[0].read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as hata:
                raise ValueError(f"{kimlik}: eval kanıtı okunamadı: {hata}") from hata
            if not isinstance(eval_verisi, dict):
                raise ValueError(f"{kimlik}: eval kanıtı nesne olmalı")
            _validate_real_agent_evidence(eval_verisi, eval_yollari[0])
    return veri


def uret(kok: pathlib.Path = KOK) -> str:
    veri = oku(kok)
    kapilar = veri["gates"]
    gecen = sum(k["status"] == "passed" for k in kapilar)
    hazir = sum(k["status"] == "ready" for k in kapilar)
    kalan_metinleri = {
        "real-agent-comparison": "Gerçek bir ajan adaptörü ve bağımsız hakemle aynı vakaları baseline/skill olarak koşup sonucu yayımlamak.",
        "independent-adoption": "Proje sahibi dışındaki en az bir kullanıcının sabitlenmiş release üzerinden kurulum ve görev kanıtını kabul formuyla göndermesi.",
    }
    kalan = [
        kalan_metinleri.get(kapi["id"], kapi["title"])
        for kapi in kapilar
        if kapi["status"] != "passed"
    ]
    kalan_satirlari = [f"{sira}. {metin}" for sira, metin in enumerate(kalan, start=1)]
    if not kalan_satirlari:
        kalan_satirlari = ["Bütün v1 kapıları kanıtla geçti."]
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
            *kalan_satirlari,
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
