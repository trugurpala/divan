# v1 Hazırlık Karnesi

Hedef sürüm: v1.0.0

> **Bugünkü sonuç:** 3/8 kapı kanıtla geçti; 3 kapının otomasyonu hazır fakat canlı kanıtı henüz kaydedilmedi. Bütün kapılar geçmeden Divan v1 veya ‘dünya standardı’ ilan edilmez.

| Kapı | Durum | Kanıt |
|---|---|---|
| Kararlı public skill ve komut sözleşmesi | ✅ Geçti | `AGENTS.md`<br>`docs/Standartlar-ve-Limitler.md`<br>`docs/Vezir-Katalogu.md` |
| Yapısal doğrulama ve davranış eval sözleşmesi yayın kapısı | ✅ Geçti | `.github/workflows/teftis.yml`<br>`evals/run.py`<br>`tests/test_eval_runner.py` |
| README, Pages ve Wiki canlı yüzey doğrulaması | ✅ Geçti | `.github/workflows/site-testi.yml`<br>`.github/workflows/wiki-sync.yml`<br>`.divan/evidence/teftis-20260718-v0103.md` |
| Claude Code ve Codex Linux/macOS/Windows temiz-host uyumluluk matrisi | 🟡 Hazır; canlı kanıt bekliyor | `.github/workflows/uyumluluk.yml`<br>`docs/Kurulum.md` |
| Kayıtlı kaldırma ve önceki kurulumu geri yükleme tatbikatı | 🟡 Hazır; canlı kanıt bekliyor | `scripts/kaldir-codex.sh`<br>`scripts/kaldir-codex.ps1`<br>`.github/workflows/uyumluluk.yml` |
| Etiketli GitHub Release, sürüm notu ve sabitlenebilir kurulum | 🟡 Hazır; canlı kanıt bekliyor | `.github/workflows/release.yml`<br>`release-manifest.json`<br>`CHANGELOG.md` |
| Beyan edilmiş gerçek ajan ve hakemle yayımlanmış kör A/B kanıtı | ⬜ Bekliyor | `evals/README.md` |
| Bağımsız kullanıcıdan tekrar üretilebilir kurulum ve görev kanıtı | ⬜ Bekliyor | `.github/ISSUE_TEMPLATE/kabul-kaniti.yml` |

## Durumların anlamı

- **Geçti:** kanıt üretildi ve tekrar denetlenebilir.
- **Hazır:** uygulama/CI kapısı yazıldı; `main` veya Release üstünde başarılı koşu bekleniyor.
- **Bekliyor:** ürünün kendi kendine uyduramayacağı gerçek dış kanıt gerekiyor.

## v1 için kalan gerçek işler

1. Gerçek bir ajan adaptörü ve bağımsız hakemle aynı vakaları baseline/skill olarak koşup sonucu yayımlamak.
2. Proje sahibi dışındaki en az bir kullanıcının sabitlenmiş release üzerinden kurulum ve görev kanıtını kabul formuyla göndermesi.

Bu sayfa elle güncellenmez. Kaynak `registry/v1-gates.json`; üretim `python scripts/v1.py --render`, sapma teftişi `python scripts/v1.py --check` komutudur.
