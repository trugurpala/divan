# Durum ve Yol Haritası · v0.12.1

Son doğrulama tarihi: 2026-07-19.

## Şu anda yayımlanan

- 5 paket ve 41 skill.
- Vibe coder için beş niyetli ferman seçici.
- 4 özgün skill / 13 vaka için sağlayıcı-bağımsız kör A/B eval koşucusu;
  Claude gerçek ajanı ve read-only kör Codex hakemi adaptörleri.
- Claude ve Codex için aynı 5 paket/41 skill'i sunan yerel pazarlar ile
  dry-run-first işlemsel çift-host kurucu.
- Yerel teftiş, Agent Skills, iki host pazarı, Claude Code plugin doğrulaması,
  CodeQL, Ruff, mypy, Coverage ve actionlint kapıları.
- Dal önizlemesi ve `main` sonrası canlı GitHub Pages testi.
- Repodaki `docs/*.md` kaynaklarından otomatik GitHub Wiki derleme/yayın kapısı.
- Yapılandırılmış aday formu, makine-okunur Aday Meclisi ve haftalık salt-okunur
  GitHub keşif nöbeti; otomatik kurulum yok.
- Tek komutlu sürüm yüzeyi hazırlığı ve sapma teftişi; `main` sonrası Pages +
  Wiki eşliğinden CHANGELOG kaynaklı tag/GitHub Release'a giden yayın kapısı.
- Claude Code resmî doğrulaması ve Linux/macOS/Windows Codex kur-keşfet-kaldır matrisi.
- UTF-8/LF metin sözleşmesi, locale-bağımsız subprocess çıktısı, McCabe 25
  karmaşıklık bütçesi ve yalnız yeniden üretilebilir cache'leri silebilen
  allowlist tabanlı repo hijyeni.

## Dürüst açıklar

- Bağımsız kullanıcıdan tekrar üretilebilir benimseme kanıtı yok.
- Gerçek Claude/Codex A/B sonucu yayımlandı: skill 0, baseline 1, beraberlik 2.
  Önceden eşik yoktur; kalite artışı iddiası yapılmaz.
- v0.12.0 tag/Release yayımlandı ve `e9a2642e` `main` commit'ine bağlıdır.
  Release arşivi/checksum'u, Pages, Wiki ve iki hosttaki global native kurulum
  `.divan/evidence/teftis-20260719-v012-release-install.md` ile doğrulandı.
- GitHub Wiki Git deposu başlatıldı; `wiki-sync` her `main` belge değişiminde 17
  çıktıyı yayımlar ve canlı `Home.md` sürümünü yeniden okur.

## Sıradaki ürün kanıtı

1. v0.12.1 merge/tag/Release/Pages/Wiki ve çift-host global kurulum kanıtı
   `main` teslimini bekliyor.
2. ✓ Gerçek ajan/hakem adapter'ıyla ilk yayımlanabilir kör A/B kanıtı.
3. Sabitlenmiş v0.12.0 release'ini deneyen bağımsız kullanıcı kabul kanıtı.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- En az bir bağımsız, yeniden üretilebilir kullanıcı kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md

Kapıların canlı karnesi: [[v1 Hazırlık Karnesi|V1-Hazirlik]].
