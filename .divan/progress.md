# Divan İlerleme Defteri

Son güncelleme: 2026-07-18

## Güncel hedef

Gerçek ajan/hakem A/B sonucu ve proje sahibi dışındaki bağımsız kullanıcı kanıtı
ile kalan iki v1 kapısını dürüstçe kapatmak.

## Yapıldı

- Canlı `main` README'sinin 37 skill/v0.7 döneminde kaldığı doğrulandı.
- PR #1'in önce v0.8.2/41 skill içerdiği, yeşil fakat taslak olduğu doğrulandı;
  yayın düzeltmelerinin SemVer karşılığı yeni işlev nedeniyle v0.9.0 oldu.
- Eksik teslimin kök nedeni “PR hazır = yayın tamam” varsayımı olarak belirlendi.
- Yayın tamamlama planı ve ADR kaydı başlatıldı.
- Türkçe README ürün değeri, öz-gelişim döngüsü ve dürüst durumla genişletildi.
- İngilizce README, CHANGELOG ve VERSION eklendi.
- BLUEPRINT geçmiş/gelecek yol haritası ve sıradaki kesin adımla düzeltildi.
- Sadrazam Yayın Kanunu hem Divan paketine hem Work skill'ine işlendi.
- CI; sürüm, iki README, CHANGELOG, BLUEPRINT, kurulum ve progress kaydını
  birlikte denetleyecek şekilde güçlendirildi; yeni regresyon testi geçti.
- PR #1 taslaktan çıkarıldı; `teftis` #29 ve `site-testi` #8 başarıyla geçti.
- PR #1 squash ile `main`e birleşti (`6893e8043518f55f014a61765fc17b7c657ae295`).
- Varsayılan dalda README/TR, README/EN, VERSION, CHANGELOG ve BLUEPRINT
  yeniden okundu; GitHub Pages üzerinde v0.9.0, 41 vezir ve Yayın Kanunu görüldü.
- v0.10.0 vibe coder planı yazıldı; beş niyetli ferman seçici ürün yüzeyine
  eklendi.
- Dört özgün skill'deki 12 vakayı keşfeden; baseline/skill koşusu, A/B körleme,
  opsiyonel hakem/eşik ve JSON kanıt üreten sağlayıcı-bağımsız eval koşucusu
  eklendi.
- Aday Meclisi güvenlik davranışıyla güncel eval toplamı 4 skill / 13 vakadır.
- PR site testi eski canlı sayfa yerine dalın `docs/` önizlemesini test edecek
  şekilde düzeltildi; haftalık canlı nöbet korundu.
- Sadrazam 0.8.0'a niyetten en küçük yola geçiş ve gerçek adaptör olmadan kalite
  iddiasını reddeden Eval Kanunu eklendi; Work skill'i aynı metinle eşitlendi.
- PR #3'te `teftis` #37 ve dalın yerel önizlemesini Chromium'da tıklayan
  `site-testi` #13 başarıyla geçti.
- PR #3 squash ile `main`e birleşti (`361a6d672b9db2519a3e21d5c71ec95db7663b1e`).
- Varsayılan dalda VERSION, iki README, eval koşucusu, site kaynağı, Sadrazam ve
  BLUEPRINT yeniden okundu; v0.10.0 kayıtları eşleşti.
- Site workflow'u her `main` push'ında Pages'in repo `VERSION`ına gelmesini
  bekleyip canlı etkileşimi Chromium'da yeniden tıklayacak şekilde güçlendirildi.
- Boş/varsayılan GitHub Wiki ayrı bir teslim yüzeyi olarak kayda alındı.
- `wiki-pages.json` ve `scripts/wiki.py`, 14 Wiki sayfası ile `_Sidebar.md`yi
  repodaki sürümlü `docs/*.md` kaynaklarından deterministik üretecek şekilde
  eklendi; eksik kaynak, yinelenen slug, kırık Wiki bağlantısı ve sürüm farkı
  teftişi kuruldu.
- `wiki-sync` PR'da kaynağı denetleyecek, `main` sonrası ayrı Wiki Git deposuna
  yazacak ve canlı `Home.md` üzerinde sürümü yeniden okuyacak şekilde eklendi.
- Context7 ve OpenAI'nin güncel resmi rehberleriyle portable Agent Skills ile
  OpenAI Agents SDK runtime'ı arasındaki sınır Wiki'de açıklandı.
- Mühürdar'ın Wiki rolü belgelendi; mevcut ChatGPT Work Mühürdar etkinleştirildi.
- Sadrazam 0.8.1'e Bilgi Yüzeyleri Kanunu eklendi; proje ve Work kopyaları
  aynı metinle eşitlendi.
- `punkpeye/awesome-mcp-servers` bugünkü repo, CONTRIBUTING, MIT lisansı,
  `check-glama.yml`, son commitler ve açık katkı kuyruğuyla incelendi; 3.012
  GitHub girişli bir registry/index olarak `REFERENCE` kararı aldı.
- `registry/candidates.json` Aday Meclisi tek doğru kaynağı; kimlik, mükerrerlik,
  yaşam döngüsü, lisans kanıtı, karar/durum ve inceleme tarihi kapılarıyla kuruldu.
- `scripts/meclis.py`, insan-okunur `docs/Aday-Meclisi.md` dosyasının defterden
  ayrılmasını engelliyor; mükerrer URL ve lisanssız ADOPT regresyon testleri eklendi.
- GitHub kaynak-adayı issue formu ve haftalık salt-okunur keşif workflow'u
  eklendi. Keşif aday kodunu indirmiyor/çalıştırmıyor; yalnız bounded issue açıyor.
- Kaynak Küratörü Meclis yaşam döngüsüyle proje ve Work'te eşitlendi.
- PR #6'da `meclis` #1, `teftis` #46, `site-testi` #22 ve `wiki-sync` #3
  başarıyla geçti; squash commit `70cde8960438840153a47880571e269d37c9abbf`
  ile `main`e birleşti.
- `main` sonrası `meclis` #2, `teftis` #47, `site-testi` #23 ve Pages #17
  başarıyla geçti. `wiki-sync` #4 ilk Wiki sayfası kaydedilmediği için beklenen
  `Repository not found` engelini yeniden doğruladı; canlı Wiki iddiası yok.
- GitHub/Context7/OpenAI/Mühürdar ortak teftişinde canlı Wiki'nin HTTP 404 olduğu,
  kaynak check'inin geçtiği ve publish clone adımının `divan.wiki.git` yokluğunda
  kırıldığı doğrulandı; ilk sayfa şartı GitHub Docs'tan yeniden okundu.
- “Otomatik üretilir” yazdığı halde üreticisi olmayan Vezir Kataloğu için
  `scripts/katalog.py` ve regresyon testleri eklendi. Çok satırlı frontmatter
  yüzünden `claude-api` açıklamasını `/-…` gösteren kullanıcı hatası düzeltildi.
- GitHub Actions checkout/setup-python/setup-node/github-script kullanımları
  resmî depolardaki güncel major sürümlere taşındı; Wiki eksikliği artık tek
  `Save Page` iyileştirme yolunu doğrudan Actions hata mesajında veriyor.
- PR #8'de `wiki-sync` #5, `meclis` #3, `teftis` #52 ve `site-testi` #25 geçti;
  squash commit `6706952ccb9e4c8874593299cda4d1fdd7c2efd7` ile `main`e birleşti.
- Ana dalda `teftis` #53, `site-testi` #26, `meclis` #4 ve Pages #19 geçti.
  `wiki-sync` #6, ilk Home sayfası eksikliğini doğrudan `Save Page` talimatıyla
  durdurdu. Katalog main'den yeniden okunarak 41 kayıt ve doğru `claude-api`
  açıklaması doğrulandı.
- Repo sahibi ilk Wiki Home sayfasını kaydetti. Raw `Home.md` HTTP 200 verdi ve
  varsayılan karşılama metni okundu; `divan.wiki.git` başlangıç engeli kalktı.
  16 sayfalık kaynak paketini yayımlamak için README/Wiki durum değişikliğiyle
  `wiki-sync` yeniden tetikleniyor.
- PR #10'da `wiki-sync` #7, `teftis` #58 ve `site-testi` #28 geçti; squash
  commit `b19e6ccaee534d77a8ca3f0e52e28d38381e0a0d` ile `main`e birleşti.
- Ana dal `wiki-sync` #8, Wiki commit `ebbbf66` ile 16 dosyada 652 satır
  yayımladı ve canlı `Home.md` üzerinde v0.10.3 + “Fermanını seç” readback'ini
  geçti. `teftis` #59, `site-testi` #29 ve Pages #21 de başarılıdır.
- `release-manifest.json` ve `scripts/yayin.py`; tek komutla deterministik sürüm
  yüzeylerini hazırlar, CHANGELOG anlatısını insan sorumluluğunda bırakır ve
  sapmayı CI hatasına çevirir.
- `release` workflow'u yerel/resmî teftişlerden sonra Pages ile Wiki'nin aynı
  sürüme gelmesini bekler; CHANGELOG'dan not üretip tag/Release oluşturur. Mevcut
  etiketi taşımadan yalnız release sayfasını eşitleyerek tekrarlı çalışır.
- Claude Code resmî doğrulaması ve Codex Linux/macOS/Windows kurulum, 41 skill keşfi,
  kayıtlı kaldırma/geri yükleme tatbikatı `uyumluluk` matrisine bağlandı.
- Sekiz kapılı `registry/v1-gates.json`, deterministik Wiki karnesi, bağımsız
  kabul issue formu ve Sadrazam `/yayin` emri eklendi.
- PR #12'nin `teftis` #64, `site-testi` #31, `wiki-sync` #9, `meclis` #5 ve
  yeni `uyumluluk` #1 kapıları geçti; squash commit `5680337a` ile `main`e birleşti.
- Ana dalda `teftis` #65, `uyumluluk` #2, `wiki-sync` #10, `site-testi` #32,
  `meclis` #6, Pages #23 ve `release` #1 başarıyla tamamlandı.
- `release` akışı Linux/macOS/Windows kur-kaldır, bütün yerel/resmî teftiş,
  canlı Pages/Wiki readback ve Chromium tıklamasından sonra v0.11.0 etiketini
  değişmez biçimde `5680337a` commit'ine bağladı ve GitHub Release'i yayımladı.
- Canlı Pages ile Wiki `v0.11.0` + “Fermanını seç” döndürdü; Wiki v1 karnesi
  kayıt sonrası 6/8 geçen kapıyı gösterecek şekilde yeniden üretildi.

## Devam ediyor

- Yalnız dış kanıt isteyen gerçek ajan/hakem ve bağımsız kullanıcı kapıları.

## Bilinen açıklar

- Eval koşucusu ve fixture testleri var; beyan edilmiş güvenilir gerçek ajan
  adaptörü/hakemiyle yayımlanmış A/B sonucu henüz yok.
- Bağımsız kullanıcı/adopsiyon kanıtı henüz yok; başarı iddiası yapılamaz.

## Sıradaki kesin adım

Beyan edilmiş gerçek ajan + bağımsız hakem adaptörünü güvenilir yürütme ortamında
koş; sonucu yayımla. Paralelde v0.11.0 sabit release'i için ilk bağımsız kabul
kanıtını `.github/ISSUE_TEMPLATE/kabul-kaniti.yml` akışından topla.
