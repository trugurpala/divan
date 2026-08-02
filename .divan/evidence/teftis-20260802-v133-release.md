# v1.3.3 yayın teftişi

- Version: v1.3.3
- Source commit: d65c36c22c4d4c3f27bd892d2cf56f34e551ad57

## Sonuç

v1.3.3 değişmez etiketi ve GitHub Release'i yayımlandı. Release taslak veya
ön sürüm değildir.

## Kanıt

- Ana dal commit'i: `d65c36c22c4d4c3f27bd892d2cf56f34e551ad57`
- Release: https://github.com/trugurpala/divan/releases/tag/v1.3.3
- Release workflow: `30755947059` — başarılı
- Release kapıları: Ubuntu, macOS ve Windows Codex — başarılı
- Yayın kapıları: yerel yayın, şema, Pages/Wiki senkronu, Chromium Pages,
  sürüm eşitleme, attestation ve değişmez Release doğrulaması — başarılı
- Main quality gate: `30755947067` — başarılı
- Main Pages deployment: `30755946549` — başarılı
- Main Wiki sync, site tests, compatibility, CodeQL, scorecard ve candidate
  review — başarılı

## Varlık ve checksum doğrulaması

| Varlık | SHA-256 |
|---|---|
| `divan.pyz` | `682a9fb83d038a16b748244b08b4864011b392795f0b65c29b73ec526a4785f0` |
| `divan-project.pyz` | `85b332bf9a02457bff099c5a6107f176f0a7753b83cfe83d61999697917bc5a1` |

İki değer de Release checksum dosyalarındaki değerlerle indirildikten sonra
birebir eşleşti. Release'te ZIP, SPDX SBOM ve attestation kayıtları da vardır.

## Yerel kurulum

`python scripts/divan.py install --host codex --source
https://github.com/trugurpala/divan.git --ref v1.3.3 --profile auto --execute`
sonrasında `doctor --host codex --ref v1.3.3 --json` sonucu `healthy` döndü;
skills, instructions, commands, agents, hooks, MCP ve native lifecycle
kapasiteleri etkin bulundu.

## Sınır

Bu kayıt CI ve yayın kanıtıdır; bağımsız kullanıcı kabulü veya dış kullanım
iddiası değildir.
