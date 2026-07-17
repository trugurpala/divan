# Divan

![teftis](https://github.com/trugurpala/divan/actions/workflows/teftis.yml/badge.svg)

**Vibe coder'ın vezirler kurulu.** Sen fermanı verirsin; Divan işi baştan sona,
doğrulanmış şekilde bitirir. Claude Code, Cursor, Codex ve Agent Skills
standardını destekleyen tüm ajanlarla uyumludur.

> Bu proje Anthropic, Claude, Vercel veya başka bir kurumla bağlı ya da
> onlarca onaylanmış değildir. "Claude Code ile uyumludur" ifadesi yalnızca
> tanımlayıcı kullanımdır.

## Kurulum (Claude Code)

```
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan
/plugin install core-pack@divan
/plugin install ui-pack@divan
/plugin install react-pack@divan
```

## Komutlar

Sadrazam kuruluyken: `/ferman <iş>` işi baştan sona teslim eder,
`/vezir <fikir>` Divan'a yeni skill yetiştirir, `/teftis` repoyu denetler.

**Codex tek komut (Windows):** `irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.ps1 | iex`

**Canlı sayfa:** https://trugurpala.github.io/divan/

## Vezirler (paketler)

| Paket | Ne yapar | Kaynak / Lisans |
|---|---|---|
| **sadrazam** | Uçtan uca orkestratör: Ferman → Divan → Plan → İcra → Teftiş → Takdim | Özgün, MIT |
| **core-pack** | Beyin fırtınası, plan yazma/yürütme, sistematik debugging, TDD, doğrulama | obra/superpowers, MIT |
| **ui-pack** | Özgün frontend tasarım, tarayıcı testi, design-system üretici | Anthropic Apache 2.0 + Next Level Builder MIT |
| **zanaat-pack** | Ehl-i Hiref: algoritmik sanat, canvas/poster, tema, MCP inşası, web artifact, GIF, Claude API | anthropics/skills, Apache 2.0 |
| **react-pack** | React best practices, composition patterns, web tasarım kuralları | Vercel Labs, MIT |

## Divan Protokolü

Sadrazam kurulduğunda, "baştan sona yap", "büyük düşün", "ajans gibi çalış"
dediğin her istek altı fazdan geçer: **Ferman** (hedef netleşir) → **Divan**
(alternatifler tartılır) → **Plan** → **İcra** (TDD ile inşa) → **Teftiş**
(kanıtla doğrulama) → **Takdim** (bitmiş iş + sonraki adımlar).

## Lisans

Derleme ve özgün skill'ler: MIT. Üçüncü taraf skill'ler kendi lisanslarını
korur — bkz. [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Kaldırma

Divan iz bırakmadan gider: [docs/Kaldirma.md](docs/Kaldirma.md).

## Katkı

Divan kendini toplulukla geliştirir: [CONTRIBUTING.md](CONTRIBUTING.md) yolu,
[UPSTREAM.md](UPSTREAM.md) kaynak politikasını (neden fork değil, vendoring)
anlatır. Sadrazam kuruluysa "Divan'a yeni vezir yaz" demen yeterli —
`vezir-yetistirme` skill'i seni yürütür.
