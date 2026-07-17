# Divan — Blueprint

> Tek gerçek kaynak. Bu dosyayı okuyan herhangi bir ajan veya insan,
> projeyi kaldığı yerden sürdürebilir. Sohbet geçmişine bağımlılık yoktur.

## Vizyon
Padişah (kullanıcı) fermanı verir; Divan (skill paketleri) işi baştan sona,
kanıtıyla bitirir. Hedef kitle: AI ajanlarıyla üretim yapan vibe coder'lar.

## Mimari Kararlar (ADR)
1. **Neden skill/plugin, neden MCP değil:** Ürün prosedürel bilgidir (nasıl
   yapılır). Skill'ler progressive disclosure ile token-verimlidir ve Agent
   Skills açık standardı sayesinde Claude Code, Cursor, Codex ve 30+ ajanda
   çalışır. MCP canlı veri/aksiyon içindir; ihtiyaç doğduğunda (v2) eklenir.
2. **Neden uygulama değil (henüz):** Dağıtım GitHub + `/plugin` komutuyla
   sıfır altyapı maliyetiyle çalışır. Hosted web uygulaması, ödeme ve premium
   içerik v2'nin işidir.
3. **Lisans stratejisi:** Derleme ve özgün skill'ler MIT. Üçüncü taraf
   skill'ler kendi lisanslarını korur (THIRD_PARTY_LICENSES.md). Anthropic'in
   proprietary document-skills'i (docx/pdf/pptx/xlsx) ASLA dahil edilmez.

## Standartlar
- Agent Skills açık standardı (agentskills.io): SKILL.md frontmatter,
  name ≤ 64, description ≤ 1024 karakter.
- Her push'ta CI teftişi: `scripts/validate.py` (JSON geçerliliği, frontmatter,
  proprietary sızıntı, placeholder kontrolü).
- Tarayıcı testi kullanıcı tarafında: ui-pack'teki `webapp-testing` skill'i
  (Playwright) ile.

## v0.6 Vendoring Hedef Listesi (keşif raporu, 2026-07-17)
Öncelik sırasıyla; her biri alınmadan önce LICENSE dosyası bizzat okunacak:
1. Karpathy-skills (100K+ yıldız fenomen, tek CLAUDE.md, 4 ilke) — lisans DOĞRULANACAK
2. VoltAgent/awesome-agent-skills'ten seçme (20K yıldız, 1000+ skill; tek tek lisans bak)
3. Remotion best-practices (video üretimi — vibe coder talebi yüksek)
4. Caveman (çıktı-token kısıcı; fatura dostları için)
5. android/skills + Expo skill (mobil ordu)
YASAK: sızdırılmış system-prompt depoları (x1xhlol vb.) — lisanssız + etik dışı, popülerliği fark etmez.

## Yol Haritası
- **v0.1 ✓** 4 paket, 13 skill, landing page, CI, teftiş
- **v0.2** Özgün Türkçe skill'ler, kalıcı domain, README demo GIF, logo
- **v0.5** awesome-claude-skills listelerine PR, topluluk geri bildirimi
- **v1.0** Kararlı sürüm + dokümantasyon
- **v2.0** Hosted premium: web app + MCP + ödeme (Stripe)

## Durum Günlüğü
- 2026-07-17k: Keşif raporu işlendi — MÜŞAVİR veziri (stack danışmanı: proje türüne göre 2026 varsayılanları + tazelik protokolü) ve AYLIK NÖBET (upstream değişim bekçisi: cron + otomatik issue) eklendi. v0.6 vendoring hedef listesi BLUEPRINTe girdi. 35 vezir.
- 2026-07-17j: SEFERBERLİK — ordu 15ten 34 vezire çıktı: core-pack +7 (superpowers MIT), yeni zanaat-pack 7 (Anthropic Apache, Ehl-i Hiref), react-pack +5 (Vercel MIT). Teftiş 2 upstream spec ihlali daha yakalayıp onardı; 4 yama UPSTREAM.mdde belgeli. 5 paket.
- 2026-07-17i: Codex tek-komut kurulum scriptleri (kur-codex.ps1 Windows / kur-codex.sh unix) eklendi; git gerektirmez (zip indirir). Kurulum belgesi güncellendi.
- 2026-07-17h: Canlı upstream denetimi — 12 taşınan vezirin 12si bugünkü kaynaklarla birebir (tek fark bilinçli spec yaması, UPSTREAM.md tablosunda belgeli). Komut/subagent çakışması yok. docs/Kaldirma.md (komple kaldırma rehberi) eklendi.
- 2026-07-17g: 8-katman karnesine göre eksikler kapandı - subagents (kâşif: keşif öncüsü, müfettiş: bağımsız denetçi) ve hooks (SessionStart: defteri otomatik oku) eklendi; teftiş v3 bunları da denetliyor; docs uyumluluk matrisi. Sadrazam v0.4.0.
- 2026-07-17f: Hafıza katmanı geldi — defterdar skill'i (AGENTS.md+BLUEPRINT+.divan/ nizamı, 4 şablon), /defter komutu, Sadrazam'a zorunlu kayıt nizamı, para-dokunan işlere spec-first+risk-register kuralı. Sadrazam v0.3.0. Dünya standardı boşluk analizi raporuna dayanır.
- 2026-07-17e: Akıl sayfaları (Değer, GitHub Kullanımı, Test ve Teftiş) docs/ altına; gerçek Playwright testi tests/site_testi.py yazıldı, canlıda TEMİZ geçti; haftalık site-testi CI eklendi. Wiki push GitHub kısıtı yüzünden bekliyor (ilk sayfa UI ister).
- 2026-07-17d: İlk vizyondaki komutlar tamamlandı (/ferman, /vezir, /teftis); GitHub Pages, Discussions, issue etiketleri açıldı. Upstream tamlık doğrulandı (birebir).
- 2026-07-16: v0.1 derlendi (vibeforge → Divan rebrand, Sadrazam yazıldı,
  landing yayında). GitHub push token bekliyor.
- 2026-07-17c: Teftiş v2 (spec tam denetim) 3 gerçek kusur yakaladı: 2 Vercel skill klasör-ad uyuşmazlığı (yüklenmiyordu, düzeltildi), 1 frontmatter <> ihlali (düzeltildi). Wiki içeriği docs/ altında; GitHub wiki ilk sayfa açılınca aynalanacak.
- 2026-07-17b: Topluluk dosyaları (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, şablonlar), UPSTREAM.md ve vezir-yetistirme meta-skill eklendi.
- 2026-07-17: Teftiş script'i + CI + BLUEPRINT eklendi. SEO güncellemesi
  site/index.html'de hazır; push sonrası canlıya alınacak.
