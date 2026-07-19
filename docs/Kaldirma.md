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
ve o işlemde oluşturulan kayıtları gösterir. Geri alırken yalnız `created`
alanındaki Divan girdilerini hedefle; başka marketplace veya eklentileri silme.
Kurucunun sahiplik denetimli yolu bunu otomatik uygular:

```bash
python scripts/kur-hostlar.py --rollback-transaction <install-....json>
```

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
