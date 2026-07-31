# Hızlı Başlangıç

Divan'ı kullanmak için skill veya ajan adı ezberlemen gerekmez. Önce hedefini
söyle, sonra Divan'ın kanıt zincirini izle. Hükümdar sensin; kapsamı yalnız sen
genişletebilirsin. Divan bir model veya ayrı üçüncü taraf runtime değildir:
Divan Engine aynı repodaki modüler icra çekirdeği, Divan Nizamı ise yetki
düzenidir. Güncel v1 hazırlık karnesi **8/8** kapının geçtiğini gösterir:
değişmez v0.18.5 ile Divan'dan ayrı gerçek projede üretilen schema-2 makbuz
çevrimdışı yeniden doğrulandı. Ürün sözleşmesi:
[[Topluluk Standartları|Topluluk-Standartlari]].

Sadrazam'ın ilerleme sözleşmesi, çalışma uzadığında host ajanını ham teknik
günlük yerine işe başlarken ve anlamlı aşama değişimlerinde ne yaptığını, bunun
neden önemli olduğunu ve sırada ne bulunduğunu kısa biçimde söylemeye
yönlendirir.

## Yerel Seyir ekranını aç

Divan'ın ne yaptığını tarayıcıda sade biçimde izlemek için:

```powershell
python scripts/divan.py status --project . --open --lang auto
```

Komut kullanılabilir bir portu kendisi seçer ve gerçek adresi yazdırır. Seyir
salt okunurdur, yalnız `127.0.0.1` üzerinde çalışır ve `Ctrl+C` ile kapanır.
Sabit bir örnek URL'yi açmak yerine her zaman komutun ürettiği adresi kullan.

## 1. Beş dakikalık güvenli yolu çalıştır

Aşağıdaki örnekler Güncel kaynak sürümünü sabitler. Güncel kaynak Son yayımlanan
sürümden farklıysa bütün `--ref` komutlarında Son yayımlanan sürümü kullan.
Yalnız değişmez tag ve GitHub Release'i bulunan bir ref'i kur. Önce yazmayan
kurulum önizlemesi, sonra aynı sabit sürümün uygulaması:

```powershell
python scripts/divan.py install --host both --ref v1.0.1
python scripts/divan.py install --host both --ref v1.0.1 --execute
```

Durumu değiştirmeyen doctor ve kontrollü yükseltme:

```powershell
python scripts/divan.py doctor --host both --ref v1.0.1
python scripts/divan.py update --host both --ref v1.0.1
python scripts/divan.py update --host both --ref v1.0.1 --execute
```

Kesinti/başarısızlıkta günlüğün gösterdiği yolla geri al:

```powershell
python scripts/divan.py recover "C:\Users\you\.divan\transactions\upgrade-20260721-120000.json"
```

Örnek yolu doctor çıktısındaki tam `recovery_command` ile değiştir. Kurulumu
yalnız bu işlemin oluşturduğu Divan kayıtlarıyla geri almak/kaldırmak için:

```powershell
python scripts/divan.py recover "C:\Users\you\.divan\transactions\install-20260721-120000.json"
```

Host'a göre elle kaldırma: [docs/Kaldirma.md](Kaldirma.md). Ayrıntı ve tek-host
seçenekleri: [[Kurulum]].

## 2. Divan Engine düzenini gör

Dokuz modülü, bağımlılık grafiğini ve Hükümdardan başlayan yetki zincirini
projeyi değiştirmeden doğrula:

```powershell
python scripts/divan.py architecture --json
python scripts/divan.py validate
```

Ayrıntı: [[Divan Engine|Divan-Engine]].

## 3. Hedef projenin sahiplik ve sapmasını denetle

Host güncellemesi Divan eklentilerini; project güncellemesi kurulu Divan Proje
Sözleşmesi yüzeylerini değiştirir. Önce salt-okunur durumu ve dry-run planını
gör:

```powershell
python scripts/divan.py project status --project . --json
python scripts/divan.py project update --project .
python scripts/divan.py project repair --project .
```

Yalnız plan doğruysa `--execute` ekle. `project update` kullanıcı değişikliğini
ezmez; `project repair` yalnız sahiplik kaydındaki eksik tam Divan dosyasını
geri getirir. Kalite sözleşmesi için `audit`, sahiplik/sapma için
`project status` kullanılır. Ayrıntı:
[[Divan Proje Sözleşmesi|Project-Contract]].

## 4. Niyetini ferman olarak yaz

Kopyalayıp doldur:

```text
Ferman: [istediğim sonucu yaz].
Önce mevcut projeyi tanı, en küçük planı çıkar, uygula, test et;
README/plan/canlı yüzey etkileniyorsa aynı turda güncelle.
Kanıtsız “bitti” deme ve sıradaki kesin adımı kaydet.
```

Örnekler:

- “Kullanıcı girişini baştan sona ekle.”
- “Bu hatanın kök nedenini bul, regresyon testiyle düzelt.”
- “Landing'i özgün bir görsel yönle yeniden tasarla ve tarayıcıda doğrula.”
- “Bu repoyu tanı; mimari, risk ve sıradaki işi kalıcı deftere yaz.”

## 5. Teslimde beş kanıtı ara

1. Ne istendiği ve hangi varsayımların yapıldığı.
2. Uygulanan kısa plan.
3. Değişen gerçek dosyalar.
4. Test/CI/tarayıcı çıktısı.
5. `main`, release ve canlı durumunun birbirinden doğru ayrılması.

## 6. Gerçek işi temiz-proje kanıtına bağla

Doğrulanmış hedefin varsa önce hiçbir şey yazmayan planı gör. Plan doğruysa
uygula; bakımcı veya dış kullanıcı olman teknik sonucu değiştirmez:

```powershell
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası>
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası> --execute
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
```

VERIFIED geçişi gerçek kod ve test/doğrulama dosyalarını atomik olarak hedef
makbuzuna bağlar; yalnız plan dosyası kanıt sayılmaz.

Yalnız `valid-clean-room-adoption` sonucu v1'e adaydır. Bu kayıt bağımsız
kullanıcı sayısı veya verim artışı iddiası değildir; gerçek test/regresyon
kontrollerinin gizlilik sınırlı makine kanıtıdır.

Canlı ferman seçici: https://trugurpala.github.io/divan/#basla

Sorular, tekrar üretilebilir hatalar, güvenlik ve öneriler için yollar:
[SUPPORT.md](../SUPPORT.md).
