# Divan

![teftis](https://github.com/trugurpala/divan/actions/workflows/quality-gate.yml/badge.svg)
![version](https://img.shields.io/badge/version-1.0.1-1f6feb)
![license](https://img.shields.io/badge/license-MIT-2ea44f)

**Türkçe** · [English](README.en.md) · [Wiki](https://github.com/trugurpala/divan/wiki) · [Değişiklikler](CHANGELOG.md) · [Yol haritası](BLUEPRINT.md)

<img src="docs/assets/muhurdar-idle.png" alt="Divan'ın Mühürdar maskotu" width="128" align="right">

**Hükümdar sensin. Divan, kodlama ajanının etrafındaki tek üründür — 41 beceri,
5 paket, kalıcı proje hafızası ve bağımsız denetim.**
Sen fermanı verirsin; Divan planlar, TDD ile inşa eder, kanıtıyla teslim eder
ve kaldığın yeri asla unutmaz. Claude Code/Desktop Code ve Codex'te yerel
plugin olarak; Cursor ve diğer Agent Skills uyumlu ajanlarda taşınabilir.

Host desteği tek bir “uyumlu” pazarlama sözüyle değil, kanıt seviyesiyle
yayınlanır. Bugün Claude Code ve Codex doğrulanmıştır; diğer hostların mevcut
seviyesi, hedefi, yetenek haritası ve resmî kaynağı
[host uyumluluk kaydında](registry/host-compatibility.json) ayrı tutulur.

**Güncel kaynak:** v1.0.1 · **Son yayımlanan:** v1.0.0 · **Release:** https://github.com/trugurpala/divan/releases · **Canlı sayfa:** https://trugurpala.github.io/divan/ · **Canlı Wiki:** https://github.com/trugurpala/divan/wiki · **Katalog:** [docs/skill-catalog.md](docs/skill-catalog.md) · **Host uyumluluğu:** [docs/Host-Uyumlulugu.md](docs/Host-Uyumlulugu.md) · **v1 karnesi:** [docs/V1-Hazirlik.md](docs/V1-Hazirlik.md)

Divan Engine, ürünün yalnız Python standart kütüphanesiyle çalışan yerleşik
icra çekirdeğidir. Divan Nizamı, Hükümdar öncelikli yetki düzenini tanımlar;
ikinci bir ürün değildir. Çekirdek bu repoda kalır ve başka bir agent
runtime'ına veya dış repoya bağımlı olmaz.
Divan Nizamı yerel iş akışı yönetişimidir, kimlik doğrulama sistemi değildir;
güvenlik sınırı host işletim sistemi hesabı ile repo izinleridir.

## Neden Divan?

Tek tek iyi prompt'lar yetmez. Üretim işi; doğru yeteneğin seçilmesini, kararın
diskte kalmasını, değişikliğin test edilmesini ve kullanıcının gördüğü yüzün de
aynı turda yayımlanmasını ister.

| Sorun | Divan'ın cevabı |
|---|---|
| Ajan plansız kodluyor | Sadrazam: brief → plan → icra → teftiş → takdim |
| Her oturumda proje unutuluyor | Claude Code'un doğrudan okuduğu `CLAUDE.md` + AGENTS, BLUEPRINT ve `.divan/` kayıtları |
| “Çalışıyor” deniyor, kanıt yok | Test, resmî doğrulayıcı ve bağımsız müfettiş kapısı |
| Binlerce skill bağlamı ve güveni bozuyor | Kürasyon, lisans/köken denetimi ve aşamalı yükleme |
| Harici swarm/harness karmaşık ve pahalı | Önce yerel tek oturum; gerekirse sınırlı subagent/worktree |
| PR hazır ama ürün hâlâ eski | Yayın Kanunu: vitrin + Wiki + CHANGELOG + merge + canlı doğrulama |
| Bağlı bir araç işin kapsamını büyütüyor | Divan Nizamı: kapsamı yalnız Hükümdar genişletebilir; her devir daha dardır |
| Sohbette teknik işin takibi zorlaşıyor | Sade ilerleme sözleşmesi: şu an ne olduğunu, neden önemli olduğunu ve sıradakini bildir |

Divan yeni bir model veya ayrı bir üçüncü taraf ajan runtime'ı değildir. Kendi
modüler icra çekirdeğiyle mevcut kodlama ajanına **çalışma disiplini, uzmanlık
ve teslim hafızası** ekleyen, denetlenebilir bir Agent Skills dağıtımıdır.

## Divan Engine ve Divan Nizamı

Skill adlarını ezberlemek yerine hedefi yaz. Sadrazam projeyi güvenli biçimde
inceler, framework'ü belirler, en küçük yetkin ekibi seçer ve değişen dosyaların
README, Wiki, site, test ve yayın etkilerini grafikte genişletir. Core Pack
mühendislik disiplinini, UI Pack arayüz kalitesini sağlar. React Pack yalnız
React projesinde; Zanaat Pack yalnız yaratıcı veya entegrasyon işinde devreye
girer. Ayrıntılar: [Divan Engine](docs/Divan-Engine.tr.md).

Nizâm-ı Sefer eksik olan icra muhakemesini ekler. Plan artık yapısal riski,
host kesinliğini, ihtiyatlı bağlam bütçesini, gereken model sınıfını, sefer
sayısını, görev bağımlılıklarını, devir noktasını, kanıtları ve en fazla üç
paralel iş hattını açıklar. Model çağırmaz ve aday modelin hesapta bulunduğunu
varsaymaz:

```powershell
python scripts/divan.py plan --project . --intent "API'yi güvenli yap, test et ve yayınla" --host-profile auto --json
python scripts/divan.py plan --project . --intent "API'yi güvenli yap, test et ve yayınla" --host-profile codex --context-window 1050000 --target released --json
```

Son yetki Hükümdardadır. Ferman; sınırları belli işi Sadrazam ve Divan üzerinden
uzmanlara ve sağlayıcılara devreder. Bir aracın bağlı olması yetki vermez;
kapsamı yalnız Hükümdar genişletebilir. Dokuz modüllü sözleşmeyi yazmadan gör
ve doğrula:

```powershell
python scripts/divan.py architecture --json
python scripts/divan.py validate
```

Kanonik uzman komutu `/divan`dır. Eski `/company` ve `company-validate` adları
v1 boyunca sınırlı uyumluluk takma adları olarak kalır.

Aynı sözleşmeyi hedef projeye önce yazmayan önizlemeyle kur:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto
python scripts/divan.py init --project . --profile standard --locale auto --execute
python scripts/divan.py audit --project . --format json
```

Divan reposu `DCS-*`, kurulu proje ise yalnız uygulanabilir `DPS-*` kurallarını
izler ve kanıtı `.divan/` altında tutar. Ayrıntılar:
[Divan Proje Sözleşmesi](docs/Project-Contract.tr.md).

Kurulumdan sonra sahiplik ve sapmayı yazmadan oku; proje schema güncellemesini
veya güvenli onarımı uygulamadan önce planını gör:

```powershell
python scripts/divan.py project status --project . --json
python scripts/divan.py project update --project .
python scripts/divan.py project update --project . --execute
python scripts/divan.py project repair --project .
python scripts/divan.py project repair --project . --execute
```

Host `update`, Claude/Codex içindeki Divan paketlerini değiştirir. Project
`update`, hedef repoda yalnız Divan'ın sahip olduğu yüzeyleri taşır. `audit`,
DPS kalite kanıtını; `project status`, sahiplik parmak izlerini ve sapmayı
değerlendirir. Doğrulanmış hedefler arşivlenebilir. Ana v1 kanıt yolu, Divan'dan
ayrı gerçek projedeki görevi sınırlı test/regresyon kontrolleriyle bir kez
çalıştırır, host sürümünü doğrudan gözler ve gizlilik sınırlı schema-2 makbuzu
mühürler:

```powershell
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası>
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası> --execute
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
python divan-project.pyz adoption verify .divan/adoption/<proof-id>/adoption-receipt.json
```

VERIFIED geçişi adı verilen proje-göreli dosyaları hedef makbuzuna atomik olarak
hash'ler; yalnız plan dosyası kanıtı reddedilir. Önizleme yazmaz ve subprocess
başlatmaz. Bakımcı ile dış kullanıcı aynı teknik
kapıya tabidir; kişinin sıfatı uygunluğu değiştirmez. Yalnız
`valid-clean-room-adoption` v1'e aday olabilir. Eski schema-1 export makbuzları
doğrulanmaya devam eder fakat v1 kanıtı sayılmaz.
İndirilen `divan-project.pyz` ile `divan-project.pyz.sha256` aynı klasörde
kalmalıdır. Kanıt yürütmesi, izlenen kaynak sapmasını güvenli biçimde
reddedebilmek için bir Git reposu da gerektirir.

## Kendi kendini nasıl geliştirir?

Divan gelişmeyi “daha çok skill yükle” diye tanımlamaz:

1. Kaynağı ve gerçek repo kimliğini bulur.
2. Lisans, köken, hook/script ve araç yetkilerini denetler.
3. Mevcut 41 beceriyle çakışmayı ve gerçek ürün boşluğunu ölçer.
4. Haftalık **Meclis** keşfi ve yapılandırılmış topluluk formuyla aday üretir;
   hiçbir adayı otomatik kurmaz.
5. Kimlik, lisans, yürütme yüzeyi ve kanıta göre ADOPT, ADAPT, REFERENCE veya
   REJECT kararını [aday defterine](docs/Aday-Meclisi.md) işler.
6. Gerekirse en küçük özgün skill'i yazar ve davranış eval'ini ekler.
7. Yerel test + Agent Skills + Claude Code doğrulamasını geçirir.
8. `/yayin` ve `release-manifest.json` ile README, Wiki, site, CHANGELOG,
   marketplace ve sürüm kaydındaki sapmayı CI'da durdurur.
9. Yayın istenmişse PR'ı ara sonuç sayar; `main`, Pages ve Wiki aynı sürüme
   gelince changelog'dan tag ile GitHub Release üretir.

Bu döngünün son örneği: [40 repoluk kaynak kürasyonu](reports/2026-07-18-claude-repo-kurasyonu.md).

## İlerlemeyi yerelde izle

Seyir; Divan'ın mevcut hedef, görev, Git, kontrol ve makbuz kanıtını sakin bir
yerel sayfada gösterir. Salt okunurdur, bulut servisi veya API anahtarı
kullanmaz ve yalnız `127.0.0.1` adresine bağlanır. İzlemek istediğin projede:

```powershell
python scripts/divan.py status --project . --open --lang auto
```

Divan boş bir port seçer, çalışan adresin tamamını terminale yazar ve `--open`
varsa aynı adresi açar. Adres geçicidir; `Ctrl+C` ile kapatılır. Belgelerdeki
örnek bir portu yeniden kullanma.

## Kurulum

Aşağıdaki komutlar Güncel kaynak sürümünü sabitler. Güncel kaynak Son yayımlanan
sürümden farklıysa bütün `--ref` komutlarında Son yayımlanan sürümü kullan.
Yalnız değişmez tag ve GitHub Release'i bulunan bir ref'i kur.

### En hızlı ilk kurulum: repo klonlamadan tek doğrulanmış dosya

Eşleşen GitHub Release yayımlandıktan sonra bağımsız kurucuyu ve checksum
dosyasını indir, bilgisayarında doğrula, yazmayan planı gör ve sonra uygula:

```powershell
$tag = "v1.0.0"
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz" -OutFile divan.pyz
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz.sha256" -OutFile divan.pyz.sha256
$expected = ((Get-Content .\divan.pyz.sha256 -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
$actual = (Get-FileHash .\divan.pyz -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "Divan bootstrap SHA-256 eşleşmiyor" }
python .\divan.pyz doctor --host codex --json
python .\divan.pyz install --host codex --profile auto
python .\divan.pyz install --host codex --profile auto --execute
```

Bu tek dosya release'in değişmez kaynak commit'ini, beş paketini ve 41
becerilik tam kataloğunu taşır; başka kaynak veya ref'i reddeder. `divan.pyz`
dosyasını sakla: yarım kalan bir işlem olursa doctor, aynı dosyayla çalışacak
tam recovery komutunu üretir.

Repo checkout'u içinden yazmayan planı görüp aynı sabit release'i iki hosta
kurmak için:

```powershell
python scripts/divan.py install --host both --ref v1.0.1
python scripts/divan.py install --host both --ref v1.0.1 --execute
```

Codex Desktop için tek bir açık `auto` profil komutu yerel CLI'ı tanılar ve
kanıtlayabildiği en güçlü yolu seçer:

```powershell
python scripts/divan.py install --host codex --profile auto --ref v1.0.1
python scripts/divan.py install --host codex --profile auto --ref v1.0.1 --execute
```

Codex CLI sağlıklıysa tam yerel plugin yolu korunur. CLI bulunamazsa,
çalıştırılamazsa veya işletim sistemi erişimi reddederse checksum ile
doğrulanan 41 becerilik fallback seçilir. Fallback skill ve talimatları sağlar;
yerel komut, ajan, hook, MCP yapılandırması veya yerel yaşam döngüsü sağladığını
iddia etmez. Host geçersiz JSON döndürürse gerçek uyumluluk sorunu gizlenmeden
kurulum durur.

Güvenlik için kurucu, kaynağı/ref'i kanıtlanamayan mevcut bir `divan` pazarının
veya `@divan` eklentisinin üzerine yazmaz; kaydı olduğu gibi bırakıp açık bir
hata verir.

Kurucu Claude Code/Desktop Code ile Codex'in resmî plugin CLI'larını kullanır,
mevcut eklentileri işlem kaydına alır ve alakasız eklentilere dokunmaz. Tek-host,
elle kurulum, eski kopya göçü ve kaldırma: [docs/Kurulum.md](docs/Kurulum.md).

Beş dakikalık güvenli yaşam döngüsü:

```powershell
python scripts/divan.py doctor --host both --ref v1.0.1
python scripts/divan.py update --host both --ref v1.0.1
python scripts/divan.py update --host both --ref v1.0.1 --execute
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
python scripts/divan.py recover "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

Tek dosyalık `divan.pyz`, yükseltme sırasında içindeki değişmez release
kimliğini kullanır; çıkarıldığı geçici klasörü Git checkout gibi yorumlamaz.

Örnek günlük yolunu doctor çıktısındaki tam `recovery_command` ile değiştir.
`install-...json` geri alması bu kurulumun oluşturduğu Divan kayıtlarını kaldırır;
host'a göre elle kaldırma ve sahiplik sınırları: [docs/Kaldirma.md](docs/Kaldirma.md).

## Temiz geliştirme

```powershell
python scripts/verify.py
python scripts/hygiene.py --check
python scripts/hygiene.py --clean
```

`verify.py`, yerel geliştirme ile CI'ın ortak doğrulama yoludur. Python
bytecode'unu kapatır, araç cache'lerini repo dışına yönlendirir, çekirdek
kapıları çalıştırır ve ikinci bir hijyen kontrolüyle biter. `--check`; birinci
taraf metinde UTF-8/BOM/mojibake, locale'e bırakılmış metin
subprocess'i ve repo cache'lerini reddeder. `--clean` yalnız sabit allowlist'teki
yeniden üretilebilir cache'leri kalıcı siler; `.divan/evidence`, eval sonuçları,
manifestler, worktree'ler ve kullanıcı/rollback yedeklerine dokunmaz. Repo metni
UTF-8/LF, çekirdek Python karmaşıklık bütçesi McCabe 25 olarak CI'da sabittir.

## Bir dakikada başla

Skill adı ezberlemek zorunda değilsin. [Canlı ferman seçicide](https://trugurpala.github.io/divan/#basla)
niyetini seç; Divan gerekli paketi, kopyalanabilir fermanı ve teslim akışını
göstersin.

| Niyet | Paket | Divan'ın ilk hareketi |
|---|---|---|
| Özellik çıkar | `sadrazam` + `core-pack` | Brief → plan → TDD → teftiş → yayın |
| Bug düzelt | `core-pack` | Belirti → kök neden → regresyon testi |
| Arayüz tasarla | `ui-pack` + `react-pack` | Estetik yön → sistem → tarayıcı doğrulaması |
| Projeyi tanı | `sadrazam` + `core-pack` | Kanıtlı arama → mimari/risk haritası → defter |
| Kanıtla ve yayınla | `sadrazam` + `core-pack` | A/B eval → kör hakem → CI → canlı doğrulama |

## Davranış eval'i

Yapısal doğrulama “skill daha iyi çalışıyor” demek değildir. v0.10 serisi aynı
vakayı baseline ve skill koşullarında gerçek ajan adaptörüyle çalıştıran,
çıktıları A/B körleştiren ve isteğe bağlı hakem/eşik uygulayan koşucu ekler:

```bash
python evals/run.py --check
python evals/run.py --run --skill kaynak-kuratori \
  --adapter "python /guvenilir/yol/agent_adapter.py" \
  --judge "python /guvenilir/yol/judge_adapter.py" \
  --provenance provenance.json
```

Hakem veya gerçek adaptör yoksa koşucu başarı oranı uydurmaz; sonucu
`review_required` olarak kaydeder. Provenance kaydı koşunun ajan/hakem/ortam
kimliğini açıklar; tek başına kalite kanıtı değildir. v0.12.0'ın ilk gerçek
Claude→Codex kör A/B koşusu üç vakada skill 0, baseline 1, beraberlik 2 sonucu
verdi; önceden belirlenmiş eşik olmadığı ve skill galibiyeti bulunmadığı için
kalite artışı iddiası değildir. Kamu sonucu:
[evals/results/claude-codex-baglam-muhafizi-v012.json](evals/results/claude-codex-baglam-muhafizi-v012.json).
Protokol: [evals/README.md](evals/README.md).

## Komutlar (Claude Code)

| Komut | Ne yapar |
|---|---|
| `/ferman <iş>` | İşi Divan Protokolü ile baştan sona teslim eder |
| `/sefer <iş>` | Tek oturum, subagent veya izole takım arasından en küçük güvenli düzeni seçer |
| `/defter kur\|yaz\|oku\|karar` | Proje hafızası: kur, işle, kaldığın yeri özetle, ADR kaydet |
| `/divan <iş>` | Divan Engine ile hedefi keşif, plan, etki ve kanıt zincirine taşır |
| `/vezir <fikir>` | Uyumluluk komutu: Divan'a standartlara uygun yeni beceri geliştirir |
| `/teftis` | Repoyu ve hafıza sağlığını denetler |
| `/yayin <semver>` | Bütün sürüm yüzeylerini hazırlar; CI → canlı yüzey → tag/Release zincirini tamamlar |

## Paketler (41 beceri)

| Paket | Öne çıkanlar | Kaynak / Lisans |
|---|---|---|
| **sadrazam** (5) | Uçtan uca orkestratör · **ordu-nizamı** (yerel üç kademeli ajan sevki) · **defterdar** (kalıcı proje hafızası: AGENTS.md+BLUEPRINT+.divan) · **müşavir** (2026 stack danışmanı, tazelik protokollü) · vezir-yetiştirme. Ayrıca: kâşif+müfettiş subagent'ları, oturum başında defteri okuyan hook | Özgün, MIT |
| **core-pack** (18) | Beyin fırtınası→plan→TDD→doğrulama zinciri, sistematik debugging, code review, worktrees · **kaynak-küratörü** (repo/lisans/köken süzgeci) · **arama-ustası** (kanıtlı rg + isteğe bağlı AST) · **bağlam-muhafızı** (bütçe, maskeleme, devir) · **temkin** · **kural-hazinesi** | superpowers MIT + özgün + MIT uyarlama + CC0 |
| **ui-pack** (3) | Şablon kokmayan frontend tasarım, tarayıcıda Playwright testi, 84 stillik design-system üretici | Apache 2.0 + MIT |
| **react-pack** (8) | React best practices, composition, view transitions, React Native, Vercel deploy/optimize, web tasarım ve yazım kuralları | Vercel Labs, MIT |
| **zanaat-pack** (7) | Ehl-i Hiref: algoritmik sanat, canvas/poster, tema fabrikası, MCP inşası, web artifact, Slack GIF, Claude API | Anthropic, Apache 2.0 |

## Nasıl çalışır

`/ferman` → mevcut defter okunur; yeni hafıza yalnızca sen istersen kurulur → müşavir stack seçer →
kâşif keşfeder → plan → temkinle TDD → **müfettiş bağımsız denetler** →
kanıt `.divan/evidence/`e → Takdim. Ertesi oturumda hook kaldığın yeri okur.
Para-dokunan işte (borsa/ödeme) spec-first + risk-register zorunlu.

İş gerçekten bölünebiliyorsa `/sefer` üç kademeden en küçüğünü seçer: **Ocak**
(tek oturum), **Sefer** (sınırları belirli subagent) veya **Ordu** (worktree ile
izole paralel uygulama; Agent Teams yalnızca açık deneysel tercih). Karar ve
aday karnesi: [docs/Orkestrasyon-Karari.md](docs/Orkestrasyon-Karari.md).

**Mühürdar**, Divan'ın temkinli mühür bekçisidir: çalışma sürerken kanıtı
izler, teslimden önce teftişi hatırlatır. Maskot, ürün davranışını değiştiren
bir ajan değil; Divan'ın doğrulama disiplininin görsel yüzüdür.

## Güncellik ve namus

Her push yerel test, resmî Agent Skills ve Claude Code doğrulayıcılarından geçer
(klasör=name, ≤64/≤1024, çakışma, paket sürümü). **Aylık nöbet** upstream'leri
SHA-256 ile simetrik kıyaslar,
fark bulursa kendiliğinden issue açar. Lisanssız içerik ne kadar popüler
olursa olsun alınmaz — kararlar [UPSTREAM.md](UPSTREAM.md) tablosundadır.

## Dürüst durum

Divan v1.0.0, makine destekli sekiz hazırlık kapısının tamamı geçtikten sonra
yayımlandı. 41 becerinin tamamı yapısal olarak doğrulanır; 4 özgün skill için
13 davranış vakası ve sağlayıcı-bağımsız A/B koşucusu vardır. Kararlı sözleşme;
tek repo, beş modüler paket, stdlib-only Divan Engine, Hükümdar öncelikli Divan
Nizamı, kurulu Divan Proje Sözleşmesi ve Claude Code/Codex yaşam döngüsünü
korur. Değişmez tag, checksum ve attestation bağlı yedi varlık, SBOM, Pages,
Wiki ve temiz-host matrisi
[v1.0.0 yayın kanıtında](.divan/evidence/teftis-20260731-v100-release.md)
kayıtlıdır. Temiz-proje sonucu sınırlı teknik akışı kanıtlar; bağımsız kullanıcı
sayısı, üçüncü taraf onayı, pazar benimsemesi, hız, gelir, kalite artışı veya
“dünyanın en iyisi” iddiası değildir.

## Kaldırma

Divan güvenli biçimde kaldırılabilir: [docs/Kaldirma.md](docs/Kaldirma.md).
Skill metinlerinin yanında açık kaynak doğrulama/kurulum betikleri ve bazı
üçüncü taraf varlıkları bulunur; otomatik telemetri veya eve arama yoktur.

## Katkı

[CONTRIBUTING.md](CONTRIBUTING.md) yolu anlatır; sadrazam kuruluysa
"Divan'a yeni skill geliştir" demen yeterlidir. Blueprint ve durum günlüğü:
[BLUEPRINT.md](BLUEPRINT.md).

> Bu proje Anthropic, Claude, OpenAI veya Vercel ile bağlı ya da onlarca
> onaylanmış değildir; uyumluluk ifadeleri yalnızca tanımlayıcıdır.
> Lisans: derleme ve özgün skill'ler MIT; üçüncü taraflar kendi
> lisanslarını korur — [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Standartlar ve topluluk

Divan'ın `DCS-001`–`DCS-011` arasındaki on bir zorunlu ürün kuralı
[Topluluk Standartları](docs/Topluluk-Standartlari.md) sayfasında ve
`python scripts/standards.py --check` kapısında yaşar. Kullanım sorusu, hata,
özel güvenlik bildirimi, yetenek önerisi ve temiz-proje kabul kanıtı için tek doğru
yollar [SUPPORT.md](SUPPORT.md) içindedir. Katkı rehberi:
[Türkçe](CONTRIBUTING.tr.md) · [English](CONTRIBUTING.en.md).

v1 hazırlık durumu: **8/8** kapı geçti. Değişmez v0.18.5, Windows 11, Codex ve
Divan'dan ayrı gerçek bir projede makinece doğrulanabilir bir temiz-proje kanıtı
üretti; gizlilik incelemesinden geçen makbuz repoya kaydedilip çevrimdışı yeniden
doğrulandı. Bu sınırlı teknik kanıt; bağımsız kullanıcı sayısı, üçüncü taraf
onayı, pazar benimsemesi, hız veya kalite artışı iddiası değildir.
Önizleme bu özeti önce public GitHub Release API'sinden okur; yayın otoritesi
doğrulanamazsa proje komutları başlamadan kapalı başarısız olur.
