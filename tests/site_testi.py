#!/usr/bin/env python3
"""Divan canli sayfa testi — gercek tarayicida (Chromium/Playwright).
Kullanim: pip install playwright && playwright install chromium && python tests/site_testi.py"""
import os, pathlib, sys
from playwright.sync_api import sync_playwright

URL = os.environ.get("DIVAN_SITE_URL", "https://trugurpala.github.io/divan/")
SURUM = (pathlib.Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
hatalar = []

with sync_playwright() as p:
    tarayici = p.chromium.launch()
    baglam = tarayici.new_context(ignore_https_errors=os.environ.get("PROXY_SSL")=="1")
    sayfa = baglam.new_page()
    konsol_hatalari = []
    sayfa.on("console", lambda m: konsol_hatalari.append(m.text) if m.type == "error" else None)
    sayfa.on("pageerror", lambda e: konsol_hatalari.append(str(e)))

    yanit = sayfa.goto(URL, wait_until="networkidle", timeout=30000)
    if yanit.status != 200:
        hatalar.append(f"HTTP {yanit.status}")
    if "Divan" not in sayfa.title():
        hatalar.append(f"Baslik hatali: {sayfa.title()}")
    if not sayfa.get_by_text("Padişah sensin").is_visible():
        hatalar.append("'Padişah sensin' gorunmuyor")
    if not sayfa.get_by_text("trugurpala/divan").first.is_visible():
        hatalar.append("Kurulum komutu gorunmuyor")
    if not sayfa.get_by_text(f"v{SURUM}").first.is_visible():
        hatalar.append(f"v{SURUM} vitrinde gorunmuyor")
    if sayfa.locator("article.vezir").count() != 5:
        hatalar.append(f"Paket karti sayisi {sayfa.locator('article.vezir').count()} != 5")
    if sayfa.locator("#protokol ol.protokol li").count() != 6:
        hatalar.append("Protokol 6 faz degil")
    if sayfa.locator("[data-niyet]").count() != 5:
        hatalar.append("Ferman secici 5 niyet sunmuyor")
    sayfa.get_by_role("button", name="Bug düzelt").click()
    if sayfa.locator("#secici-paket").inner_text() != "core-pack":
        hatalar.append("Bug niyeti core-pack secmiyor")
    if "kök nedenini bul" not in sayfa.locator("#secici-komut").inner_text():
        hatalar.append("Bug fermani guncellenmiyor")
    if sayfa.locator("#secici-akis li").count() != 5:
        hatalar.append("Secili teslim akisi 5 adim degil")
    # mobil gorunum
    sayfa.set_viewport_size({"width": 390, "height": 844})
    if not sayfa.locator("h1").is_visible():
        hatalar.append("Mobilde h1 gorunmuyor")
    sayfa.screenshot(path="/tmp/divan-site.png", full_page=True)
    if konsol_hatalari:
        hatalar.append(f"Konsol hatalari: {konsol_hatalari[:3]}")
    tarayici.close()

if hatalar:
    print("SITE TESTI BASARISIZ:")
    for h in hatalar: print("  X", h)
    sys.exit(1)
print(f"SITE TESTI TEMIZ ✓ — HTTP 200, v{SURUM}, 5 niyet, etkilesim, 5 paket, 6 faz, mobil, konsol=0 hata")
