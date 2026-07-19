# ADR 0003 — Clean Code ve güvenli repo hijyeni kapısı

## Bağlam

Divan'ın kurulum zinciri işlemsel olsa da repo kodlama/EOL sözleşmesi ve
üretilmiş artefakt kapısı taşımıyordu. Üç çekirdek fonksiyon 25 üzeri McCabe
karmaşıklığına ulaştı. Kullanıcı geçmiş çöplerin kalıcı temizlenmesini isterken
aktif rollback yedeğinin kör silinmesi veri kaybı riski oluşturuyor.

## Seçenekler

1. Yalnız bugünkü dosyaları silmek.
2. Bütün uzun dosyaları geniş kapsamlı yeniden yazmak.
3. Kanıtlı allowlist temizliği, UTF-8/LF sözleşmesi ve 25 karmaşıklık bütçesini
   birlikte uygulamak.

## Karar

3. seçenek kabul edildi. Temizlik aracı yalnız yeniden üretilebilir allowlist
artefaktlarını silebilir; bilinmeyen veya kullanıcıya ait veride fail-closed
davranır. Aktif rollback yedeği korunur. Karmaşıklık kapısı yalnız sınırı aşan
kritik fonksiyonlarda davranış-korumalı parçalama gerektirir.

## Sonuçlar

- Basit kodlama/cache sorunları CI'da tekrarlanabilir biçimde yakalanır.
- Temizlik komutu güvenli ve idempotent olur.
- Geniş ve riski yüksek “temiz kod” yeniden yazımı yapılmaz.
- v1 bağımsız kabul kapısı etkilenmez; kalite artışı iddiası üretilmez.
