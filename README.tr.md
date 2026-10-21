# Divan

**Vibe coding, engineered.**

[Tanıtım sitesi](https://trugurpala.github.io/divan/) · [English](README.md) · [İlk kullanım](docs/getting-started.md) · [Editör ve ajanlar](docs/compatibility.md) · [Güncel ön sürüm](https://github.com/trugurpala/divan/releases/tag/v2.0.0-alpha.5) · [Geliştirme](docs/development.md)

Divan, doğal dille anlattığın yazılım işini projeyi anlayarak uygulama, hata giderme,
inceleme ve doğrulanmış teslime taşır. Codex eklentisi olarak veya aynı yedi Agent
Skills becerisini destekleyen başka bir kodlama ajanında kullanabilirsin.

> Kayıt düğmesine iki kez basınca iki sipariş oluşuyor. Kök nedeni bul, düzelt ve nasıl denediğini göster.

Sonucu kendi dilinle anlat; isteğinin başına “Divan” yazman gerekmez. Teslimde
çalışan değişikliği, gerçekten yapılan testleri
ve varsa kalan engeli gör. İçeride hangi becerinin veya alt ajanın seçileceğini bilmen gerekmez.

**Divan nerede?** Eklenti kurulduktan sonra Codex'te proje klasöründe açtığın yeni
sohbette çalışır. "Bu projeyi incele ve sonraki yararlı değişikliği söyle" diye
başlayabilirsin; isteğin başına Divan adını yazman gerekmez. Aynı beceriler uyumlu
kodlama ajanlarına proje bazında da
kurulur. Kaynak deposu ayrı bir uygulama veya canlı servis değildir.

Codex eklentisi yerel proje dosyaları ve komut çalıştırma erişimi gerektirir;
tarayıcıdaki genel ChatGPT sohbetinde bu erişim varmış gibi davranmaz. Kurulu
olması da oturumun dosya ve komut izinlerini değiştirmez.

İlk kez kullanırken becerinin gerçekten açıldığını doğrulama yolu
[ilk kullanım rehberinde](docs/getting-started.md) var.

## Kurulum

### Codex eklentisi

Repo marketplace'ini ekle, ardından proje klasöründe yeni sohbet aç:

```bash
codex plugin marketplace add trugurpala/divan --ref main
codex plugin add divan@divan
```

Desteklenen Codex yüzeyinde marketplace üzerinden **Divan** eklentisini de seçebilirsin. Günlük kullanım doğal dildir; ayrı bir Divan komut dili öğrenmen gerekmez. Yerel kaynak koddan kurulum için [geliştirme rehberini](docs/development.md) kullan.

### Diğer kodlama ajanları

Node.js 22.20+ varsa Divan'ı kullanacağın proje klasöründe çalıştır:

```sh
npx --yes skills@1.7.4 add https://github.com/trugurpala/divan/tree/main/plugins/divan/skills --skill '*'
```

Kurulum ekranından ajanını ve proje kapsamını seç. Yedi beceriyi birlikte tut;
aynı iş akışının parçalarıdır. Açık kaynak [Vercel Skills CLI](https://github.com/vercel-labs/skills)
kurulum sırasında kod indirebilir ve seçtiğin kapsama beceri dosyalarını yazar.
Editörü kurmaz veya yeni araç erişimi vermez.

| Nerede? | Kurulum yolu |
| --- | --- |
| Codex | Yukarıdaki eklenti veya taşınabilir beceriler; aynı projede birini seç |
| Claude Code | Taşınabilir kurulumda `--agent claude-code` |
| Cursor | Taşınabilir kurulumda `--agent cursor` |
| GitHub Copilot | Beceri destekleyen yüzeyde `--agent github-copilot` |
| Diğer Agent Skills uygulamaları | Uygulamanın keşif dizinini ve kurucunun destek listesini kontrol et |

[Uyumluluk, kurulum kanıtı, güncelleme ve kaldırma rehberi](docs/compatibility.md)
ayrıntıları açıklar. Dosyanın kurulması, uygulamada algılanması ve gerçek işte başarı
ayrı kontrollerdir; her editör ve modelde uçtan uca test edildiği iddia edilmez.

## Kullanım

```text
Bu projeyi incele.
Bu özelliği en küçük doğru değişiklikle yap.
Bu hatanın kök nedenini bul ve düzelt.
Gerçekten bitti mi kontrol et.
```

İstediğin sonucu kendi dilinle anlat. Yazım hatalarını düzeltmen, teknik terimleri
bilmen veya hangi becerinin çalışacağını seçmen gerekmez. Beceri etkin olduğunda Divan mevcut projeyi okur,
uygun araçları seçer, çalışırken anlamlı gelişmeleri bildirir ve sonucu kontrol eder.

```text
Sipariş formunda adres bazen kayboluyo. Düzelt ve nasıl denediğini göster.
Improve this form without changing the design. Explain the result in English.
Kaldığımız yerden devam et. Ne çalışıyor, ne eksik, sade anlat.
```

Ürünün sonucunu veya dışarıda yapılacak işlemin kapsamını değiştiren eksik bilgi varsa
sorar; rutin mühendislik kararlarını kendisi verir. [İlk kullanım rehberi](docs/getting-started.md)
kurulumu, örnek işleri, ilerleme bildirimlerini ve sık karşılaşılan sorunları açıklar.

Eksik araç gerektiğinde kurulu beceri, yapılandırılmış MCP, oturumda kullanılabilen araç ve çalışan servis durumunu ayrı doğrular. Gerekli kurulumu amacı, kaynağı ve etkisiyle sunar. Proje kuralları ve kararları kısa, bağlantılı Markdown belgelerinde saklanır. [Belge haritası](docs/README.md) ve [50 maddelik kaynak rehberi](docs/reference-library.md) yalnız ilgili olduğunda okunur; 50 araç otomatik kurulmaz.

## Mimari

- tek beceri kaynağı ve yerel Codex eklentisi;
- 7 odaklı çekirdek skill;
- yalnız gerektiğinde yüklenen progressive-disclosure mühendislik referansları;
- deterministik doğrulama ve paketleme;
- MCP server, hosted backend, özel agent runtime veya paketlenmiş UI yok;
- mevcut hatta yayınlanan lifecycle hook yok.

Yayınlanabilir paket `plugins/divan/` altındadır.

| Beceri | Görevi |
| --- | --- |
| `divan` | İsteği koordine eder, ilgili sonraki adımı seçer |
| `repo-audit` | Projeyi ve erişilebilir yetenekleri inceler |
| `implementation-plan` | Doğrulanabilir değişiklikleri planlar ve uygulatır |
| `root-cause-debug` | Hatayı üretir, kök nedenini bulur ve düzeltir |
| `quality-review` | Mühendislik ve kullanıcı deneyimi risklerini inceler |
| `completion-proof` | Tamamlandı demeden sonucu doğrular |
| `project-contract` | Proje kurallarını ve devam notlarını korur |

Araçlar, hesap doğrulaması, çalıştırma izinleri ve alt ajanlar kullanılan uygulamadan
gelir. Divan kurulumu kendiliğinden API bağlantısı eklemez veya uygulama kısıtını kaldırmaz.

## Kalite modeli

Divan kaliteyi yalnız kod stili olarak görmez. İlgili işlerde correctness, security, reliability, type/API sınırları, database bütünlüğü, i18n, responsive davranış, accessibility, loading/empty/error durumları, network resilience, performance, observability, dependency disiplini, testler ve kanıta dayalı definition of done kontrol edilir.

## Doğrulama

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/package_divan_v2.py
```

Windows'ta `./scripts/check.ps1` yeterlidir. Mevcut Python 3.12+ kurulumunu veya varsa Codex'in hazır Python ortamını bulur; paket yüklemez. CI, Python 3.13 ile Linux ve Windows üzerinde tam test kümesini çalıştırır.

Bu mekanik kontroller repo ve paket bütünlüğünü kanıtlar; model doğruluğu veya hız artışı iddiası değildir.

[Tekrarlanabilir sipariş yarışı görevi](evals/order-concurrency/README.md) ayrı bir
davranış kontrolüdür. Aynı başlangıç kodunda Divan becerisini elle okuyan ajan ve
becerisiz kontrol ajanı iki eşzamanlılık durumunu da çözdü. Bu tek görevde kalite
üstünlüğü gözlenmedi; Codex'in beceriyi kendiliğinden açtığı da doğrulanmadı.

## Bakım

[Tanıtım setinde](docs/launch-kit.md) düzenlenebilir Figma görselleri, Türkçe paylaşım kartı ve doğrulanabilir kısa metin bulunur.

Gerçek görev sonucunu veya hatayı [görev bildirim formuyla](https://github.com/trugurpala/divan/issues/new/choose)
paylaş: uygulama/sürüm, kurulum yolu, gözlenen sonuç ve sır içermeyen küçük bir örnek
ekle. Başarılı ve başarısız denemeler değerlidir. Katkı için [AGENTS.md](AGENTS.md) ve
[geliştirme rehberini](docs/development.md) oku; odaklı değişikliğin ardından kontrolleri çalıştır.

Güncel Codex eklentisinin kurulumu için yukarıdaki repo marketplace'ini kullan.

## Lisans

[MIT](LICENSE). Her taşınabilir beceri aynı lisans bildirimini içerir. Dış keşif
katalogları başvuru kaynağıdır; paketlenmiş bağımlılık veya ortaklık değildir.
