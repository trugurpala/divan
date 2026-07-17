# Stack 2026 — Konsensüs Tablosu

**Son güncelleme: 2026-07-17** · 6 aydan eskiyse önermeden önce web'de doğrula.

| Katman | 2026 varsayılanı | Savunulabilir alternatif | Neden |
|---|---|---|---|
| Framework | Next.js (App Router) + React 19 + TS | Astro (içerik), SvelteKit | Ekosistem + Vercel entegrasyonu; boilerplate pazarının tamamı burada |
| Stil | Tailwind 4 + shadcn/ui (+Radix) | - | Kompozisyon + erişilebilirlik + hız üçlüsü fiili standart |
| Veritabanı | Postgres (Supabase) | Neon; ölçekte self-hosted | Auth+storage+realtime+RLS tek serviste; çıkış yolu açık (Supabase=Postgres) |
| ORM | Drizzle | Prisma (ekip biliyorsa) | SQL-yakın, hafif, edge-uyumlu; karmaşık join/window'da üstün |
| Auth | Better Auth; Supabase'deysen Supabase Auth | Clerk (en hızlı MVP, B2C) | Kullanıcı verisi kendi Postgres'inde; org/passkey/RBAC eklentili; kullanıcı-başı fiyat cezası yok |
| Ödeme | Stripe | Lemon Squeezy / Paddle / Polar (MoR) | Altın standart; vergi derdinde MoR'a geç |
| Hosting | Vercel | Cloudflare | Sıfır-config Next.js; ücretsiz katman MVP taşır |
| E-posta | Resend | Postmark, SES (hacim) | React email şablonları + DX |
| Mobil | Expo (React Native) | - | Tek kod, mağaza dağıtımı; RevenueCat ödeme |
| AI | Vercel AI SDK + Claude API; pgvector | - | Ayrı vektör DB kurma: aynı Postgres, tek yedek |
| İzleme | Sentry + PostHog | - | Hata + ürün analitiği ücretsiz katmanla |

## Ücretsiz başlangıç noktaları
- nextjs/saas-starter (resmî Next.js ekibi; Postgres+Drizzle+Stripe+shadcn, MIT)
- create-t3-app (MIT, ~29K yıldız; tRPC+Prisma/Drizzle seçmeli)

## Kaynak izleri (tazelerken tekrar bak)
makerkit.dev/blog/saas/saas-stack-2026 · supastarter.dev/blog/best-saas-stack ·
marsdevs.com best-tech-stack-2026 · State of JS anketi · Next.js/Tailwind release notları

## Tazeleme ritüeli
Çeyrekte bir: yukarıdaki kaynakları tara, tabloyu güncelle, "Son
güncelleme" tarihini değiştir, BLUEPRINT durum günlüğüne not düş.
