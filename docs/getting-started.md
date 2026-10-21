# Divan ile ilk işin

Divan, Codex eklentisi veya uyumlu bir kodlama ajanında taşınabilir beceriler olarak
çalışır. Proje klasörünü aç, Divan'ı etkinleştir ve istediğin
sonucu anlat. Beceri adlarını veya hangi aracın kullanılacağını bilmen gerekmez.
English instructions and examples follow below.

Claude Code, Cursor, GitHub Copilot ve diğer uygulamalar için
[editör ve ajan kurulum rehberini](compatibility.md) kullan. Aşağıdaki kurulum
komutları Codex eklentisine aittir; günlük kullanım örnekleri ortak akışı anlatır.

## Kur ve kontrol et

Plugin destekleyen Codex CLI'da:

```sh
codex plugin marketplace add trugurpala/divan --ref main
codex plugin add divan@divan
codex plugin list --marketplace divan --json
```

Listede Divan'ın kurulu ve etkin olduğunu kontrol et; sonra proje klasöründe **yeni
bir Codex sohbeti** aç. Yerel geliştirme kopyasını kullanıyorsan
[geliştirme rehberindeki](development.md) yerel marketplace adımlarını izle.
Bu eklenti için ayrıca Python, Node, npx, Docker veya bir API anahtarı kurman gerekmez.
Geliştirdiğin uygulamanın kendi gereksinimleri ayrı değerlendirilir.

İlk oturumda becerinin gerçekten açıldığını görmek istersen Codex'te bir kez
`$divan` ile çağır: “`$divan Bu projeyi incele; okuduğun Divan SKILL.md yolunu ve
erişebildiğin dosyaları söyle.`” Codex'te beceriler [açıkça `$` ile
çağrılabilir](https://developers.openai.com/blog/eval-skills). Eklenti listesinde
görünmesi veya istekte “Divan” yazması, beceri dosyasının okunduğunu tek başına
kanıtlamaz. Günlük isteğini yine doğal dille verebilirsin; etkinleşmeden
şüphelenirsen açık çağrıyı kullan. İlk gerçek görevde yapılan değişiklik ve test
çıktısını ayrıca kontrol et.

## Sonucu anlat

| İhtiyacın | Yazabileceğin istek |
| --- | --- |
| Mevcut projeyi anlama | Divan, bu projede ne çalışıyor, ne eksik? İncele ve önceliği sade anlat. |
| Özellik geliştirme | Divan, müşterileri isimle arayabileyim. Mevcut ekranı koru ve aramayı çalışır halde dene. |
| Hata giderme | Divan, kayıt düğmesine iki kez basınca iki sipariş oluşuyor. Kök nedeni bul ve düzelt. |
| Devam etme | Divan, önceki kararları ve bugünkü kodu okuyup kaldığımız yerden devam et. |
| Yalnız değerlendirme | Divan, kodu değiştirmeden bu yaklaşımı değerlendir. |
| Başka dil | Divan, fix this bug and explain the result in English. |

İstediğin dilde yazabilirsin. Karışık terimler veya yazım hataları anlamı değiştirmiyorsa
Divan işi sürdürür; iki farklı ürün sonucu çıkabilecekse kısa bir soru sorar. Kod,
dosya adları ve API alanları yalnız konuşma dili değişti diye yeniden adlandırılmaz.
Bu, her dilde aynı başarı oranı ölçüldüğü anlamına gelmez.

## Çalışırken ne göreceksin?

Divan önce neyi ele alacağını kısaca söyler. İş sürerken bulduğu önemli durumu,
yaptığı değişikliği veya engeli bildirir. Uzayan sessizlikte, yeni sonuç yoksa
neyi beklediğini söyler; ölçülmemiş yüzde veya bitiş saati üretmez. Ajanın aktif
çalışması dışında kendiliğinden arka plan bildirimi göndermez.

“Ne durumdayız?” sorusu işi iptal etmez. “Şimdilik dur” dersen çalışmayı durdurur.
Bir karar gerekiyorsa nedenini ve somut seçenekleri açıklar; bağımsız işlere devam eder.
Mevcut erişim ile yeni hesap, ücretli servis veya kalıcı yayın yetkisini ayrı tutar.

Teslimde neyin değiştiğini, nasıl denendiğini, nereden kullanacağını ve varsa kalan
engeli görürsün. Çalıştırılmayan test veya denenmeyen yayın başarılı diye sunulmaz.

## Güncelleme ve sık karşılaşılan durumlar

GitHub marketplace kurulumu için:

```sh
codex plugin marketplace upgrade divan
codex plugin add divan@divan
```

Yeni sohbet aç ve plugin listesini tekrar kontrol et. Yerel kaynak kurulumu için
checkout'u güncelledikten sonra `codex plugin add divan@divan` yeterlidir.

- **`plugin` komutu yok:** kullandığın Codex sürümü/yüzeyi plugin yönetimini desteklemiyor
  olabilir. Codex'i güncelle veya desteklenen uygulamanın plugin ekranını kullan.
- **Divan listede var ama etkin değil:** aynı isimdeki marketplace kaynağını ve plugin
  durumunu incele; tekrar kur ve yeni sohbet aç.
- **Bağlantı/izin hatası:** Divan, erişemediği işlemi belirtir. Hangi hesap veya aracın
  gerektiğini açıklamadan senden anahtar istememelidir; anahtarları sohbete yapıştırma.
- **Bir servis öneriliyor:** amacını, resmi kaynağını, kapsamını, maliyetini ve nasıl
  doğrulanacağını sorabilirsin. Katalogda görünmesi kurulu olduğu anlamına gelmez.

## First task in English

For Codex, install with the commands above, check the plugin list, and open a new session
in your project. Tell Divan the outcome you need:

> Divan, people can submit this order twice. Find the cause, fix it, and show how you checked it.

Divan follows the language you request, keeps your existing project conventions,
chooses relevant tools, and reports meaningful progress. Ask for status without
restarting the task. It asks for missing decisions that affect the result and ends
with what changed, observed checks, how to use it, and any remaining blocker.

For updates, upgrade the marketplace, reinstall the plugin, and start a new session.
The plugin has no separate service or API key requirement; your application's own
dependencies are evaluated only when needed.
