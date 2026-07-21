# Divan Topluluk Standartlari

> Bu dosya `registry/community-standards.json` kaynagindan uretilir. Elle degistirmeyin.

Dogrulama: `python scripts/standartlar.py --check`

## DCS-001 - Bes dakikada ilk basari

**English:** Five-minute first success

**Duzey:** required

Yeni kullanici pinlenmis kurulum, salt-okunur onizleme, doctor sonucu ve kurtarma komutuna ulasir.

**Kontroller:**
- `python scripts/validate.py`

**Kanıt:**
- `docs/Kurulum.md`
- `scripts/kur-hostlar.py`
- `tests/test_host_install.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-002 - Frameworkten bagimsiz cekirdek

**English:** Framework-independent core

**Duzey:** required

Host CLI'leri sinirda adapter olarak kalir; cekirdek politika ve islem durumu stdlib JSON sozlesmelerini kullanir.

**Kontroller:**
- `python scripts/validate.py`

**Kanıt:**
- `scripts/kur-hostlar.py`
- `scripts/legacy_state.py`
- `tests/test_host_install.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-003 - Kucuk ve tutarli kod

**English:** Small, cohesive code

**Duzey:** required

Temiz kod ratcheti yeni karmasikligi, uzun fonksiyonlari ve buyuk modulleri onler; eski borc kuculur.

**Kontroller:**
- `python scripts/hijyen.py --check`

**Kanıt:**
- `scripts/hijyen.py`
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
- `scripts/kur-hostlar.py`
- `tests/test_validate.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-005 - Iddialardan once test ve kanit

**English:** Tests and evidence before claims

**Duzey:** required

Davranis degisiklikleri once basarisiz regresyon testiyle baslar; kalite iddialari gercek adapter ve kor hakem protokolune dayanir.

**Kontroller:**
- `python -m unittest discover -s tests -v`
- `python evals/run.py --check`

**Kanıt:**
- `tests/test_eval_runner.py`
- `tests/test_real_adapters.py`
- `evals/README.md`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-006 - Guvenli tedarik zinciri

**English:** Secure supply chain

**Duzey:** required

Bagimliliklar ve Actions degismez olarak pinlenir, izinler asgari olur ve yayin artefaktlari kanitlanir.

**Kontroller:**
- `python -m unittest tests.test_workflows -v`

**Kanıt:**
- `.github/workflows/teftis.yml`
- `.github/workflows/codeql.yml`
- `tests/test_workflows.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-007 - Geri alinabilir yasam dongusu

**English:** Reversible lifecycle

**Duzey:** required

Kurulum, kaldirma, kurtarma ve geri alma acik, belgeli ve yalnizca kanitlanmis Divan sahipligini etkileyen islemlerdir.

**Kontroller:**
- `python -m unittest tests.test_host_install -v`

**Kanıt:**
- `scripts/kur-hostlar.py`
- `scripts/kaldir-codex.ps1`
- `scripts/kaldir-codex.sh`
- `tests/test_host_install.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-008 - Kesfedilebilir ve eszamanli belgeler

**English:** Discoverable synchronized documentation

**Duzey:** required

Turkce ve Ingilizce kritik yollar, Wiki, Pages ve yayin metaverisi yayin manifestosu ile eszamanli kalir.

**Kontroller:**
- `python scripts/yayin.py --check`
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
- `python scripts/devral.py --check`

**Kanıt:**
- `CONTRIBUTING.md`
- `.github/ISSUE_TEMPLATE`
- `scripts/devral.py`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.

## DCS-010 - Erisilebilir, ozel ve kanit odakli isletim

**English:** Accessible, private, evidence-led operation

**Duzey:** required

Cekirdek kullanim telemetri gerektirmez; metin ciktilari renksiz calisir, UTF-8/LF korunur ve benimsenme iddialari kamu kanitina dayanir.

**Kontroller:**
- `python scripts/hijyen.py --check`
- `python scripts/v1.py --check`

**Kanıt:**
- `scripts/hijyen.py`
- `registry/v1-gates.json`
- `docs/V1-Hazirlik.md`

**Istisna politikasi:** Dar, belgelenmis ve sureli istisnalar standard-exceptions.json kaydiyla sinirlidir.
