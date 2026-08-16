# AgencyBench-01 — anahtar teslim sınavı

- Tarih: 2026-08-16
- Dal: `feat/agency-os-turnkey-v1`
- Ferman: Yerel Operasyon Vaka Sistemi
- Sonuç: **TURNKEY_BLOCKED**
- Neden: `WORKERS_OFFLINE`

## Sonuç

Divan kendi hattını Ferman'dan iş paketi grafiğine kadar gerçekten
yürüttü ve çalışan atama adımında durdu. Bu makinede kod yazacak hiçbir
worker kurulu değil, bu yüzden uygulama üretilmedi.

Uygulama elle yazılmadı. Yazılsaydı ölçüm anlamsız olurdu: bu sınav
Divan'ın ne yapabildiğini ölçer, insanın ne yapabildiğini değil.

## Nereye kadar gitti

| Aşama | Durum |
|---|---|
| Ferman | tamam |
| Spec derleme | tamam |
| Ürün sözleşmesi | tamam |
| UX kabul sözleşmesi | tamam |
| Mimari kararlar | tamam |
| İş paketi grafiği | tamam — 4 paket |
| Bağlam derleme | tamam — paket başına sınırlı paket |
| Çalışan atama | **engelli** |
| Yürütme, test, tarayıcı, güvenlik, teftiş, teslim | çalıştırılmadı |

Üretilen iş paketleri: `WP-P1-roles`, `WP-P1-queue`, `WP-P2-ledger`,
`WP-P3-report`. İki P1 paketi bağımsızdır; P2 ve P3 üstündeki bandı bekler.

## Kapı matrisi

17 kabul kapısının tamamı `BLOCKED` ve her biri nedenini taşır. Hiçbiri
`PASS` görünmüyor. Sahte `READY` üretilmedi.

## Ölçümler

| Ölçüm | Değer |
|---|---|
| Toplam iş paketi | 4 |
| Attempt | 0 |
| Codex attempt | 0 |
| Claude attempt | 0 |
| Retry | 0 |
| Stall | 0 |
| Çalışan değişimi | 0 |
| Teftiş bulgusu | 0 |
| Otomatik onarılan bulgu | 0 |
| İnsan sorusu | 0 |
| Hard gate sorusu | 1 |
| **HUMAN_INTERVENTION_COUNT** | **0** |
| Token güveni | estimated |
| Tahmini token | 207 |
| Duvar saati | 0.047 s |

`HUMAN_INTERVENTION_COUNT` sıfırdır: koşu bir yardım isteği yüzünden değil,
bir makine gerçeği yüzünden durdu. Tek hard gate sorusu, kurulu ve
kimliği doğrulanmış bir çalışanın bulunmamasıdır.

## Engelin doğası

Deep Doctor aynı makinede `codex` ve `claude` yeteneklerini `OFFLINE` /
`TOOL_NOT_INSTALLED` olarak raporlar. Benchmark bu tek doğruluk modelini
okur, kendi ikinci gerçeğini üretmez.

Bu engel kaldırılabilir ama sahibin kararıdır: kodlama CLI'larını kurmak ve
oturum açmak kimlik/hesap işlemidir ve mandate'te hard gate olarak
tanımlıdır. Divan bunu kendi başına yapmaz.

## Sınır

Bu kayıt Divan'ın planlama hattının gerçekten çalıştığının kanıtıdır. Teslim
edilmiş bir uygulama, performans veya kalite iddiası değildir.
