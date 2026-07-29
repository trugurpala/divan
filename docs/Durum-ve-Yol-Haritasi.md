# Durum ve Yol Haritası · v0.18.1

Son durum tarihi: 2026-07-29.

> **En güncel yayımlanmış sürüm v0.18.0'dır.** PR #54 uygulamayı, PR #55 sürüm
> hazırlığını tamamladı. Değişmez tag/GitHub Release, beş varlık, checksum,
> SPDX SBOM, çift attestation, Pages ve Wiki kanıtıyla yayımlandı.

## Şu anda yayımlanan

- Değişmez `v0.18.0` etiketi ve ona bağlı GitHub Release, beş varlık, checksum
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

## v0.17.0 — tek Divan, modüler çekirdek

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

Bu kapsam 538 test, bağımsız inceleme, yedi PR kontrolü ve tam yayın zinciriyle
yayımlanmıştır. Yayın; hız, gelir veya bağımsız kullanıcı başarısı iddiası
değildir.

## Dürüst açıklar

- Bağımsız kullanıcıdan tekrar üretilebilir benimseme kanıtı yok.
- Gerçek Claude/Codex A/B sonucu yayımlandı: skill 0, baseline 1, beraberlik 2.
  Önceden eşik yoktur; kalite artışı iddiası yapılmaz.
- v0.17.0'ın tam yerel doğrulaması 538 test, 7 platform atlaması, %76
  kapsam, Ruff, mypy, Clean Code, 41 skill, strict plugin doğrulaması ve
  deterministik runner ile tamamlandı. Bağımsız son inceleme açık P0-P3 bulgusu
  olmadığını doğruladı. PR #49, bütün zorunlu CI kapıları ve canlı yayın kanıtı
  `.divan/evidence/teftis-20260729-v017-release.md` kaydına bağlandı.
- v0.17 yayını bağımsız kullanıcı kabulü değildir; issue #34 kapanmadan v1
  karnesi **7/8** kalır.

## v0.18 — yayımlanan Nizâm-ı Sefer

- Ferman; hedef, workflow aşamaları ve bağımlılıklardan oluşan makine-okunur
  görev grafiğine çevrilir.
- Risk, yapısal karmaşıklık, host kimliği ve bağlam bütçesi açıklanabilir
  kurallarla hesaplanır.
- En fazla üç bağımsız sefer açılır; `unknown` veya `ambiguous` hostta sıralı
  güvenli yürütme seçilir.
- Model politikası taşınabilir `economy`, `balanced` ve `frontier` sınıfları
  üzerinden çalışır. Tam model adı yalnız host doğrulaması gereken adaydır.
- Goal klasörü `route.json` taşır; görev, bağımlılık, sefer, devir ve kanıt
  yükümlülükleri oturumlar arasında kalır.
- Uygulama PR #54 ile `7c674874` commit'inde `main`e birleşti; 562 test, iki
  bağımsız inceleme ve zorunlu CI kapıları geçti. Sürüm PR #55,
  `3bbbd95881a7c33f64e3e9f8d23824e3eef8977e` commit'inde birleşti. Değişmez
  v0.18.0 tag/Release'i, beş varlık, iki attestation türü, Pages ve Wiki
  yeniden okunarak doğrulandı.

## Sıradaki ürün kanıtı

1. Native host adaptörleri ve tek-komut kurulum profillerini ayrı, kanıtlı
   dilimler halinde uygula; sahte “her hostta tam uyum” iddiası kurma.
2. Yayımlanan sabit sürümü kullanan, repo sahibi olmayan bağımsız kullanıcıdan
   gizlilik sınırlı ve tekrar üretilebilir kabul kanıtı topla.
3. Kabul kaydını tekrar doğrula; owner canary veya maintainer fixture ile kapıyı
   geçilmiş sayma.
4. Kanıt geçerliyse issue #34 ve v1 karnesini ayrı, denetlenebilir değişiklikle
   güncelle.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- En az bir bağımsız, yeniden üretilebilir kullanıcı kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md

Kapıların canlı karnesi: [[v1 Hazırlık Karnesi|V1-Hazirlik]].
