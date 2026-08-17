# Ürün zekâsı — AgencyBench-02'nin ölçülen davranışından çıkanlar

Date: 2026-08-17
Kaynak: bu kampanyada gerçekten yaşanan olaylar. Hiçbiri fikir turundan
gelmiyor; her maddenin arkasında bu depoda bir kanıt belgesi veya bir commit
var.

## V1.1 — bir sonraki sürümde kapanabilir

**1. Çalışana gözetimsiz çalıştığını söyle, her yolda.**
Bir onarım denemesi doğru bir plan üretip "bu planı uygulamamı onaylıyor
musunuz?" diye sordu ve kapalı bir boruya sorduğu için hiçbir şey üretmedi.
Divan bunu `work-rejected` kaydetti: yanlış hikâye, çünkü iş hiç denenmedi.
`5bcbca3` bunu yürütme ve denetim yollarında kapattı. Kalan iş: aynı sözleşmeyi
gelecekte eklenen her çalışan çağırma yolunun taşıdığını bir testle sabitlemek,
çünkü bu sınıf hata bu kampanyada dört kez tek bir rotada düzeltilip
diğerlerinde açık kaldı.

**2. Sessiz üretmeyen denemeyi ayrı sınıflandır.**
`FailureClass` bugün yedi değer taşıyor ve "temiz çıktı, iş üretmedi" durumu
`work-rejected` ile aynı kutuda. Ama ikisi farklı şeyler: biri "yaptığı iş
yanlış", diğeri "hiç iş yapmadı". İkincisi `RETRYABLE_CLASSES` içinde olmalı,
çünkü yeniden denemek güvenli; birincisi olmamalı. Kurtarma deneyinde bu ayrım
olmadığı için politika haklı olarak "yeniden denemek güvenli değil" dedi ve
kurtarılabilir bir durum kaybedildi.

**3. Çalışan dökümünü her zaman sakla.**
Kurtarma deneyinde açıklanamayan bir başarısızlık var ve tek sebebi o koşuda
dökümün tutulmamış olması. Döküm tutulduğu ilk koşuda kök neden bir dakikada
bulundu. Döküm kanıt değil, ama kanıtın nereden geldiğini söyleyen tek şey.

**4. Sidecar'ın ne taşıdığını sözleşmeden türet.**
Kurulum adayından önce ikili, bildirilen 93 modülün 59'unu taşıyordu; eksikler
arasında bu kampanyanın kanıtladığı yeteneklerin çoğu vardı. `ee49575` bunu
`modules.json`'dan türeterek kapattı. Kalan iş: aynı çapraz denetimi Tauri
kaynak listesi için de kurmak, çünkü orada da sessiz eksilme mümkün.

**5. Ölçüm aracını ürünün sözleşmesine bağla.**
Bu kampanyada düşen kapıların on üçü aracın hatasıydı, ürünün değil. Neredeyse
hepsinin sebebi aynı: araç, ürünün değişen sözleşmesini takip etmiyordu. Bir
kapı aracı, sınadığı sözleşmeden türetilebilirse bu sınıf hata kaybolur.

**6. Kanıt ölçümünü kirlilikten koru.**
Bir RED kanıtında iki onarım aynı dosyaya dokunduğu için kırmızı listeye başka
bir onarımın testleri karıştı; bir diğerinde mutasyon dosyaya hiç inmedi ve
"kanıt" aslında boştu. İkisi de fark edildi ve tekrarlandı, ama ikisi de
otomatikleşebilir: mutasyonun indiğini doğrulayan ve dokunulan dosyaların
başka onarımlarla kesişmediğini kontrol eden bir sarmalayıcı.

## V1.2 — bir sonraki sürümden sonra

**1. Yetki kararını mutasyonla aynı işleme almayı mimari kural yap.**
Hakem, yetkinin "sözdizimsel olarak merkezî ama mutasyon anında atomik değil"
olduğunu buldu. Merkezîleştirmek yetmiyor; kararın hâlâ doğru olduğu an ile
yazma anı aynı olmalı. Bu, Divan'ın ürettiği her uygulama için bir üretim kuralı
olabilir, tek tek bulunacak bir kusur değil.

**2. Göç alanlarının yeni yazımlara ulaşmasını engelle.**
`payload_reference_status` eski satırlar için eklendi ve yeni kayıtlara sızdı;
doğrulama da onları kabul etti. Bir alanın "yalnız göç için" olduğunu söylemek
yetmiyor, yeni yazım yolunda ulaşılamaz olması gerekiyor.

**3. Atomik olmayanı toparlanabilir yap.**
İki dizin yeniden adlandırması Windows'ta atomik yapılamaz. Doğru cevap
pencereyi küçültmek değil, niyet kaydı yazıp başlangıçta okumaktı. Bu kalıp
Divan'ın kendi durum yazımları için de geçerli.

**4. Sağlayıcı bağımsızlığını gerçekten sağla.**
Bütün denetimlerde yazan ve denetleyen aynı satıcı, çünkü makinede ikinci satıcı
yok. Bu bir sınır ve öyle kaydedildi, ama bağımsızlığın yarısı eksik demek. İkinci
bir satıcı kurulabilir hale gelmeden bağımsız denetim tam değil.

**5. Doctor'ın söylediğini kurulumdan sonra da ölç.**
Kurulum kabul testi Doctor'ın 15 yeteneği beş farklı durumda bildirdiğini
gösterdi ve bu, kurulumun makineyi gerçekten okuduğunun kanıtıydı. Bu ölçüm
kurulum hattının kalıcı bir parçası olmalı, elle koşulan bir betik değil.

## V2 — daha büyük değişiklik gerektiren

**1. Kriptografik ledger mührü, isteğe bağlı profil.**
ADR 0014 ayrıcalıklı dosya tahrifatını tehdit modeli dışına yazdı, çünkü
anahtarsız bir hash zinciri hash'i de yeniden yazan birine karşı çalışmaz ve
yerel çevrimdışı bir uygulamanın anahtar tutacak yeri yok. Kapatılabilir hali:
Windows CNG veya DPAPI korumalı imzalama anahtarı, varsa TPM desteği, imzalı
ledger kontrol noktaları ve isteğe bağlı dış tanık. Zorunlu değil, profil.

**2. Başarısızlıktan öğrenmeyi kurtarma anına bağla.**
`failure_learning` modülü var ve sınırlı ders adayı üretiyor, ama henüz kurtarma
ve denetim noktalarından çağrılmıyor. Bu kampanyada öğrenilmeye değer en az
sekiz gerçek başarısızlık yaşandı; hiçbiri kendiliğinden hafızaya girmedi.

**3. Kapı aracını ürünle birlikte üret.**
En radikal çıkarım da en çok kanıtı olan: bu kampanyada ürün 111 testle yeşil
kalırken ölçüm aracı on üç kez yanıldı. Divan bir uygulama üretirken onun kabul
aracını da üretebilir ve sözleşme değiştiğinde ikisi birlikte değişir. Bugün
araç elle yazılıyor ve ürünün gerisinde kalıyor.
