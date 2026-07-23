# Hızlı Başlangıç

Divan'ı kullanmak için skill veya ajan adı ezberlemen gerekmez. Önce hedefini
söyle, sonra Divan'ın kanıt zincirini izle. Divan yerel bir skill/plugin
dağıtımıdır; model veya runtime değildir. Güncel v1 karnesi **7/8** kapının
geçtiğini, bağımsız kullanıcı kanıtının beklediğini gösterir. Ürün sözleşmesi:
[[Topluluk Standartları|Topluluk-Standartlari]].

## 1. Beş dakikalık güvenli yolu çalıştır

Önce yazmayan kurulum önizlemesi, sonra aynı sabit sürümün uygulaması:

```powershell
python scripts/divan.py install --host both --ref v0.14.0
python scripts/divan.py install --host both --ref v0.14.0 --execute
```

Durumu değiştirmeyen doctor ve kontrollü yükseltme:

```powershell
python scripts/divan.py doctor --host both --ref v0.14.0
python scripts/divan.py update --host both --ref v0.14.0
python scripts/divan.py update --host both --ref v0.14.0 --execute
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

## 2. Niyetini ferman olarak yaz

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

## 3. Teslimde beş kanıtı ara

1. Ne istendiği ve hangi varsayımların yapıldığı.
2. Uygulanan kısa plan.
3. Değişen gerçek dosyalar.
4. Test/CI/tarayıcı çıktısı.
5. `main`, release ve canlı durumunun birbirinden doğru ayrılması.

Canlı ferman seçici: https://trugurpala.github.io/divan/#basla

Sorular, tekrar üretilebilir hatalar, güvenlik ve öneriler için yollar:
[SUPPORT.md](../SUPPORT.md).
