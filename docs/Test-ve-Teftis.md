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
python scripts/release.py --check
python scripts/v1.py --check
python -m unittest discover -s tests -p 'test_*.py'
```

## 2. Soğuk klon testi (kullanıcının gerçeği)
```
git clone https://github.com/trugurpala/divan /tmp/test && cd /tmp/test
python scripts/validate.py
```
Senin makinende çalışan değil, **taze klonda çalışan** bakidir.

## 3. Tarayıcı testi — Playwright (önizleme + canlı kanıt)
`tests/site_testi.py` gerçek Chromium açar; sürümü, ferman seçicinin beş
niyetini, seçim sonrası paket/prompt/akış değişimini, ürün yüzeyini ve mobil
görünümü denetler. PR sırasında yalnız mevcut canlıyı test etmek yeni değişikliği
kanıtlamaz; CI bu nedenle `docs/` içeriğini yerel HTTP sunucusunda açar. Haftalık
nöbet ve her `main` push'ı ayrıca GitHub Pages'in beklenen `VERSION`a gelmesini
bekler, sonra aynı etkileşimi canlı adreste tıklar. Localde:
```
pip install playwright==1.61.0 && playwright install chromium
python tests/site_testi.py

# Belirli bir yerel/preview adresi
DIVAN_SITE_URL=http://127.0.0.1:8000/ python tests/site_testi.py
```
Ürün kodun için aynı disiplin: ui-pack'teki **webapp-testing** skill'i,
ajanına "yaptım" yerine "tarayıcıda tıkladım, işte ekran görüntüsü"
dedirtir. Kural basit: **kanıtsız "bitti" yok sayılır.**

## 4. Yayın testi — varsayılan dal gerçektir

Özellik dalındaki veya taslak PR'daki yeşil test yalnızca “hazır” kanıtıdır.
Kamusal teslimde ayrıca PR hazır duruma getirilir, yetki kapsamındaysa `main`e
birleştirilir ve GitHub'daki README ile kurulum yolu varsayılan daldan yeniden
okunur. Tag/release yoksa durum “main'de”dir; “release yayımlandı” değildir.

## 5. Wiki testi — kaynak ile canlı yüzey aynı değildir

GitHub Wiki ayrı bir Git deposudur. Kaynak sayfalar `docs/*.md` altında yaşar;
`wiki-pages.json` hangilerinin yayımlanacağını belirler. Yerelde:

```bash
python scripts/wiki.py --check
python scripts/wiki.py --build /tmp/divan-wiki
```

PR'da `wiki-sync` yalnız derleme, bağlantı ve sürüm tutarlılığını denetler.
`main` sonrası aynı iş akışı Wiki deposuna yazar ve
`raw.githubusercontent.com/wiki/.../Home.md` üzerinden beklenen sürümü yeniden
okur. Bu son adım geçmeden “Wiki canlı güncel” denmez.

## 6. Release ve temiz-host testi

`uyumluluk` matrisi Claude Code'un resmî plugin doğrulayıcısını temiz runner'da
çalıştırır; Codex kurucusunu Linux, macOS ve Windows'ta boş geçici dizine kurar, 41
skill'i sayar ve manifestli kaldırma/geri alma yolunu uygular. `release` akışı
ise bütün teftişlerden sonra Pages ile Wiki'nin aynı `VERSION`ı göstermesini
bekler. Ardından CHANGELOG'dan not üretir; tag yoksa oluşturur, varsa etiketi
taşımadan yalnız Release sayfasını eşitler.
