# “100 Claude Repos” Listesi — Divan Kürasyon Raporu

İnceleme tarihi: 2026-07-18

## Sonuç

Paylaşım “100 repo” başlığını taşıyor; kullanıcı tarafından sağlanan ve kaynak
gönderide görünen bölüm **40 bağlantı** içeriyor. Bağlantıların tamamı gerçek
hedeflerine çözüldü. Bunların biri Anthropic organizasyon sayfası, 39'u repo
bağlantısıdır.

- 40 bağlantı çözüldü.
- 6 repo verilen kimlikle bulunamadı.
- 2 erişilebilir repo arşivlenmiş durumda.
- 3 bağlantı yeni bir kanonik ada yönleniyor; bir bağlantı aynı kanonik repoyu
  ikinci kez gösteriyor.
- Yalnızca 8 öğe doğrudan skill/plugin veya bunların dizini niteliğinde.
- Geri kalanlar ajan framework'ü, SDK, uygulama, UI şablonu, araştırma kodu veya
  organizasyon kataloğu; bunları “Claude firmware'i” diye kurmak kategori
  hatası olur.

## Uygulanan karar

Toplu kurulum yapılmadı. Divan'ın gerçek eksiği olan kaynak kürasyonu için
özgün `kaynak-kuratori` skill'i eklendi. Bu skill kısa bağlantı çözümü, repo
türü sınıflandırması, lisans/yürütme yüzeyi kapıları, mevcut yeteneklerle
çakışma ve `ADOPT / ADAPT / REFERENCE / REJECT` kararlarını zorunlu kılar.

### Yüksek değerli adaylar

| Kaynak | Tür | Doğrulanan lisans sinyali | Divan kararı | Gerekçe |
|---|---|---|---|---|
| `anthropics/skills` | Resmî skill koleksiyonu | Alt dizin bazlı; tek kök lisans yok | MEVCUT | Divan zaten açık lisanslı seçili skill'leri kaynak kaydıyla taşıyor |
| `anthropics/claude-plugins-official` | Resmî plugin pazarı | Apache-2.0 kök lisans | REFERENCE | Tüm pazarı vendoring yerine ihtiyaç halinde seçili plugin |
| `anthropics/knowledge-work-plugins` | Bilgi işi plugin'leri | Apache-2.0 kök lisans | REFERENCE | Work'teki Slack, Figma, GitHub ve veri eklentileriyle büyük ölçüde örtüşüyor |
| `hesreallyhim/awesome-claude-code` | Dizin | CC BY-NC-ND 4.0 | REFERENCE | Türev ve ticari kullanım kısıtlı; içerik kopyalanmaz |
| `quemsah/awesome-claude-plugins` | Dizin | Kök lisans bulunamadı | REJECT COPY | Keşif için okunabilir; yeniden dağıtım yapılmaz |
| `sickn33/antigravity-awesome-skills` | Dizin; `agentic-awesome-skills` adına taşınmış | Kök lisans bulunamadı | REJECT COPY | Ad değişmiş; lisans kapısı geçilmedi |
| `VoltAgent/awesome-agent-skills` | Dizin | MIT | REFERENCE | Dizin lisansı, bağlantılı hedeflerin lisansı değildir; hedefler tek tek denetlenir |
| `alirezarezvani/claude-skills` | Skill koleksiyonu | MIT | REFERENCE | Geniş kapsamın çoğu mevcut Divan/Work yetenekleriyle örtüşüyor |
| `upstash/context7` | Dokümantasyon/MCP altyapısı | MIT | PROJECT OPTION | Genel skill değil; somut projede canlı kütüphane dokümanı gerektiğinde değerlendirilir |

## Tam bağlantı dökümü

| # | Çözülen hedef | Sınıf | Durum / karar |
|---:|---|---|---|
| 1 | `anthropics/claude-code` | Ürün/ajan | REFERENCE; Divan'a vendoring yok |
| 2 | `anthropics/claude-quickstarts` | Başlangıç uygulamaları | PROJECT OPTION |
| 3 | `anthropics/skills` | Skill koleksiyonu | Seçili açık lisanslı içerik zaten mevcut |
| 4 | `anthropics/claude-plugins-official` | Plugin pazarı | REFERENCE |
| 5 | `github.com/orgs/anthropics/repositories` | Organizasyon kataloğu | DISCOVERY ONLY |
| 6 | `hesreallyhim/awesome-claude-code` | Dizin | REFERENCE; kopyalama yok |
| 7 | `quemsah/awesome-claude-plugins` | Dizin | Kök lisans yok; REJECT COPY |
| 8 | `sickn33/agentic-awesome-skills` | Dizin | Taşınmış; kök lisans yok; REJECT COPY |
| 9 | `VoltAgent/awesome-agent-skills` | Dizin | REFERENCE; hedef lisansı ayrı |
| 10 | `alirezarezvani/claude-skills` | Skill koleksiyonu | REFERENCE; yüksek örtüşme |
| 11 | `langchain-ai/langchain` | LLM framework | PROJECT OPTION |
| 12 | `langchain-ai/langgraph` | Ajan workflow framework | PROJECT OPTION |
| 13 | `microsoft/autogen` | Çok ajan framework | PROJECT OPTION; native orkestrasyonun yerine alınmadı |
| 14 | `crewAIInc/crewAI` | Çok ajan framework | PROJECT OPTION; native orkestrasyonun yerine alınmadı |
| 15 | `metaGPT/metaGPT` | Ajan framework | Verilen hedef bulunamadı; REJECT |
| 16 | `AntonOsika/gpt-engineer` | Kod ajanı | Taşınmış ve arşivli; REJECT |
| 17 | `sweepai/sweep` | PR otomasyon ürünü | REFERENCE; GitHub akışlarıyla örtüşüyor |
| 18 | `continue-repl/continue` | Kod asistanı | Verilen hedef bulunamadı; REJECT |
| 19 | `BloopAI/bloop` | Kod arama uygulaması | Arşivli; Divan'da `arama-ustasi` mevcut; REJECT |
| 20 | `agentprotocol/agentprotocol` | Ajan standardı | Verilen hedef bulunamadı; REJECT |
| 21 | `anthropics/knowledge-work-plugins` | Plugin koleksiyonu | REFERENCE; bağlı Work eklentileriyle örtüşüyor |
| 22 | `vercel/ai` | AI SDK | PROJECT OPTION; Work'te uzman eklenti mevcut |
| 23 | `upstash/context7` | Dokümantasyon/MCP | PROJECT OPTION |
| 24 | `fixie-ai/ultravox` | Ses ajanı altyapısı | PROJECT OPTION |
| 25 | `superagent-ai/superagent` | Ajan altyapısı | PROJECT OPTION |
| 26 | `xlang-ai/OpenAgents` | Ajan framework | PROJECT OPTION |
| 27 | `ysymyth/ReAct` | Araştırma/referans kodu | REFERENCE |
| 28 | `mem0ai/mem0` | Bellek altyapısı | PROJECT OPTION; Divan proje hafızasıyla aynı katman değil |
| 29 | `helixml/helix` | AI uygulama altyapısı | PROJECT OPTION |
| 30 | `trpc/trpc` | API kütüphanesi | PROJECT OPTION; Claude skill'i değil |
| 31 | `ChatGPTNextWeb/NextChat` | UI uygulaması | PROJECT OPTION |
| 32 | `open-webui/open-webui` | UI uygulaması | PROJECT OPTION |
| 33 | `mckaywrigley/chatbot-ui` | UI uygulaması | PROJECT OPTION |
| 34 | `lencx/ChatGPT` | Masaüstü uygulama | PROJECT OPTION |
| 35 | `Nutlope/chatGPT-clone` | UI şablonu | Verilen hedef bulunamadı; REJECT |
| 36 | `vercel/chatbot` | UI şablonu | `vercel-labs/ai-chatbot` adresinden taşınmış; PROJECT OPTION |
| 37 | `ChatGPTNextWeb/NextChat` | UI uygulaması | #31 ile aynı kanonik repo; DUPLICATE |
| 38 | `ivanfioravanti/chatbot-ui` | UI uygulaması | PROJECT OPTION |
| 39 | `louislam/ChatGPT-web` | UI uygulaması | Verilen hedef bulunamadı; REJECT |
| 40 | `zk-ml/chatglm-web` | UI uygulaması | Verilen hedef bulunamadı; REJECT |

## Kanıt sınırları

- Arşiv, erişilebilirlik ve kanonik adlar GitHub repository metadata'sından
  2026-07-18 tarihinde doğrulandı.
- Lisans metni yalnızca benimseme adayı olan kaynaklarda okundu. “Project
  option” satırları için bu rapor bir lisans onayı değildir; somut kullanım
  öncesi yeniden denetim gerekir.
- Bu liste benchmark değildir. Hız, gelir veya kalite artışı iddialarını
  destekleyen tekrarlanabilir karşılaştırma sunmadığı için bu iddialar Divan'a
  taşınmadı.

Kaynak gönderi: https://x.com/HeyZaraKhan/status/2057161326548377891
