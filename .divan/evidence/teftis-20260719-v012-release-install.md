# v0.12.0 yayın ve global kurulum kanıtı

Tarih: 2026-07-19

## Kaynak ve yayın

- PR: https://github.com/trugurpala/divan/pull/17
- `main` commit: `e9a2642e4a14b182f7e97281df138578b63a7657`
- Etiket: `v0.12.0`; aynı `main` commit'ine bağlı.
- Release: https://github.com/trugurpala/divan/releases/tag/v0.12.0
- Release workflow: https://github.com/trugurpala/divan/actions/runs/29702535903
- Arşiv: `divan-v0.12.0.zip`, SHA-256
  `107dbbbd165968acfa7977b3cfefa6749c88aa2b103967aa800a3775da254657`.
- Checksum varlığı aynı hash'i, `source_commit=e9a2642e...` ve `tag=v0.12.0`
  değerlerini taşıdı.

## CI ve canlı yüzeyler

- Teftiş: https://github.com/trugurpala/divan/actions/runs/29702535860
- CodeQL: https://github.com/trugurpala/divan/actions/runs/29702535861
- Üç işletim sistemi uyumluluk matrisi:
  https://github.com/trugurpala/divan/actions/runs/29702535873
- Site testi: https://github.com/trugurpala/divan/actions/runs/29702535899
- Wiki sync: https://github.com/trugurpala/divan/actions/runs/29702535867
- Pages deployment: https://github.com/trugurpala/divan/actions/runs/29702535440
- `main` README, Pages ve raw Wiki HTTP 200 döndürdü ve `v0.12.0` içerdi.

## Global çift-host kurulum

Dry-run sonrasında şu sabit kaynaktan işlemsel kurulum yapıldı:

```text
source=https://github.com/trugurpala/divan.git
ref=v0.12.0
hosts=claude,codex
```

Sonuç:

- Claude Code/Desktop Code: 5 Divan paketi, 41 skill, hepsi enabled.
- Codex: 5 Divan paketi, 41 skill, hepsi enabled.
- Claude tarafındaki 2 eski eklenti ve 3 eski marketplace korundu.
- Codex tarafındaki 11 eski eklenti ve 4 eski marketplace korundu.
- İşlem kaydı: `%USERPROFILE%\.divan\transactions\install-20260719T202942Z-8a94eb3e.json`.
- Eski loose Codex skill dizinleri silinmedi. Önceki manifest sahiplik hash'i
  taşımadığından otomatik migration fail-closed bırakıldı; bu veri kaybını önler.

## Davranış kanıtı sınırı

Gerçek Claude/Codex karşılaştırması yayımlandı; üç vakada skill 0, baseline 1,
beraberlik 2 oldu. Önceden eşik yoktur ve kalite artışı iddiası yapılmaz.
v1 karnesi 7/8'dir; yalnız bağımsız kullanıcı kabul kanıtı bekler.
