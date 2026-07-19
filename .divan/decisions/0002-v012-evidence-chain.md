# 0002 — v0.12 Evidence Chain

Durum: Kabul edildi

## Bağlam

Divan'ın v1'e giden iki dış kanıt kapısı açıktır. Bu kanıtlar ürün tarafından
uydurulamaz; ancak Windows kurulum akışı ve gerçek eval koşusunun provenance
kayıtları daha tekrar üretilebilir hale getirilebilir.

## Seçenekler

1. Dış kanıt gelene kadar hiçbir teknik iyileştirme yapmamak.
2. v1 kapılarını fixture/yerel sonuçla kapatmak.
3. Windows kurulum kontratını gerçek testle doğrulamak ve gerçek eval için gizli
   veri içermeyen provenance sözleşmesi eklemek.

## Karar

Üçüncü seçenek seçildi. v1 kapıları `pending` kalır; gerçek ajan, bağımsız
hakem ve bağımsız kullanıcı kanıtı dışarıdan gelmeden durum değiştirilmez.

## Sonuç

v0.12 çalışması güvenilir, denetlenebilir kanıt üretimini kolaylaştırır; kalite
veya benimseme iddiasını otomatik olarak yükseltmez.
