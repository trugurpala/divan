# Durum ve Yol Haritası · v0.18.3

Son durum tarihi: 2026-07-30.

> **En güncel yayımlanmış sürüm v0.18.2'dir.** PR #60 yerel Seyir ekranını,
> tek dosyalık temiz-host kurucusunu ve kanıta dayalı timeout politikasını
> tamamladı. Değişmez tag/GitHub Release, yedi varlık, checksum, SPDX SBOM,
> attestations ve üç işletim sistemi yaşam döngüsü canary'siyle yayımlandı.

## Şu anda yayımlanan

- Değişmez `v0.18.2` etiketi ve ona bağlı GitHub Release, yedi varlık, checksum
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
- Codex Desktop için açık `auto` profil; sağlıklı CLI'da native kurulum, kanıtlı
  çalıştırma engelinde sınırları belirtilen checksum-backed 41-skill fallback.
- Vibe coder için yalnız loopback'te çalışan, yetenek URL'siyle korunan iki
  dilli Seyir ekranı; aktif hedefi, kanıtlı adımı ve sıradaki işi gösterir.
- Repo indirmeden kullanılabilen, checksum ve kaynak commit'i doğrulanan tek
  dosyalık `divan.pyz`; yazma öncesi plan, doctor ve güvenli recovery komutları.
- Yerel ve CI süre ölçümlerinden türetilen sınırlı timeout politikası ile aynı
  kanıtlı arıza iki düzeltmeden sonra sürerse durduran devre kesici.
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

- Schema-2 temiz-proje mekanizması hazırdır; henüz yayımlanmış mekanizmayla
  üretilip repoya kaydedilmiş gerçek makbuz yoktur.
- Gerçek Claude/Codex A/B sonucu yayımlandı: skill 0, baseline 1, beraberlik 2.
  Önceden eşik yoktur; kalite artışı iddiası yapılmaz.
- v0.17.0'ın tam yerel doğrulaması 538 test, 7 platform atlaması, %76
  kapsam, Ruff, mypy, Clean Code, 41 skill, strict plugin doğrulaması ve
  deterministik runner ile tamamlandı. Bağımsız son inceleme açık P0-P3 bulgusu
  olmadığını doğruladı. PR #49, bütün zorunlu CI kapıları ve canlı yayın kanıtı
  `.divan/evidence/teftis-20260729-v017-release.md` kaydına bağlandı.
- v0.17 yayını temiz-proje kabul kanıtı değildir; gerçek schema-2 makbuz
  kaydedilip yeniden doğrulanmadan v1 karnesi **7/8** kalır.

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

## v0.18.1 — yayımlanan Codex Desktop auto-install

- Eksik, çalıştırılamayan, erişimi engellenen, geçersiz JSON döndüren ve sağlıklı
  Codex CLI durumları birbirinden ayrılır.
- Açıkça seçilen `auto` profili sağlıklı CLI'da native yolu değiştirmez; kanıtlı
  Windows çalıştırma engelinde checksum-backed 41-skill fallback'i seçebilir.
- Fallback; komut, ajan, hook, MCP veya native yaşam döngüsü desteği iddia etmez.
- PR #58 `f367de92e09b4f56e205d7e2883d988b3b4d2797` commit'inde birleşti. Dokuz
  yayın kontrolü, beş indirilen varlığın SHA-256 değeri, strict SLSA doğrulaması
  ve uzak Windows kur-keşfet-kaldır canary'si geçti.

## v0.18.2 — yayımlanan Seyir ve temiz-host kurucusu

- Yerel Seyir ekranı yalnız `127.0.0.1` üzerinde çalışır; durum istekleri
  yetenek belirteci ister ve yetkisiz istekler oturum ömrünü uzatmaz.
- `divan.pyz` tek dosyada kaynak commit'ini ve 41 becerilik kataloğu taşır;
  checksum doğrulaması ve yazmayan plan olmadan kurulum iddiası oluşturmaz.
- Akıllı timeout değerleri ölçülmüş yerel/CI kanıtlarına bağlıdır; aynı kanıtlı
  hata iki düzeltmeden sonra sürerse döngü durur ve Hükümdara taşınır.
- PR #60 `d3a2a41f9b88c3639f9832c24dd898fd8b88cbe4` commit'inde birleşti. Dokuz
  ana yayın kontrolü, yedi indirilen varlığın SHA-256 değeri, strict
  attestations, SPDX 2.3 SBOM, Pages, Wiki ve Linux/macOS/Windows yaşam döngüsü
  canary'leri geçti.

## Sıradaki ürün kanıtı

1. Schema-2 mekanizmasını değişmez release olarak yayımla.
2. Divan'dan ayrı, gerçek ve doğrulanmış hedef içeren projede yazmayan planı gör:
   `python scripts/divan.py adoption prove --project . --goal <goal-id> --host codex`
3. Aynı planı `--execute` ile çalıştır; host sürümünü gözle, sınırlı
   test/regresyon kontrollerini geçir ve gizlilik sınırlı makbuzu mühürle.
4. `valid-clean-room-adoption` makbuzunu çevrimdışı yeniden doğrula. Yalnız
   bundan sonra issue #34 ve v1 karnesini ayrı değişiklikle güncelle.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- Yayımlanmış mekanizmayla üretilmiş, makinece doğrulanabilir bir temiz-proje
  kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md

Kapıların canlı karnesi: [[v1 Hazırlık Karnesi|V1-Hazirlik]].
