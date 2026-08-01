# Durum ve Yol Haritası · v1.0.3

Son durum tarihi: 2026-08-01.

> **En güncel yayımlanmış sürüm v1.0.3'tür.** PR #82
> `ce0c87103a1e96f62ccabdf63dc6df9ee9b195fb` commit'inde birleşti ve
> değişmez tag/GitHub Release olarak yayımlandı. Yedi varlık, checksum, SPDX
> SBOM, attestations, Windows/macOS/Linux temiz-host kapıları, Chromium, Pages,
> Wiki ve indirilen runner checksumları doğrulandı.

## Şu anda yayımlanan

- Değişmez `v1.0.3` etiketi ve ona bağlı GitHub Release, yedi varlık, checksum
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
- Seyir, uzun doğrulamalarda benchmark'a dayalı normal bekleme aralığını ve
  dikkat eşiğini açıklar; kullanıcı sessiz ekranı çökme zannetmez.
- Divan Engine, üst proje taramasında `.worktrees`, fixture projeleri ve skill
  içi yardımcı klasörlerden gelen eski ajan/test gürültüsünü workspace veya test
  hedefi gibi göstermez; açıkça proje kökü verilirse yine inceler.
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

- Repoda bir makinece doğrulanmış schema-2 temiz-proje makbuzu vardır. Bu,
  bağımsız kullanıcı sayısı, üçüncü taraf onayı veya pazar benimsemesi değildir.
- Gerçek Claude/Codex A/B sonucu yayımlandı: skill 0, baseline 1, beraberlik 2.
  Önceden eşik yoktur; kalite artışı iddiası yapılmaz.
- v1.0.3'ün tam yerel doğrulaması 715 test ve 14 platform atlamasıyla geçti.
  Yayın ayrıca üç işletim sistemi, strict attestations, Pages/Wiki readback ve
  release asset checksumlarıyla sınırlandırılmıştır; bütün host ve ortamları
  kapsadığı iddia edilmez.

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
- v1 sonrası Seyir sertleştirmesi, son 20 ana dal `quality-gate.yml` koşusunu
  timeout benchmark defterine ekledi ve kullanıcıya normal bekleme/dikkat
  eşiğini sade dille göstermeye başladı.
- PR #60 `d3a2a41f9b88c3639f9832c24dd898fd8b88cbe4` commit'inde birleşti. Dokuz
  ana yayın kontrolü, yedi indirilen varlığın SHA-256 değeri, strict
  attestations, SPDX 2.3 SBOM, Pages, Wiki ve Linux/macOS/Windows yaşam döngüsü
  canary'leri geçti.

## v0.18.3 — yayımlanan temiz-proje kanıt mekanizması

- `adoption prove`, yazmayan önizleme ile başlayıp sabit host probu ve sınırlı
  test/regresyon kontrollerini bir kez çalıştırır.
- Schema-2 makbuz; değişmez release, ayrı proje, doğrulanmış hedef, kaynak
  kararlılığı, gözlenen host ve gizlilik sınırlarını çevrimdışı doğrular.
- PR #63 `294958620e6382fe10296ab15246e100fab84764` commit'inde birleşti.
  Dokuz ana/yayın workflow'u, yedi indirilen varlığın SHA-256 değeri, strict
  attestations, SPDX 2.3 SBOM, Pages ve Wiki geçti.
- Yayımlanmış runner ile üretilip repoya kaydedilmiş temiz-proje makbuzu henüz
  olmadığı için v1 dürüstçe **7/8** kalır.

## v0.18.4 — yayımlanan gerçek kanıt sınırı

- `goal advance --evidence`, uygulama, regresyon testi ve doğrulama dosyalarını
  VERIFIED geçişine atomik olarak bağlar.
- `adoption prove`, yalnız gerçek terminal olayındaki spec dışı dosya
  özetlerini kabul eder; plan-only hedefi tamamlanmış saymaz.
- Genel `VERSION` dosyası ve Divan dışı marketplace ayrı projeyi yanlışlıkla
  reddetmez; Divan'a ait tam imzalar kapıyı güvenli biçimde durdurur.
- PR #64 `2eb36bdd24e383c90e1e62e53ad1c6c5d5730000` commit'inde birleşti.
  Dokuz ana/yayın workflow'u, 695 test, yedi indirilen varlık, strict
  attestations, Pages ve Wiki geçti.
- Gerçek Windows temiz-proje denemesi, çalışan `codex.cmd` yanında uzantısız
  npm shim'inin erişim hatasına takılan host sürüm probunu buldu. v0.18.5 bu
  son kullanıcı kusurunu regresyon testiyle düzeltir.

## v0.18.5 — yayımlanan Windows güven düzeltmesi ve 8/8 hazırlık

- Windows host sürüm probu, shell açmadan `.cmd`, `.exe` ve taşınabilir
  fallback sırasını kullanır; Linux/macOS mantıksal komut sözleşmesi değişmez.
- PR #65 `f65d62a857e744dce0b370414e6686b9c49258d7` commit'inde birleşti.
  Ana dal kalite, CodeQL, uyumluluk, Pages, Wiki, site ve release kapıları
  geçti; yedi yayın varlığı yeniden indirilip SHA-256 ve attestations ile
  doğrulandı.
- Değişmez v0.18.5 runner'ı, Windows 11 ve Codex `0.146.0` üzerinde Divan'dan
  ayrı gerçek projedeki VERIFIED hedef için sınırlı testi geçirdi.
- Gizlilik incelemeli schema-2 makbuz hem JSON hem Markdown olarak çevrimdışı
  yeniden doğrulandı. v1 hazırlık karnesi bu sınırlı teknik kanıtla **8/8**'dir;
  bağımsız kullanıcı, pazar benimsemesi, hız veya kalite artışı iddia edilmez.

## v1.0.0 — yayımlanan kararlı Divan sözleşmesi

- Tek repo, beş modüler paket, 41 beceri, stdlib-only Divan Engine, Hükümdar
  öncelikli Divan Nizamı ve kurulu Divan Proje Sözleşmesi kararlı sınırdır.
- PR #67 `2f73e0514d97d4ec9597b3d313f20c82d7770b77` commit'inde birleşti.
- Release hattı üç işletim sisteminde temiz kurulum, bütün yayın kapıları,
  Pages/Wiki eşliği ve canlı Chromium kontrolünden sonra v1.0.0'ı yayımladı.
- Yedi varlık yeniden indirildi; SHA-256, iki sidecar, master manifest, SPDX
  SBOM, iki gömülü runner kimliği ve strict attestations doğrulandı.

## v1.0.1 — yayımlanan paketli yükseltme düzeltmesi

- Tek dosyalık `divan.pyz update --execute`, çıkarılmış bootstrap klasörünü Git
  checkout sanmak yerine içindeki değişmez release kimliği, commit'i ve katalog
  digest'ini kullanır.
- PR #69 `62f30f39d78be6b15e39f6e2aa9b7c19e7fb0949` commit'inde birleşti; 698 test,
  iki PR kalite koşusu ve bütün ana/yayın workflow'ları geçti.
- Yedi varlık yeniden indirildi; SHA-256 ve strict attestations doğrulandı.
  İndirilen runner mevcut Windows/Codex kurulumunu v1.0.1'e yükseltti; doctor
  sağlıklı döndü ve ikinci execute no-op oldu.

## v1.0.2 — yayımlanan sakin keşif ve kullanıcı dostu bekleme düzeltmesi

- Seyir'in uzun doğrulama bekleme açıklaması ile Divan Engine'in üst proje
  keşif sessizliği aynı kullanıcı-dostu hatta bağlandı.
- Divan Engine artık `.worktrees`, fixture ağaçları, dependency/build cache'leri
  ve skill-içi yardımcı klasörleri ebeveyn proje taramasında kullanıcı workspace'i
  veya test hedefi gibi büyütmez. Bu klasörlerden biri açıkça proje kökü verilirse
  yine incelenebilir.
- PR #80 `f227e2d30ab1a6f010a3d5acf18740f6eab09e70` commit'inde birleşti.
  PR kapıları, main `quality-gate`, `release`, `compatibility`, `codeql`,
  `site-tests`, `scorecard`, `wiki-sync`, `candidate-review` ve Pages geçti.
- v1.0.2 GitHub Release değişmezdir; yedi varlık yeniden indirildi, SHA-256
  manifestleri ve GitHub attestations ile doğrulandı.

## v1.0.3 — yayımlanan kullanıcı dostu kontrol düzlemi

- Sağlıklı doctor insan çıktısı READY sonucunda durur; JSON sözleşmesindeki
  `next_command` alanı string kalır ve sağlıklı durumda boş döner.
- Bozuk veya yarım işlem günlüğü, boş yönlendirme yerine kopyalanabilir tam
  kurtarma komutu verir; bozuk host registry girdisi denetimi çökertmez.
- İlk kurulum, günlük doğal dil fermanı ve bakım/kurtarma yolları README, Wiki
  ve Pages'te ayrı kullanıcı yolculuklarıdır.
- Codex verified iddiası CLI yüzeyiyle sınırlıdır; Desktop, IDE extension ve
  mobil ayrı canary oluşana kadar doğrulanmış sayılmaz.
- PR #82 `ce0c87103a1e96f62ccabdf63dc6df9ee9b195fb` commit'inde birleşti. 715
  test, 14 beklenen skip, zorunlu PR/main workflow'ları, yedi indirilen varlık,
  checksum sidecar'ları, strict attestations ve gerçek Windows/Codex CLI
  yükseltme geri-okuması geçti.

## Sıradaki ürün adımı

1. ✓ 8/8 kanıt PR'ını bütün kalite kapılarından geçirip `main`e birleştir.
2. ✓ Canlı README, Pages, Wiki ve v1 karnesini varsayılan daldan geri oku.
3. ✓ v1.0.0'ı değişmez tag/Release, yedi varlık, SBOM, attestation ve canlı
   geri-okuma kapılarıyla yayımla.
4. ✓ v1.0.1 yayın kanıtını ve son sürüm etiketlerini `main`e eşitle.
5. ✓ v1.0.2 sakin keşif yayınını ve son sürüm etiketlerini `main`e eşitle.
6. ✓ Onaylı v1.0.3 kullanıcı dostu kontrol düzlemini test-first tamamla:
   sağlıklı doctor, yüzey-bazlı host doğruluğu ve kurulum/günlük
   kullanım/bakım ayrımı.
7. ✓ PR kontrolleri ve bağımsız incelemeden sonra `main`e birleştir; v1.0.2 tag
   ve varlıklarını değiştirmeden yeni v1.0.3 release hattını çalıştır.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- Yayımlanmış mekanizmayla üretilmiş, makinece doğrulanabilir bir temiz-proje
  kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md

Kapıların canlı karnesi: [[v1 Hazırlık Karnesi|V1-Hazirlik]].
