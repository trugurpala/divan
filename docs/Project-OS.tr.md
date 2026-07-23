# Divan Project OS

[English](Project-OS.md)

Divan Project OS, hedef projeye kurulan gözetimli ve taşınabilir ürün
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
python scripts/divan.py audit --project . --format json
```

Kurulum yalnız `.divan/` yüzeyine ve `AGENTS.md` / `CLAUDE.md` içindeki işaretli
bloğa sahip olur. Kullanıcı metni korunur; bozuk işaretçi işlemi durdurur. Aynı
kurulumun ikinci çalışması diff üretmez.

## Hedef ve kanıt yaşam döngüsü

```text
DISCOVERED → SPECIFIED → PLANNED → IMPLEMENTING
→ VERIFIED → PREVIEWED → RELEASED → OBSERVED
```

`BLOCKED` ve `FAILED` açık sonuçlardır. Makbuz; hash'leri, seçilen akışları,
değişen göreli yolları, kontrolleri, sağlayıcı kanıtını ve zaman damgalarını
tutar. Secret, gizli muhakeme, kişisel mutlak yol veya alakasız eklenti
envanteri yazmaz.

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

Yönlendirme ve paket seçimi için [Company OS](Company-OS.tr.md), Divan dağıtım
sözleşmesi için [Topluluk Standartları](Topluluk-Standartlari.md) belgesine bak.
