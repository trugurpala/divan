---
description: Proje hafızası — kur, yaz, oku veya karar kaydet (defterdar nizamı)
argument-hint: kur | yaz | oku | karar konu
---
`defterdar` skill'ini yükle ve şu alt komutu uygula: $ARGUMENTS

- **kur**: Önce çakışmaları denetle; kullanıcının onayıyla AGENTS.md +
  BLUEPRINT.md + .divan/ iskeletini şablonlardan oluştur. Mevcut dosyaların
  üzerine yazma; açık yetki yoksa git init/commit/push yapma. Para-dokunan projeyse
  risk-register.md ekle ve spec-first kuralını AGENTS.md'ye yaz.
- **yaz**: bu oturumda yapılanları .divan/progress.md'ye ve BLUEPRINT durum
  günlüğüne tarihli işle; "sıradaki adım"ı net bırak. Commit yalnızca kullanıcı
  açıkça yetki verdiyse atılır.
- **oku**: AGENTS.md → BLUEPRINT → progress.md → son 5 commit sırasıyla oku;
  "kaldığımız yer"i 3 cümlede özetle ve sıradaki adımı öner.
- **karar**: verilen konuyu .divan/decisions/ altına ADR şablonuyla kaydet,
  BLUEPRINT ADR özetine tek satır ekle.

Alt komut verilmediyse "oku" varsay.
