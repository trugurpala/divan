# Durum ve Yol Haritası · v0.10.2

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

## Dürüst açıklar

- Beyan edilmiş gerçek ajan ve hakem adapter'ıyla yayımlanmış A/B sonucu yok.
- Claude Code ve Codex temiz-makine kurulum matrisi henüz otomatik değil.
- Bağımsız kullanıcıdan tekrar üretilebilir benimseme kanıtı yok.
- v0.10.2 için etiketli GitHub release, ayrıca oluşturulana kadar yoktur.
- GitHub Wiki Git deposu ilk sayfa arayüzde bir kez kaydedilene kadar canlı Wiki
  yayını 404 verir; kaynak/CI hazır olsa da “Wiki canlı güncel” değildir.

## v0.11.0 sırası

1. Claude Code + Codex temiz-ortam kurulum, keşif ve kaldırma matrisi.
2. Gerçek ajan/hakem adapter'ıyla ilk yayımlanabilir kör A/B kanıtı.
3. Her yayın öncesi VERSION, marketplace, tag ve release notes eşliği.
4. Ölçülebilir dış kullanıcı kabul formu ve issue akışı.

## v1.0 kapıları

- Kararlı public skill/command sözleşmesi.
- Başarısız davranış eval'inde yayını durduran gerçek-agent kapısı.
- En az bir bağımsız, yeniden üretilebilir kullanıcı kanıtı.
- Etiketli release, sabitlenebilir kurulum ve geri alma tatbikatı.

Kararların ayrıntılı kaynağı:
https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md
