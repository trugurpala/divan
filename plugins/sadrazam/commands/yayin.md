---
description: Sürüm yüzeylerini tek kaynaktan hazırla, teftiş et ve kanıtlı yayına götür
argument-hint: "[semver]"
---

# /yayin — Unutulamaz yayın zinciri

1. `AGENTS.md`, `BLUEPRINT.md`, `.divan/progress.md`, `VERSION` ve
   `release-manifest.json` dosyalarını oku.
2. Kullanıcı yeni sürüm istediyse `python scripts/release.py --prepare <semver>`
   çalıştır. Bu yalnız deterministik sürüm yüzeylerini değiştirir; CHANGELOG ve
   BLUEPRINT anlatısını yapılan gerçek işe göre aynı turda yaz.
3. Katalog, Meclis ve v1 sayfası kaynakları değiştiyse kendi `--render`
   komutlarını çalıştır; elle üretilen çıktıyı düzeltme.
4. `python scripts/release.py --check` dahil repo teftişini çalıştır.
5. PR → zorunlu CI → `main` → Pages/Wiki → tag/GitHub Release sırasını ayrı
   kanıtlarla tamamla. Workflow başarısızsa son başarılı aşamayı söyle;
   sonrakini olmuş gibi anlatma.
6. `.divan/progress.md`, kanıt dosyası ve BLUEPRINT günlüğünü kapanışta işle.

GitHub Release sayfası `CHANGELOG` bölümünden üretilir. Etiket varsa taşınmaz;
yalnız Release notu eşitlenir. v1 ancak `registry/v1-gates.json` içindeki bütün
kapılar `passed` olduğunda ilan edilir.
