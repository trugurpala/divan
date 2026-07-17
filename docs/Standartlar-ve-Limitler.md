# Standartlar ve Limitler

Divan, Agent Skills açık standardına (agentskills.io/specification) ve
Claude Code marketplace şemasına uyar. CI'daki `scripts/validate.py` her
push'ta şunları denetler:

## Skill (SKILL.md) kuralları
| Kural | Limit | İhlal sonucu |
|---|---|---|
| `name` uzunluğu | ≤ 64 karakter | hata |
| `name` deseni | küçük harf/rakam/tire; tire ile başlayamaz/bitemez | hata |
| `name` = klasör adı | birebir aynı | **skill hiç yüklenmez** |
| `description` | zorunlu, ≤ 1024 karakter; ne yaptığı + ne zaman | hata |
| Frontmatter'da `<` `>` | yasak (prompt injection riski) | hata |
| Ad çakışması | iki pakette aynı skill adı olamaz | hata |
| Gövde uzunluğu | ≤ 500 satır önerisi; fazlası references/ dosyalarına | uyarı |
| Alanlar | name, description, license, allowed-tools, metadata, compatibility | fazlası uyarı |

## Marketplace kuralları
- Katalog `.claude-plugin/marketplace.json` konumunda olmalı; `name`,
  `owner.name` ve her girdide `name`+`source` zorunlu.
- `strict: true` (varsayılan): her paket kendi `plugin.json`'ına sahiptir.
- Girdi sürümü ile plugin.json sürümü uyuşmazsa uyarı.

## Bağlam bütçesi
Skill'ler aşamalı yüklenir: başlangıçta yalnızca ad+açıklama (~100 token/skill);
gövde ancak tetiklenince okunur. Divan'ın 14 skill'inin boşta maliyeti ~1.4K
token civarındadır — MCP sunucularının onlarca bin token'lık yüküyle
karşılaştırın.
