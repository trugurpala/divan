# SSS

Divan yerel bir skill/plugin dağıtımıdır; model veya ayrı bir üçüncü taraf
runtime değildir. Kendi modüler Divan Engine çekirdeği aynı repoda yaşar. On
bir zorunlu ürün kuralı [[Topluluk Standartları|Topluluk-Standartlari]]
sayfasındadır. v1 durumu **7/8** kapıdır; schema-2 temiz-proje mekanizması hazır,
fakat yayımlanmış mekanizmayla üretilmiş gerçek makbuz beklenmektedir.

**Son v1 kanıtını kim verebilir?**
Kişinin bakımcı veya dış kullanıcı olması teknik sonucu değiştirmez. Divan'dan
ayrı gerçek projede doğrulanmış hedef için önce yazmayan plan, sonra uygulama
çalıştırılır:

```powershell
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
```

Yalnız `valid-clean-room-adoption` geçerlidir; bu sonuç üçüncü taraf onayı veya
pazar benimsemesi iddia etmez.

**Neden repoları tek tek fork'lamadık?**
Marketplace tek repo olmak zorunda: `/plugin marketplace add` tek depo okur.
Dört ayrı fork tek kurulum komutu oluşturamaz. Bu yüzden vendoring: seçili
skill'ler lisans ve telifleriyle tek çatıya kopyalanır (bkz. UPSTREAM.md).
MIT/Apache-2.0 buna açıkça izin verir.

**Neden MCP değiliz?**
Ürünümüz prosedürel bilgi (nasıl yapılır). Skill'ler aşamalı yüklemeyle
token-verimli ve tüm Agent Skills uyumlu ajanlarda çalışır. MCP canlı
veri/aksiyon içindir; bağlandığında sağlayıcı katmanında kalır ve tek başına
yetki yaratmaz.

**Company OS ve Project OS ne oldu?**
Ürün adı hep Divan'dır. İcra çekirdeğinin kanonik adı **Divan Engine**,
yetki modelinin adı **Divan Nizamı**, hedef repoya kurulan katmanın adı
**Divan Proje Sözleşmesi**dir. Eski `Company OS`, `Project OS`, `/company` ve
`company-validate` adları v1 boyunca uyumluluk yüzeyi olarak korunur.

**Divan başka bir repoya veya agent runtime'ına bağımlı mı?**
Hayır. Dokuz modüllü çekirdek bu repoda ve Python standart kütüphanesiyle
çalışır. Dış repolar yalnız araştırma kaynağı; GitHub, Context7 veya Vercel gibi
bağlantılar ise sınırları belli sağlayıcılardır. Divan'ın çekirdeği olmazlar.

**Neden uygulama değiliz?**
GitHub + `/plugin` dağıtımı sıfır altyapı maliyeti demek. Hosted premium
(web app + ödeme) v2'nin işi — bkz. BLUEPRINT.md yol haritası.

**Başka ortama taşısak plan devam eder mi?**
Evet. Tek gerçek kaynak repodaki BLUEPRINT.md'dir; durum günlüğü oradadır.
Herhangi bir ajan/insan o dosyayı okuyup kaldığı yerden sürer.

**Divan kendini nasıl geliştirir?**
`vezir-yetistirme` skill'i + CONTRIBUTING.md yolu: topluluk yeni beceri önerir,
ajan iskeletler, CI teftişi geçen PR birleşir.

**Soru, hata veya güvenlik bildirimi nereye gider?**
Kullanım sorusu Discussions Q&A'ya, tekrar üretilebilir hata bug formuna,
güvenlik açığı özel advisory'ye gider. Yetenek ve temiz-proje kabul kanıtı için de
ayrı formlar vardır: [SUPPORT.md](../SUPPORT.md).
