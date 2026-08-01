# Divan Yazım ve Üslup Sözleşmesi

Bu sözleşme README, Wiki, site, sürüm notu, issue, pull request ve kullanıcıya
gösterilen bütün Divan metinleri için geçerlidir. Amaç süslü görünmek değil;
okurun ne olduğunu, ne yapacağını ve sonucu nasıl doğrulayacağını ilk okumada
anlamasıdır.

## Yazmaya başlamadan önce

Önce kullanıcının sorusunu yazın, sonra Divan'ın cevabını verin. İnsan önce
sonucu görür; iç mimariyi ve istisnaları gerektiği yerde okur.

Her paragraf tek ana fikir taşır. Kısa ve orta uzunlukta cümleleri, etken çatıyı
ve somut fiilleri tercih edin.

## Dil kuralları

- “Değer sağlar”, “güçlendirir”, “optimize eder” ve benzeri kanıtsız pazarlama
  kalıplarını kullanmayın.
- Aynı bilgiyi farklı başlıklarda tekrarlamayın.
- Teknik bir terimi ilk kullanımda günlük dille açıklayın.
- Ferman (kullanıcı isteği), Hükümdar (proje sahibi), Teftiş (doğrulama) ve
  Nöbet (upstream bakım incelemesi) adlarını koruyun; ilk kullanımda karşılığını
  yazın. Kullanıcıya rol yapmayı dayatmayın.
- Kanıtlanmayan hız, başarı oranı, kalite artışı veya “dünya standardı” iddiası
  yazmayın.
- Türkçe ve İngilizce metinleri kelime kelime çevirmeyin. Bilgi sırasını ve
  anlamı koruyun; her dilde doğal cümle kurun.
- `de/da`, `ki` ve `mi` bağlama göre değişir. Bunları kör bir düzenli ifadeyle
  düzeltmeyin; insan incelemesinde cümlenin anlamına göre değerlendirin.
- Noktalama işaretinden önce boşluk bırakmayın. Kısaltmalarda ve büyük harflerde
  güncel TDK kurallarını izleyin.

## Otomatik kapı ve insan incelemesi

`python scripts/prose.py --check` yalnız güvenle belirlenebilen hataları kapatır:
UTF-8 bozulması, bilinen açık yazım yanlışları, yanlış noktalama boşluğu,
yinelenen boşluk veya noktalama, bozuk Markdown ve sürüm/yol sapması. JSON çıktı
için `python scripts/prose.py --check --json` kullanılır.

Uzun paragraf, edilgen anlatım, kanıtsız üstünlük, teknik terim yoğunluğu ve
tekrar gibi bağlama bağlı konular uyarıdır. Yazar veya inceleyen kişi bu
uyarıları metnin amacıyla birlikte değerlendirir.

## Kaynaklar

Erişim tarihi: 1 Ağustos 2026.

- [Hacettepe Üniversitesi TDK Yazım Kuralları sunumu](https://pdb.hacettepe.edu.tr/baharhizmeticiegitim/TDK_Yazim_Kurallari_200319.pdf): yazım, büyük harf, kısaltma ve noktalama örnekleri için gönderilen eğitim kaynağı. PDF repoya kopyalanmaz.
- [TDK Yazım Kuralları sunuşu](https://tdk.gov.tr/icerik/yazim-kurallari/sunus/): güncel kanonik giriş.
- [Büyük harflerin kullanıldığı yerler](https://tdk.gov.tr/icerik/yazim-kurallari/buyuk-harflerin-kullanildigi-yerler/)
- [Kısaltmalar](https://tdk.gov.tr/icerik/yazim-kurallari/kisaltmalar/)
- [Noktalama işaretleri](https://tdk.gov.tr/icerik/yazim-kurallari/noktalama-isaretleri-aciklamalar/)

Bu kaynaklardan uzun metin kopyalanmaz. Divan yalnız uyguladığı kuralları kendi
cümleleriyle özetler ve kaynağa bağlantı verir.
