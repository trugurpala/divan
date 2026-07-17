# Divan İlerleme Defteri

Son güncelleme: 2026-07-18

## Güncel hedef

v0.11.0 için Claude Code + Codex temiz-ortam uyumluluk matrisini CI'a bağlamak;
ardından gerçek ajan/hakem adaptörüyle ilk yayımlanabilir A/B kanıtını üretmek.

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

## Devam ediyor

- v0.11.0 temiz-ortam matrisi ve gerçek adaptörlü A/B kanıt sözleşmesi.

## Bilinen açıklar

- Eval koşucusu ve fixture testleri var; beyan edilmiş güvenilir gerçek ajan
  adaptörü/hakemiyle yayımlanmış A/B sonucu henüz yok.
- v0.10.2 için GitHub tag/release oluşturulmadı.
  Bu nedenle “etiketli release” iddiası yapılmıyor.
- GitHub Wiki etkin fakat ilk `Home` sayfası web arayüzünde kaydedilmediği için
  ayrı Wiki Git deposu yok; post-merge `wiki-sync` #2 `Repository not found`
  ile doğru biçimde kırıldı. Canlı Wiki doğrulandı denmiyor.
- Bağımsız kullanıcı/adopsiyon kanıtı henüz yok; başarı iddiası yapılamaz.
- Desteklenen hostlar için temiz-ortam kurulum/uyumluluk matrisi henüz otomatik değil.

## Sıradaki kesin adım

Claude Code ve Codex kurulumlarını temiz geçici dizinlerde tekrarlayan matrisi
tasarla; host başına kurulum, keşif ve kaldırma kanıtını CI çıktısına bağla.
