#!/usr/bin/env python3
"""Divan canli sayfa testi — gercek tarayicida (Chromium/Playwright).
Kullanim: pip install playwright && playwright install chromium && python tests/site_testi.py"""
import os, sys
from playwright.sync_api import sync_playwright

URL = "https://trugurpala.github.io/divan/"
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
    if sayfa.locator("article.vezir").count() != 4:
        hatalar.append(f"Vezir karti sayisi {sayfa.locator('article.vezir').count()} != 4")
    if sayfa.locator("ol.protokol li").count() != 6:
        hatalar.append("Protokol 6 faz degil")
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
print("SITE TESTI TEMIZ ✓ — HTTP 200, baslik, padisah, 4 vezir, 6 faz, mobil, konsol=0 hata; ekran goruntusu alindi")
