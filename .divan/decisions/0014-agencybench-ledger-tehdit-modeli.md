# ADR 0014: AgencyBench-02 için dondurulmuş ledger kabul sözleşmesi ve tehdit modeli

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-16
- **Karar sahibi:** Hükümdar

## Karar

AgencyBench-02'nin Fermanı "audit edilebilir immutable ledger **benzeri** kayıt"
ister. Bu gereksinim aşağıdaki güvence kümesi olarak yorumlanır ve bu
kampanyanın sonuna kadar dondurulur. Bağımsız hakem bu kümenin dışında yeni
zorunlu gereksinim türetemez.

### Zorunlu ledger güvencesi

- Uygulama düzeyinde salt ekleme: kayıt olayları eklenir, güncellenmez,
  silinmez.
- Düzeltme eski olayı değiştirmez; telafi edici ters kayıt ve yerine geçen yeni
  olay üretir.
- Aynı iş olayının tekrarı ekonomik etkiyi çoğaltmaz.
- Her olay, ait olduğu iş verisine hash ile bağlıdır ve doğrulama bu bağı yeniden
  hesaplar.
- Eksik, kesilmiş veya yeniden sıralanmış satırlar tespit edilir.
- Doğrulama bozulmayı ve uygulama yoluyla yapılmış tahrifatı gösterebilir.
- Kiracı ve rol yetkilendirmesi geçerlidir.
- Denetim izi vardır.

### Mevcut tehdit sınırı

Uygulamanın kendi HTTP arayüzü, kullanıcı arayüzü ve olağan yerel işletim
yolları. Saldırgan, bu yollardan geçen herkes olabilir.

### Zorunlu tehdit modelinin dışında olan

Windows dosya sistemi üzerinde veritabanı dosyasına ve bütün doğrulama
metaverisine sınırsız yazma yetkisi olan ayrıcalıklı bir saldırganın, ledger'ı
ve bütün hash ile çapa bilgisini baştan yeniden üretmesine karşı kriptografik
inkâr edilemezlik.

Bu, "ledger benzeri" gereksiniminden "dış kriptografik güven çapası"
gereksinimi türetmez. Anahtarsız bir hash zinciri, hash'i de yeniden yazan
birine karşı çalışmaz; yerel ve çevrimdışı çalışması Ferman'ın açık şartı olan
bir uygulamanın anahtar tutacak yeri yoktur.

## Neden

Beş bağımsız denetim turu bu sınırı her seferinde P0 olarak işaretledi ve iki
onarım turu bunu daraltmaya çalıştı: kuyruk kesilmesi yakalanır oldu, doğrudan
veritabanı değişikliği yakalanır oldu. İkisi de gerçek iyileştirmeydi. İkisi de
sınırı kaldırmadı, çünkü sınır uygulamanın değil işletim ortamının sınırıdır.

Bir kalite kapısı, kapatılması o ortamda mümkün olmayan bir şeyi zorunlu
kılarsa, geçmesi mümkün olmayan bir kapıdır ve hiçbir teslimi ayırt etmez. Bu
karar kapıyı gevşetmez; kapının neyi ölçtüğünü söyler.

## Sınırlar

Bu karar yalnız AgencyBench-02'nin kabul sözleşmesini bağlar. Divan'ın kendi
güvenlik kapıları, `LOCAL_STATE_DACL_POLICY` dahil, değişmez.

## Gelecek güvenlik iyileştirmesi

Aşağıdakiler AgencyBench-02'yi engellemez; ürün zekâsı defterine isteğe bağlı
profil olarak yazılır:

- anahtarlı imzalama
- işletim sistemi anahtar deposuna dayalı imza
- Windows CNG, DPAPI veya TPM destekli anahtar
- salt ekleme dış tanık
- uzak şeffaflık günlüğü

## Hakem talimatı

Hakem, bu belgeyi ve tehdit sınırını görür. Ayrıcalıklı dosya sistemi
yeniden yazımını yine zorunlu P0 olarak işaretlerse, bulgu `OUT_OF_FROZEN_SCOPE`
olarak sınıflandırılır; PASS veya FAIL sayılmaz.
