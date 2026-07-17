# Divan

![teftis](https://github.com/trugurpala/divan/actions/workflows/teftis.yml/badge.svg)
![version](https://img.shields.io/badge/version-0.10.0-1f6feb)
![license](https://img.shields.io/badge/license-MIT-2ea44f)

**Türkçe** · [English](README.en.md) · [Değişiklikler](CHANGELOG.md) · [Yol haritası](BLUEPRINT.md)

<img src="docs/assets/muhurdar-idle.png" alt="Divan'ın Mühürdar maskotu" width="128" align="right">

**Padişah sensin. Divan, vibe coder'ın vezirler kuruludur — 41 skill, 5 paket,
kalıcı proje hafızası ve bağımsız denetim.**
Sen fermanı verirsin; Divan planlar, TDD ile inşa eder, kanıtıyla teslim eder
ve kaldığın yeri asla unutmaz. Claude Code'da tam güç; Codex, Cursor ve tüm
Agent Skills uyumlu ajanlarda taşınabilir.

**Sürüm:** v0.10.0 · **Canlı sayfa:** https://trugurpala.github.io/divan/ · **Katalog:** [docs/Vezir-Katalogu.md](docs/Vezir-Katalogu.md)

## Neden Divan?

Tek tek iyi prompt'lar yetmez. Üretim işi; doğru yeteneğin seçilmesini, kararın
diskte kalmasını, değişikliğin test edilmesini ve kullanıcının gördüğü yüzün de
aynı turda yayımlanmasını ister.

| Sorun | Divan'ın cevabı |
|---|---|
| Ajan plansız kodluyor | Sadrazam: brief → plan → icra → teftiş → takdim |
| Her oturumda proje unutuluyor | Defterdar: AGENTS.md, BLUEPRINT ve `.divan/` kayıtları |
| “Çalışıyor” deniyor, kanıt yok | Test, resmî doğrulayıcı ve bağımsız müfettiş kapısı |
| Binlerce skill bağlamı ve güveni bozuyor | Kürasyon, lisans/köken denetimi ve aşamalı yükleme |
| Harici swarm/harness karmaşık ve pahalı | Önce yerel tek oturum; gerekirse sınırlı subagent/worktree |
| PR hazır ama ürün hâlâ eski | Yayın Kanunu: vitrin + CHANGELOG + merge + canlı doğrulama |

Divan yeni bir model veya ayrı bir ajan runtime'ı değildir. Mevcut kodlama
ajanına **çalışma disiplini, uzmanlık ve teslim hafızası** ekleyen, denetlenebilir
bir Agent Skills dağıtımıdır.

## Kendi kendini nasıl geliştirir?

Divan gelişmeyi “daha çok skill yükle” diye tanımlamaz:

1. Kaynağı ve gerçek repo kimliğini bulur.
2. Lisans, köken, hook/script ve araç yetkilerini denetler.
3. Mevcut 41 vezirle çakışmayı ve gerçek ürün boşluğunu ölçer.
4. Gerekirse en küçük özgün skill'i yazar ve davranış eval'ini ekler.
5. Yerel test + Agent Skills + Claude Code doğrulamasını geçirir.
6. README, katalog, CHANGELOG ve BLUEPRINT'i aynı değişiklikte günceller.
7. Yayın istenmişse PR'ı ara sonuç sayar; `main` ve canlı yüz doğrulanmadan
   “yayımlandı” demez.

Bu döngünün son örneği: [40 repoluk kaynak kürasyonu](reports/2026-07-18-claude-repo-kurasyonu.md).

## Kurulum

**Claude Code:**
```
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan     # orkestratör + hafıza + müşavir (çekirdek)
/plugin install core-pack@divan    # metodoloji + kural hazinesi
/plugin install ui-pack@divan
/plugin install react-pack@divan
/plugin install zanaat-pack@divan
```

**Codex (Windows, tek komut):**
```powershell
irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.ps1 | iex
```
macOS/Linux ve ayrıntılar: [docs/Kurulum.md](docs/Kurulum.md)

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

Yapısal doğrulama “skill daha iyi çalışıyor” demek değildir. v0.10.0 aynı
vakayı baseline ve skill koşullarında gerçek ajan adaptörüyle çalıştıran,
çıktıları A/B körleştiren ve isteğe bağlı hakem/eşik uygulayan koşucu ekler:

```bash
python evals/run.py --check
python evals/run.py --run --skill kaynak-kuratori \
  --adapter "python /guvenilir/yol/agent_adapter.py" \
  --judge "python /guvenilir/yol/judge_adapter.py"
```

Hakem veya gerçek adaptör yoksa koşucu başarı oranı uydurmaz; sonucu
`review_required` olarak kaydeder. Protokol: [evals/README.md](evals/README.md).

## Komutlar (Claude Code)

| Komut | Ne yapar |
|---|---|
| `/ferman <iş>` | İşi Divan Protokolü ile baştan sona teslim eder |
| `/sefer <iş>` | Tek oturum, subagent veya izole takım arasından en küçük güvenli düzeni seçer |
| `/defter kur\|yaz\|oku\|karar` | Proje hafızası: kur, işle, kaldığın yeri özetle, ADR kaydet |
| `/vezir <fikir>` | Divan'a standartlara uygun yeni skill yetiştirir |
| `/teftis` | Repoyu ve hafıza sağlığını denetler |

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
12 davranış vakası ve sağlayıcı-bağımsız A/B koşucusu vardır. Henüz güvenilir bir
gerçek ajan adaptörüyle yayımlanmış karşılaştırma sonucu, bağımsız kullanıcı
kanıtı veya ölçülmüş verim benchmark'ı yoktur. Bunlar gelmeden hız, gelir veya
“dünyanın en iyisi” iddiası yapılmaz.

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
