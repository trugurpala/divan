# Divan

![teftis](https://github.com/trugurpala/divan/actions/workflows/teftis.yml/badge.svg)

**Vibe coder'ın vezirler kurulu — 37 skill, 5 paket, hafıza, bağımsız denetçi.**
Sen fermanı verirsin; Divan planlar, TDD ile inşa eder, kanıtıyla teslim eder
ve kaldığın yeri asla unutmaz. Claude Code'da tam güç; Codex, Cursor ve tüm
Agent Skills uyumlu ajanlarda taşınabilir.

**Canlı sayfa:** https://trugurpala.github.io/divan/ · **Katalog:** [docs/Vezir-Katalogu.md](docs/Vezir-Katalogu.md)

## Kurulum

**Claude Code:**
```
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan     # orkestratör + hafıza + müşavir (çekirdek)
/plugin install core-pack@divan    # metodoloji + kural hazinesi
/plugin install ui-pack@divan  &&  /plugin install react-pack@divan  &&  /plugin install zanaat-pack@divan
```

**Codex (Windows, tek komut):**
```powershell
irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.ps1 | iex
```
macOS/Linux ve ayrıntılar: [docs/Kurulum.md](docs/Kurulum.md)

## Komutlar (Claude Code)

| Komut | Ne yapar |
|---|---|
| `/ferman <iş>` | İşi Divan Protokolü ile baştan sona teslim eder |
| `/defter kur\|yaz\|oku\|karar` | Proje hafızası: kur, işle, kaldığın yeri özetle, ADR kaydet |
| `/vezir <fikir>` | Divan'a standartlara uygun yeni skill yetiştirir |
| `/teftis` | Repoyu ve hafıza sağlığını denetler |

## Paketler (37 vezir)

| Paket | Öne çıkanlar | Kaynak / Lisans |
|---|---|---|
| **sadrazam** (4) | Uçtan uca orkestratör · **defterdar** (kalıcı proje hafızası: AGENTS.md+BLUEPRINT+.divan) · **müşavir** (2026 stack danışmanı, tazelik protokollü) · vezir-yetiştirme. Ayrıca: kâşif+müfettiş subagent'ları, oturum başında defteri okuyan hook | Özgün, MIT |
| **core-pack** (15) | Beyin fırtınası→plan→TDD→doğrulama zinciri, sistematik debugging, code review (isteme+alma), paralel ajan sevki, git worktrees · **temkin** (4 ihtiyat ilkesi) · **kural-hazinesi** (9 CC0 seçme kural) | superpowers MIT + özgün + CC0 |
| **ui-pack** (3) | Şablon kokmayan frontend tasarım, tarayıcıda Playwright testi, 84 stillik design-system üretici | Apache 2.0 + MIT |
| **react-pack** (8) | React best practices, composition, view transitions, React Native, Vercel deploy/optimize, web tasarım ve yazım kuralları | Vercel Labs, MIT |
| **zanaat-pack** (7) | Ehl-i Hiref: algoritmik sanat, canvas/poster, tema fabrikası, MCP inşası, web artifact, Slack GIF, Claude API | Anthropic, Apache 2.0 |

## Nasıl çalışır

`/ferman` → defter yoksa kurulur (hafıza doğar) → müşavir stack seçer →
kâşif keşfeder → plan → temkinle TDD → **müfettiş bağımsız denetler** →
kanıt `.divan/evidence/`e → Takdim. Ertesi oturumda hook kaldığın yeri okur.
Para-dokunan işte (borsa/ödeme) spec-first + risk-register zorunlu.

## Güncellik ve namus

Her push CI teftişinden geçer (Agent Skills spec: klasör=name, ≤64/≤1024,
ayraç yasağı, çakışma). **Aylık nöbet** upstream'leri md5 ile kıyaslar,
fark bulursa kendiliğinden issue açar. Lisanssız içerik ne kadar popüler
olursa olsun alınmaz — kararlar [UPSTREAM.md](UPSTREAM.md) tablosundadır.

## Kaldırma

Divan iz bırakmadan gider: [docs/Kaldirma.md](docs/Kaldirma.md).
Yalnızca Markdown'dır; telemetri yok, eve arama yok.

## Katkı

[CONTRIBUTING.md](CONTRIBUTING.md) yolu anlatır; sadrazam kuruluysa
"Divan'a yeni vezir yaz" demen yeterlidir. Blueprint ve durum günlüğü:
[BLUEPRINT.md](BLUEPRINT.md).

> Bu proje Anthropic, Claude, OpenAI veya Vercel ile bağlı ya da onlarca
> onaylanmış değildir; uyumluluk ifadeleri yalnızca tanımlayıcıdır.
> Lisans: derleme ve özgün vezirler MIT; üçüncü taraflar kendi
> lisanslarını korur — [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
