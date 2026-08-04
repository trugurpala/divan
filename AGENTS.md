# Divan çalışma sözleşmesi

## Amaç

Divan, Claude Code ve Codex için doğrulanmış yerel kurulum yolları sunan,
Agent Skills uyumlu taşınabilir bir skill ve proje işletim sistemi
derlemesidir. Başka bir yapay zekâ hostunun veya uygulama çalışma zamanının
yerine geçmez. Değişiklikler vibe coder için düşük bilişsel yükü,
taşınabilirliği, lisans açıklığını, güvenli geri dönüşü ve kanıtlı teslimi
korumalıdır.

## Önce oku

- Ürün yönü ve kararlar: `BLUEPRINT.md`
- Upstream kökenleri ve yamalar: `UPSTREAM.md`
- Lisans envanteri: `THIRD_PARTY_LICENSES.md`
- Yerel teftiş: `scripts/validate.py`
- Katalog teftişi: `scripts/catalog.py --check`
- Yayın yüzeyleri: `release-manifest.json` ve `scripts/release.py --check`
- v1 kabul defteri: `registry/v1-gates.json` ve `scripts/v1.py --check`
- Claude Code devralması: `CLAUDE.md` ve `scripts/handoff.py --check`
- Codex sınırları: `docs/OpenAI-ve-Codex-Uyumlulugu.md`
- Davranış ve skill ölçümü: `evals/README.md`
- Kamuya açık yazı ve dil: `docs/Yazim-ve-Uslup.md` ve `scripts/prose.py --check`

## Her işte izlenecek sıra

1. Kullanıcının istediği sonucu, izin verilen kapsamı, değişmemesi gerekenleri
   ve “bitti” ölçütünü kısa ve sınanabilir biçimde çıkar. Belirsizlik düşük
   riskli bir yerel incelemeyle giderilebiliyorsa ilerle; ürün yönünü veya dış
   sistemleri değiştirecek bir seçim gerekiyorsa kullanıcıya dön.
2. Dosya değiştirmeden önce ilgili kodu, testleri, belgeleri, `git status`u,
   geçerli dalı ve uzak depo ilişkisini oku. Kullanıcının mevcut değişikliklerini
   sahiplenme, silme, düzeltme veya başka değişikliklerin içine karıştırma.
3. Hata ya da iyileştirme işinde önce mevcut davranışı yeniden üret ve bir
   baseline (başlangıç ölçümü) kaydet. Yeniden üretilemeyen sorunda neden
   kanıtlanmış gibi davranma.
4. En küçük kullanılabilir çözümü uygula. İstek yerel ve geri alınabilir kod,
   test veya belge değişikliğini açıkça gerektiriyorsa her dosya için yeniden
   onay isteme; kapsam dışı veya geri döndürülmesi zor adıma geçme.
5. Değişikliği önce hedefli testle, sonra ilgili daha geniş kapılarla doğrula.
   Diff'i hata, güvenlik, geriye uyumluluk, gereksiz karmaşıklık ve belge
   sapması için yeniden incele.
6. Kanonik doğrulamayı çalıştır ve yalnız gözlenen sonucu raporla. Timeout,
   atlanan test, eksik araç veya ölçüm gürültüsü başarı değildir; sonucu
   `belirsiz` veya `engelli` olarak açıkla.
7. Sonuçta değişen dosyaları, çalıştırılan komutları, gerçek çıktıyı, kalan
   riskleri ve kullanıcıdan gereken tek sonraki kararı yaz. Kanıt görmeden
   “onaylandı”, “en iyi”, “hızlandı” veya “bitti” deme.

## Çalışma kuralları

- En küçük yeterli değişikliği yap; üçüncü taraf harness'i veya çalışma zamanı
  bağımlılığını varsayılan yol haline getirme.
- Lisansı doğrulanmamış içeriği kopyalama. Taşınan her içerik için `UPSTREAM.md`
  ve `THIRD_PARTY_LICENSES.md` kayıtlarını güncel tut.
- Dış kaynak keşfini doğrudan kuruluma çevirme. Meclis varsa adayı
  `registry/candidates.json` yaşam döngüsüne işle; ADOPT/ADAPT kararı bile ayrı
  pin+atıf+eval+teftiş uygulaması ister.
- Kullanıcı açıkça istemedikçe repo başlatma, commit, stage, push, pull request,
  merge, tag, release veya hesap/depo ayarı değişikliği yapma. Testlerin geçmesi
  kullanıcı onayı ya da yayın yetkisi sayılmaz.
- Paralel ajanları yalnızca bağımsız ve sınırları belirli işler için kullan.
  Aynı dosyayı eşzamanlı yazdırma; paralel yazım gerekiyorsa ayrı worktree kullan.
- Ürünü değiştiren işte README, katalog, kurulum belgesi, Wiki kaynağı ve site
  sayılarını aynı değişiklikte eşitle. Wiki etkinse `scripts/wiki.py --check`
  ve `wiki-sync` yayın kanıtını da zorunlu yüzey say.
- Kamusal teslimde taslak PR'ı son durum sayma. Yetki kapsamındaysa CI sonrası
  varsayılan dala birleştir; README/kurulum/canlı sayfayı varsayılan daldan
  yeniden oku. Tag yoksa “release yayımlandı” deme.
- Her sürümde `/yayin`/`scripts/release.py` yolunu kullan; `VERSION`, marketplace,
  `CHANGELOG.md`, README'ler, BLUEPRINT, Wiki, site ve kurulum referansını
  eşitle. `.divan/progress.md` sıradaki kesin adımı taşımalı. `main` sonrası
  Pages/Wiki/tag/Release kanıtını ayrı ayrı doğrula.
- Bir skill'in davranışı iyileştirdiğini iddia etmeden önce `evals/README.md`
  protokolünü kullan. Gerçek ajan adaptörü/hakem koşmadıysa yalnız sözleşme veya
  mekanik doğrulama raporla; win-rate, hız ya da kalite artışı uydurma.
- README, Wiki, site, sürüm notu, issue ve PR metninde
  `docs/Yazim-ve-Uslup.md` sözleşmesini uygula. Önce kullanıcı sonucunu yaz;
  Divan terimini ilk kullanımda günlük karşılığıyla açıkla.

## Gerçek benchmark ve iyileştirme protokolü

Bu bölüm; kullanıcı “iyileştir”, “hızlandır”, “en iyi”, “benchmark”, “başarı
oranı” veya benzeri ölçülebilir bir üstünlük istediğinde ve değişiklik performans,
maliyet, doğruluk, güvenilirlik ya da ajan davranışı iddiası doğurduğunda
zorunludur. Yalnız yazım veya belge düzenlemesinde ölçülebilir ürün iddiası yoksa
göstermelik benchmark çalıştırma.

1. Değişiklikten önce tek birincil metriği, yönünü (`lower-is-better` veya
   `higher-is-better`), doğruluk kapılarını, kabul eşiğini, veri setini, süre/
   maliyet bütçesini ve değiştirilebilir dosya sınırını yaz. Metrik seçilemiyorsa
   “en iyi” iddiasını reddet ve önce ölçüm tasarla.
2. Isınma koşusunu ölçüme katma. Baseline ve her aday için aynı komutu, girdiyi,
   seed'i, sürümü, cache durumunu ve makul ölçüde aynı Windows ortamını kullan.
   Ham örnekleri sakla; yalnız yuvarlanmış tek sayı yayımlama.
3. Baseline'ı en az üç bağımsız ölçümle çalıştır. Kullanıcı gerçekten “en iyi
   yaklaşımı” istiyorsa ve maliyet sınırı izin veriyorsa en az üç anlamlı,
   birbirinden farklı aday dene; her adayı da en az üç kez ölç. Bir koşu uzun,
   ücretli, kota sınırlı veya dış hizmete bağımlıysa kör tekrar yapma: sınırı
   açıkla, kullanıcıdan yetki/bütçe iste veya sonucu `belirsiz` bırak.
4. Süre/maliyet metriğinde medyanı, en düşük/en yüksek örneği ve mümkünse
   dağılım ölçüsünü raporla. Düşük değer iyiyse iyileşme yüzdesi
   `(baseline_medyanı - aday_medyanı) / baseline_medyanı * 100`; yüksek değer
   iyiyse `(aday_medyanı - baseline_medyanı) / baseline_medyanı * 100` olarak
   hesaplanır. Sıfır baseline'da yüzde üretme.
5. Ajan/skill davranışında `evals/README.md` protokolünü kullan: en az üç
   temsilî vaka, kör A/B eşlemesi, gerçek adaptör, bağımsız hakem, sabitlenmiş
   model/ortam kimliği ve provenance gerekir. Fixture veya `--check`, kalite
   artışı kanıtı değildir. Nondeterministik ve yüksek etkili iddialarda bütçe
   izin veriyorsa tam koşuyu üç bağımsız seed/oturumla tekrarla.
6. Adayı yalnız bütün doğruluk/güvenlik testleri geçerse, önceden yazılmış eşiği
   aşarsa, fark ölçüm gürültüsünden büyükse ve önemli ikincil metriği bozmazsa
   kabul et. Adaylar eşitse en küçük, en okunabilir ve en az bağımlı olanı seç.
   Hiçbiri kazanmazsa baseline'ı koru; sırf değişiklik yapmak için kötü adayı
   birleştirme.
7. Deneyleri birbirine karıştırma. Ayrı worktree, ayrı yama veya açıkça sınırlı
   dosya seti kullan. Reddedilen adaylardan yalnız ajanın oluşturduğu deney
   değişikliklerini kaldır; kullanıcının başlangıç değişikliklerine dokunma.

## GitHub araştırması ve güvenli benimseme

- Önce yerel kök nedeni ve baseline'ı çıkar. Yerel adaylar hedefi geçmiyorsa
  resmî belgeler, ardından GitHub üzerindeki güncel ve ilgili projeler araştırılır.
- Her aday için depo URL'si, incelenen tam commit SHA'sı, lisans, son bakım
  durumu, CI/test kanıtı, açık güvenlik/uyumluluk riski ve Divan'daki karşılanan
  kullanıcı açığı kaydedilir. Yıldız sayısı tek başına kalite kanıtı değildir.
- Lisansı belirsiz, uyumsuz veya kaynaksız kodu, promptu ya da varlığı kopyalama.
  Uyumlu kod alınacaksa yalnız gereken küçük parçayı tam commit'e sabitle;
  `UPSTREAM.md`, `THIRD_PARTY_LICENSES.md`, gerekirse `NOTICE.md` ve ilgili
  testleri aynı değişiklikte güncelle. Uygunsa kod taşımak yerine fikri bağımsız
  ve Divan sözleşmesine uygun biçimde uygula.
- İndirilen scripti, Action'ı, binary'yi, hook'u veya paketi kaynak ve izin
  incelemesi yapmadan çalıştırma. Pin, checksum, en dar yetki ve izole deneme
  kullan; güvenlik kapısını hız için zayıflatma.
- Dış aday entegre edildikten sonra aynı baseline komutu, aynı en az üç ölçüm ve
  aynı doğruluk kapıları yeniden çalıştırılır. Kazanmayan veya kanıtlanamayan
  aday varsayılan yol yapılmaz.

## Windows 11 ve yerel ortam

- Bu deponun birincil kullanıcı ortamını Windows 11 + PowerShell + Codex olarak
  kabul et; yine de değişikliklerin desteklenen diğer host ve işletim
  sistemlerini bozmadığını mevcut matrisle doğrula.
- Gerçek çalışan Python yorumlayıcısını ve araç sürümlerini kaydet. Yolları
  `pathlib` ile kur, boşluk içeren PowerShell yollarını doğru tırnakla ve UTF-8
  kullan. WSL'yi, Docker'ı veya yeni global bağımlılığı sırf kolaylık için
  zorunlu yol yapma.
- Kullanıcı açıkça istemedikçe PATH, PowerShell execution policy, Windows
  Registry, kimlik bilgileri, global Codex ayarları veya başka projeleri
  değiştirme. Secret, kullanıcı adı ve kişisel home yolunu sonuç/benchmark
  dosyasına yazma.
- Cache, bytecode, coverage ve geçici benchmark çıktılarını repo dışında tut.
  Windows'a özgü çözüm eklersen hedefli Windows testi ve mevcut çapraz-platform
  doğrulamasını birlikte çalıştır.

## Doğrulama

Teslimden önce çapraz-platform, cache'leri depo dışında tutan kanonik yolu
çalıştır:

```bash
python scripts/verify.py
git diff --check
```

Doğrulayıcı ilk ve son adımda hijyen kapısını çalıştırır; Python bytecode,
Ruff, mypy ve coverage cache'lerini geçici olarak depo dışına yönlendirir.
`scripts/hygiene.py --clean` yalnız mevcut allowlist için açık bir bakım
komutudur ve normal doğrulama sırasında çağrılmaz.

Claude Code veya Agent Skills şemasını etkileyen değişikliklerde CI'daki resmî
doğrulayıcıların yerel karşılıklarını da çalıştır. Kanıt görmeden “bitti” deme.
