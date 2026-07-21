# Divan'ı Komple Kaldırma

Misafirlik bitti mi? Divan iz bırakmadan gider. Sıra önemli:

## 1. Claude Code/Desktop Code'dan paketleri kaldır
```
/plugin uninstall sadrazam@divan
/plugin uninstall core-pack@divan
/plugin uninstall ui-pack@divan
/plugin uninstall react-pack@divan
/plugin uninstall zanaat-pack@divan
```

## 2. Marketplace kaydını sil
```
/plugin marketplace remove divan
```
Bu ikisi komutları, skill'leri, subagent'ları (kâşif, müfettiş) ve
SessionStart hook'unu tamamen devre dışı bırakır.

## 3. Codex'ten yerel paketleri kaldır

```powershell
codex plugin remove sadrazam@divan
codex plugin remove core-pack@divan
codex plugin remove ui-pack@divan
codex plugin remove react-pack@divan
codex plugin remove zanaat-pack@divan
codex plugin marketplace remove divan
```

`~/.divan/transactions/install-*.json` dosyası kurulum öncesi host listelerini
ve o işlemde oluşturulan kayıtların kesin native parmak izlerini gösterir. Geri
alırken yalnız `created` alanında parmak izi hâlâ birebir eşleşen Divan girdilerini
hedefle; değiştirilmiş satırı, başka marketplace veya eklentileri silme. Eski,
parmak izsiz schema-1 günlükleri güvenli biçimde otomatik geri alınamaz.
Kurucunun sahiplik denetimli yolu bunu otomatik uygular:

```bash
python scripts/kur-hostlar.py --rollback-transaction "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

`upgrade-*.json` schema-2 kayıtları farklıdır: `before_rows` kanıtlanmış eski
marketplace source/ref ve paket sürümlerini; `target`, `removed`, `created`,
`verified`, forward `pending` ve ayrı `recovery_pending` alanları ise yükseltme
yaşam döngüsünü taşır. `created` girdileri selector ile yetinmez; tam sürüm,
marketplace kökü, kurulum yolu ve native provenance parmak izini taşır. Başarısız
yükseltme yalnız işlem tarafından oluşturulmuş hedef Divan satırlarını kaldırır
ve eski iki-host durumunu ters host sırasında yeniden kurar; alakasız satırları
silmez. `rollback-incomplete` kaydında yazılı kesin komutu kullanın:

```bash
python scripts/kur-hostlar.py --rollback-transaction "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
```

Recovery tekrar kesilirse aynı komut güvenle yeniden çalıştırılabilir. Journal
kanıtlamadığı bir `@divan` satırını elle silmeyin; önce doctor ve journal
alanlarıyla sahipliği inceleyin.
Recovery başlamadan önce journal geçiş sırası da doğrulanır: paket kayıtları
sabit prefix sırasında olmalı, marketplace oluşturma önceki marketplace
kaldırma kanıtına dayanmalı ve her recovery intent'i aynı hostun kesin
`created`/`removed` kaydına bağlanmalıdır. Geçersiz kayıt hiçbir host CLI'ına
ulaşmaz.

Aynı işlemde `--migrate-legacy` tamamlandıysa rollback önce karantinadaki
doğrulanmış loose skill'leri ve çakışma yedeklerini işlem öncesi konumlarına
geri getirir; ardından native paketleri ve pazarı kaldırır.

## 4. (İsteğe bağlı) Proje hafızası dosyaları
Defterdar'ın SENİN projende ürettiği dosyalar sana aittir. `.divan/`,
`AGENTS.md` ve `BLUEPRINT.md` başka araçlar veya ekip üyeleri tarafından da
kullanılıyor olabilir; otomatik bir silme komutu çalıştırma. Önce yedek al,
`git status` ile sahipliği ve değişiklikleri denetle, sonra yalnızca Divan'a ait
olduğundan emin olduğun dosyaları tek tek kaldır.

## 5. Cursor/Codex'e elle kopyaladıysan
Kopyaladığın skill klasörlerini ilgili skill dizininden tek tek kaldır. Codex
kurucusunun oluşturduğu `~/.codex/divan-install-*.tsv` kaydı hedefleri ve varsa
önceki sürüm yedeklerini gösterir; yedekleri geri yüklemeden önce içeriklerini
incele.

Yedek klasörünü cache ile karıştırma: aktif kurulum manifestinin `yedek` alanı
bir kullanıcı skill'ini geri yüklemek için gerekir ve körlemesine silinmez.
`python scripts/hijyen.py --clean` bu yedeklere dokunmaz.

v0.12.0 fallback kurucusu kullanıldıysa kayıtlı kaldırma/geri alma yolu:

```bash
bash scripts/kaldir-codex.sh
```

```powershell
./scripts/kaldir-codex.ps1
```

Betikler bütün manifesti önce doğrular; her hedefin `installed_sha256` özeti
kurulum kaydıyla eşleşmedikçe hiçbir dosyayı taşımaz. Doğrulanan Divan kopyaları
silinmez, `~/.codex/divan-quarantine/` altına taşınır; çakışma sırasında alınan
yedekler yerine konur ve ara hata bütün taşıma işlemlerini geri alır. Eski,
özet alanı bulunmayan manifest fail-closed reddedilir. Şüphede manifest yolunu
açık argüman ver ve önce içeriğini oku.
Yarım kalan fallback/göç işlemleri `divan-transactions/legacy-*.json` günlüğüyle
`python scripts/legacy_state.py recover --journal <günlük.json>` üzerinden
yeniden ve güvenli biçimde toparlanabilir.

## 6. Önbellek kalıntısı (nadiren gerekir)
Repo içindeki Python/Ruff/mypy/coverage önbellekleri için
`python scripts/hijyen.py --clean` kullan. Araç sabit allowlist dışındaki
manifest, kanıt, worktree, kurulum klonu ve kullanıcı yedeğini silmez. Claude
Code marketplace klonlarını `~/.claude/` altında tutar; adım 2 bunları host'un
kendi CLI'ı üzerinden yönetir.

Hepsi bu — otomatik telemetri veya eve arama yoktur. Depoda Markdown skill
metinlerinin yanında açık kaynak betikler ve bazı üçüncü taraf varlıkları da
bulunur; kaldırma kapsamını kurulum kaydından doğrula.
