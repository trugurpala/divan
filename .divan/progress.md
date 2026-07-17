# Divan İlerleme Defteri

Son güncelleme: 2026-07-18

## Güncel hedef

v0.10.0 için otomatik skill-vs-baseline davranış eval koşucusunu tasarlamak;
ölçülmemiş başarı iddialarını yayın kapısında reddetmek.

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

## Devam ediyor

- v0.10.0 davranış eval koşucusu için sözleşme ve başarı ölçütleri.

## Bilinen açıklar

- Davranış eval dosyaları var; otomatik skill-vs-baseline eval koşucusu henüz yok.
- v0.9.0 `main` ve GitHub Pages üzerinde; GitHub tag/release oluşturulmadı.
  Bu nedenle “etiketli release” iddiası yapılmıyor.
- Bağımsız kullanıcı/adopsiyon kanıtı henüz yok; başarı iddiası yapılamaz.
- Desteklenen hostlar için temiz-ortam kurulum/uyumluluk matrisi henüz otomatik değil.

## Sıradaki kesin adım

v0.10.0 eval sözleşmesini yaz; aynı görevleri skill açık/kapalı koşup ölçülebilir
çıktıları karşılaştıran koşucuyu CI'a bağla.
