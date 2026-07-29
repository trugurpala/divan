# Durum ve Yol Haritası · v0.17.0

Son durum tarihi: 2026-07-29.

> **En güncel yayımlanmış sürüm v0.16.0'dır.** v0.17.0 şu anda yerel adaydır;
> PR, CI, merge, değişmez tag, GitHub Release, Pages ve Wiki kanıtı tamamlanana
> kadar yayımlanmış sayılmaz.

## Şu anda yayımlanan

- Değişmez `v0.16.0` etiketi ve ona bağlı GitHub Release, beş varlık, checksum
  manifestleri, SPDX SBOM, attestations, Pages ve Wiki kanıtı.
- 5 paket ve 41 beceri.
- Vibe coder için beş niyetli ferman seçici.
- 4 özgün skill / 13 vaka için sağlayıcı-bağımsız kör A/B eval koşucusu;
  Claude gerçek ajanı ve read-only kör Codex hakemi adaptörleri.
- Claude ve Codex için aynı 5 paket/41 beceriyi sunan yerel pazarlar ile
  dry-run-first işlemsel çift-host kurucu.
- Yerel teftiş, Agent Skills, iki host pazarı, Claude Code plugin doğrulaması,
  CodeQL, Ruff, mypy, Coverage ve actionlint kapıları.
- Dal önizlemesi ve `main` sonrası canlı GitHub Pages testi.
- Repodaki `docs/*.md` kaynaklarından otomatik GitHub Wiki derleme/yayın kapısı.
- Yapılandırılmış aday formu, makine-okunur Aday Meclisi ve haftalık salt-okunur
  GitHub keşif nöbeti; otomatik kurulum yok.
- Tek komutlu sürüm yüzeyi hazırlığı ve sapma teftişi; `main` sonrası Pages +
  Wiki eşliğinden CHANGELOG kaynaklı tag/GitHub Release'a giden yayın kapısı.
- Claude Code resmî doğrulaması ve Linux/macOS/Windows Codex kur-keşfet-kaldır matrisi.
- UTF-8/LF metin sözleşmesi, locale-bağımsız subprocess çıktısı, McCabe 25
  karmaşıklık bütçesi ve yalnız yeniden üretilebilir cache'leri silebilen
  allowlist tabanlı repo hijyeni.

## v0.17.0 adayı — tek Divan, modüler çekirdek

- Ürün adı **Divan** olarak kalır; ikinci bir ürün veya repo oluşturulmaz.
- **Divan Engine**, bu repodaki stdlib-only icra çekirdeğidir.
- **Divan Nizamı**, yetkinin
  `Hükümdar → Ferman → Sadrazam → Divan → Uzman → Sağlayıcı`
  sırasıyla daralmasını tanımlar. Kapsamı yalnız Hükümdar genişletebilir.
- **Divan Proje Sözleşmesi**, hedef repoya kurulan gözetimli yaşam döngüsünün
  kanonik adıdır.
- Dokuz modüllü bağımlılık grafiği ve iki dilli yetki sözleşmesi
  `python scripts/divan.py architecture --json` ile görünür olur.
- Eski Company OS, Project OS, `/company`, `company-validate` ve Python yolları
  v1 boyunca uyumluluk yüzeyi olarak korunur.
- Çekirdek başka bir agent runtime'ına veya dış repoya bağımlı olmaz.

Bu maddeler aday kapsamıdır; test, bağımsız inceleme ve yayın zinciri
tamamlanmadan sonuç veya kalite artışı iddiası değildir.

## Dürüst açıklar

- Bağımsız kullanıcıdan tekrar üretilebilir benimseme kanıtı yok.
- Gerçek Claude/Codex A/B sonucu yayımlandı: skill 0, baseline 1, beraberlik 2.
  Önceden eşik yoktur; kalite artışı iddiası yapılmaz.
- v0.17 adayının tam yerel doğrulaması 538 test, 7 platform atlaması, %76
  kapsam, Ruff, mypy, Clean Code, 41 skill, strict plugin doğrulaması ve
  deterministik runner ile tamamlandı. Bağımsız son inceleme açık P0-P3 bulgusu
  olmadığını doğruladı. PR/CI ve canlı yayın kanıtı henüz tamamlanmış olarak
  kaydedilmemiştir.
- v0.17 yayını bağımsız kullanıcı kabulü değildir; issue #34 kapanmadan v1
  karnesi **7/8** kalır.

## Sıradaki ürün kanıtı

1. v0.17 adayında çekirdek, uyumluluk, dokümantasyon ve yayın yüzeylerini tam
   yerel doğrulamadan geçir.
2. Bağımsız inceleme sonrası PR aç; bütün zorunlu CI kapıları yeşil olmadan
   birleştirme.
3. Birleşen committen değişmez v0.17.0 tag/Release üret; beş varlığı,
   checksum'ları, attestations, Pages ve Wiki'yi canlı geri oku.
4. Ayrı kapı olarak, sabitlenmiş release'i deneyen bağımsız kullanıcıdan
   gizlilik sınırlı ve tekrar üretilebilir kabul kanıtı topla.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- En az bir bağımsız, yeniden üretilebilir kullanıcı kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md

Kapıların canlı karnesi: [[v1 Hazırlık Karnesi|V1-Hazirlik]].
