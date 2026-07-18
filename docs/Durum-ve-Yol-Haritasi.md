# Durum ve Yol Haritası · v0.11.1

Son doğrulama tarihi: 2026-07-18.

## Şu anda yayımlanan

- 5 paket ve 41 skill.
- Vibe coder için beş niyetli ferman seçici.
- 4 özgün skill / 13 vaka için sağlayıcı-bağımsız kör A/B eval koşucusu.
- Yerel teftiş, Agent Skills doğrulaması, Claude Code plugin doğrulaması.
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
- v0.11.1 tag/Release yayımlandı; etiket `5680337a` commit'ine bağlıdır ve
  [Releases sayfası](https://github.com/trugurpala/divan/releases/tag/v0.11.1)
  sabit kurulumun tek doğru kanıtıdır.
- GitHub Wiki Git deposu başlatıldı; `wiki-sync` her `main` belge değişiminde 17
  çıktıyı yayımlar ve canlı `Home.md` sürümünü yeniden okur.

## Sıradaki ürün kanıtı

1. Gerçek ajan/hakem adapter'ıyla ilk yayımlanabilir kör A/B kanıtı.
2. Sabitlenmiş v0.11.1 release'ini deneyen bağımsız kullanıcı kabul kanıtı.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- En az bir bağımsız, yeniden üretilebilir kullanıcı kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md

Kapıların canlı karnesi: [[v1 Hazırlık Karnesi|V1-Hazirlik]].
