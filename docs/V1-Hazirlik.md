# v1 Hazırlık Karnesi

Hedef sürüm: v1.0.0

> **Bugünkü sonuç:** 7/8 kapı kanıtla geçti; 1 kapının otomasyonu hazır fakat canlı kanıtı henüz kaydedilmedi. Bütün kapılar geçmeden Divan v1 veya ‘dünya standardı’ ilan edilmez.

| Kapı | Durum | Kanıt |
|---|---|---|
| Kararlı public skill ve komut sözleşmesi | ✅ Geçti | `AGENTS.md`<br>`docs/Standartlar-ve-Limitler.md`<br>`docs/skill-catalog.md` |
| Yapısal doğrulama ve davranış eval sözleşmesi yayın kapısı | ✅ Geçti | `.github/workflows/quality-gate.yml`<br>`.github/workflows/codeql.yml`<br>`evals/run.py`<br>`tests/test_eval_runner.py`<br>`tests/test_real_adapters.py` |
| README, Pages ve Wiki canlı yüzey doğrulaması | ✅ Geçti | `.github/workflows/site-tests.yml`<br>`.github/workflows/wiki-sync.yml`<br>`.divan/evidence/teftis-20260719-v012-release-install.md`<br>[https://github.com/trugurpala/divan/actions/runs/29702535899](https://github.com/trugurpala/divan/actions/runs/29702535899)<br>[https://github.com/trugurpala/divan/actions/runs/29702535867](https://github.com/trugurpala/divan/actions/runs/29702535867) |
| Claude Code ve Codex native Linux/macOS/Windows temiz-host yaşam döngüsü | ✅ Geçti | `.github/workflows/compatibility.yml`<br>`scripts/host_lifecycle.py`<br>`tests/test_host_install.py`<br>`.divan/evidence/teftis-20260719-v012-release-install.md`<br>[https://github.com/trugurpala/divan/actions/runs/29702535873](https://github.com/trugurpala/divan/actions/runs/29702535873) |
| Kayıtlı kaldırma ve önceki kurulumu geri yükleme tatbikatı | ✅ Geçti | `scripts/host_lifecycle.py`<br>`tests/test_host_install.py`<br>`scripts/uninstall_codex.sh`<br>`scripts/uninstall_codex.ps1`<br>[https://github.com/trugurpala/divan/actions/runs/29633649098](https://github.com/trugurpala/divan/actions/runs/29633649098) |
| Etiketli GitHub Release, sürüm notu ve sabitlenebilir kurulum | ✅ Geçti | `release-manifest.json`<br>`.divan/evidence/teftis-20260719-v012-release-install.md`<br>[https://github.com/trugurpala/divan/releases/tag/v0.12.0](https://github.com/trugurpala/divan/releases/tag/v0.12.0)<br>[https://github.com/trugurpala/divan/actions/runs/29702535903](https://github.com/trugurpala/divan/actions/runs/29702535903) |
| Beyan edilmiş gerçek ajan ve hakemle yayımlanmış kör A/B kanıtı | ✅ Geçti | `evals/results/claude-codex-baglam-muhafizi-v012.json`<br>`evals/README.md`<br>`evals/adapters/claude_agent.py`<br>`evals/adapters/codex_judge.py`<br>`tests/test_real_adapters.py` |
| Doğrulanmış temiz-proje kullanımı | 🟡 Hazır; canlı kanıt bekliyor | `.github/ISSUE_TEMPLATE/kabul-kaniti.yml`<br>`plugins/sadrazam/divan_runtime/adoption.py`<br>`plugins/sadrazam/divan_runtime/adoption_proof.py`<br>`tests/test_adoption_v2.py`<br>`tests/test_adoption_proof.py` |

## Durumların anlamı

- **Geçti:** kanıt üretildi ve tekrar denetlenebilir.
- **Hazır:** uygulama/CI kapısı yazıldı; `main` veya Release üstünde başarılı koşu bekleniyor.
- **Bekliyor:** gerekli gerçek teknik kanıt henüz üretilmedi.

## v1 için kalan gerçek işler

1. Yayımlanmış sabit bir Divan release'iyle gerçek ve ayrı bir projede makinece doğrulanabilir temiz-proje kanıtı üretmek.

Bu sayfa elle güncellenmez. Kaynak `registry/v1-gates.json`; üretim `python scripts/v1.py --render`, sapma teftişi `python scripts/v1.py --check` komutudur.
