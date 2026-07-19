# v0.12.2 Windows Salt-Okunur Cache Teftişi

Tarih: 2026-07-20 (Europe/Istanbul)

- Gerçek yeni worktree'de `evals/__pycache__` dizini `ReadOnly, Directory`
  öznitelikleriyle üretildi; v0.12.1 temizleyici içerikleri sildikten sonra
  `PermissionError [WinError 5]` ile kök dizini kaldıramadı.
- Önce `test_clean_removes_readonly_generated_directory` eklendi ve aynı
  nedenle kırmızı olduğu görüldü.
- İlk tüm-ağacı yazılabilir yapan çözüm bağımsız incelemede reddedildi: gerçek
  junction testi repo dışındaki hedefin modunu değiştirebildiğini gösterdi.
- Son `_retry_readonly` çözümü yalnız `shutil.rmtree` tarafından
  `PermissionError` ile bildirilen gerçek yolu düzeltir; symlink ve Windows
  reparse point/junction üzerinde fail-closed kalır. Junction testi dış dosyanın
  varlığını ve salt-okunur modunu koruduğunu doğrular.
- 101 test geçti; Windows'ta 1 POSIX ve ayrıcalık isteyen 1 symlink testi
  beklendiği gibi atlandı. Ruff/C90 ve mypy temiz, branch coverage %64 ve
  `fail_under=55` kapısı geçti.
- Hijyen temizliği, `validate`, `devral`, katalog, v1, yayın, eval, Wiki,
  Meclis, upstream ve `git diff --check` kapıları taze koşuda geçti.

Bu bakım sürümü temizlik kapsamını genişletmez; yedek, kanıt, manifest ve
kullanıcı dosyaları yine silinmez.

## Kamusal teslim ve kurulum

- PR #21 bütün zorunlu CI kontrollerinden geçti ve
  `c226dccff4a91e7da6f54227942f78367836d934` ile `main`e birleşti.
- Release workflow `29705195263` başarıyla tamamlandı. Değişmez `v0.12.2`
  etiketi aynı commit'e bağlı; taslak/ön-sürüm olmayan GitHub Release ZIP ve
  SHA-256 varlıklarını yayımlar.
- Canlı Pages ve Wiki `v0.12.2` döndürdü; release Chromium etkileşim kontrolü
  geçti.
- Global kurulum dry-run sonrasında sahiplik kayıtlı v0.12.1 işlemini geri aldı
  ve `install-20260719T215712Z-c9095665.json` işlemiyle doğrulandı.
- Claude ve Codex'in her birinde 5 paket/41 skill etkin ve ref `v0.12.2` olarak
  geri okundu. GitKraken, Prompts.chat, OpenAI bundled/runtime ve kişisel
  `vibe-coder-standard` eklentileri korundu.
