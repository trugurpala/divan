# Divan

![teftis](https://github.com/trugurpala/divan/actions/workflows/teftis.yml/badge.svg)
![version](https://img.shields.io/badge/version-0.12.2-1f6feb)
![license](https://img.shields.io/badge/license-MIT-2ea44f)

**Türkçe** · [English](README.en.md) · [Wiki](https://github.com/trugurpala/divan/wiki) · [Değişiklikler](CHANGELOG.md) · [Yol haritası](BLUEPRINT.md)

<img src="docs/assets/muhurdar-idle.png" alt="Divan'ın Mühürdar maskotu" width="128" align="right">

**Padişah sensin. Divan, vibe coder'ın vezirler kuruludur — 41 skill, 5 paket,
kalıcı proje hafızası ve bağımsız denetim.**
Sen fermanı verirsin; Divan planlar, TDD ile inşa eder, kanıtıyla teslim eder
ve kaldığın yeri asla unutmaz. Claude Code/Desktop Code ve Codex'te yerel
plugin olarak; Cursor ve diğer Agent Skills uyumlu ajanlarda taşınabilir.

**Sürüm:** v0.12.2 · **Release:** https://github.com/trugurpala/divan/releases · **Canlı sayfa:** https://trugurpala.github.io/divan/ · **Canlı Wiki:** https://github.com/trugurpala/divan/wiki · **Katalog:** [docs/Vezir-Katalogu.md](docs/Vezir-Katalogu.md) · **v1 karnesi:** [docs/V1-Hazirlik.md](docs/V1-Hazirlik.md)

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

Divan yeni bir model veya ayrı bir ajan runtime'ı değildir. Mevcut kodlama
ajanına **çalışma disiplini, uzmanlık ve teslim hafızası** ekleyen, denetlenebilir
bir Agent Skills dağıtımıdır.

## Kendi kendini nasıl geliştirir?

Divan gelişmeyi “daha çok skill yükle” diye tanımlamaz:

1. Kaynağı ve gerçek repo kimliğini bulur.
2. Lisans, köken, hook/script ve araç yetkilerini denetler.
3. Mevcut 41 vezirle çakışmayı ve gerçek ürün boşluğunu ölçer.
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

## Kurulum

Önce değişiklik yapmayan planı gör, sonra aynı sabit release'i iki hosta kur:

```powershell
python scripts/kur-hostlar.py --host both --ref v0.12.2
python scripts/kur-hostlar.py --host both --ref v0.12.2 --execute
```

Güvenlik için kurucu, kaynağı/ref'i kanıtlanamayan mevcut bir `divan` pazarının
veya `@divan` eklentisinin üzerine yazmaz; kaydı olduğu gibi bırakıp açık bir
hata verir.

Kurucu Claude Code/Desktop Code ile Codex'in resmî plugin CLI'larını kullanır,
mevcut eklentileri işlem kaydına alır ve alakasız eklentilere dokunmaz. Tek-host,
elle kurulum, eski kopya göçü ve kaldırma: [docs/Kurulum.md](docs/Kurulum.md).

## Temiz geliştirme

```powershell
python scripts/hijyen.py --check
python scripts/hijyen.py --clean
```

`--check`; birinci taraf metinde UTF-8/BOM/mojibake, locale'e bırakılmış metin
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
| `/vezir <fikir>` | Divan'a standartlara uygun yeni skill yetiştirir |
| `/teftis` | Repoyu ve hafıza sağlığını denetler |
| `/yayin <semver>` | Bütün sürüm yüzeylerini hazırlar; CI → canlı yüzey → tag/Release zincirini tamamlar |

## Paketler (41 vezir)

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

Divan açık standartlara ve GitHub'ın açık kaynak topluluk dosyalarına uyumludur;
ancak henüz v1.0 değildir. 41 skill yapısal olarak doğrulanır; 4 özgün skill için
13 davranış vakası ve sağlayıcı-bağımsız A/B koşucusu vardır. v0.11 yayın
yüzeylerini ve temiz-host matrisini otomatikleştirir. İlk güvenilir gerçek
ajan/hakem karşılaştırması yayımlanmıştır; bağımsız kullanıcı kanıtı hâlâ dış
kapıdır. Güncel, makine-okunur durum [v1 hazırlık karnesinde](docs/V1-Hazirlik.md)
bulunur; bağımsız kanıt gelmeden hız, gelir veya “dünyanın en iyisi” iddiası
yapılmaz.

## Kaldırma

Divan güvenli biçimde kaldırılabilir: [docs/Kaldirma.md](docs/Kaldirma.md).
Skill metinlerinin yanında açık kaynak doğrulama/kurulum betikleri ve bazı
üçüncü taraf varlıkları bulunur; otomatik telemetri veya eve arama yoktur.

## Katkı

[CONTRIBUTING.md](CONTRIBUTING.md) yolu anlatır; sadrazam kuruluysa
"Divan'a yeni vezir yaz" demen yeterlidir. Blueprint ve durum günlüğü:
[BLUEPRINT.md](BLUEPRINT.md).

> Bu proje Anthropic, Claude, OpenAI veya Vercel ile bağlı ya da onlarca
> onaylanmış değildir; uyumluluk ifadeleri yalnızca tanımlayıcıdır.
> Lisans: derleme ve özgün vezirler MIT; üçüncü taraflar kendi
> lisanslarını korur — [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
