# Pusula Continuity Protocol

Amaç: uzun geliştirme oturumunda doğruluğu sohbet geçmişine bağlamadan sürdürmek.

## Okuma sırası

Yeni veya sıkıştırılmış her ajan oturumu yalnız şu sırayı okur:

1. `.specify/memory/constitution.md`
2. `specs/003-divan-pusula-web/spec.md`
3. `.pusula/plan-lock.json`
4. en yüksek geçerli `.pusula/continuity/checkpoint-XX.json`
5. checkpoint içindeki `next_actions`

Tam sohbet dökümü, eski tool logları veya ECC'nin bütün skill kataloğu varsayılan context'e alınmaz.
Gereken bilgi evidence/source ref üzerinden talep üzerine yeniden yüklenir.

## Zorunlu checkpointler

`00`, `25`, `50`, `75`, `100`.

Bir çeyrek sınırı geçilmeden önce `scripts/pusula_checkpoint.py` ile yeni capsule oluşturulur ve
validate edilir. Son capsule bozuksa sonraki çeyreğe başlanmaz.

## Capsule içeriği

- exact baseline SHA
- constitution ve plan sürümü
- active spec
- progress yüzdesi
- tamamlanan task ID'leri
- en fazla 12 kabul edilmiş karar
- en fazla 20 doğrulanmış gerçek
- en fazla 8 açık risk/engel
- en fazla 5 sıradaki aksiyon
- en fazla 16 evidence/source ref
- maliyet özeti
- capsule SHA-256 digest

Capsule gizli anahtar, raw tool logu, uzun diff, stack trace veya tam doküman kopyası taşımaz.
Bunlar yalnız ref ile işaretlenir.

## Token bütçesi

Bir capsule'ın kanonik JSON gövdesi 12.000 karakteri aşamaz. Amaç yaklaşık birkaç bin tokenlık
hızlı yeniden başlatma bağlamıdır; kesin tokenizer varsayımı yapılmaz.

Limit aşılırsa geçmiş anlatı kısaltılmaz diye rastgele silinmez. Önce eski ayrıntılar evidence ref'e
dönüştürülür; yalnız mevcut karar, risk ve sıradaki işler capsule'da kalır.

## %25 kuralı

- 0-25: governance + product spine + owned source/CI contracts.
- 25-50: Mizan + connectors + agent runtime.
- 50-75: evidence/security + deployment/resilience.
- 75-100: human UX + adversarial eval + production/rollback proof.

Her sınırda constitution compliance yeniden kontrol edilir. Plan değişikliği gerekiyorsa sebep yeni
GoalRevision/plan amendment olarak kaydedilir; eski checkpoint yeniden yazılmaz.

## Resume davranışı

Ajan devam etmeden önce:

- capsule digestini yeniden hesaplar,
- baseline/spec/plan referanslarının hâlâ bulunduğunu doğrular,
- tamamlanmış taskleri tekrar yapmaz,
- `next_actions[0]` ile başlar,
- provider fiyat/özellik kararı eskiyse Mizan Radar review açar.

Referanslardan biri kayıpsa durum `BLOCKED` olur; hafızadan tahmin ederek devam edilmez.
