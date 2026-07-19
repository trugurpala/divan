# v1 Hazırlık Karnesi

Hedef sürüm: v1.0.0

> **Bugünkü sonuç:** 5/8 kapı kanıtla geçti; 1 kapının otomasyonu hazır fakat canlı kanıtı henüz kaydedilmedi. Bütün kapılar geçmeden Divan v1 veya ‘dünya standardı’ ilan edilmez.

| Kapı | Durum | Kanıt |
|---|---|---|
| Kararlı public skill ve komut sözleşmesi | ✅ Geçti | `AGENTS.md`<br>`docs/Standartlar-ve-Limitler.md`<br>`docs/Vezir-Katalogu.md` |
| Yapısal doğrulama ve davranış eval sözleşmesi yayın kapısı | ✅ Geçti | `.github/workflows/teftis.yml`<br>`.github/workflows/codeql.yml`<br>`evals/run.py`<br>`tests/test_eval_runner.py`<br>`tests/test_real_adapters.py` |
| README, Pages ve Wiki canlı yüzey doğrulaması | ✅ Geçti | `.github/workflows/site-testi.yml`<br>`.github/workflows/wiki-sync.yml`<br>`.divan/evidence/teftis-20260718-v0103.md` |
| Claude Code ve Codex native Linux/macOS/Windows temiz-host yaşam döngüsü | 🟡 Hazır; canlı kanıt bekliyor | `.github/workflows/uyumluluk.yml`<br>`scripts/kur-hostlar.py`<br>`tests/test_host_install.py` |
| Kayıtlı kaldırma ve önceki kurulumu geri yükleme tatbikatı | ✅ Geçti | `scripts/kur-hostlar.py`<br>`tests/test_host_install.py`<br>`scripts/kaldir-codex.sh`<br>`scripts/kaldir-codex.ps1`<br>[https://github.com/trugurpala/divan/actions/runs/29633649098](https://github.com/trugurpala/divan/actions/runs/29633649098) |
| Etiketli GitHub Release, sürüm notu ve sabitlenebilir kurulum | ✅ Geçti | `release-manifest.json`<br>[https://github.com/trugurpala/divan/releases/tag/v0.11.0](https://github.com/trugurpala/divan/releases/tag/v0.11.0)<br>[https://github.com/trugurpala/divan/actions/runs/29633649098](https://github.com/trugurpala/divan/actions/runs/29633649098) |
| Beyan edilmiş gerçek ajan ve hakemle yayımlanmış kör A/B kanıtı | ⬜ Bekliyor | `evals/README.md`<br>`evals/adapters/claude_agent.py`<br>`evals/adapters/codex_judge.py`<br>`tests/test_real_adapters.py` |
| Bağımsız kullanıcıdan tekrar üretilebilir kurulum ve görev kanıtı | ⬜ Bekliyor | `.github/ISSUE_TEMPLATE/kabul-kaniti.yml` |

## Durumların anlamı

- **Geçti:** kanıt üretildi ve tekrar denetlenebilir.
- **Hazır:** uygulama/CI kapısı yazıldı; `main` veya Release üstünde başarılı koşu bekleniyor.
- **Bekliyor:** ürünün kendi kendine uyduramayacağı gerçek dış kanıt gerekiyor.

## v1 için kalan gerçek işler

1. Gerçek bir ajan adaptörü ve bağımsız hakemle aynı vakaları baseline/skill olarak koşup sonucu yayımlamak.
2. Proje sahibi dışındaki en az bir kullanıcının sabitlenmiş release üzerinden kurulum ve görev kanıtını kabul formuyla göndermesi.

Bu sayfa elle güncellenmez. Kaynak `registry/v1-gates.json`; üretim `python scripts/v1.py --render`, sapma teftişi `python scripts/v1.py --check` komutudur.
