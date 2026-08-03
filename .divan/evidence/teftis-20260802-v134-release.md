# v1.3.4 yayın teftişi

- Version: v1.3.4
- Source commit: 0fe544124daab90de9c4600349d411f79946857b

## Sonuç

v1.3.4 değişmez etiketi ve GitHub Release'i yayımlandı. Release taslak veya ön
sürüm değildir.

## Kanıt

- Release: https://github.com/trugurpala/divan/releases/tag/v1.3.4
- Release workflow: `30762821192` — başarılı
- Release kapıları: Ubuntu, macOS ve Windows Codex — başarılı
- Yayın kapıları: yerel yayın, resmî şema, Pages/Wiki senkronu, Chromium
  Pages, sürüm notu, attestation ve değişmez Release doğrulaması — başarılı
- PR #106: Quality Gate, CodeQL, bağımlılık incelemesi, Wiki, site testi ve
  Linux/macOS/Windows host doğrulaması — başarılı

## Varlık ve checksum doğrulaması

GitHub Release'ten yeniden indirilen yedi varlığın SHA-256 değeri, API'nin
yayımladığı digest ile birebir eşleşti. Ana iki çalıştırıcının digest'leri:

| Varlık | SHA-256 |
|---|---|
| `divan.pyz` | `c2ef7ea802080718d6d8c9ff33b2f73c1a627a4833b760c58bedbd2127c6dbd9` |
| `divan-project.pyz` | `6862385357bd3338c348969cfed70f767d2b7a4e0cbd838193db7ff8876754fb` |

`gh attestation verify` iki `.pyz` varlığı için başarılı döndü. ZIP, SPDX SBOM
ve checksum sidecar'ları da aynı release içinde yer alır.

## Canlı geri okuma

- GitHub Pages: HTTP 200
- GitHub Wiki Home: HTTP 200
- `v1.3.4` tag: `0fe544124daab90de9c4600349d411f79946857b`

## Sınır

Bu kayıt CI ve yayın kanıtıdır; bağımsız kullanıcı kabulü, dış kullanım,
performans veya kalite artışı iddiası değildir.
