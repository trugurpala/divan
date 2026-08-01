# Divan Wiki · v1.2.0

![Divan'ın doğrulanmış teslim mührü](https://raw.githubusercontent.com/trugurpala/divan/main/docs/assets/github/muhurdar-seal.svg)

**Hükümdar sensin.** Divan, vibe coder'ın niyetini planlı, denetlenebilir ve
kalıcı bir teslim akışına çeviren tek üründür: tek repo, modüler çekirdek,
5 paket, 42 beceri, yerel Seyir ekranı ve kanıtlı denetim. Aynı paketler Claude
Code/Desktop Code ve Codex'e yerel plugin olarak kurulur; proje hafızası,
davranış eval'i ve yayın teftişi aynı çatıdadır.

Divan bir model veya ayrı üçüncü taraf runtime değildir. Divan Engine, bu
repodaki modüler ve stdlib-only icra çekirdeğidir; Divan Nizamı ise yetkinin
Hükümdardan başlayıp daralarak devredilmesini belirler. İkisi de aynı Divan
ürününün parçalarıdır; başka repo veya harici agent runtime zorunlu değildir.
v1 hazırlık durumu **8/8** kapıdır: değişmez v0.18.5,
Windows 11, Codex ve Divan'dan ayrı gerçek projede makinece doğrulanabilir
temiz-proje kanıtı üretti; gizlilik incelemeli makbuz çevrimdışı doğrulandı.

Son kapı kişinin kimliğini değil, Divan'dan ayrı gerçek projedeki makine
kanıtını ölçer. Önce yazmayan planı gör, sonra aynı planı uygula:

```powershell
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası>
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası> --execute
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
```

İlk iki komut gerçek kod/test kanıtını hedefe atomik bağlar; yalnız plan
dosyasıyla VERIFIED olunamaz. Son iki komut yayımlanmış runner, host ve test
sonucunu gizlilik sınırlı makbuza dönüştürür.

Yeni Sadrazam sözleşmesi, host ajanını başlangıçta ve anlamlı aşama
değişimlerinde şu an ne olduğunu, neden önemli olduğunu ve sırada ne bulunduğunu
kısa insan diliyle bildirmeye yönlendirir. Komut, dosya ve alt ajan günlükleri
yalnız gerçek bir engeli açıklıyorsa öne çıkar. Repo testleri bu sözleşmenin
dağıtımını doğrular; yeni bir gerçek-ajan A/B sonucu iddia etmez.

Yayımlanan v0.18 hattındaki **Nizâm-ı Sefer**, fermanı risk ve yapısal karmaşıklığa
göre görev grafiğine, en fazla üç bağımsız çalışma hattına ve kalıcı
`route.json` kaydına dönüştürür. Host belirsizse sıralı çalışır; model ve bağlam
kapasitesini doğrulamadan varmış gibi göstermez. Bu özellik değişmez
`v0.18.0` kurulumunun parçasıdır.

> **Güncel kaynak:** v1.2.0 · **Son yayımlanan:** v1.1.0 · `main` ürün kaynağı · Wiki bu repodaki
> `docs/*.md` kaynaklarından otomatik yayımlanır. Elle Wiki düzenlemek yerine
> kaynak belgeyi değiştir; teftiş ve eşitleme zinciri farkı yakalasın.

v0.18.2, önceki planlama ve Codex Desktop kurulum sınırlarını korurken yerel
Seyir ekranını, tek dosyalık doğrulanabilir `divan.pyz` kurucusunu, kanıta
dayalı timeout politikasını ve Linux/macOS/Windows yaşam döngüsü kanıtını
yayımlar. İkinci ürün, repo veya üçüncü taraf runtime oluşturmaz.
Seyir, uzun kalite kapılarında artık ölçülmüş normal bekleme aralığını ve dikkat
eşiğini kullanıcı dostu dille gösterir; sessiz ekranı çökme zannettirmez.
v1.1.0 yayımlanan hattı ayrıca Divan'a ait geçici worktree'leri, fixture
projelerini ve skill içi yardımcı klasörleri normal kullanıcı workspace'i gibi
göstermez; sağlıklı doctor READY sonucunda durur ve takip ekranı gerçek proje
köküne odaklı kalır.

## Fermanını seç

| Niyetin | İlk durak | Sonuç |
|---|---|---|
| Bir özellik çıkar | [[Hızlı Başlangıç|Hizli-Baslangic]] | Brief → plan → TDD → kanıt → yayın |
| Bir bug düzelt | [[Test ve Teftiş|Test-ve-Teftis]] | Kök neden → regresyon testi → dar düzeltme |
| Arayüz tasarla | [[Vibe Coder İçin Değer|Vibe-Coder-Icin-Deger]] | Estetik yön → sistem → tarayıcı kanıtı |
| Divan'ı kur | [[Kurulum]] | Hostuna uygun en küçük kurulum yolu |
| Projenin ilerlemesini izle | [[Hızlı Başlangıç|Hizli-Baslangic]] | Yerel Seyir → şu anki görev → sıradaki adım |
| Divan'ın sürüm durumunu gör | [[Durum ve Yol Haritası|Durum-ve-Yol-Haritasi]] | Yayımlanan, açık ve sıradaki sürüm ayrımı |

Canlı etkileşimli seçici: https://trugurpala.github.io/divan/#basla

## Rehberler

- [[Hızlı Başlangıç|Hizli-Baslangic]] — ilk beş dakika
- [[Kurulum]] — Claude Code, Codex, Cursor ve diğer uyumlu hostlar
- [[Host Uyumluluğu|Host-Uyumlulugu]] — resmî kaynaklı yetenek ve kanıt matrisi
- [[Divan Engine|Divan-Engine]] — tek ürün, dokuz modül ve Hükümdar öncelikli nizam
- [[Divan Proje Sözleşmesi|Project-Contract]] — hedef repoya kurulan gözetimli sözleşme
- [[Vibe Coder İçin Değer|Vibe-Coder-Icin-Deger]] — kurunca ne değişir?
- [[Beceri Kataloğu|Beceri-Katalogu]] — 42 beceri ve tetikleyicileri
- [[Aday Meclisi|Aday-Meclisi]] — sürekli keşif ve ADOPT/ADAPT/REFERENCE/REJECT kararları
- [[Orkestrasyon Kararı|Orkestrasyon-Karari]] — Ocak, Sefer ve Ordu
- [[Test ve Teftiş|Test-ve-Teftis]] — yerel, CI, tarayıcı ve yayın kanıtı
- [[Standartlar ve Limitler|Standartlar-ve-Limitler]] — kabul kapıları
- [[Topluluk Standartları|Topluluk-Standartlari]] — DCS-001–DCS-011 ürün sözleşmesi
- [[OpenAI ve Codex Uyumluluğu|OpenAI-ve-Codex-Uyumlulugu]] — runtime/skill sınırı
- [[GitHub Kullanımı|GitHub-Kullanimi]] — repo, Actions, Pages ve Wiki
- [[Mühürdar]] — Divan'ın kanıt bekçisi
- [[Durum ve Yol Haritası|Durum-ve-Yol-Haritasi]] — bugün ve sıradaki sürüm
- [[v1 Hazırlık Karnesi|V1-Hazirlik]] — hangi kabul kapısı gerçekten geçti?
- [[SSS]] · [[Kaldırma|Kaldirma]]

## Tek doğru kaynak

- [README Türkçe](https://github.com/trugurpala/divan/blob/main/README.tr.md)
- [README English](https://github.com/trugurpala/divan/blob/main/README.md)
- [CHANGELOG](https://github.com/trugurpala/divan/blob/main/CHANGELOG.md)
- [BLUEPRINT](https://github.com/trugurpala/divan/blob/main/BLUEPRINT.md)
- [Kaynak kod](https://github.com/trugurpala/divan)
- [Destek yolları](https://github.com/trugurpala/divan/blob/main/SUPPORT.md)

Wiki yol gösterir; sürüm ve mimari kararların son sözü repodaki `VERSION` ve
`BLUEPRINT.md` dosyalarındadır.
