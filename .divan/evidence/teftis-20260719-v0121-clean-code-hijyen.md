# v0.12.1 Clean Code ve Repo Hijyeni — Yerel Teftiş

Tarih: 2026-07-19 (Europe/Istanbul)

## Başlangıç kanıtı

- `python -m unittest discover -s tests -v`: 87 test geçti, 1 POSIX testi
  Windows'ta beklenen biçimde atlandı.
- `ruff check .`: temiz.
- `mypy scripts`: 11 kaynak dosyada hata yok.
- McCabe 15 keşfi yedi fonksiyon buldu; 25 üzerinde yalnız
  `validate.denetle` (44), `rollback_transaction` (30) ve
  `_validate_real_agent_evidence` (28) vardı.
- Birinci taraf izlenen metinde geçersiz UTF-8 veya doğrulanmış mojibake yoktu.
  Host CLI ve eval Git çıktısında iki locale-bağımlı `text=True` çağrısı vardı.

## TDD kanıtı

- `tests/test_hijyen.py`, eksik `scripts/hijyen.py` nedeniyle önce kırmızı oldu.
- CI hijyen komutu ile C90/25 beklentileri önce iki assertion failure verdi.
- UTF-8 subprocess testleri `encoding` anahtarı olmadığı için önce `KeyError`
  verdi.
- Tarihsel sürüm testi, `History v1.2.3` satırının yanlış biçimde `v1.2.4`
  yapılmasını yakaladı; `version_patterns` sonrasında tarihsel satır korundu.
- Bağımsız ilk inceleme gerçek LF kontrolü, subprocess alias/kodlama kapsamı,
  ana teftişe hijyen entegrasyonu ve çok dosyalı yayın atomikliği açıklarını
  buldu. Her bulgu önce kırmızı regresyon testiyle üretildi, sonra kapatıldı.
- Küçük inceleme bulguları için `.worktrees`/cache ağaçları dosya sistemi
  fallback'inde de budandı ve depo dışına çıkan metin symlink'i reddedildi.
- İkinci inceleme, `encoding=`/`errors=` ile örtük açılan subprocess metin modu
  ile bozuk UTF-8/sözdizimli Python kaynağında tarayıcı çökmesini üretti. İki
  durum da kırmızı testten sonra deterministik issue raporuna dönüştürüldü.
- İkinci incelemenin son kararında kritik/önemli bulgu kalmadı. Tek küçük bulgu
  da kapatıldı: rollback geri alması dahi başarısızsa özgün dosyayı taşıyan
  geçici kurtarma yedeği silinmez ve tam yolu `RuntimeError` içinde verilir.

## Kalıcı temizlik

- Ana repo: `evals/__pycache__`, `evals/adapters/__pycache__`,
  `scripts/__pycache__`, `tests/__pycache__` silindi.
- Aktif Codex rollback yedeği: yalnız
  `ui-ux-pro-max/scripts/__pycache__` silindi. Manifestin işaret ettiği 36
  birinci taraf olmayan kullanıcı dosyası/skill içeriği korundu.
- Birleşmiş PR #17/#16'nın yerel dalları ve GitHub uzak dalları silindi.
- Açık PR olmadığı ve kalan 15 uzak `codex/*` dalının birleşmiş PR'lara ait
  olduğu GitHub'dan doğrulandı; bu dallar da kalıcı silindi. `main`, aktif dal
  ve sahipliği belirsiz `claude/*` dalı korundu.
- PR #17 worktree Git kaydı ve 14 MB içeriği kaldırıldı. Windows'ta bir süreç
  boş üst dizin handle'ını tuttuğu için boş klasörün son kaldırması teftiş
  sonunda yeniden denenecektir; ürün veya Git kaydı içermez.

## Taze yerel kapılar

- `python scripts/hijyen.py --check`: temiz.
- `python scripts/validate.py`: 5 paket / 41 skill; yalnız iki uzun upstream
  skill gövdesi tavsiye uyarısı.
- `python scripts/devral.py --check`: temiz.
- `python scripts/katalog.py --check`: 41 skill / 5 paket.
- `python scripts/v1.py --check`: geçerli, hedef 1.0.0; bağımsız kabul bekliyor.
- `python scripts/yayin.py --check`: v0.12.1, 27 kamusal yüzey.
- `python evals/run.py --check`: 4 skill / 13 vaka sözleşmesi.
- `python -m unittest discover -s tests -v`: 99 test geçti; 1 POSIX ve 1
  ayrıcalık isteyen symlink testi Windows'ta beklenen biçimde atlandı.
- `ruff check .`: temiz; C90 McCabe 25 dahildir.
- `mypy scripts`: 12 kaynak dosyada hata yok.
- `coverage run ... && coverage report`: toplam %63 branch coverage,
  `fail_under=55` kapısı geçti.
- `python scripts/wiki.py --check`: v0.12.1 / 17 sayfa.
- `python scripts/meclis.py --check`: 1 aday; geçerli.
- `python scripts/upstream-denetim.py`: izlenen upstream tabanları temiz.
- `agentskills validate`: resmî `skills-ref==0.1.1` ile 41/41 geçti.
- Claude Code `plugin validate --strict`: kök + 5 paket, 6/6 geçti.
- `git diff --check`: hata yok.

Bu kanıt mekanik kalite ve teslim kapılarını gösterir; davranış win-rate'i veya
v1 bağımsız kullanıcı kabulü iddiası değildir.

## Kamusal teslim ve global kurulum

- PR #19 bütün zorunlu kontrollerden geçti ve
  `4125c31ea51170414c1349c1992182b0968e6b9d` ile `main`e birleşti.
- Release workflow `29704548820` başarıyla tamamlandı. `v0.12.1` değişmez etiketi
  aynı commit'e bağlı; GitHub Release taslak/ön-sürüm değildir ve ZIP ile
  SHA-256 varlıklarını yayımlar.
- Canlı Pages ve Wiki doğrudan geri okumada `v0.12.1` döndürdü; release
  workflow'un Chromium etkileşim adımı da geçti.
- Global kurulum dry-run ile başladı. Mevcut v0.12.0 kurulumu ilk doğrulanmış
  işlem günlüğüyle sahiplik kontrollü kaldırıldı; yeni kurulum
  `install-20260719T213732Z-5a357853.json` işleminde `verified` oldu.
- Claude ve Codex'in her birinde 5 paket/41 skill etkin; source
  `https://github.com/trugurpala/divan.git`, ref `v0.12.1` olarak geri okundu.
  GitKraken, Prompts.chat, OpenAI bundled/runtime ve kişisel
  `vibe-coder-standard` eklentileri eksiksiz korundu.
- İlk yükseltme denemesi mevcut kaydı kanıtsız sahiplenmeyi reddederek hiçbir
  değişiklik yapmadan `rolled-back` oldu; ardından doğrulanmış önceki işlem
  üzerinden desteklenen kaldır-yeniden-kur yolu kullanıldı.
