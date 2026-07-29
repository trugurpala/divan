# Divan Wiki · v0.17.0

![Mühürdar](https://raw.githubusercontent.com/trugurpala/divan/main/docs/assets/muhurdar-idle.png)

**Hükümdar sensin.** Divan, vibe coder'ın niyetini planlı, denetlenebilir ve
kalıcı bir teslim akışına çeviren tek üründür. Aynı 5 paket/41 beceri Claude
Code/Desktop Code ve Codex'e yerel plugin olarak kurulur; proje hafızası,
davranış eval'i ve yayın teftişi aynı çatıdadır.

Divan bir model veya ayrı üçüncü taraf runtime değildir. Divan Engine, bu
repodaki modüler ve stdlib-only icra çekirdeğidir; Divan Nizamı ise yetkinin
Hükümdardan başlayıp daralarak devredilmesini belirler. İkisi de aynı Divan
ürününün parçalarıdır. v1 durumu **7/8** kapıdır: bağımsız kullanıcı kabul
kanıtı hâlâ bekleniyor.

> **Güncel kaynak:** v0.17.0 · **Son yayımlanan:** v0.17.0 · `main` ürün kaynağı · Wiki bu repodaki
> `docs/*.md` kaynaklarından otomatik yayımlanır. Elle Wiki düzenlemek yerine
> kaynak belgeyi değiştir; teftiş ve eşitleme zinciri farkı yakalasın.

v0.17.0 dokuz modüllü Divan Engine sözleşmesini, Hükümdar öncelikli yetki
zincirini ve eski adlar için sınırlı uyumluluğu yayımlar. PR #49, bütün zorunlu
CI kapıları, değişmez tag/Release, checksum ve attestation bağlı beş varlık,
Pages ve Wiki yayın kanıtında doğrulanmıştır.

## Fermanını seç

| Niyetin | İlk durak | Sonuç |
|---|---|---|
| Bir özellik çıkar | [[Hızlı Başlangıç|Hizli-Baslangic]] | Brief → plan → TDD → kanıt → yayın |
| Bir bug düzelt | [[Test ve Teftiş|Test-ve-Teftis]] | Kök neden → regresyon testi → dar düzeltme |
| Arayüz tasarla | [[Vibe Coder İçin Değer|Vibe-Coder-Icin-Deger]] | Estetik yön → sistem → tarayıcı kanıtı |
| Divan'ı kur | [[Kurulum]] | Hostuna uygun en küçük kurulum yolu |
| Projenin durumunu gör | [[Durum ve Yol Haritası|Durum-ve-Yol-Haritasi]] | Yayımlanan, açık ve sıradaki iş ayrımı |

Canlı etkileşimli seçici: https://trugurpala.github.io/divan/#basla

## Rehberler

- [[Hızlı Başlangıç|Hizli-Baslangic]] — ilk beş dakika
- [[Kurulum]] — Claude Code, Codex, Cursor ve diğer uyumlu hostlar
- [[Divan Engine|Divan-Engine]] — tek ürün, dokuz modül ve Hükümdar öncelikli nizam
- [[Divan Proje Sözleşmesi|Project-Contract]] — hedef repoya kurulan gözetimli sözleşme
- [[Vibe Coder İçin Değer|Vibe-Coder-Icin-Deger]] — kurunca ne değişir?
- [[Beceri Kataloğu|Beceri-Katalogu]] — 41 beceri ve tetikleyicileri
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
