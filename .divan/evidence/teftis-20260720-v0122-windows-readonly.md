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
