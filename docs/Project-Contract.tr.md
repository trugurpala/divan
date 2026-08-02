# Divan Proje Sözleşmesi

[English](Project-OS.md)

Divan Proje Sözleşmesi, hedef projeye kurulan gözetimli ve taşınabilir ürün
sözleşmesidir. Yetkili niyeti spec, plan, görev, uygulama kanıtı, preview,
release ve canlı geri okumaya taşır. Kullanıcı veya kodlama ajanı çağırır;
daemon, barındırılan kontrol düzlemi, model ya da bağımsız ajan runtime'ı
değildir.

## İki standart katmanı

- **DCS-*** Divan repo dağıtımını yönetir: köken, bakım, belge, host uyumu ve
  kamusal release yüzeyleri.
- **DPS-*** kurulu proje için çalışır: niyet, mimari, bakım kolaylığı, test,
  güvenlik, UX, sözleşmeler, güvenilirlik, belge, kurtarma, SEO ve release
  kanıtı.

Yalnız uygulanabilir DPS kuralları çalışır. `DPS-011` SEO bir `public-web`
projesine uygulanır; Python kütüphanesine zorlanmaz. İstisna; sahip, gerekçe,
etkilenen standart ve en fazla 180 günlük son tarih ister.

## Projeyi başlat

Durum değiştiren her komut, `--execute` verilene kadar dry-run'dır:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto
python scripts/divan.py init --project . --profile standard --locale auto --execute
python scripts/divan.py audit --project . --json
```

Kurulum yalnız `.divan/` yüzeyine ve `AGENTS.md` / `CLAUDE.md` içindeki işaretli
bloğa sahip olur. Kullanıcı metni korunur; bozuk işaretçi işlemi durdurur. Aynı
kurulumun ikinci çalışması diff üretmez.

## Sahiplik, sapma, güncelleme ve onarım

Kurulum schema 2 `.divan/config.json` ile `.divan/install-state.json` üretir.
Kurulum durumu; değişmez Divan sürüm/ref/commit kimliğini, proje kimlik hash'ini
ve yönetilen her tam dosya veya işaretli blok payload hash'ini bağlar. Kullanıcı
metnini kaydetmez.

```powershell
python scripts/divan.py project status --project . --json
python scripts/divan.py project update --project .
python scripts/divan.py project update --project . --execute
python scripts/divan.py project repair --project .
python scripts/divan.py project repair --project . --execute
```

`project status` saf sahiplik/sapma okumasıdır; lock, journal, cache, yedek veya
ağ isteği oluşturmaz. Yüzey sınıflarından `CURRENT`, `UPDATE_AVAILABLE`,
`DRIFTED` veya `BLOCKED` sonucu üretir. `project update` yalnız çalışan checkout
ya da doğrulanmış runner içindeki değişmez Divan kodunu kullanır; uzaktan ref
indirmez ve hedef proje kodunu çalıştırmaz. Tam dosyada gözlenen hash kayıtlı
hash'e, işaretli blokta ise tek geçerli marker çifti ile blok hash'i kayda
uymalıdır. Bayat plan, kullanıcı değişikliği, symlink/reparse, bilinmeyen schema
veya sahipsiz hedef yazmadan durur.

`project repair` daha dardır: yalnız kayıtlı fakat eksik tam Divan dosyasını
geri getirir veya kanonik transaction'ı kurtarır. Değiştirilmiş dosya, bozuk
marker bloğu veya sahipsiz yol için force-overwrite yapmaz.

Host ve proje komutları farklıdır:

| Komut | Kapsam | Anlam |
|---|---|---|
| `divan.py update --host ...` | Claude/Codex host | Kurulu Divan plugin paketlerini değiştirir |
| `divan.py project update --project ...` | Hedef repo | Sahip olunan proje sözleşmesi yüzeylerini taşır ve yeniler |
| `divan.py audit --project ...` | Uygulanabilir DPS standartları | Proje kalite kanıtını değerlendirir |
| `divan.py project status --project ...` | Sahiplik ve sapma | Kayıtlı, gözlenen ve istenen payload'ı karşılaştırır |

## Hedef rotası ve Nizâm-ı Sefer

`goal start`, `spec.md`, `plan.md` ve `tasks.md` yanında artık `route.json`
üretir. Hash'i makbuza bağlanır. Böylece yeni oturum; host/bağlam varsayımını,
görev bağımlılıklarını, sefer sınırlarını, model sınıfını, kanıtı ve kamusal
yüzey yükümlülüklerini sohbet geçmişine güvenmeden sürdürebilir.

```powershell
python scripts/divan.py goal start --project . --intent "API'yi güvenli yap ve yayınla" --host-profile auto --target released
python scripts/divan.py goal start --project . --intent "API'yi güvenli yap ve yayınla" --host-profile codex --context-window 1050000 --target released --execute
```

İlk komut yazmayan önizlemedir. İkincideki bağlam penceresi Hükümdar beyanıdır;
üretici limiti veya model erişimi kanıtı değildir. `route.json` içermeyen eski
hedefler okunmaya ve doğrulanmaya devam eder.

## Hedef ve kanıt yaşam döngüsü

```text
DISCOVERED → SPECIFIED → PLANNED → IMPLEMENTING
→ VERIFIED → PREVIEWED → RELEASED → OBSERVED
```

`BLOCKED` ve `FAILED` açık sonuçlardır. Makbuz; hash'leri, seçilen akışları,
değişen göreli yolları, kontrolleri, sağlayıcı kanıtını ve zaman damgalarını
tutar. Secret, gizli muhakeme, kişisel mutlak yol veya alakasız eklenti
envanteri yazmaz.

`VERIFIED`, `RELEASED` veya `OBSERVED` hedefler kanıt kaybetmeden aktif kümeden
arşivlenebilir:

```powershell
python scripts/divan.py goal archive --project . --goal <goal-id>
python scripts/divan.py goal archive --project . --goal <goal-id> --execute
```

Divan receipt'i ve bütün artefakt hash'lerini yeniden doğrular,
`.divan/archive/YYYY-MM-DD-<goal-id>/` altına kopyalar, arşivi doğruladıktan
sonra yalnız bağlı kaynakları kaldırır. Bitmemiş, başarısız, değişmiş, güvensiz
veya çakışan hedefler `BLOCKED` kalır.

Eski v0.15 schema-1 makbuzunda imzalı olay tarihi yoktur. Divan yerel saati veya
dosya metadata'sını tahmin olarak kullanmaz; sahip geçmiş terminal olay tarihini
açıkça beyan eder ve bu beyan `archive.json` içine bağlanır:

```powershell
python scripts/divan.py goal archive --project . --goal <goal-id> --recorded-on YYYY-MM-DD
python scripts/divan.py goal archive --project . --goal <goal-id> --recorded-on YYYY-MM-DD --execute
```

Doğrulanmış hedeften sonra ana v1 yolu, işi Divan'dan ayrı bir projede
makinece kanıtlar. Önizleme salt okunurdur ve subprocess başlatmaz. Uygulama;
sabit host sürüm probunu çalıştırır, sınırlı test/regresyon planını bir kez
yürütür, kaynak sapmasını denetler ve schema-2 JSON/Markdown makbuzlarını atomik
olarak mühürler:

```powershell
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası>
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası> --execute
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
python divan-project.pyz adoption verify .divan/adoption/<proof-id>/adoption-receipt.json
```

VERIFIED geçişi proje-göreli kanıt yollarını doğrular; bağlantı, yol kaçışı,
eksik dosya, secret ve boyut sınırını aşan dosyaları reddeder. Kabul edilen
dosyaların hash'leri, durum geçişiyle aynı atomik yazımda hedef makbuzuna
bağlanır. Yalnız üretilmiş şartname veya plan dosyalarına dayanan bir hedef
VERIFIED olamaz; `adoption prove` ayrıca gerçek kanıtın VERIFIED olayında
kaydedildiğini bağımsız olarak denetler.

Operatör rolü yalnız açıklayıcıdır; bakımcı ve dış kullanıcı aynı teknik kapıya
tabidir. Makbuz; hash, kaba sonuç, süre, kontrol sınıfı ve gözlenen host sürümünü
tutar; secret, e-posta, kullanıcı adı, mutlak yol, remote URL, alakasız eklenti
envanteri, ham argv ve komut çıktısı gövdesini reddeder. Yalnız
`valid-clean-room-adoption` ve `eligible_for_v1: true` sonucu kapıya adaydır.

`adoption export` schema-1 uyumluluğu için kalır. Bu makbuzlar yalnız
`valid-schema-1-owner-canary` veya
`valid-schema-1-independent-declaration` olarak doğrulanır ve v1'e hiçbir zaman
uygun olmaz. Değişmez v0.18.5 ile üretilen gerçek schema-2 makbuzu repoya
kaydedilip yeniden doğrulandığı için v1 hazırlık karnesi **8/8**'dir.
Runner ile `.sha256` yan dosyası birlikte kalmalı; yürütme, Git tarafından
izlenen kaynak sapmasını reddedebilmek için bir Git reposu gerektirir.
Yan dosya indirme bütünlüğünü kanıtlar; v1 kapısı ayrıca incelenmiş release
runner özetini `registry/v1-gates.json` içinde sabitler ve birebir eşleşme ister.
Önizleme bu özeti sabit public GitHub Release API'sinden okur; yayın otoritesi
ulaşılamazsa veya farklıysa hiçbir proje komutu başlamaz.

Public web projesinde salt-okunur denetim:

```powershell
python scripts/seo.py audit --project . --profile standard --json
```

Denetim; metadata, canonical ve dil bağlantıları, sosyal kartlar, yapılandırılmış
veri, robots, sitemap ve yerel bağlantıları tek yapılandırılmış yayın origin'i
ile karşılaştırır. Statik kontroller tek başına kapıyı tamamlamaz. Başlatılan
public-web projeleri sınırlı `.divan/lighthouse.json`, `.divan/seo-tools.json`
ve `.github/workflows/divan-seo.yml` sözleşmelerini alır. Sabitlenmiş workflow
Lighthouse CI'ı incelenmiş Linux/AMD64 OCI digest'iyle; Lychee'yi resmî release
arşivi SHA256 değeri ve tam 13 üyeli arşiv sözleşmesiyle doğrular. Link, path
traversal veya üye sapmasını reddeder ve yalnız iç içe doğrulanmış binary
yolunu çalıştırır. Yönetilen komut planındaki acquisition argv, execution argv,
outputs ve digest aynı registry nesnesinden workflow'a aktarılır; native JSON
üretilir ve tek GitHub artefaktı yüklenir.
Yerel audit araç indirmez, çalıştırmaz veya sağlayıcı yetkisi vermez.

Runtime-rendered web projeleri init sırasında yayın URL'sini
`--expected-url https://app.example.com/` ile vermelidir. URL yoksa init
`BLOCKED` olur, çalıştırılabilir SEO workflow'u üretmez ve güvenli devam
komutunu döndürür.

Yerel native artefaktlar en fazla `OBSERVED_UNVERIFIED` olabilir; kullanıcının
yazdığı JSON hiçbir zaman `PASS` üretemez. Yetkili doğrulama açıkça
`verify-github` komutuyla yapılır. Repo kimliği temiz yerel Git HEAD ve normalize
`github.com` origin'inden türetilir; CLI değeri yalnız eşleşmeyi doğrulayabilir.
Bu yol tam koşu denemesi, commit/tree, canonical workflow baytları/digest'i,
GitHub artefakt ilişkisi/digest'i ve native JSON ZIP için sabit, kimliği
doğrulanmış `gh api` geri okumalarını kullanır. Eksik
GitHub capability veya herhangi bir uyumsuzluk fail-closed kalır.

Search Console varsayılan olarak kapalıdır. Opt-in yapılandırması hesap,
property ve sağlayıcı tarafından yönetilen kimlik doğrulama ister; yapılandırma
tek başına `CONFIGURED_UNVERIFIED` olur. READY durumu ProviderCapabilityV1 ve
sağlayıcı geri-okuma kanıtı olmadan verilmez. Denetim URL göndermez veya Search
Console'u değiştirmez.

Yönlendirme, Divan Nizamı ve paket seçimi için [Divan Engine](Divan-Engine.tr.md), Divan dağıtım
sözleşmesi için [Topluluk Standartları](Topluluk-Standartlari.md) belgesine bak.
