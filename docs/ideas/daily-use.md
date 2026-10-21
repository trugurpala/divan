# Divan ile günlük geliştirme

## Problem

Bir vibe coder'ın kendi diliyle anlattığı yazılım işini, araç isimlerini ve ajan
adımlarını yönetmesini gerektirmeden, nasıl çalışan ve doğrulanmış sonuca taşırız?
Hedef kullanıcı mevcut veya yeni projesini günlük işte kullanan, sonucu tarif eden
ama her görev için beceri, MCP ve servis seçmek istemeyen kişidir.

Başarı; doğru işin yapılması, kullanıcının çalışma boyunca ne olduğunu anlayabilmesi,
sonucu deneyebilmesi ve sonraki oturumda kararların kaybolmamasıdır. Kaynak sayısı,
yeni araç kurulumu veya büyük bir plan tek başına başarı ölçütü değildir.

## Değerlendirilen yönler

| Yön | Kullanıcı değeri | Uygulanabilirlik ve bedel | Karar |
| --- | --- | --- | --- |
| Doğal dilde tek giriş, mevcut yedi beceriyle uygulama ve kanıt | Günlük isteği doğrudan çalışan sonuca bağlar | Mevcut Codex araçlarını kullanır; yönlendirme ve iletişimin gerçek görevlerde sınanması gerekir | Öncelik |
| Her iş için geniş beceri ve eklenti seçim menüsü | Uzman kullanıcıya görünür kontrol sağlar | Seçim yükünü kullanıcıya taşır; kurulum ve bakım yüzeyi büyür | Yalnız somut bir karar gerektiğinde kısa seçenekler |
| Ayrı kontrol paneli ve kalıcı ajan servisi | Oturum dışı iş yönetimi sağlayabilir | Yeni runtime, erişim ve işletim sorumluluğu doğurur; mevcut beceri ürünü için kanıtlanmış ihtiyaç yok | Bu talebin çözümü olarak eklenmez |

## Seçilen yön

Divan'ın tek doğal dil girişini güçlendiriyoruz. Kullanıcı “şu kaydetme işini düzelt”
diye başladığında mevcut projeyi inceleyen, gerekli yeteneği seçen, uygulayan ve aynı
akışı yeniden deneyen mevcut yedi beceri birlikte çalışır. Türkçe, İngilizce veya
karışık teknik ifadeler, yeni bir ürün ya da araç seçme görüşmesine dönüşmez.

İletişim ürünün parçasıdır: başlangıçta amaç, çalışırken bulgu ve sonraki kontrol,
bitişte kullanılabilir sonuç ve kanıt gösterilir. Kullanıcı bir karar vermek
zorundaysa soru somut sonuçlara dayanır. Aynı kapsamda verilmiş yetki korunur;
yıkıcı bir işlemin hedefi belirsizse önce kapsam netleştirilir.

## Doğrulanacak varsayımlar

- [ ] Yazım hatalı ve karışık dilli istekten doğru sonuç çıkarılabiliyor: aynı küçük
  repo görevini farklı ifadelerle izole oturumlarda uygulat, gerçek diff ve testi incele.
- [ ] Durum sorusu ve dil değişikliği işi koparmıyor: uygulama sırasında bir takip
  mesajı ver, önceki hedefin ve kısıtların korunduğunu gözle.
- [ ] Gerekli soru ile rutin seçim ayrılabiliyor: bir belirsiz veri silme isteği ve
  bir sıradan test seçimi kullan; ilkinde hedef netleşmeden silme, ikincisinde gereksiz
  izin döngüsü olmadığını gözle.
- [ ] İletişim ve teslim yeterli: zamanlı işlem kaydında anlamlı güncellemeleri,
  son yanıtta kullanım yolunu, taze kanıtı ve kalan sınırları ayrı incele.

Bu maddeler kabul ölçütleridir; kutular test kaydı olmadan tamamlanmış sayılmaz.
Mekanik validator geçişi model davranışını veya tüm dillerde kaliteyi kanıtlamaz.

## Kalıcı ürün kapsamı ve sınırlar

Çalışan gerçek akış, hata davranışı, mevcut mimariye uyum, güncel test ve devam
notları teslimin parçasıdır. Bu hedef MVP veya demo kapsamına düşürülmez. Sınırlı
geliştirme dilimi, sürdürülen üründeki belirli davranışı iyileştirir.

Sırf yaygın diye paket kurulmaz; var olmayan araç veya servis çalışıyor sayılmaz.
Ayrı arayüz, sürekli arka plan ajanı ve otomatik herkese açık yayın bu akışın
varsayılanı değildir. Bunlar gerçek bir kullanıcı ihtiyacı ve uygun yetkiyle ayrıca
değerlendirilir. Çok dilli kalite veya verimlilik artışı, karşılaştırmalı ölçüm
olmaksızın pazarlama iddiasına dönüşmez.
