# Etkin plan — v0.18.0 yayın kapanışı

Kanonik hedef: `.divan/spec/v0.18.0-nizam-i-sefer.md`.

1. Uygulama PR #54 ve sürüm PR #55 kimliğini değişmez v0.18.0 etiketiyle bağla.
2. Beş Release varlığını indir; GitHub digest, iki checksum manifesti, ZIP
   sürümü ve SPDX 2.3 SBOM bilgisini yeniden hesaplayarak doğrula.
3. Her varlık için release/v0.2 ve SLSA provenance/v1 attestation kayıtlarını,
   imzalayan workflow'u ve kaynak commit'i doğrula.
4. README, iki dil, Pages/site, Wiki, yol haritası, blueprint ve ilerleme
   defterindeki aday ifadelerini yalnız gerçek yayından sonra güncelle.
5. Yayın sonrası PR'ı zorunlu CI üzerinden korumalı `main`e taşı; release
   workflow'unun mevcut varlıkları byte-byte doğrulayıp idempotent kalmasını,
   Pages ve Wiki'nin v0.18.0'a yakınsamasını bekle.
6. Sonraki sürümü başlatmadan önce native host adaptörlerini ayrı kanıtlı
   dilimlere ayır; desteklenmeyen yeteneğe “tam uyum” deme.

Issue #34 dış kullanıcı gerektirir. Sahip canary'si ve temiz-host CI bu kapıyı
kapatmaz; v1 bağımsız kabul gelene kadar 7/8 kalır.
