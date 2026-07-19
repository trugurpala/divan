# Clean Code ve Repo Hijyeni Tasarımı

## Amaç

Divan'ın güvenli kurulum ve kanıt zincirini bozmadan, basit çevre sorunlarını
tekrar oluşmadan yakalamak: üretilmiş dosya birikimi, Windows karakter kodlaması
sapması, kontrolsüz fonksiyon karmaşıklığı ve sahipliği belirsiz yedek silme.

## Denetim bulguları

- 87 test, Ruff ve mypy başlangıçta temizdir.
- Birinci taraf metinlerde UTF-8 bozulması bulunmadı; ancak repo düzeyinde
  kodlama/EOL sözleşmesi yoktur ve iki subprocess yolu sistem locale'ine bağlıdır.
- McCabe 15 eşiğinde yedi fonksiyon uyarı verir. Bunlardan yalnız üçü 25'i aşar:
  `validate.denetle` (44), `kur-hostlar.rollback_transaction` (30) ve
  `v1._validate_real_agent_evidence` (28).
- Repo içinde Python cache'leri ve kapanmış PR #17'ye ait 14 MB worktree vardır.
- `~/.codex/divan-backups` içindeki `ui-ux-pro-max` kopyası aktif kaldırma
  manifestinde geri yükleme hedefidir. Yedeğin tamamını silmek veri kaybıdır;
  yalnız yeniden üretilebilir `__pycache__` içeriği temizlenebilir.

## Karar

Üç katmanlı, fail-closed bir hijyen sözleşmesi uygulanır:

1. `.gitattributes` ve `.editorconfig` birinci taraf metni UTF-8/LF olarak
   sabitler; subprocess ve dosya okuma yolları açıkça UTF-8 kullanır.
2. `scripts/hijyen.py --check` izlenen birinci taraf metinlerde UTF-8/BOM/
   mojibake ve repo içindeki izinli cache artefaktlarını denetler.
   `--clean` yalnız sabit allowlist'teki yeniden üretilebilir artefaktları siler;
   kanıt, kullanıcı yedeği, manifest veya bilinmeyen dosyaya dokunmaz.
3. Ruff C90 kapısı karmaşıklığı 25 ile sınırlar. Yalnız yeni kapıyı aşan üç
   fonksiyon davranış değişmeden küçük, isimli doğrulayıcılara ayrılır.

## Silme sınırı

Kalıcı silme yalnız şu kanıtlı hedefleri kapsar:

- repo/worktree içindeki `__pycache__`, `.ruff_cache`, `.mypy_cache`,
  `.pytest_cache`, `.coverage` ve `htmlcov`;
- temiz ve birleşmiş PR'lara ait `.worktrees/*` kayıtları;
- kapanmış PR'ların yerel ve uzak `codex/` dalları;
- aktif yedeğin içindeki yalnız `__pycache__` dizinleri.

Release kanıtları, `.divan/evidence`, eval sonuçları, kullanıcı belgeleri,
Codex/Claude yapılandırma yedekleri ve manifestçe geri yükleme için kullanılan
skill yedeği korunur.

## Teslim

Değişiklik v0.12.1 bakım sürümü olarak bütün yayın yüzeylerine taşınır. Tam yerel
teftiş, bağımsız kod incelemesi, PR CI, `main` birleştirmesi, tag/Release,
Pages/Wiki readback ve Claude+Codex global yeniden kurulum kanıtlanmadan bitti
sayılmaz. Bu çalışma davranış kalite artışı veya v1 bağımsız kabul kanıtı değildir.
