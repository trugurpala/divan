# OpenAI ve Codex Uyumluluğu

Divan'ın taşınabilir skill katmanı ile OpenAI Agents SDK aynı şey değildir.
Bu ayrım kullanıcıdan gizlenmez.

## Bugün ne çalışır?

| Katman | Divan'daki durum |
|---|---|
| Agent Skills | `plugins/*/skills/*/SKILL.md`; Codex ve Agent Skills uyumlu hostlara kopyalanabilir |
| Codex proje hafızası | `AGENTS.md`, `BLUEPRINT.md` ve `.divan/` düz dosyaları |
| Davranış eval'i | Sağlayıcı-bağımsız JSON stdin/stdout adapter sözleşmesi |
| OpenAI Agents SDK uygulaması | Divan'ın zorunlu runtime'ı değildir; henüz yerleşik adapter yayımlanmadı |
| OpenAI API anahtarı | Divan'ın kurulumu ve yerel yapısal teftişi için gerekmez |

## Neden runtime eklenmedi?

OpenAI'nin güncel Agents SDK rehberi SDK'yı araçlar, guardrail'ler, handoff'lar,
session'lar ve tracing içeren uygulama çalışma zamanı olarak tanımlar. Divan ise
öncelikle farklı kodlama ajanlarına taşınan prosedürel skill ve teslim
kurallarıdır. Uygulama runtime'ı ile bilgi paketini tek ürünmüş gibi göstermek
kurulum maliyetini ve güvenlik yüzeyini gereksiz büyütür.

Gerçek OpenAI adapter'ı eklendiğinde en küçük yol izlenecek: önce tek `Agent` ve
`Runner`, sonra ihtiyaç kanıtlanırsa araç/handoff; çalıştırma izi ve eval sonucu
model, adapter ve hakem bilgisiyle yayımlanacak.

## Kaynaklar

- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents
- OpenAI agent evals: https://developers.openai.com/api/docs/guides/agent-evals
- OpenAI Agents Python: https://github.com/openai/openai-agents-python
- Divan eval protokolü: https://github.com/trugurpala/divan/blob/main/evals/README.md

Bu sayfa uyumluluğu açıklar; Anthropic, OpenAI veya başka bir sağlayıcının Divan'ı
onayladığı anlamına gelmez.
