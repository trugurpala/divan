# Divan — Blueprint

> **Tek gerçek kaynak.** Bu dosyayı okuyan herhangi bir ajan (Claude Code, Cursor,
> Codex) veya insan, projeyi kaldığı yerden sürdürebilir. Sohbet geçmişine
> bağımlılık yoktur; plan burada yaşar.

## Vizyon

Divan, vibe coder'ın vezirler kuruludur. **Padişah = kullanıcı.** Padişah ferman
verir; Sadrazam (orkestratör skill) ve vezir paketleri işi baştan sona,
doğrulanmış şekilde bitirir. Hedef kitle: AI ajanlarıyla ürün geliştiren,
disiplin katmanını hazır isteyen geliştiriciler.

## Mimari kararlar (ADR)

1. **Neden Skill/Plugin, neden MCP değil:** Ürün prosedürel bilgidir ("nasıl
   yapılır"), canlı veri erişimi değildir. Skill'ler progressive disclosure ile
   token-verimlidir ve Agent Skills açık standardı sayesinde Claude Code,
   Cursor, Codex dahil onlarca ajanda çalışır. MCP, canlı sistem erişimi
   (DB, API) gerektiğinde v2'de eklenir.
2. **Neden uygulama değil (henüz):** Dağıtım GitHub + `/plugin` komutuyla
   sürtünmesizdir. Hosted web uygulaması + ödeme, v2 premium katmandır.
3. **Lisans stratejisi:** Derleme ve özgün skill'ler MIT. Üçüncü taraflar kendi
   lisanslarını korur (THIRD_PARTY_LICENSES.md). Anthropic'in proprietary
   document-skills'i (docx/pdf/pptx/xlsx) asla dahil edilmez.
4. **Marka:** Ürün adında Claude/Anthropic/Superpowers kullanılmaz; yalnızca
   "ile uyumludur" tanımlayıcı ifadesi.

## Standartlar

- **Agent Skills spec** (agentskills.io): her SKILL.md'de frontmatter zorunlu;
  `name` ≤ 64 karakter, `description` ≤ 1024 karakter.
- **CI teftişi:** `scripts/validate.py` her push'ta GitHub Actions ile çalışır
  (JSON geçerliliği, frontmatter, proprietary sızıntı kontrolü).
- **Sayfa kalitesi:** landing sayfası SEO meta + Open Graph + canonical +
  favicon taşır; erişilebilirlik (focus-visible, prefers-reduced-motion) korunur.

## Yol haritası

- **v0.1** ✓ — 4 paket (sadrazam, core, ui, react), 13 skill, landing sayfası, CI
- **v0.2** — Türkçe özgün skill'ler genişler; kalıcı isim/logo kararı; özel domain
- **v0.5** — awesome-claude-skills listelerine PR; topluluk geri bildirimi (dot. linki)
- **v1.0** — kararlı sürüm; dokümantasyon sitesi; demo GIF'li README
- **v2.0** — hosted premium: web uygulaması + MCP entegrasyonları + ödeme (Stripe)

## Durum günlüğü

- 2026-07-16 — v0.1 derlendi: rebrand (Divan), Sadrazam yazıldı, landing yayında,
  lisans hijyeni tamam. GitHub push, geçerli token/yerel push bekliyor.
  Sonraki adım: repo'yu GitHub'a al, `/plugin marketplace add` ile uçtan uca test et.
