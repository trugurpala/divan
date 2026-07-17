# Test ve Teftiş — "Ne Kadar Localde Test, O Kadar Baki"

Vibe coding'in tek gerçek sigortası budur: ajanın "çalışıyor" demesi değil,
**localde kanıt üretmesi**. Divan'ın üç katmanlı test aklı:

## 1. Statik ve resmî teftiş (her push)
`python scripts/validate.py` — JSON, temel frontmatter, name=klasör,
≤64/≤1024, eval sözleşmesi, yol güvenliği, ad çakışması ve vitrin tutarlılığı.
`VERSION`, marketplace, iki README, CHANGELOG, BLUEPRINT ve kurulum belgesi
aynı sürümü söylemezse teftiş kırılır; `.divan/progress.md` sıradaki kesin
adımı taşımak zorundadır. CI bunun ardından
`skills-ref==0.1.1` ile 41 skill'i ve Claude Code 2.1.212 ile marketplace ile
beş paketi doğrular. Yerelde önce bağımlılıksız teftişi çalıştır:
```
python scripts/validate.py
python -m unittest discover -s tests -p 'test_*.py'
```

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
pip install playwright==1.61.0 && playwright install chromium
python tests/site_testi.py
```
Ürün kodun için aynı disiplin: ui-pack'teki **webapp-testing** skill'i,
ajanına "yaptım" yerine "tarayıcıda tıkladım, işte ekran görüntüsü"
dedirtir. Kural basit: **kanıtsız "bitti" yok sayılır.**

## 4. Yayın testi — varsayılan dal gerçektir

Özellik dalındaki veya taslak PR'daki yeşil test yalnızca “hazır” kanıtıdır.
Kamusal teslimde ayrıca PR hazır duruma getirilir, yetki kapsamındaysa `main`e
birleştirilir ve GitHub'daki README ile kurulum yolu varsayılan daldan yeniden
okunur. Tag/release yoksa durum “main'de”dir; “release yayımlandı” değildir.
