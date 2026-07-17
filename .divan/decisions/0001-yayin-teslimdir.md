# ADR-0001 — Yayın teslimdir

Tarih: 2026-07-18
Durum: Kabul edildi

## Bağlam

v0.8.2 kodu, dokümanı ve testleri özellik dalında hazırlandı; fakat PR taslak
kaldığı için varsayılan GitHub sayfası eski README ve eski planı göstermeye
devam etti. Teknik olarak doğru dal, kullanıcı açısından yanlış ürün yüzü
oluşturdu.

## Seçenekler

1. PR bağlantısını teslim saymak.
2. Kullanıcıya merge işini bırakmak.
3. “Yayınla” kapsamındaki işlerde dal → CI → hazır PR → merge → canlı doğrulama
   zincirinin tamamını teslim tanımına almak.

## Karar

Üçüncü seçenek seçildi. Kullanıcı kamuya açık veya dünya çapında kullanılacak
bir ürün istediğinde PR hazırlanması ara durumdur. Teslim ancak yetki kapsamı
içinde `main` birleşmesi, görünür sürüm notu ve canlı yüzey doğrulamasıyla
tamamlanır. Birleştirme yetkisi yoksa bu durum açık blocker olarak yazılır;
“yayınlandı” denmez.

## Sonuçlar

- Sadrazam'a Yayın Kanunu eklenir.
- CHANGELOG ve BLUEPRINT sürüm eşliği CI kapısı olur.
- Her oturum `progress.md` içinde sıradaki kesin adımı taşır.
- Release etiketi ayrı bir aşamadır; etiket yoksa sürüm “main'de” olarak
  tanımlanır, “release yayımlandı” denmez.
