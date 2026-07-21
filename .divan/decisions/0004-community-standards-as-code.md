# ADR 0004: Topluluk standartlarını kod olarak yönet

## Bağlam

Divan'ın v0.12.2 kalite, hijyen, yayın ve lisans kapıları güçlüdür; ancak bu
kurallar tek bir ürün sözleşmesinde birleşmez. GitHub `main` dalı zorunlu
kontrollerle korunmaz, destek yolu dağınıktır ve kurucunun doctor/upgrade yaşam
döngüsü yoktur. Framework ve host CLI değişiklikleri çekirdek işlem koduna
doğrudan yayılabilmektedir.

## Seçenekler

1. Kuralları yalnız belgede toplamak: ucuz, fakat sapmayı engellemez.
2. On standardı makine-okunur registry, doğrulayıcı, test ve CI kanıtıyla
   yönetmek: mevcut stdlib mimarisini korur ve ihlali erken durdurur.
3. Yeni framework, dashboard ve governance bot kurmak: bugünkü ölçekte gereksiz
   çalışma zamanı, güven ve bakım yükü getirir.

## Karar

İkinci seçenek seçildi. DCS-001..DCS-010 tek registry'de tutulacak; generated
belge, expiring exception ve Clean Code ratchet aynı kapıya bağlanacak. Claude
ve Codex host davranışı adaptör sınırına alınacak. Kurulum yaşam döngüsü
read-only doctor ve provenance-gated transactional upgrade ile tamamlanacak.
GitHub güvenlik ve branch kuralları repo içi kanıtla eşlenecek.

## Sonuçlar

- Yeni kod için karmaşıklık 10, fonksiyon 50 ve modül 400 sınırı uygulanır;
  mevcut borç yalnız küçülebilen baseline'da tutulur.
- Release zinciri checksum yanında SPDX SBOM ve artifact attestation üretir.
- `main` zorunlu kontroller olmadan değişemez; recovery için yönetici bypass'ı
  korunur.
- Telemetri, hosted dashboard ve üçüncü taraf runtime eklenmez.
- v0.13.0 bu mekanik güvenceyi yayımlar; bağımsız kullanıcı kanıtı olmadan v1
  veya davranış kalitesi iddiası yapılmaz.

