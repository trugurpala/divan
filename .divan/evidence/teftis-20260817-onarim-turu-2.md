# Teftiş — onarım turu 2, bütçenin son turu

Date: 2026-08-17
Benchmark head: `8a8c500` · suite 119 tests, green, worktree clean
Repair budget: 2 cycles; this is the second and last

## Hakemin ikinci turu ne buldu

**P0: yok.** İkinci kez. Dondurulmuş sözleşme sonrası hiçbir turda kapsam içi
P0 çıkmadı.

Bir P1 ve üç P2. Turun 1'de kapatılan dört şeyin hiçbirinde yeni ihlal
bulunmadı; hakem kiracı yalıtımı, merkezî yetki, süresi dolmuş sahip reddi,
komisyon yuvarlama, işlem kimliği, belge indirme yetkisi, yedekleme atomikliği
ve iki fazlı geri yüklemede ek bir şey bulamadığını ayrıca yazdı.

## R2A — hash kaynak kimliğini kapsamıyordu

Hakemin bulgusu ince ve haklıydı: `entry_hash` payload hash'ini içeriyor,
`source_type` ve `source_id`'yi içermiyordu. Aynı içerikli iki iş satırı varsa,
bir kaydın referansını diğerine çevirmek doğrulamayı atlatıyordu — doğrulama
yeni satırı dereference ediyor, aynı payload'ı buluyor ve geçerli diyor. Kayıt
satırın **içeriğine** bağlıydı, **kimliğine** değil; güvence kimliği istiyor.

Bu, bir önceki turdaki onarımın yarım kalmış tarafı. Referans eklendi,
doğrulama onu takip etmeye başladı, ama referansın kendisi hash'in dışında
kaldı.

**Hakemin kendi muhakemesi burada kayda değer.** Bulguyu belgelenmiş kapsam dışı
sınırdan kendisi ayırdı: "bunu tespit etmek hash zincirini veya çapayı yeniden
hesaplamayı gerektirmiyor, dolayısıyla belgelenmiş tam yeniden yazma
sınırlamasından farklı." Doğru: bir tamsayı kolonu değişiyor ve zincir hâlâ
doğrulanıyor. Dondurulmuş sözleşmenin arkasına saklanmadı, sınırın nerede
bittiğini gösterdi.

Onarım kimliği hash'lenen malzemeye kattı. Ledger salt ekleme olduğu için eski
kayıtlar yeniden yazılmadı: her kayıt bir hash biçim sürümü taşıyor, doğrulama
kaydın taşıdığı sürümle çalışıyor, ve yeni bir kayıt eski biçimle yazılamıyor.
Tanınmayan bir sürüm atlanmıyor, başarısızlık sayılıyor.

**RED:** hakemin tam tetikleyicisi dahil dört test kırmızı:

```
not ok - repointing an identical standalone commission reference breaks its ledger entry
not ok - repointing an identical document-download reference breaks its ledger entry
not ok - changing only source type breaks its ledger entry
not ok - new entries record the current ledger hash format version
```

## R2B — üç P2

Hakem bunları engelleyici saymadı ve derecesi değiştirilmedi. Üçü de onarıldı
çünkü üçü de somut ve küçük, ve "bozuk bir istek sunucuyu düşürebilir" bilerek
bırakılacak bir şey değil.

- Bozuk bir istek hedefi (`GET http://[::1 HTTP/1.1`) `new URL` içinde hata
  fırlatıp süreci sonlandırabiliyordu. Artık 4xx ile cevaplanıyor ve sunucu
  ayakta kalıyor.
- Dosya yazımı ile veritabanı kaydı arasında çökme, sahibi olmayan bir dosya
  bırakıyordu. Artık başlangıçta uzlaştırılıyor ve sahipsiz dosya hiçbir zaman
  indirilemiyor.
- Başka bir vakadaki süresi dolmuş kira, canlı bir claim gibi sayılıp meşru bir
  yeniden atamayı 409 ile engelliyordu. Artık yalnız canlı claim'ler sayılıyor,
  ve tek canlı claim kuralı korunuyor.

**RED:** üç test kırmızı, üçü de kendi bulgusuna ait:

```
not ok - malformed request targets cannot stop the server or damage its ledger
not ok - startup removes interrupted unowned document writes while preserving owned files, idempotently
not ok - reassignment ignores an unrelated expired lease but still counts valid claims
```

## Kanıt hijyeni

İki onarım da aynı dosyaya dokunuyor ve R2B sonra geldi, dolayısıyla R2A'nın
kanıtı için dosyayı geri almak R2B'yi de geri alıyor. R2A'nın kırmızı
listesindeki altı testten dördü kendisine, ikisi R2B'ye ait. R2B'nin listesi
temiz: üç kırmızı, üçü de kendisinin.

Bu, turun 1'de fark edilen aynı kirlilik. Otomatik bir koruma yerine burada
elle ayrıştırıldı ve ürün zekâsı defterine V1.1 maddesi olarak yazıldı.

## Sonuç

İki onarım kapandı, ikisi de RED ile yük taşıdığı gösterildi. Süit 119 test ile
yeşil ve deney öncesi de yeşildi.

Onarım bütçesi doldu. Sıradaki adım son hakem turu ve verdict; kapsam içi P0
veya P1 kalırsa TURNKEY_BLOCKED yazılacak. Bütçe kendiliğinden uzatılmayacak,
çünkü döngünün kendini beslemesi bu kampanyanın engellemek için var olduğu şey.
