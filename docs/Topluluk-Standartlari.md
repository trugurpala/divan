# Divan Topluluk Standartlari

> Bu dosya `registry/community-standards.json` kaynagindan uretilir. Elle degistirmeyin.

Dogrulama: `python scripts/standards.py --check`

Bu `DCS-*` kurallari Divan repo dagitimini yonetir. Hedef kurulu proje,
Project OS tarafindan yalniz uygulanabilir `DPS-*` kurallariyla denetlenir.
Project OS ayrimi ve komutlari: `docs/Project-OS.tr.md`.

## DCS-001 - Bes dakikada ilk basari

**English:** Five-minute first success

**Duzey:** required

Yeni kullanici pinlenmis kurulum, salt-okunur onizleme, doctor sonucu ve kurtarma komutuna ulasir.

**Kontroller:**
- `python scripts/validate.py`

**Kanıt:**
- `docs/Kurulum.md`
- `scripts/host_lifecycle.py`
- `tests/test_host_install.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-002 - Frameworkten bagimsiz cekirdek

**English:** Framework-independent core

**Duzey:** required

Host CLI'leri sinirda adapter olarak kalir; cekirdek politika ve islem durumu stdlib JSON sozlesmelerini kullanir.

**Kontroller:**
- `python scripts/validate.py`

**Kanıt:**
- `scripts/host_lifecycle.py`
- `scripts/legacy_state.py`
- `tests/test_host_install.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-003 - Kucuk ve tutarli kod

**English:** Small, cohesive code

**Duzey:** required

Temiz kod ratcheti yeni karmasikligi, uzun fonksiyonlari ve buyuk modulleri onler; eski borc kuculur.

**Kontroller:**
- `python scripts/hygiene.py --check`
- `python scripts/clean_code.py --check`

**Kanıt:**
- `scripts/hygiene.py`
- `scripts/clean_code.py`
- `registry/clean-code-baseline.json`
- `docs/Standartlar-ve-Limitler.md`
- `pyproject.toml`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-004 - Acik veri ve hata sozlesmeleri

**English:** Explicit data and error contracts

**Duzey:** required

Kamuya acik otomasyon yapilandirilmis cikti, eyleme donuk hata ve sifir olmayan cikis durumu saglar.

**Kontroller:**
- `python scripts/validate.py`

**Kanıt:**
- `scripts/validate.py`
- `scripts/host_lifecycle.py`
- `tests/test_validate.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-005 - Iddialardan once test ve kanit

**English:** Tests and evidence before claims

**Duzey:** required

Davranis degisiklikleri once basarisiz regresyon testiyle baslar; kalite iddialari gercek adapter ve kor hakem protokolune dayanir.

**Kontroller:**
- `python -m unittest discover -s tests -v`
- `coverage run -m unittest discover -s tests`
- `coverage report --fail-under=64`
- `python evals/run.py --check`

**Kanıt:**
- `tests/test_eval_runner.py`
- `tests/test_real_adapters.py`
- `evals/README.md`
- `pyproject.toml`
- `.github/workflows/quality-gate.yml`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-006 - Guvenli tedarik zinciri

**English:** Secure supply chain

**Duzey:** required

Bagimliliklar ve Actions degismez olarak pinlenir, izinler asgari olur ve yayin artefaktlari kanitlanir.

**Kontroller:**
- `python -m unittest tests.test_workflows -v`

**Kanıt:**
- `.github/workflows/quality-gate.yml`
- `.github/workflows/codeql.yml`
- `tests/test_workflows.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-007 - Geri alinabilir yasam dongusu

**English:** Reversible lifecycle

**Duzey:** required

Host kurulumu, proje guncellemesi, onarim, arsiv, kurtarma ve geri alma acik, belgeli ve yalnizca kanitlanmis Divan sahipligini etkileyen islemlerdir.

**Kontroller:**
- `python -m unittest tests.test_host_install -v`
- `python -m unittest tests/test_host_upgrade.py tests/test_host_upgrade_authority.py tests/test_host_upgrade_locking.py tests/test_host_upgrade_security.py -v`
- `python -m unittest tests.test_project_lifecycle tests.test_goal_archive tests.test_adoption -v`

**Kanıt:**
- `scripts/host_lifecycle.py`
- `scripts/host_upgrade.py`
- `scripts/host_transactions.py`
- `scripts/host_install_journal.py`
- `scripts/host_journal.py`
- `scripts/host_journal_scan.py`
- `scripts/host_journal_transitions.py`
- `scripts/host_state.py`
- `plugins/sadrazam/company/project_state.py`
- `plugins/sadrazam/company/project_lifecycle.py`
- `plugins/sadrazam/company/project_transactions.py`
- `plugins/sadrazam/company/goal_archive.py`
- `plugins/sadrazam/company/adoption.py`
- `scripts/uninstall_codex.ps1`
- `scripts/uninstall_codex.sh`
- `tests/test_host_install.py`
- `tests/test_host_upgrade.py`
- `tests/test_host_upgrade_security.py`
- `tests/test_host_upgrade_authority.py`
- `tests/test_host_upgrade_locking.py`
- `tests/test_project_lifecycle.py`
- `tests/test_goal_archive.py`
- `tests/test_adoption.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-008 - Kesfedilebilir ve eszamanli belgeler

**English:** Discoverable synchronized documentation

**Duzey:** required

Turkce ve Ingilizce kritik yollar, Wiki, Pages ve yayin metaverisi yayin manifestosu ile eszamanli kalir.

**Kontroller:**
- `python scripts/release.py --check`
- `python scripts/wiki.py --check`

**Kanıt:**
- `release-manifest.json`
- `wiki-pages.json`
- `docs/Home.md`
- `README.en.md`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-009 - Katkici ve destek hazirligi

**English:** Contributor and support readiness

**Duzey:** required

Kullanicilar soru, hata, guvenlik, skill onerisi ve kabul kanitini ayirir; katkilara tek yerel denetim sirasi sunulur.

**Kontroller:**
- `python scripts/handoff.py --check`

**Kanıt:**
- `CONTRIBUTING.md`
- `.github/ISSUE_TEMPLATE`
- `scripts/handoff.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-010 - Erisilebilir, ozel ve kanit odakli isletim

**English:** Accessible, private, evidence-led operation

**Duzey:** required

Cekirdek kullanim telemetri gerektirmez; metin ciktilari renksiz calisir, UTF-8/LF korunur ve benimsenme iddialari kamu kanitina dayanir.

**Kontroller:**
- `python scripts/hygiene.py --check`
- `python scripts/v1.py --check`

**Kanıt:**
- `scripts/hygiene.py`
- `registry/v1-gates.json`
- `docs/V1-Hazirlik.md`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-011 - Ingilizce teknik cekirdek ve izlenebilir etki

**English:** English technical core and traceable impact

**Duzey:** required

Kanonik teknik girisler Ingilizce adlandirilir; Turkce yerellestirme korunur ve Company OS her degisikligi rol, framework, paket ve gecis etkilerine baglar.

**Kontroller:**
- `python scripts/naming.py --check`
- `python scripts/divan.py company-validate`

**Kanıt:**
- `registry/naming-policy.json`
- `scripts/naming.py`
- `scripts/divan.py`
- `plugins/sadrazam/company/roles.json`
- `plugins/sadrazam/company/workflows.json`
- `plugins/sadrazam/company/frameworks.json`
- `plugins/sadrazam/company/impact-graph.json`
- `tests/test_company_engine.py`
- `tests/test_naming.py`

**Istisna politikasi:** Eski Turkce teknik adlar yalniz registry/naming-policy.json icindeki sureli uyumluluk kayitlariyla korunabilir.
