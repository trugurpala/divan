# Divan

**Vibe coding, engineered.**

Divan; Codex ile yazılım geliştiren kullanıcıların teknik ayrıntıya boğulmadan, doğal dille daha disiplinli ve doğrulanabilir ürün geliştirmesine yardımcı olan bir mühendislik eklentisidir.

## Kurulum

Repo marketplace'ini ekle:

```bash
codex plugin marketplace add trugurpala/divan --ref main
```

Ardından desteklenen Codex yüzeyinde marketplace üzerinden **Divan** eklentisini kur. Günlük kullanım doğal dildir; ayrı bir Divan komut dili öğrenmen gerekmez.

## Kullanım

```text
Divan, bu projeyi incele.
Divan, bu özelliği en küçük doğru değişiklikle yap.
Divan, bu hatanın kök nedenini bul ve düzelt.
Divan, gerçekten bitti mi kontrol et.
```

Divan arka planda repo inceleme, sınırlı planlama, kök neden analizi, mühendislik kalite kontrolü ve tamamlanma kanıtını yürütür.

## Mimari

- tek Codex plugin;
- 7 odaklı çekirdek skill;
- yalnız gerektiğinde yüklenen progressive-disclosure mühendislik referansları;
- deterministik doğrulama ve paketleme;
- MCP server, hosted backend, özel agent runtime veya paketlenmiş UI yok;
- mevcut hatta yayınlanan lifecycle hook yok.

Yayınlanabilir paket `plugins/divan/` altındadır.

## Kalite modeli

Divan kaliteyi yalnız kod stili olarak görmez. İlgili işlerde correctness, security, reliability, type/API sınırları, database bütünlüğü, i18n, responsive davranış, accessibility, loading/empty/error durumları, network resilience, performance, observability, dependency disiplini, testler ve kanıta dayalı definition of done kontrol edilir.

## Doğrulama

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_divan_v2*.py" -v
python scripts/package_divan_v2.py
```

Bu mekanik kontroller repo ve paket bütünlüğünü kanıtlar; model doğruluğu veya hız artışı iddiası değildir.

## Bakım

Divan'ı değiştirmeden önce `AGENTS.md` dosyasını oku. Aktif repo ürün kodu, testler, doğrulama ve kullanıcı dokümantasyonuna odaklı tutulur; oturuma özel geliştirme süreci çıktıları yayınlanan ürünün parçası değildir.

Eski Divan sürümleri Git geçmişi ve yayımlanmış legacy release'lerden geri getirilebilir; aktif paketin parçası değildir.

## Lisans

MIT
