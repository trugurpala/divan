# Spec Kit v0.16.4 izole spike ve karar tazelemesi

- Tarih: 2026-08-16
- Aday: `github-spec-kit`
- İncelenen sürüm: `v0.16.4`
- İncelenen commit: `d1f50fcbe684a4222059c4ba7f2d7eabcca87402`
- Lisans: MIT
- Karar: **ADAPT** (mevcut karar korundu, kanıt tazelendi)

## Yöntem

Kanonik checkout'a hiçbir zaman `init` yapılmadı. Depo dışında, tek
kullanımlık bir geçici dizinde pinned tek seferlik çalıştırma kullanıldı:

```text
uvx --from git+https://github.com/github/spec-kit.git@v0.16.4 specify init demo-app --script ps --integration claude --ignore-agent-tools
```

Makineye kalıcı kurulum yapılmadı; `registry/candidates.json` içindeki
`autonomy: never-auto-install` kuralı korundu.

## Önce hafıza

Spike'tan önce aday defterine bakılmalıydı: `github-spec-kit` zaten
`ADAPT` kararıyla kayıtlıydı ve `cf0abe28` commit'inde incelenmişti. Bu
kayıt yeni bir karar değil, daha yeni sürümün doğrulanmasıdır. Bu, memory
first ilkesinin neden kural olması gerektiğinin somut örneğidir.

## Gözlenen yapı

Üretilen ayak izi yalnız iki dizindir ve proje dosyalarına dağılmaz:

| Yüzey | İçerik |
|---|---|
| `.claude/skills/speckit-*` | 10 Agent Skill: constitution, specify, clarify, plan, checklist, tasks, analyze, implement, converge, taskstoissues |
| `.specify/templates` | spec, plan, tasks, checklist, constitution şablonları |
| `.specify/memory` | `constitution.md` ve şablon kaydı |
| `.specify/scripts/powershell` | Windows script varyantı; 6 script |
| `.specify/integration.json` | Claude entegrasyon durumu |
| `.specify/workflows` | `workflow-registry.json` ve bundled `speckit` workflow'u |

## Alınmaya değer kalıplar

- **specification sözleşmesi**: öncelikli kullanıcı hikâyeleri (P1/P2/P3),
  edge case'ler, fonksiyonel gereksinimler, anahtar varlıklar, ölçülebilir
  başarı ölçütleri ve açık varsayımlar.
- **checklist**: gereksinim yazımının birim testi. Doğrulama değil,
  gereksinimin kendisinin netliğini ve tamlığını sınar. Divan'da karşılığı
  yoktu.
- **analyze**: spec, plan ve görev artefaktları arasında yıkıcı olmayan
  tutarlılık raporu. Mandate §11'deki Müşavir plan itirazının tam karşılığı.
- **converge**: kod tabanını spec'e karşı ölçüp kalan işi göreve çevirir.
  "Kod yazıldı" ile "Hazır" arasındaki boşluğu kapatan tamlık eleştirmeni.
- **tasks sözleşmesi**: faz, hikâye grubu, açık bağımlılık ve paralellik
  bölümleri.

## Neden ADOPT değil

`.specify/` kendi `memory/constitution.md`, şablon, entegrasyon ve workflow
kaydını taşır. Bundled `speckit` workflow'u kendi tanımıyla
`specify → plan → tasks → implement with review gates` akışını yürütür.
Bu, Divan Core'un yanında **ikinci bir state ve orkestrasyon otoritesidir**.
Divan'ın tek ürün, tek çekirdek ve tek yetki zinciri sözleşmesiyle
bağdaşmaz. Ayrıca skill'ler `.claude/skills/` altına kurulur ve Divan'ın
kendi skill yüzeyiyle çakışır.

## Uygulanan sınır

- Spec Kit kurulmaz; artefakt sözleşmesi Divan'da bağımsız uygulanır.
- `.specify` state'i kanonik Divan state'i yapılmaz.
- `CLAUDE.md` ve `AGENTS.md` yetkisi değiştirilmez.
- Spec derleyici hiçbir zaman execution veya merge yetkisi almaz.

## Sınır

Bu kayıt lisans, yapı ve yetki sınırı incelemesidir. Kalite artışı, hız
veya benimseme iddiası değildir; upstream kodu kopyalanmamıştır.
