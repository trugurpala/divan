# SSS

**Neden repoları tek tek fork'lamadık?**
Marketplace tek repo olmak zorunda: `/plugin marketplace add` tek depo okur.
Dört ayrı fork tek kurulum komutu oluşturamaz. Bu yüzden vendoring: seçili
skill'ler lisans ve telifleriyle tek çatıya kopyalanır (bkz. UPSTREAM.md).
MIT/Apache-2.0 buna açıkça izin verir.

**Neden MCP değiliz?**
Ürünümüz prosedürel bilgi (nasıl yapılır). Skill'ler aşamalı yüklemeyle
token-verimli ve tüm Agent Skills uyumlu ajanlarda çalışır. MCP canlı
veri/aksiyon içindir; ihtiyaç doğunca (v2) eklenir.

**Neden uygulama değiliz?**
GitHub + `/plugin` dağıtımı sıfır altyapı maliyeti demek. Hosted premium
(web app + ödeme) v2'nin işi — bkz. BLUEPRINT.md yol haritası.

**Başka ortama taşısak plan devam eder mi?**
Evet. Tek gerçek kaynak repodaki BLUEPRINT.md'dir; durum günlüğü oradadır.
Herhangi bir ajan/insan o dosyayı okuyup kaldığı yerden sürer.

**Divan kendini nasıl geliştirir?**
`vezir-yetistirme` skill'i + CONTRIBUTING.md yolu: topluluk yeni skill önerir,
ajan iskeletler, CI teftişi geçen PR birleşir.
