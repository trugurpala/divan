# Kurulum

Divan yerel bir skill/plugin dağıtımıdır; model veya ayrı bir üçüncü taraf
runtime değildir. Divan Engine aynı repodaki modüler, stdlib-only icra
çekirdeğidir; Divan Nizamı Hükümdar öncelikli yetki düzenidir. İlk kez
kullanıyorsanız bu sırayı izleyin. Aşağıdaki örnekler Güncel kaynak sürümünü
sabitler. Güncel kaynak Son yayımlanan sürümden farklıysa bütün `--ref`
komutlarında Son yayımlanan sürümü kullan. Yalnız değişmez tag ve GitHub
Release'i bulunan bir ref'i kur. v1.0.2 artık son yayımlanan release'tir:

## Repo klonlamadan en hızlı ilk kurulum

Eşleşen GitHub Release yayımlandıktan sonra tek dosyalık kurucuyu ve checksum
dosyasını indirip doğrula:

```powershell
$tag = "v1.0.2"
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz" -OutFile divan.pyz
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz.sha256" -OutFile divan.pyz.sha256
$expected = ((Get-Content .\divan.pyz.sha256 -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
$actual = (Get-FileHash .\divan.pyz -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "Divan bootstrap SHA-256 eşleşmiyor" }
python .\divan.pyz doctor --host codex --json
python .\divan.pyz install --host codex --profile auto
python .\divan.pyz install --host codex --profile auto --execute
```

İlk `install` yalnız planı gösterir; `--execute` aynı sabit release'i uygular.
Kurucu, içine gömülü beş paket/41 beceri kataloğu ile kaynak commit'ini
doğrular ve başka kaynak veya ref'i reddeder. `divan.pyz` dosyasını recovery
komutları için sakla.

Repo checkout'u kullanan iki-host yaşam döngüsü:

```powershell
python scripts/divan.py install --host both --ref v1.0.2
python scripts/divan.py install --host both --ref v1.0.2 --execute
python scripts/divan.py doctor --host both --ref v1.0.2
python scripts/divan.py update --host both --ref v1.0.2
python scripts/divan.py update --host both --ref v1.0.2 --execute
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
python scripts/divan.py recover "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

## Kurulumdan sonra yerel Seyir

İzlemek istediğiniz proje klasöründe:

```powershell
python scripts/divan.py status --project . --open --lang auto
```

Divan işletim sisteminden boş bir port ister, çalışan adresi terminale yazar ve
`--open` ile aynı adresi açar. Sunucu yalnız `127.0.0.1` üzerinde, salt okunur
ve geçici çalışır; `Ctrl+C` ile kapanır. Bulut servisi, veritabanı veya API
anahtarı kullanılmaz.

## Codex Desktop için tek komutluk güvenli seçim

Codex Desktop'ta önce hiçbir şey yazmadan kararı gör:

```powershell
python scripts/divan.py install --host codex --profile auto --ref v1.0.2
```

Aynı sabit release'i uygulamak için yalnız `--execute` ekle:

```powershell
python scripts/divan.py install --host codex --profile auto --ref v1.0.2 --execute
```

`auto` profili kendiliğinden etkinleşmez; kullanıcının açık seçimidir. Divan
Codex CLI sonucunu şu şekilde ayırır:

| CLI tanısı | Seçilen yol |
|---|---|
| `healthy` | Beş paket ve 41 beceriyi içeren tam yerel plugin kurulumu |
| `missing` | Checksum ve kaynak commit'i doğrulanan 41-skill fallback |
| `not-executable` | Checksum ve kaynak commit'i doğrulanan 41-skill fallback |
| `access-denied` | Checksum ve kaynak commit'i doğrulanan 41-skill fallback |
| `invalid-json` | Kurulum durur; host protokol sorunu fallback ile gizlenmez |

Skill fallback, bütün 41 beceriyi ve talimatları kurar; sürüm, değişmez ref,
kaynak commit'i, release arşiv SHA-256 değeri ve beceri başına kurulu dosya
SHA-256 kaydı üretir. Ancak yerel plugin komutları, ajanlar, hook'lar, MCP
yapılandırması ve host yaşam döngüsü bu modda yoktur. Başarılı çıktı tam
manifest yolunu, sınırı, geri alma komutunu ve sıradaki adımı açıkça yazar.

Örnek yolu doctor çıktısındaki tam `recovery_command` ile değiştir.
`install-...json` geri alması yalnız o kurulumun oluşturduğu Divan kayıtlarını
kaldırır. Host'a göre elle kaldırma için [[Kaldırma|Kaldirma]], soru/hata/güvenlik için
[SUPPORT.md](../SUPPORT.md), ürün sözleşmesi için
[[Topluluk Standartları|Topluluk-Standartlari]] sayfasını kullanın.

## Divan Engine sözleşmesini gör

Repo checkout'unda dokuz modülü, bağımlılık grafiğini ve Hükümdardan başlayan
yetki zincirini hiçbir hedef projeyi değiştirmeden doğrulayabilirsiniz:

```powershell
python scripts/divan.py architecture --json
python scripts/divan.py validate
```

Kanonik mimari [Divan Engine](Divan-Engine.tr.md), hedef repoya kurulan katman
ise [Divan Proje Sözleşmesi](Project-Contract.tr.md) belgesindedir. Eski
`Company OS`, `Project OS` ve `company-validate` adları v1 boyunca yalnız
uyumluluk yüzeyi olarak korunur.

## Host güncellemesi ile proje güncellemesi

Yukarıdaki `update --host` komutu Claude/Codex içindeki global Divan paketlerini
değiştirir. Divan'ı bir hedef repoya `init --execute` ile kurduktan sonra
`.divan/config.json` schema ve sahip olunan Divan Proje Sözleşmesi yüzeyleri
ayrı proje yaşam döngüsüne girer:

```powershell
python scripts/divan.py project status --project . --json
python scripts/divan.py project update --project .
python scripts/divan.py project update --project . --execute
python scripts/divan.py project repair --project .
python scripts/divan.py project repair --project . --execute
```

Project update uzaktan indirme yapmaz; çalışan sabit checkout veya doğrulanmış
`divan-project.pyz` içindeki payload'a yükseltir. Kullanıcı değişikliği, bozuk
marker, symlink/reparse veya sahipsiz hedef yazmadan `BLOCKED` olur. Repair force
seçeneği sunmaz ve yalnız kayıtlı eksik tam Divan dosyasını geri getirir.
`audit` DPS kalite kanıtını, `project status` sahiplik ve drift'i değerlendirir.

## Claude Code/Desktop Code + Codex (önerilen yerel yol)

Kurucu varsayılan olarak yalnız planı gösterir; host durumunu değiştirmez:

```powershell
python scripts/divan.py install --host both --ref <release-tag>
```

Çıktıyı inceledikten sonra aynı sabit referansı uygula:

```powershell
python scripts/divan.py install --host both --ref <release-tag> --execute
```

Kurulumdan önce veya sonra iki hostun durumunu hiçbir şeyi değiştirmeden kontrol
edin:

```powershell
python scripts/divan.py doctor --host both --ref <release-tag>
```

Doctor, CLI erişilebilirliğini, Divan pazarı kaynak/ref bilgisini, beş paketin
sürümünü ve etkinliğini, pazarsız kalmış paketleri ve tamamlanmamış işlemleri
raporlar. Otomasyon için yalnız JSON çıktı alın:

```powershell
python scripts/divan.py doctor --json --host both --ref <release-tag>
```

Her doctor sonucu bir sonraki kesin komutu yazar; tamamlanmamış işlemde bu,
ilgili `--rollback-transaction` komutudur. Doctor host CLI'larını veya işlem
günlüklerini değiştirmez.
Okunamayan veya bozuk bir işlem günlüğü de `attention` sonucudur; tanı kaydı
bildirilir, fakat doctor hiçbir recovery ya da host değiştirme komutu çalıştırmaz.

## Güvenli sürüm yükseltme

Yükseltme de varsayılan olarak yalnız remove/add/install planını gösterir:

```powershell
python scripts/divan.py update --host both --ref <yeni-release-tag>
```

Planı aynı sabit hedefe uygulamak için `--execute` ekleyin:

```powershell
python scripts/divan.py update --host both --ref <yeni-release-tag> --execute
```

GitHub Release'ten indirilen tek dosyalık `divan.pyz`, hedef commit/ref/katalog
kanıtını içindeki değişmez release sözleşmesinden okur; çıkarıldığı geçici
klasörü Git checkout saymaz.

Kaynak, ref ve beş `@divan` paketinin sürümleri hedef sözleşmeyle zaten
aynıysa işlem `no-op` döner. Yükseltme başlamadan önce iki hosttaki mevcut
Divan pazarının istenen depoya ait olduğunu, checkout ref'ini, paket kümesini,
sürümleri, etkinliği ve kurulum yollarını kanıtlar. Bilinmeyen/yabancı kaynak,
eksik veya fazla Divan paketi ya da sürüm uyuşmazlığı journal veya dış mutasyon
oluşmadan reddedilir.

Execute modunda schema-2 günlüğü her remove/add/install çağrısından önce
`pending` niyetini diske yazar; recovery niyetini ayrı `recovery_pending`
alanında tutar. Önceki marketplace ve paket satırlarını commit, katalog özeti,
tam kurulum yolu ve native provenance kanıtlarıyla `before_rows` altında saklar.
Her paket ve marketplace kaldırmasından hemen önce native durum yeniden okunur;
önceki okumadan sonra değişen bir satır varsa kaldırma çağrısı yapılmadan durulur.
İki host doğrulanmadan işlem tamamlanmış sayılmaz. Aktif bir yükseltme günlüğü
veya işlem kilidi varken yeni execute/no-op çağrısı başlamaz.
Kilit dosyası süreçler arası kernel kilidi taşır: süreç kaybında dosya kalsa da
kilit otomatik serbest kalır; çalışan başka bir süreç ise işlemi kapalı tutar.
Native `--execute` kurulum ve yükseltme aynı kilidi ve aktif-günlük kapısını
kullanır; kuru çalıştırmalar kilit veya host CLI çağrısı oluşturmaz.
`install-*.json` ve `upgrade-*.json` taramasında okunamayan ya da yapısal olarak
geçersiz günlükler fail-closed reddedilir; yalnız doğrulanmış terminal kayıtlar
yeni işleme izin verir.
Hata veya kesintide yalnız bu işlemin oluşturduğu hedef satırlar kaldırılır;
kanıtlanmış önceki source/ref/package sürümleri hostların ters sırasında yeniden
kurulur. Alakasız marketplace ve eklentiler korunur.

Otomatik geri alma da kesilirse günlük `rollback-incomplete` kalır ve içindeki
tam `recovery_command` çalıştırılır:

```powershell
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
```

Aynı recovery komutu idempotenttir; dış komut başarıdan hemen sonra kesilmiş
olsa bile mevcut durumu yeniden okuyup eksik adımdan güvenle devam eder.
Eski marketplace geri eklendiğinde source/ref/root/commit/katalog özeti tam
parmak izi, herhangi bir eski paket kurulmadan önce yeniden doğrulanır.

Uzak Claude pazarı değişmez bir release etiketi ister. Bir commit SHA'sını CI
veya geliştirme doğrulamasında kullanacaksanız, aynı temiz checkout'u yerel
kaynak olarak verin: `--source <repo-yolu> --ref <40-karakter-SHA>`.
Yerel kaynak yalnız çözümlenmiş marketplace kökü aynı checkout olduğunda,
çalışma ağacı temizken ve HEAD istenen SHA ile birebir eşleşirken kanıtlanır.
Değiştirilebilir bir checkout yerinde transactional sürüm değiştirmek için
kullanılmaz; böyle bir durum journal oluşmadan reddedilir.

Repo üzerinden geliştirme yapıyorsanız önce
`python scripts/hygiene.py --check` çalıştırın. Cache temizliği gerektiğinde
`--clean` yalnız yeniden üretilebilir allowlist'i siler; kurulum manifestleri,
kanıtlar ve geri alma yedekleri korunur.

Kurucu, aynı isimde mevcut bir `divan` pazarı veya pazarsız kalmış `@divan`
eklentisi görürse onun kaynak ve ref bilgisini güvenilir biçimde kanıtlayamadığı
için durur; mevcut pazarı veya eklentileri değiştirmez. Önce host'un kendi
listeleme komutlarıyla kayıtları inceleyin ve yalnız size ait olduklarından
eminseniz elle kaldırıp işlemi yeniden çalıştırın.

Başarılı native kurulum günlüğü oluşturulan her satırın kesin parmak izini taşır.
Claude paket yolu kendi sürümlü `~/.claude/plugins/cache/divan/<paket>/<sürüm>`
önbelleğinden, Codex yolu marketplace kökündeki `plugins/<paket>` konumundan
kanıtlanır. Claude yolu kanıtlanmış kullanıcı-scope marketplace yapılandırmasının
tam cache köküyle birebir eşleşmeli ve plugin satırı `scope: user` taşımalıdır.
Codex marketplace satırı ref bildirmiyorsa önceki değişmez ref ve commit istenen
hedeften değil, kurulu marketplace Git checkout'undan salt-okunur türetilir.
Codex'in kökte oluşturduğu `.codex-marketplace-install.json` bu checkout'ta izin
verilen tek kirli girdidir: normal dosya olmalı; kesin native alanları source,
ref ve Git HEAD revision kanıtlarıyla birebir uyuşmalıdır. Başka untracked/staged
değişiklik, symlink/reparse point veya metadata tahrifi işlemi durdurur.
Eski, parmak izsiz schema-1 günlükleri otomatik silme yapmadan
fail-closed durur; recovery sırasında dışarıdan değiştirilmiş satırlar korunur.
Schema-1 recovery, host CLI'dan önce işlem yolu, host kümesi, durum, pending
niyeti, tüm parmak izi çapraz bağları ve varsa aynı state dizinindeki legacy
günlük kimliğini doğrular.

Her dış CLI değişikliğinden önce işlem günlüğü atomik yazılır. Kesinti sonrası
`in-progress`, `recovering` veya `rollback-incomplete` kaydını yalnız o işlemin
oluşturduğu girdilerle geri almak için:

```bash
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
```

Eski gevşek-skill göçü de tüm hedeflerin kurulum özetini önce doğrular; değişmiş
dosyaya dokunmaz, hedefleri silmek yerine `.codex/divan-quarantine/` altında
saklar ve ara hata olursa bütün taşıma işlemlerini tersine çevirir.
Göç ve fallback kopyalama adımları da ayrı, atomik bir legacy günlüğü tutar;
ana işlem günlüğü kesinti sonrası önce bu alt işlemi, sonra host kayıtlarını
idempotent biçimde geri kazanır.

`--host claude` veya `--host codex` tek host seçer. Kurucu iki ürünün resmî
plugin CLI'larını kullanır, mevcut durumun tam listesini işlem kaydına yazar,
yalnız kendi eklediği `divan` kayıtlarını geri alır ve alakasız eklentilere
dokunmaz. Kayıtlar `~/.divan/transactions/` altındadır. Claude Desktop'ın Code
yüzeyi kullanıcı kapsamındaki Claude Code eklentilerini ortak kullanır.

Önceden `kur-codex` ile kopyalanmış Divan skill'leri varsa onları ancak beş
paketin yerel kurulumu doğrulandıktan sonra taşı:

```powershell
python scripts/divan.py install --host both --ref <release-tag> --execute --migrate-legacy
```

## Elle yerel eklenti kurulumu

Claude Code:

```text
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan
/plugin install core-pack@divan
/plugin install ui-pack@divan
/plugin install react-pack@divan
/plugin install zanaat-pack@divan
```

Codex:

```powershell
codex plugin marketplace add trugurpala/divan --ref <tag-veya-commit>
codex plugin add sadrazam@divan
codex plugin add core-pack@divan
codex plugin add ui-pack@divan
codex plugin add react-pack@divan
codex plugin add zanaat-pack@divan
```

Doğrudan skill kopyalayan `kur-codex.ps1`/`.sh` yolu yalnız eski hostlar için
uyumluluk fallback'idir; yerel plugin pazarı destekleniyorsa bu yolu kullanma.

v1.0.2 eski-host fallback kaydı; betik release arşivini indirmeden önce eşlik
eden SHA-256 kaydını alır ve uyuşmayan arşivi açmadan durur:

```bash
curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/v1.0.2/scripts/install_codex.sh | DIVAN_REF=v1.0.2 bash
```

## Cursor / diğer Agent Skills uyumlu ajanlar
Skill'ler açık standarttır; repo'daki `plugins/*/skills/*` klasörlerini
ajanının skill dizinine kopyalaman yeterlidir (ör. Cursor'da proje köküne
`.cursor/skills/` ya da ajanın belgelerinde belirtilen dizin).

## Doğrulama
Kurulumdan sonra ajana "hangi skill'lerin var?" diye sor; `sadrazam` ve
`vezir-yetistirme` listede görünmelidir.

## Uyumluluk matrisi (dürüst)

Divan bütün hostları aynı kabul etmez. `skill-compatible`, `native` ve
`verified` farklı kanıt seviyeleridir; bir hostta skill okunması hook, agent,
MCP ve güncelleme yaşam döngüsünün de çalıştığı anlamına gelmez.
Kanonik dağıtım bugün 5 paket içinde 41 beceri taşır.

Güncel 11-host matrisi, resmî belge bağlantıları ve desteklenen yetenekler:
[[Host Uyumluluğu|Host-Uyumlulugu]]. Makinece doğrulanan tek kaynak
`registry/host-compatibility.json` dosyasıdır.

Bugün Claude Code ve Codex temiz-host kurulum yaşam döngüsüyle
`verified` seviyesindedir. Diğer hostlar, gerçek canary kanıtı oluşana kadar
daha düşük ve dürüst seviyede kalır.

## v1 temiz-proje kanıtı

Kurulumdan sonra gerçek bir projede doğrulanmış hedef oluştuğunda, v1'in son
teknik kapısını önce yazmayan planla incele:

```powershell
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
```

İlk komut dosya yazmaz ve subprocess başlatmaz. İkinci komut sabit host sürüm
probunu ve sınırlı test/regresyon kontrollerini bir kez çalıştırır. Bakımcı ile
dış kullanıcı aynı teknik sözleşmeye tabidir. Yalnız
`valid-clean-room-adoption` sonucu v1'e adaydır. v0.18.5 ile üretilen gerçek
schema-2 makbuzu kaydedilip yeniden doğrulandığı için v1 hazırlık durumu
**8/8**'dir.
`divan-project.pyz.sha256` dosyasını runner ile aynı klasörde tutun. Yürütme,
Git tarafından izlenen kaynak sapmasını reddedebilmek için bir Git reposu
gerektirir.
