# Kaynak Politikası (Neden Fork Değil?)

Claude Code marketplace'i tek repo okur. Divan bu nedenle seçili skill'leri,
lisans ve telif bilgilerini koruyarak bu çatı altında vendoring yöntemiyle
dağıtır. MIT, Apache-2.0 ve CC0 koşulları `THIRD_PARTY_LICENSES.md` içinde
izlenir; lisansı belirsiz içerik alınmaz.

## Kaynak tablosu

| Paket | Üst kaynak | Lisans | Alınma |
|---|---|---|---|
| core-pack | github.com/obra/superpowers | MIT | 2026-07 |
| core-pack/kural-hazinesi | github.com/PatrickJS/awesome-cursorrules | CC0-1.0 | 2026-07 |
| core-pack/baglam-muhafizi | github.com/muratcankoylan/Agent-Skills-for-Context-Engineering | MIT | 2026-07 |
| core-pack/arama-ustasi | özgün; ripgrep ve ast-grep resmî belgeleri | MIT | — |
| ui-pack (frontend-design, webapp-testing) | github.com/anthropics/skills | Apache-2.0 | 2026-07 |
| ui-pack (ui-ux-pro-max) | github.com/nextlevelbuilder/ui-ux-pro-max-skill | MIT | 2026-07 |
| react-pack | github.com/vercel-labs/agent-skills | MIT | 2026-07 |
| zanaat-pack | github.com/anthropics/skills | Apache-2.0 | 2026-07 |
| sadrazam, defterdar, müşavir, ordu-nizamı, vezir-yetiştirme, temkin | özgün (bu repo) | MIT | — |

## Güncelleme ve nöbet politikası

- Üst kaynaklar körlemesine eşitlenmez; anlamlı iyileştirmeler lisans ve ürün
  değeri açısından incelenerek taşınır.
- `scripts/upstream-denetim.py` her vendored klasörü SHA-256 ile iki yönlü
  karşılaştırır: upstream'e eklenen/silinen ve Divan'a eklenen/silinen dosyalar
  birlikte görünür.
- Bilinçli yamaların upstream taban imzası sabitlenir. Upstream aynı dosyayı
  değiştirirse izin listesi farkı gizlemez.
- Kural Hazinesi birebir bir skill kopyası değildir; dokuz CC0 kuralın
  kürasyonudur. Bu nedenle kaynak deponun commit'i ayrıca izlenir ve ilerlediğinde
  yeniden kürasyon için raporlanır.
- Bağlam Muhafızı, MIT kaynak koleksiyonundaki context-optimization fikirlerinin
  Divan'ın defterdar/ordu düzenine uyarlanmış özgün Türkçe iş akışıdır; kaynak
  commit'i kör eşitleme yerine yeniden kürasyon için izlenir.
- Anthropic'in proprietary lisanslı docx/pdf/pptx/xlsx skill'leri alınmaz.

## Bilinçli yamalar

| Dosya | Fark | Gerekçe |
|---|---|---|
| `zanaat-pack/skills/claude-api/SKILL.md` | `description` kısaltıldı | Upstream açıklaması 1024 karakter sınırını aşıyor; gövde ve referanslar korunuyor |
| `react-pack/skills/vercel-react-best-practices/AGENTS.md` | Üç göreli bağlantıya `rules/` eklendi | Upstream derleme belgesindeki üç bağlantı gerçek dosya konumuna gitmiyordu |

Vercel'in `<ViewTransition>` ve `<file-or-pattern>` değerleri upstream ile aynı
tutulur. Agent Skills standardı açılı ayraçları genel olarak yasaklamaz.

## Kürasyon kararları (2026-07-17)

| Karar | Kaynak | Lisans | Not |
|---|---|---|---|
| ALINDI | PatrickJS/awesome-cursorrules | CC0-1.0 | Dokuz kural `kural-hazinesi/references/` altında |
| UYARLANDI | muratcankoylan/Agent-Skills-for-Context-Engineering | MIT | Context bütçesi ve maskeleme ilkeleri özgün `baglam-muhafizi` akışına uyarlandı |
| KOPYALANMADI | massgen/MassGen file-search | Repo Apache-2.0; skill metadata MIT | Lisans metadata farkı nedeniyle metin taşınmadı; `arama-ustasi` resmî araç belgelerinden özgün yazıldı |
| REDDEDİLDİ | multica-ai/andrej-karpathy-skills | Lisans yok | Popülerlik yeniden dağıtım hakkı vermez; yerine özgün `temkin` yazıldı |
| KEŞİF KAYNAĞI | VoltAgent/awesome-agent-skills | MIT | Dizin niteliğinde; alınacak her hedefin lisansı ayrıca incelenir |
