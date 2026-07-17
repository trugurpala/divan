# Kurulum

## Claude Code (birincil yol)
```
/plugin marketplace add trugurpala/divan
/plugin install sadrazam@divan
/plugin install core-pack@divan
/plugin install ui-pack@divan
/plugin install react-pack@divan
```
Güncelleme: `/plugin marketplace update divan` · Kaldırma: `/plugin uninstall <paket>@divan`

## Codex — tek komut kurulum

Windows (PowerShell):
```powershell
irm https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.ps1 | iex
```
macOS/Linux:
```bash
curl -fsSL https://raw.githubusercontent.com/trugurpala/divan/main/scripts/kur-codex.sh | bash
```
Sonra Codex'i yeniden başlat. Skill'ler tetikleyici cümlelerle çalışır
("baştan sona yap", "defter kur"); /komutlar, hook ve subagent'lar Claude
Code'a özgüdür — Codex'te hafıza AGENTS.md üzerinden yürür.

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
| Skills (15 vezir) | ✓ /plugin ile | ✓ Agent Skills standardı — klasör kopyala |
| Memory (defterdar dosyaları: AGENTS.md, BLUEPRINT, .divan/) | ✓ | ✓ düz dosya + AGENTS.md'yi Codex/Cursor doğal okur |
| Komutlar (/ferman /defter /teftis) | ✓ | ✗ Claude Code'a özgü (skill tetikleyicileri yine çalışır) |
| Subagents (kâşif, müfettiş) | ✓ | ✗ Claude Code'a özgü |
| Hooks (oturum başında defteri otomatik oku) | ✓ | ✗ Claude Code'a özgü |
| Marketplace tek komut kurulum | ✓ | ✗ elle kopyalama |

Özet: skill'ler ve hafıza dosyaları her yerde taşınır; komut/subagent/hook
katmanları Claude Code'da tam güçtedir.
