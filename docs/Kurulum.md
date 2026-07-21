# Kurulum

Divan yerel bir skill/plugin dağıtımıdır; model veya runtime değildir. İlk kez
kullanıyorsanız güncel sabit sürüm için bu sırayı izleyin:

```powershell
python scripts/kur-hostlar.py --host both --ref v0.13.0
python scripts/kur-hostlar.py --host both --ref v0.13.0 --execute
python scripts/kur-hostlar.py --doctor --host both --ref v0.13.0
python scripts/kur-hostlar.py --upgrade --host both --ref v0.13.0
python scripts/kur-hostlar.py --upgrade --host both --ref v0.13.0 --execute
python scripts/kur-hostlar.py --rollback-transaction "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
python scripts/kur-hostlar.py --rollback-transaction "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

Örnek yolu doctor çıktısındaki tam `recovery_command` ile değiştir.
`install-...json` geri alması yalnız o kurulumun oluşturduğu Divan kayıtlarını
kaldırır. Host'a göre elle kaldırma için [[Kaldırma|Kaldirma]], soru/hata/güvenlik için
[SUPPORT.md](../SUPPORT.md), ürün sözleşmesi için
[[Topluluk Standartları|Topluluk-Standartlari]] sayfasını kullanın.

## Claude Code/Desktop Code + Codex (önerilen yerel yol)

Kurucu varsayılan olarak yalnız planı gösterir; host durumunu değiştirmez:

```powershell
python scripts/kur-hostlar.py --host both --ref <release-tag>
```

Çıktıyı inceledikten sonra aynı sabit referansı uygula:

```powershell
python scripts/kur-hostlar.py --host both --ref <release-tag> --execute
```

Kurulumdan önce veya sonra iki hostun durumunu hiçbir şeyi değiştirmeden kontrol
edin:

```powershell
python scripts/kur-hostlar.py --doctor --host both --ref <release-tag>
```

Doctor, CLI erişilebilirliğini, Divan pazarı kaynak/ref bilgisini, beş paketin
sürümünü ve etkinliğini, pazarsız kalmış paketleri ve tamamlanmamış işlemleri
raporlar. Otomasyon için yalnız JSON çıktı alın:

```powershell
python scripts/kur-hostlar.py --doctor --json --host both --ref <release-tag>
```

Her doctor sonucu bir sonraki kesin komutu yazar; tamamlanmamış işlemde bu,
ilgili `--rollback-transaction` komutudur. Doctor host CLI'larını veya işlem
günlüklerini değiştirmez.
Okunamayan veya bozuk bir işlem günlüğü de `attention` sonucudur; tanı kaydı
bildirilir, fakat doctor hiçbir recovery ya da host değiştirme komutu çalıştırmaz.

## Güvenli sürüm yükseltme

Yükseltme de varsayılan olarak yalnız remove/add/install planını gösterir:

```powershell
python scripts/kur-hostlar.py --upgrade --host both --ref <yeni-release-tag>
```

Planı aynı sabit hedefe uygulamak için `--execute` ekleyin:

```powershell
python scripts/kur-hostlar.py --upgrade --host both --ref <yeni-release-tag> --execute
```

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
python scripts/kur-hostlar.py --rollback-transaction "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
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
`python scripts/hijyen.py --check` çalıştırın. Cache temizliği gerektiğinde
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
Eski, parmak izsiz schema-1 günlükleri otomatik silme yapmadan
fail-closed durur; recovery sırasında dışarıdan değiştirilmiş satırlar korunur.
Schema-1 recovery, host CLI'dan önce işlem yolu, host kümesi, durum, pending
niyeti, tüm parmak izi çapraz bağları ve varsa aynı state dizinindeki legacy
günlük kimliğini doğrular.

Her dış CLI değişikliğinden önce işlem günlüğü atomik yazılır. Kesinti sonrası
`in-progress`, `recovering` veya `rollback-incomplete` kaydını yalnız o işlemin
oluşturduğu girdilerle geri almak için:

```bash
python scripts/kur-hostlar.py --rollback-transaction "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
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
python scripts/kur-hostlar.py --host both --ref <release-tag> --execute --migrate-legacy
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

v0.13.0 eski-host fallback kaydı; betik release arşivini indirmeden önce eşlik
eden SHA-256 kaydını alır ve uyuşmayan arşivi açmadan durur:

```bash
curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/v0.13.0/scripts/kur-codex.sh | DIVAN_REF=v0.13.0 bash
```

## Cursor / diğer Agent Skills uyumlu ajanlar
Skill'ler açık standarttır; repo'daki `plugins/*/skills/*` klasörlerini
ajanının skill dizinine kopyalaman yeterlidir (ör. Cursor'da proje köküne
`.cursor/skills/` ya da ajanın belgelerinde belirtilen dizin).

## Doğrulama
Kurulumdan sonra ajana "hangi skill'lerin var?" diye sor; `sadrazam` ve
`vezir-yetistirme` listede görünmelidir.

## Uyumluluk matrisi (dürüst)

| Katman | Claude Code | Codex / Cursor / diğer |
|---|---|---|
| Skills (41 vezir) | ✓ yerel plugin ile | ✓ Codex yerel plugin; diğer hostlarda Agent Skills klasörü |
| Memory (defterdar dosyaları: AGENTS.md, BLUEPRINT, .divan/) | ✓ | ✓ düz dosya + AGENTS.md'yi Codex/Cursor doğal okur |
| Komutlar (/ferman /sefer /defter /teftis) | ✓ | ✗ Claude Code'a özgü (skill tetikleyicileri yine çalışır) |
| Subagents (kâşif, müfettiş) | ✓ | ✗ Claude Code'a özgü |
| Hooks (oturum başında defteri otomatik oku) | ✓ | ✗ Claude Code'a özgü |
| Marketplace tek komut kurulum | ✓ | ✓ |

Özet: skill'ler ve hafıza dosyaları her yerde taşınır; komut/subagent/hook
katmanları Claude Code'da tam güçtedir.

`uyumluluk` CI matrisi Claude Code ve Codex pazar/paket şemalarını; fallback
yolunu ise Linux, macOS ve Windows'ta geçici, boş skill dizinlerinde 41 skill
keşfi ve kayıtlı kaldırma tatbikatıyla sınar.
