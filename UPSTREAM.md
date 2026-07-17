# Kaynak Politikası (Neden Fork Değil?)

Claude Code marketplace'i **tek repo** olmak zorundadır: `/plugin marketplace add`
tek bir depoyu okur. Dört ayrı fork, tek kurulum komutu oluşturamaz. Bu yüzden
Divan **vendoring** yapar: seçili skill'ler, lisans ve telif bilgileri korunarak
bu çatı altına kopyalanır. Bu, MIT/Apache-2.0 lisanslarının açıkça izin verdiği
bir yöntemdir (bkz. THIRD_PARTY_LICENSES.md).

## Kaynak tablosu

| Paket | Üst kaynak | Lisans | Alınma |
|---|---|---|---|
| core-pack | github.com/obra/superpowers | MIT | 2026-07 |
| ui-pack (frontend-design, webapp-testing) | github.com/anthropics/skills | Apache 2.0 | 2026-07 |
| ui-pack (ui-ux-pro-max) | github.com/nextlevelbuilder/ui-ux-pro-max-skill | MIT | 2026-07 |
| react-pack | github.com/vercel-labs/agent-skills | MIT | 2026-07 |
| sadrazam | özgün (bu repo) | MIT | — |

## Güncelleme politikası
- Üst kaynaklar dönemsel olarak elle gözden geçirilir; anlamlı iyileştirmeler
  seçilerek taşınır (körlemesine sync yok — Divan küratörlüdür).
- Her güncelleme `scripts/validate.py` teftişinden geçmek zorundadır.
- Anthropic'in proprietary lisanslı skill'leri (docx/pdf/pptx/xlsx) hiçbir
  koşulda alınmaz.

## Bilinçli yamalar (upstream'den kasıtlı farklar)
| Dosya | Fark | Gerekçe |
|---|---|---|
| react-pack/skills/web-design-guidelines/SKILL.md | frontmatter `argument-hint` değerindeki açılı ayraçlar kaldırıldı | Agent Skills spec'i frontmatter'da açılı ayracı yasaklar (prompt injection önlemi); teftiş v2+ bunu hata sayar |

Denetim usulü: `/tmp`'ye taze upstream klonu çek, vendored dizinle md5
kıyasla; fark = ya upstream güncellemesi (kürasyonla al) ya bilinçli yama
(bu tabloda belgeli olmalı). Tabloda olmayan fark teftiş konusudur.

## Seferberlik genişlemesi (2026-07-17)
| Paket | Yeni vezirler | Kaynak | Lisans |
|---|---|---|---|
| core-pack (+7) | dispatching-parallel-agents, finishing-a-development-branch, receiving/requesting-code-review, subagent-driven-development, using-git-worktrees, writing-skills | obra/superpowers | MIT |
| zanaat-pack (yeni, 7) | algorithmic-art, canvas-design, claude-api, mcp-builder, slack-gif-creator, theme-factory, web-artifacts-builder | anthropics/skills | Apache 2.0 (LICENSE.txt doğrulandı; docx/pdf/pptx/xlsx proprietary — ALINMADI) |
| react-pack (+5) | deploy-to-vercel, vercel-react-native-skills, vercel-react-view-transitions, vercel-optimize, writing-guidelines | vercel-labs/agent-skills | MIT |

Ek bilinçli yamalar: writing-guidelines ve vercel-react-view-transitions
frontmatter'ından açılı ayraçlar kaldırıldı (spec); react-view-transitions ve
react-native-skills klasörleri name alanıyla eşitlendi (spec: klasör=name).
