# Teftiş — onarım turu 1, hakemin üç bulgusuna karşı

Date: 2026-08-17
Benchmark head: `9fa6d1a` · suite 111 tests, green, worktree clean
Repair budget: 2 cycles; this is cycle 1

Üç bulgunun her biri hakemin kendi cümleleriyle görev sözleşmesine kondu ve
gerçek bir çalışan denemesiyle kapatıldı. Hiçbiri elle yazılmadı.

## R1A — yetki kararı ile mutasyon atomik değildi

Hakem, yetkinin sözdizimsel olarak merkezîleştiğini ama mutasyon anında
uygulanmadığını söylemişti: kira geçerliyken başlayan bir istek, gövdesini kira
dolduktan sonra tamamlayarak eski kararla yazabiliyordu.

Onarım, yetkilendirmeyi mutasyonun kendisiyle aynı işlemin içine aldı. Kira
orada okunuyor, satır orada yazılıyor; o noktada fark edilen bir sona erme
mutasyonu reddediyor ve olağan sona erme yolunu izliyor.

**RED:** düzeltme geri alındığında **12 test** kırmızı. Aralarında iş kaydı,
belge yükleme, bırakma ve kapatma için ayrı ayrı "kira yazımdan önce sona
erdiğinde yetki yeniden denetlenir" testleri ve HTML form yolları var. Yalnız
hakemin adını verdiği iki rota değil, bütün sahip kapsamlı mutasyonlar.

## R1B — bazı ledger olayları iş satırına bağlı değildi

Belge indirme ve tek başına duran komisyon kaydı kaynak satırı olmadan
yazılıyor, `stored` işaretleniyor ve doğrulama yalnız payload'ın kopyasını
hash'liyordu. Bu, kopyanın kendisiyle eşleştiğini kanıtlar.

Kök neden, önceki onarımın eklediği `payload_reference_status`'ın amacının
dışına taşmasıydı: göç edemeyen eski satırlar için düşünülmüştü, yeni yazılan
kayıtlara ulaşmaması gerekiyordu. Onarım, yeni yazımlar için kaynak referansını
zorunlu kıldı; artık yalnız bağlı bir kayıt yazılabiliyor.

**RED:** düzeltme geri alındığında **5 test** kırmızı: kaynak satırlarının
çözülebilirliği, her yeni kaydın bağlı olması, belge indirme satırının
kurcalanmasının yakalanması, komisyon satırının kurcalanmasının yakalanması ve
yalnız kopya payload'ın değiştirilmesinin yakalanması.

Son üçü önemli: doğrulama gevşetilerek geçilmediğini, tam tersine iki ayrı
kurcalama biçimini de yakaladığını gösteriyorlar.

## R1C — terfinin çökme penceresi vardı

Önceki onarım, **hatası yakalanan** bir yeniden adlandırmadan toparlanıyordu.
İki yeniden adlandırma arasında ölen bir süreç için yakalayacak kod yok, ve
Windows'ta iki dizin takası atomik yapılamaz.

Onarım pencereyi kaldırmak yerine toparlanabilir kıldı: ilk yeniden
adlandırmadan önce bir niyet kaydı yazılıyor, takas tamamlanınca siliniyor, ve
başlangıçta okunup yarım kalmış takas ya tamamlanıyor ya geri alınıyor.

**RED, iki kademede.** Modül tamamen kaldırıldığında bütün süit içe aktarma
hatasıyla düşüyor; bu modülün gerekli olduğunu kanıtlar, kurtarmanın çalıştığını
kanıtlamaz. Onun için modül bırakılıp yalnız kurtarma mantığı etkisiz bırakıldı,
yani onarımdan önceki davranış geri getirildi. Sonuç tam olarak beş kırmızı:

```
not ok - recovery closes the crash window between the two directory renames
not ok - recovery promotes a present staging store and its final manifest verifies
not ok - recovery restores the previous store when staging never arrived
not ok - swap recovery is idempotent
not ok - recovery with no intent record touches no file
```

## Bir kanıt hijyeni notu

Üç onarımın ikisi aynı dosyaya dokunuyor ve R1B en sonra geldi. Bu yüzden
R1C'nin kanıtı için `app.js`'i geri almak R1B'nin düzeltmesini de geri alıyor ve
kırmızı listeyi kirletiyor. İlk ölçüm bu kirlilikle alındı; yukarıdaki temiz
ölçüm yalnız yedekleme dosyalarına dokunularak yeniden yapıldı.

Kirli bir kanıtı temiz gibi sunmak, kanıt üretmemekten kötüdür.

## Sonuç

Üç bulgunun üçü de kapandı, üçü de RED ile yük taşıdığı gösterildi. Süit
111 test ile yeşil ve deney öncesi de yeşildi, dolayısıyla yukarıdaki kırmızılar
deneyin kendisi.

Sıradaki adım hakemi tekrar çağırmak. Bütçe bir tur daha.
