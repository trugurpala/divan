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
| sadrazam, defterdar, müşavir, ordu-nizamı, vezir-yetiştirme, temkin, kaynak-küratörü | özgün (bu repo) | MIT | — |

## Güncelleme ve nöbet politikası

- Üst kaynaklar körlemesine eşitlenmez; anlamlı iyileştirmeler lisans ve ürün
  değeri açısından incelenerek taşınır.
- `scripts/upstream-denetim.py` her vendored klasörü SHA-256 ile iki yönlü
  karşılaştırır: upstream'e eklenen/silinen ve Divan'a eklenen/silinen dosyalar
  birlikte görünür.
- Bilinçli yamaların upstream taban imzası sabitlenir. Upstream aynı dosyayı
  değiştirirse izin listesi farkı gizlemez.
- İncelenmiş drift kararları `registry/upstream-baselines.json` içinde kaynak
  commit'i, yerel ağaç SHA-256'sı, değişen dosyalar ve gerekçeyle tutulur. Kaynak
  HEAD veya yerel ağaç değişirse karar otomatik olarak yeniden açılır.
- Kural Hazinesi birebir bir skill kopyası değildir; dokuz CC0 kuralın
  kürasyonudur. Bu nedenle kaynak deponun commit'i ayrıca izlenir ve ilerlediğinde
  yeniden kürasyon için raporlanır.
- Bağlam Muhafızı, MIT kaynak koleksiyonundaki context-optimization fikirlerinin
  Divan'ın defterdar/ordu düzenine uyarlanmış özgün Türkçe iş akışıdır; kaynak
  commit'i kör eşitleme yerine yeniden kürasyon için izlenir.
- Dağıtılan ve kürasyon girdisi olan bütün upstream commit pinlerinin tek
  kanonik makine-okunur kaynağı `registry/upstream-baselines.json` dosyasındaki
  `sources` listesidir; drift denetimi ve SPDX üretimi aynı listeyi kullanır.
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
| UYARLANDI | “100 Claude Repos” sosyal listesi (40 sağlanan bağlantı) | İçerik kopyalanmadı | Bağlantılar kimlik, durum ve tür açısından denetlendi; özgün `kaynak-kuratori` iş akışı yazıldı |

## Upstream drift incelemesi (2026-07-19)

Güncel kaynak HEAD'lerinde 15 vendored skill farkı yeniden üretildi ve her biri
ayrı kayda bağlandı. Bu sürümde hiçbir upstream dosya otomatik kopyalanmadı;
tamamının kararı `KEEP` (mevcut doğrulanmış Divan sürümünü koru) oldu.

| Kaynak | İncelenen commit | Skill sayısı | Karar | Ana gerekçe |
|---|---|---:|---|---|
| obra/superpowers | `d884ae04edebef577e82ff7c4e143debd0bbec99` | 13 | KEEP | Yeni prompt, harness ve referanslar davranış eval'i olmadan alınmadı |
| vercel-labs/agent-skills | `f8a72b9603728bb92a217a879b7e62e43ad76c81` | 1 | KEEP | Yerel bağlantı yaması bütün kurallarda yeniden doğrulanmayı bekliyor |
| anthropics/skills | `fa0fa64bdc967915dc8399e803be67759e1e62b8` | 1 | KEEP | Claude API açıklamasının Agent Skills şema yaması korunuyor |

Superpowers kayıtları: `brainstorming`, `dispatching-parallel-agents`,
`executing-plans`, `finishing-a-development-branch`, `receiving-code-review`,
`requesting-code-review`, `subagent-driven-development`,
`systematic-debugging`, `test-driven-development`, `using-git-worktrees`,
`verification-before-completion`, `writing-plans` ve `writing-skills`.
Dosya bazlı gerekçe, değişim listesi ve yerel SHA-256 kanıtı
`registry/upstream-baselines.json` içindedir.

## GitHub Actions incelemesi (2026-07-21)

Bu Actions kaynakları depoya kopyalanmaz; yalnız aşağıdaki incelenmiş tam commit
SHA'larıyla GitHub üzerinde çalıştırılır. SHA, kaynak lisansı ve job izinleri
birlikte incelenmeden pin güncellenmez.

| Kaynak | Tam commit SHA | Amaç | Lisans | Karar ve izin sınırı |
|---|---|---|---|---|
| ossf/scorecard-action | `4eaacf0543bb3f2c246792bd56e8cdeffafb205a` | OpenSSF Scorecard SARIF ve doğrulanmış sonuç yayını | Apache-2.0 | KULLAN; yalnız `contents: read`, SARIF için `security-events: write`, sonuç imzası için `id-token: write` |
| actions/dependency-review-action | `a1d282b36b6f3519aa1f3fc636f609c47dddb294` | Pull request bağımlılık ve lisans farkı kapısı | MIT | KULLAN; yalnız `contents: read`, PR yorumu yazma yok |
| actions/attest-build-provenance | `0f67c3f4856b2e3261c31976d6725780e5e4c373` | Release ZIP ve SPDX SBOM build provenance | MIT | KULLAN; yalnız publish job'unda `id-token`, `attestations` ve v4 storage record sözleşmesi için `artifact-metadata: write` |

`actions/attest-build-provenance` v4.1.1, aynı sürümdeki `actions/attest`
eylemini çağıran resmî bir composite wrapper'dır. Yeni kurulumda doğrudan
`actions/attest` önerilse de onaylı planın immutable wrapper pini korunmuştur;
v4'ün güncel `artifact-metadata: write` gereksinimi dar job izni olarak eklenmiştir.
