# Divan İlerleme Defteri

Son güncelleme: 2026-07-18

## Güncel hedef

v0.10.0 ile vibe coder'ın ilk dakikada doğru paket/fermanı seçmesini sağlamak;
skill-vs-baseline davranış koşusunu tekrarlanabilir kanıta dönüştürmek.

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

## Devam ediyor

- v0.10.0 uzak CI, PR, `main` birleşmesi ve canlı etkileşim doğrulaması.

## Bilinen açıklar

- Eval koşucusu ve fixture testleri var; beyan edilmiş güvenilir gerçek ajan
  adaptörü/hakemiyle yayımlanmış A/B sonucu henüz yok.
- v0.9.0 `main` ve GitHub Pages üzerinde; GitHub tag/release oluşturulmadı.
  Bu nedenle “etiketli release” iddiası yapılmıyor.
- Bağımsız kullanıcı/adopsiyon kanıtı henüz yok; başarı iddiası yapılamaz.
- Desteklenen hostlar için temiz-ortam kurulum/uyumluluk matrisi henüz otomatik değil.

## Sıradaki kesin adım

Resmî doğrulayıcıları çalıştır; v0.10.0 commit'ini PR'a gönder; uzak CI sonrası
`main`e birleştir ve canlı ferman seçiciyi gerçek tarayıcıyla doğrula.
