# Durum ve Yol Haritası · v0.12.0

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

## Dürüst açıklar

- Beyan edilmiş gerçek ajan ve hakem adapter'ıyla yayımlanmış A/B sonucu yok.
- Bağımsız kullanıcıdan tekrar üretilebilir benimseme kanıtı yok.
- v0.12.0 tag/Release henüz yayımlanmadı; bu belge release adayı kaynağıdır.
  Son doğrulanmış yayın v0.11.1 ve etiketi `731db9d7` commit'ine bağlıdır.
  v0.12.0 ancak `main` sonrası [Releases sayfasından](https://github.com/trugurpala/divan/releases)
  ve tag API'sinden ayrı ayrı okununca yayımlanmış sayılır.
- GitHub Wiki Git deposu başlatıldı; `wiki-sync` her `main` belge değişiminde 17
  çıktıyı yayımlar ve canlı `Home.md` sürümünü yeniden okur.

## Sıradaki ürün kanıtı

1. v0.12.0 merge/tag/Release/Pages/Wiki ve çift-host global kurulum kanıtı.
2. Gerçek ajan/hakem adapter'ıyla ilk yayımlanabilir kör A/B kanıtı.
3. Sabitlenmiş v0.12.0 release'ini deneyen bağımsız kullanıcı kabul kanıtı.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- En az bir bağımsız, yeniden üretilebilir kullanıcı kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md

Kapıların canlı karnesi: [[v1 Hazırlık Karnesi|V1-Hazirlik]].
