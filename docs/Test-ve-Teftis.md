# Test ve Teftiş — "Ne Kadar Localde Test, O Kadar Baki"

Vibe coding'in tek gerçek sigortası budur: ajanın "çalışıyor" demesi değil,
**localde kanıt üretmesi**. Divan'ın üç katmanlı test aklı:

## 1. Statik teftiş (her push, saniyeler)
`python scripts/validate.py` — JSON şemaları, Agent Skills spec uyumu
(name=klasör, ≤64/≤1024, `<>` yasağı), ad çakışması, proprietary sızıntı.
CI'da otomatik; localde push'tan önce elle koş.

## 2. Soğuk klon testi (kullanıcının gerçeği)
```
git clone https://github.com/trugurpala/divan /tmp/test && cd /tmp/test
python scripts/validate.py
```
Senin makinende çalışan değil, **taze klonda çalışan** bakidir.

## 3. Tarayıcı testi — Playwright (canlı kanıt)
`tests/site_testi.py` gerçek Chromium açar, canlı sayfayı yükler, başlığı ve
"Padişah sensin" metnini doğrular, konsol hatalarını sayar, ekran görüntüsü
alır. Localde:
```
pip install playwright && playwright install chromium
python tests/site_testi.py
```
Ürün kodun için aynı disiplin: ui-pack'teki **webapp-testing** skill'i,
ajanına "yaptım" yerine "tarayıcıda tıkladım, işte ekran görüntüsü"
dedirtir. Kural basit: **kanıtsız "bitti" yok sayılır.**
