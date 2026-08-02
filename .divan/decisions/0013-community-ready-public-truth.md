# ADR 0013: Topluluk yüzeylerinde yayımlanmış sürüm gerçeği

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-02
- **Karar sahibi:** Hükümdar

## Karar

Divan, topluluk projesi olarak yayımlanmış sürüm bilgisini bütün ilk temas
yüzeylerinde aynı kaynaktan gösterecek. `VERSION`, İngilizce README, Türkçe
README ve sürüm rozetleri birlikte denetlenecek. Bir yüzey eski sürümü gösterirse
kalite kapısı başarısız olacak.

## Neden

Yeni kullanıcı önce README ve rozetleri görür. Bir dosyada güncel sürüm, diğerinde
eski sürüm görünmesi kurulum kararını ve yayın güvenini bozar. Bu, kod davranışı
değişmese bile gerçek bir topluluk bakım riskidir.

## Sınırlar

Tarihsel CHANGELOG ve kanıt kayıtları değiştirilmez. Yalnız güncel kurulum ve
ürün durumunu anlatan yüzeyler otomatik kapıya alınır. Türkçe ve İngilizce metin
aynı bilgiyi doğal dilleriyle anlatır; kelime kelime eşlenmesi gerekmez.

## Kanıt

`python scripts/prose.py --check --json` kaynak satırını, İngilizce ve Türkçe
rozetleri denetler. Bu karar yeni runtime bağımlılığı veya başka repo kodu
eklemez.
