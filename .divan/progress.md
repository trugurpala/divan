# Divan İlerleme Defteri

Son güncelleme: 2026-07-18

## Güncel hedef

v0.9.0'ı taslak PR'dan çıkarıp eksiksiz ürün anlatısı ve doğrulanmış `main`
yayını olarak teslim etmek.

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

## Devam ediyor

- PR güncellemesi, GitHub Actions, `main` birleşmesi ve canlı kontrol.

## Bilinen açıklar

- Davranış eval dosyaları var; otomatik skill-vs-baseline eval koşucusu henüz yok.
- v0.9.0 henüz `main` üzerinde değil; GitHub tag/release oluşturma yetkisi bu
  bağlantıda yok. Merge sonrası durum “main'de” olacak, “etiketli release” değil.
- Bağımsız kullanıcı/adopsiyon kanıtı henüz yok; başarı iddiası yapılamaz.

## Sıradaki kesin adım

Doğrulanmış v0.9.0 commit'ini PR #1'e gönder, taslaktan çıkar, GitHub Actions
sonucunu kanıt kaydına işle ve `main`/canlı yüzey yayın zincirini tamamla.
