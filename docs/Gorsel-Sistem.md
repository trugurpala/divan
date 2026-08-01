# Divan Görsel Sistemi

Divan'ın görsel dili gece mavisi, fildişi, firuze, mercan ve altın üzerine
kurulur. İnce İznik geometrisi kimliği taşır; süsleme metnin ve kanıtın önüne
geçmez. Neon robot, anlamsız küre ve rastgele parıltı kullanılmaz.

## Kanonik kaynak

[Divan — Nizamlı Müşterek](https://www.figma.com/design/Z325Jjy36I7KLdizcaZAnZ)
dosyası değişkenleri, yazı stillerini, auto-layout bileşenlerini, GitHub
varlıklarını, masaüstü/mobil sayfaları ve üretim dışa aktarım kurallarını taşır.
Repo çıktıları bu düzenlenebilir kaynaktan alınır.

2026-08-01 tarihli salt okunur geri okuma; altı gerçek sayfayı, 16 semantik
değişkeni, iki modu, altı yazı stilini, bileşen ve varyant setlerini
`docs/figma-system-manifest.json` içinde kaydeder. Bu kayıt Figma'nın yerini
almaz; repo testinin doğrulayabildiği çevrimdışı yayın kanıtıdır.

## Üretim dosyaları

Onaylanan GitHub ve site varlıkları `docs/assets/github/` altında tutulur.
Dosya adı, piksel ölçüsü, biçim, azami ağırlık, alt metin ve kullanım yüzeyi
testlerle denetlenir. SVG yalnız güvenli statik şekiller içerir; script, dış
kaynak ve olay işleyicisi içermez.
