# Divan — Claude Code devralma sözleşmesi

Bu depo sohbet geçmişinden bağımsız yürütülür. Bir göreve başlamadan önce:

1. `AGENTS.md` — bağlayıcı çalışma, teftiş ve yayın kuralları.
2. `BLUEPRINT.md` — ürün yönü, mimari kararlar ve sürüm geçmişi.
3. `.divan/progress.md` — gerçek mevcut durum ve sıradaki kesin adım.
4. Yayında `release-manifest.json` ve `registry/v1-gates.json`.

## Değişmez emirler

- Kullanıcının eski konuşmaları hatırlatmasını bekleme; karar ve ilerlemeyi aynı
  turda kalıcı kayıtlara işle.
- README, katalog, Wiki kaynağı, Pages/site, CHANGELOG ve Release ürün
  yüzeyleridir. Ürünü değiştiren işte `AGENTS.md` kurallarını uygula.
- Lisansı doğrulanmamış içeriği kopyalama; popülerlik güven kanıtı değildir.
- Kanıt görmeden “bitti”, “main'de”, “canlı” veya “release yayımlandı” deme.
- v1 için gereken dış kanıtı üretme veya varsayma.

Önce `python scripts/handoff.py --check` çalıştır. Teslimden önce `AGENTS.md`
içindeki bütün doğrulama komutlarını çalıştır. Yayında `/yayin` veya
`python scripts/release.py` akışını kullan; PR, `main`, Wiki/Pages, tag ve GitHub
Release durumlarını ayrı ayrı doğrula.
