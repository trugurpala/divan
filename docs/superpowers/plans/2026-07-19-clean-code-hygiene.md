# v0.12.1 Clean Code ve Repo Hijyeni Uygulama Planı

> **Agentic worker:** Bu planı `executing-plans`, davranış değişikliklerini
> `test-driven-development`, hata araştırmasını `systematic-debugging` ile uygula.

**Hedef:** Divan'da kodlama, gereksiz artefakt ve kontrolsüz karmaşıklık
problemlerini tekrarlanabilir kapılarla önlemek; kanıtlı çöpleri kalıcı temizlemek.

**Mimari:** Stdlib tabanlı bağımsız `scripts/hijyen.py`, mevcut `validate.py`
kapısına eklenir. Ruff C90 sınırı mevcut kalite zincirine katılır. Kritik büyük
fonksiyonlar aynı public davranışı koruyan saf yardımcı fonksiyonlara ayrılır.

**Teknoloji:** Python 3.11+ stdlib, unittest, Ruff, mypy, Git/GitHub CLI.

### Görev 1: Hijyen sözleşmesini test-first kur

**Dosyalar:** `tests/test_hijyen.py`, `scripts/hijyen.py`, `.gitignore`,
`.gitattributes`, `.editorconfig`, `scripts/validate.py`.

- [x] Bozuk UTF-8, BOM, mojibake ve allowlist cache tespiti için başarısız
  birim testlerini yaz ve beklenen nedenle kırmızı olduklarını gör.
- [x] `--check` ve güvenli `--clean` davranışını en küçük kodla uygula.
- [x] Validator entegrasyon testini önce kırmızı, sonra yeşil yap.
- [x] Birinci taraf subprocess/dosya yollarını açık UTF-8'e geçir.

### Görev 2: Karmaşıklık bütçesini test-first uygula

**Dosyalar:** `tests/test_workflows.py`, `pyproject.toml`,
`.github/workflows/teftis.yml`, `scripts/validate.py`, `scripts/v1.py`,
`scripts/kur-hostlar.py`.

- [x] C90 + `max-complexity = 25` sözleşmesini isteyen başarısız testi yaz.
- [x] Kalite yapılandırmasını ve CI komutunu ekle; Ruff'ın üç gerçek ihlali
  yakaladığını kaydet.
- [x] `validate.denetle`, `_validate_real_agent_evidence` ve
  `rollback_transaction` fonksiyonlarını davranış değiştirmeden parçala.
- [x] İlgili test kümeleri, Ruff C90 ve mypy'ı yeşile getir.

### Görev 3: Kanıtlı kalıcı temizliği uygula

- [x] `python scripts/hijyen.py --clean` ile repo cache'lerini sil.
- [ ] PR #17/#16 birleşme kanıtını yeniden okuyup temiz eski worktree ve yerel/
  uzak dalları kaldır.
- [x] Aktif Divan yedeğinde yalnız `__pycache__` dizinlerini kaldır; manifestin
  işaret ettiği `ui-ux-pro-max` geri yükleme ağacını koru.
- [x] Temizlik sonrası `--check`, Git worktree ve manifest envanterini doğrula.

### Görev 4: v0.12.1 yüzeylerini ve kalıcı hafızayı eşitle

**Dosyalar:** `CHANGELOG.md`, README'ler, kurulum/Wiki/site yüzeyleri,
`release-manifest.json`, `BLUEPRINT.md`, `.divan/progress.md`, ADR ve teftiş.

- [x] `scripts/yayin.py` yolu ile v0.12.1'i hazırla; yeni hijyen yüzeyini yayın
  manifestine ekle.
- [x] Kullanıcıya güvenli temizlik ve korunan yedek ayrımını açıkça belgelet.
- [ ] ADR, ilerleme ve yerel teftiş kanıtını tamamla; v1 7/8 durumunu değiştirme.

### Görev 5: İnceleme ve kamusal teslim

- [ ] AGENTS.md'deki tam doğrulama zincirini, Ruff C90, mypy, coverage ve
  `git diff --check` ile birlikte taze çalıştır.
- [x] Bağımsız reviewer ajanına base/head diff'ini incelet; önemli bulguları düzelt.
- [ ] Dalı commit/push et, PR aç, CI'yı izle ve yeşilse `main`e birleştir.
- [ ] `main` üzerindeki CI, tag/Release, Pages ve Wiki kanıtını doğrula.
- [ ] Sabit v0.12.1 kaynağını Claude ve Codex'e dry-run ardından global kur;
  5 paket/41 skill ve alakasız eklentilerin korunduğunu doğrula.
