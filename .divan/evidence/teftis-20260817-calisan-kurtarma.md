# Teftiş — gerçek çalışan öldürme ve kurtarma

Date: 2026-08-17
Task: `BENCH02-CASE-NOTE` · benchmark head after: `4877717`
Suite after recovery: 87 tests, green

Sahte bir alt süreçle koşan belirlenimci test zaten vardı. Bu onun yerine
geçmez, yanına gelir: gerçek bir Codex denemesi, gerçek iş yaparken sert
öldürüldü ve bunu ele alması gereken politikayla kurtarıldı.

Görev meşru. Ortaya çıkarılacak bir kusur yaratılmadı: çalışandan gerçek bir
boşluğu kapatması istendi, öldürme ise güvenilirlik deneyinin kendisi.

## Ölçülen

| Kontrol | Gözlem |
|---|---|
| Deneme başladı | `A001`, pid 55768, kendi süreç kimliğiyle |
| Gerçek ilerleme oldu | ilerleme damgası yazıldı |
| Öldürülen çalışan canlı değil | pid canlılık sondasına hayır diyor |
| Sessiz deneme yetim sayıldı | politika `orphaned` dedi |
| Kurtarma değiştirmeye karar verdi | sürdürülebilir bir kontrol noktası yok |
| Çalışma ağacı temizlendi | ölü deneme arkasında bir şey bırakmadı |
| Yerine geçen aynı görevi taşıyor | `A002`, aynı `task_id` |
| Yerine geçen farklı bir süreç | 55768 → 46656 |
| Süreç kimliği yeniden kullanılmıyor | başlangıç belirteci farklı |
| **Yerine geçen işi tamamladı** | 5 dosya, commit `4877717` |
| Önceki deneme kaydı korundu | görev iki denemeyi de taşıyor |
| Ölü deneme kendi kaydını koruyor | `replaced` durumunda, üç geçişle |

**12/12.** Öldürme `taskkill /F /T` ile ağacın tepesinden tek seferde yapıldı.
Önce çalışanı öldürmek, denetleyen sürece bir karar yazacak kadar zaman
bırakır; hakkında karar yazılmış bir deneme yetim değildir.

Kurtarma sonrası uygulama süiti 87 test ile yeşil.

## Bir aralıklı davranış, açıklanmadan bırakılıyor

Bu kanıt üçüncü koşudan alındı. İlk iki koşuda yukarıdaki on bir adım geçti,
on ikincisi düştü: yerine geçen çalışan temiz çıktı (çıkış kodu 0) ama hiçbir
dosya üretmedi ve `work-rejected` sınıflandırıldı.

Birinci koşunun sebebi bulundu ve benimdi: istenen iş zaten yapılmıştı, çalışan
haklı olarak hiçbir şey üretmedi.

İkinci koşunun sebebi bulunamadı. Aynı görev metni, aynı depo başı, izole
edilip tek başına çalıştırıldığında sorunsuz tamamlandı: 5 dosya, süit yeşil.
Aynı koşullarda farklı sonuç.

Bu, bilinen borç olarak kayda geçiyor: sert bir ağaç öldürmesinden hemen sonra
başlatılan yerine geçen deneme, ara sıra temiz çıkıp iş üretmiyor. Yeniden
üretilemedi, dolayısıyla kök nedeni yazılmıyor. Mekanizmanın kendisi
kanıtlandı; bu, o mekanizmanın üzerine binen çalışanın davranışıyla ilgili bir
gözlem.

Kapatılmamış bir gözlemi açıklanmış gibi göstermek, bu kampanyanın engellemek
için var olduğu şeyin ta kendisi olurdu.
