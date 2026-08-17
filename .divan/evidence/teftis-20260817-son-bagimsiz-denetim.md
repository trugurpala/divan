# Teftiş — son bağımsız denetim, dondurulmuş sözleşmeye karşı

Date: 2026-08-17
Reviewed: benchmark head `4877717`, 87 tests green
Reviewer: fresh Codex process, pid 57316, 169.7 s
Contract: ADR 0014's guarantee set and threat boundary, given verbatim

Tek denetim, döngü değil. Hakem yazma yetkisi olmadan, yazan oturumun geçmişi
olmadan çalıştı ve dondurulmuş güvence kümesinin dışında zorunlu gereksinim
üretemeyeceği açıkça söylendi.

## Denetimin kendisi kanıt olarak geçerli mi

| Kontrol | Gözlem |
|---|---|
| Kendi sürecinde koştu | süreç bağımsızlığı kanıtlandı |
| Yazamadı | yazma erişimi reddedildi |
| Tamamlandı | çıkış 0, zaman aşımı yok |
| Bulgu üretti | 2819 karakter |
| Kanıt olarak kullanılabilir | evet |
| Kapsam içinde engelleyici bulgu yok | **hayır — RETRY** |

**5/6.** Sağlayıcı bağımsızlığı `unavailable`: yazan ve denetleyen aynı satıcı,
bu makinede ikinci bir satıcı yok. Bu bir sınırdır ve öyle kaydedilir.

## Dondurulmuş sözleşmenin yaptığı iş

**P0: yok.**

Beş önceki denetim turunda ayrıcalıklı dosya sistemi tahrifatı her seferinde P0
işaretlenmişti ve verdict'i tek başına belirliyordu. ADR 0014 o sınırı yazılı
hale getirdikten sonra hakem ona uzanmadı ve enerjisini kapsam içine harcadı.
Kapı gevşetilmedi; kapının neyi ölçtüğü söylendi ve ölçüm işe yaradı.

## Üç bulgu, üçü de kapsam içinde

**P1 — Yetki kararı ile mutasyon arasında kira sona erebiliyor.**
Sahip veya yönetici, kira geçerliyken isteğe başlıyor, gövdeyi kira dolduktan
sonra tamamlıyor. `recordAttempt` ve `reassignCase` daha önce verilmiş yetki
kararıyla yazıyor. Yetki sözdizimsel olarak merkezî ama mutasyon anında atomik
değil.

Bu haklı bir bulgu ve önceki onarımın gözden kaçırdığı şeyi tam yerinden
tutuyor: tek bir karar noktası yapmak, o kararın hâlâ doğru olduğunu garanti
etmiyor.

**P1 — Bazı ledger olayları anlattıkları iş satırına bağlı değil.**
Belge indirme ve tek başına duran komisyon kaydı, kaynak satırı olmadan
yazılıyor ve `stored` işaretleniyor; doğrulama yalnız payload'ın kopyasını
hash'liyor. Bu, kopyanın kendisiyle eşleştiğini kanıtlar, başka bir şeyi değil.

Bu da haklı. Çakışma onarımının eklediği `payload_reference_status`, yalnız
göç edemeyen eski satırlar için düşünülmüştü; yeni yazılan kayıtlara ulaşması
gerekmiyordu.

**P1 — Geri yükleme terfisinin çökme penceresi var.**
`swapDirectory` mevcut dizini `.previous-*` adına taşıdıktan sonra, staging
yerine konmadan önce süreç ölürse, yapılandırılmış yolda depo yok ve önceki
depo rastgele adlı bir kardeşin altında, başlangıçta toparlayacak bir mekanizma
olmadan duruyor.

Bu, önceki onarımın gerçekten kapatmadığı bir şey: hatası **yakalanan** bir
yeniden adlandırma toparlanıyor, ama çalışmayı bırakan bir süreç için
yakalayacak kod yok.

## Hakemin substantiate etmediği şeyler

Kiracı yalıtımı, komisyon aritmetiği ve yuvarlama, belge yolu ve indirme
yetkisi, kayıtlı kimlik bilgisi, bozuk girdi dayanıklılığı: ayrı bir bulgu
gerekçelendirilmedi.

Hakem testleri okudu ama koşmadı, çünkü testler geçici veri yazıyor ve denetim
salt okunurdu. Bunu kendisi söyledi; sessizce atlamadı.

## Sonuç

Verdict **RETRY**. Üç P1'in üçü de dondurulmuş güvence kümesinin içinde,
üçünün de tetikleyicisi belirtilmiş, üçü de gerçek. Sınırlı onarım turu 1
başlatıldı; bütçe iki tur.
