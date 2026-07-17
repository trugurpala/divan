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

## Devam ediyor

- v0.11.0 temiz-ortam matrisi ve gerçek adaptörlü A/B kanıt sözleşmesi.

## Bilinen açıklar

- Eval koşucusu ve fixture testleri var; beyan edilmiş güvenilir gerçek ajan
  adaptörü/hakemiyle yayımlanmış A/B sonucu henüz yok.
- v0.10.0 `main` üzerinde; GitHub tag/release oluşturulmadı.
  Bu nedenle “etiketli release” iddiası yapılmıyor.
- Bağımsız kullanıcı/adopsiyon kanıtı henüz yok; başarı iddiası yapılamaz.
- Desteklenen hostlar için temiz-ortam kurulum/uyumluluk matrisi henüz otomatik değil.

## Sıradaki kesin adım

Claude Code ve Codex kurulumlarını temiz geçici dizinlerde tekrarlayan matrisi
tasarla; host başına kurulum, keşif ve kaldırma kanıtını CI çıktısına bağla.
