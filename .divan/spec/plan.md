# v0.9.0 Yayın ve Vitrin Tamamlama Planı

Tarih: 2026-07-18

## Hedef

Divan'ın v0.9.0 değişikliklerini yalnız bir özellik dalında bırakmadan, dünya
çapında anlaşılabilir bir ürün anlatısı, kalıcı sürüm kaydı ve doğrulanmış
`main` yayını olarak teslim etmek.

## Bitti ölçütü

1. Türkçe README “neden Divan?” sorusunu somut farklarla yanıtlıyor.
2. İngilizce README dünya çapındaki kullanıcı için aynı ürünü anlatıyor.
3. CHANGELOG v0.9.0 kapsamını ve doğrulama kanıtını kaydediyor.
4. BLUEPRINT geçmiş sürümler ile sıradaki işi birbirinden ayırıyor.
5. Sadrazam, PR hazırlanmasını “yayınlandı” saymayan kalıcı Yayın Kanunu taşıyor.
6. CI; marketplace sürümü, README, CHANGELOG ve BLUEPRINT eşleşmesini denetliyor.
7. Yerel testler, Agent Skills ve Claude Code doğrulayıcıları geçiyor.
8. PR taslaktan çıkarılıyor, `main`e birleşiyor ve canlı GitHub README'si yeniden okunuyor.

## Uygulama sırası

1. Canlı `main` ve PR farkını kayda geçir.
2. README/TR, README/EN, CHANGELOG ve BLUEPRINT'i birlikte güncelle.
3. Yayın Kanunu ile sürüm/vitrin CI kapısını ekle; testini yaz.
4. Bütün doğrulama katmanlarını çalıştır ve kanıt dosyasına işle.
5. PR'ı güncelle, birleştir ve canlı yüzeyi doğrula.

## Kapsam dışı

- Ölçülmemiş hız, gelir veya kalite yüzdesi iddia etmek.
- Bu turda v1.0 etiketi koymak.
- Kullanıcı kanıtı olmadan “endüstri standardı” veya “dünyanın en iyisi” demek.

## Sonuç

Tamamlandı. PR #1, iki zorunlu GitHub Actions kontrolü geçtikten sonra `main`e
birleşti. Varsayılan dal ve GitHub Pages v0.9.0 olarak yeniden okundu. Etiketli
GitHub release oluşturulmadığı açıkça kaydedildi; sıradaki iş v0.10.0 davranış
eval koşucusudur.
