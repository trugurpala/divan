# Divan

![Divan günlük dille yazılan isteği doğrulanmış teslime dönüştürür](docs/assets/github/hero.png)

[![Kalite kapısı](https://github.com/trugurpala/divan/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/trugurpala/divan/actions/workflows/quality-gate.yml)
[![Kaynak hattı 1.3.4](https://img.shields.io/badge/kaynak-1.3.8-1E4FA8)](https://github.com/trugurpala/divan/releases/latest)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-2ea44f)](LICENSE)
[![Doğrulanmış hostlar](https://img.shields.io/badge/doğrulanmış%20hostlar-Claude%20Code%20%2B%20Codex-14b8a6)](#host-uyumluluğu-ve-kanıt-düzeyleri)
[![Topluluk için ücretsiz](https://img.shields.io/badge/topluluk%20için-ücretsiz-d4a72c)](#topluluk-için-ücretsiz)

**Türkçe** · [English](README.md) · [Wiki](https://github.com/trugurpala/divan/wiki) · [Yol haritası](ROADMAP.md) · [Destek](SUPPORT.md)

> Bu, Divan'ın Türkçe ana sayfasıdır. İngilizce sürüm için [README.md](README.md) dosyasını açın.

Divan, kullandığınız kodlama ajanına plan, güvenli iş sırası, kalıcı proje
hafızası ve kanıtlanabilir teslim ekler. Sonucu günlük dille anlatırsınız.
Divan yalnız gereken yetenekleri seçer, işi görünür tutar ve doğrulanmayan
sonuca “bitti” demez.

> **Önemli sınır:** Divan bir model, bulut kodlama hizmeti veya haricî ajan
> çalışma zamanı değildir. Hostta bulunmayan aracı varmış gibi göstermez;
> test edilmemiş iddiayı kanıta dönüştürmez.

**Kaynak hattı:** v1.3.8 · **Yayımlanan paketler:** [GitHub Releases](https://github.com/trugurpala/divan/releases/latest) · **42 beceri** ·
**5 modüler paket** · **8/8 hazırlık kapısı**

## Hızlı bağlantılar

- [Divan ne işe yarar?](#divan-ne-işe-yarar)
- [Hangi kurulumu seçmelisiniz?](#hangi-kurulumu-seçmelisiniz)
- [Tek komutla kurulum](#tek-komutla-kurulum)
- [İlk gerçek iş](#ilk-gerçek-iş)
- [İşin bittiğini nasıl anlarsınız?](#hangi-kanıtlar-üretilir)
- [Soru sorun veya katkı verin](#topluluğa-katılın)

## Divan ne işe yarar?

Divan, bir isteği sınırlı plana, uygulama adımlarına, kontrollere ve teslim
makbuzuna çevirir. Kararları ve ilerlemeyi projede saklar; yeni oturum son
doğrulanmış durumdan devam eder. Son yetki proje sahibindedir. Divan ürün
kimliğinde bu role Hükümdar der; kullanıcıdan rol yapmasını istemez.

Divan şu işlerde kullanılır:

- planı ve regresyon testini atlamadan özellik geliştirmek veya hata düzeltmek;
- proje kurallarını ve kararlarını oturumlar arasında korumak;
- yalnız mevcut teknolojiye uyan becerileri seçmek;
- hazır, çalışıyor, doğrulanıyor, engelli ve tamamlandı durumlarını göstermek;
- “bitti” sözünü test, dosya, makbuz ve yayın kanıtına bağlamak.

## Divan ne yapmaz?

- Claude Code, Codex veya uyumlu başka bir hostun yerine geçmez.
- Bulduğu bütün popüler depoları kurmaz.
- Yerel Seyir verisini bulut hizmetine göndermez.
- Proje sahibinin yetkisi olmadan kapsamı büyütmez.
- Gerçek davranış değerlendirmesi olmadan hız veya kalite artışı iddia etmez.

## Nasıl çalışır?

```text
İsteğiniz
→ Ferman (sınırları belirlenmiş iş tanımı)
→ plan ve görev sırası
→ en küçük yeterli paket takımıyla uygulama
→ Teftiş (test ve kanıt kontrolü)
→ doğrulanmış teslim ve kalıcı proje hafızası
```

Plan ayrıca hazır görev kimliklerini ve owner, bağımlılık, gerekli kanıt,
shell-free argv ile ayrı manuel kontrollerini taşıyan tek deterministik ilk
görevi açıklar. İnsan çıktısı bunu `Sıradaki` diye gösterir; kayıt
`auto_execute: false` kullanır ve yürütme yetkisi vermez.

Yalnız standart Python kütüphanesini kullanan Divan Engine bu depoda yaşar.
Divan Nizamı, motorun çevresindeki sahip öncelikli yetki kuralıdır; ikinci bir
ürün değildir. Kurulan [Divan Proje Sözleşmesi](docs/Project-Contract.tr.md)
hedef projede geçerli kuralları, hedefleri ve kanıtları kaydeder.

## Hangi kurulumu seçmelisiniz?

| Durum | Seçim | Sonuç |
|---|---|---|
| Temiz bilgisayarda ilk kurulum | Release içindeki `divan.pyz` | Tek doğrulanmış dosya; repo klonlamadan kurulum |
| Divan'ı geliştirmek | Repo checkout | Kaynak, test ve yayın araçları |
| Host yerel eklentiyi destekliyor | Native profil | Komutlar, beceriler ve yaşam döngüsü |
| Yerel eklenti yolu kanıtlanamıyor | Doğrulanmış fallback | Yalnız beceri ve talimat; sahte native iddiası yok |

Claude Code ve Codex bugün doğrulanmış native hostlardır. Diğer Agent Skills
uyumlu hostlar yalnız belgelenen kanıt düzeyinde taşınabilir beceri kullanır.

## Ajanla kurulum

Bu depo adresini Codex veya Claude masaüstü uygulamasına verin ve şunu yazın:

```text
Bu GitHub deposundaki Divan'ı bilgisayarıma kur. Güvenli ve değişmez release
yolunu kullan, önce yazmayan önizlemeyi göster, kurulumu uygula, doctor ile
doğrula ve masaüstü uygulamasını ne zaman yeniden başlatmam gerektiğini söyle.
```

Ajan [`INSTALL_FOR_AGENTS.md`](INSTALL_FOR_AGENTS.md) dosyasını okur; en yeni
değişmez GitHub Release sürümünü bulur, checksum ve kaynak commit'ini doğrular,
önizler, uygular ve doctor sonucu `READY` olmadan kurulumu başarılı saymaz.
Diğer eklentilere dokunmaz. Başarılı sonuçtan sonra masaüstü uygulamasını
tamamen kapatıp yeni bir oturum açın. Günlük kullanım komut satırı değil,
doğal dildir.

## Tek komutla kurulum

### Nasıl kurulur?

Aynı değişmez sürümden `divan.pyz` ve checksum dosyasını indirin. Dosyayı
doğrulayın, yazmayan planı görün, sonra uygulayın.

```powershell
$tag = (Invoke-RestMethod "https://api.github.com/repos/trugurpala/divan/releases/latest").tag_name
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz" -OutFile divan.pyz
Invoke-WebRequest "https://github.com/trugurpala/divan/releases/download/$tag/divan.pyz.sha256" -OutFile divan.pyz.sha256
$expected = ((Get-Content .\divan.pyz.sha256 -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
$actual = (Get-FileHash .\divan.pyz -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "Divan bootstrap SHA-256 uyuşmuyor" }
python .\divan.pyz doctor --host codex --json
python .\divan.pyz install --host codex --profile auto
python .\divan.pyz install --host codex --profile auto --execute
```

Güvenilen repo checkout yolunda iki host kurulumu:

```powershell
python scripts/divan.py install --host both --ref v1.3.8
python scripts/divan.py install --host both --ref v1.3.8 --execute
python scripts/divan.py doctor --host both --ref v1.3.8
python scripts/divan.py update --host both --ref v1.3.8
python scripts/divan.py update --host both --ref v1.3.8 --execute
```

Yukarıdaki komut, indirmeden önce son yayımlanan etiketi bulur. Repo içindeki
komutlar yayımlanmış v1.3.4 etiketini sabitler. Silmeden önce
[kaldırma ve kurtarma](docs/Kaldirma.md) rehberini okuyun.
Native Codex makbuzu bekleyen marketplace'in istenen source/ref ve tam hedef
paket sözleşmesini kanıtlıyor, işlem öncesinde Divan marketplace veya eklentisi
bulunmuyorsa recovery commit ya da katalog özeti uyuşmazlığı için
`--confirm-pending-marketplace` tokenı gösterebilir. Bu önkoşullardan biri
kanıtlanamazsa token üretmeden güvenli biçimde durur. Bildirilen kök, commit ve
katalog özetini inceleyin. Tokenla ikinci çalıştırma tam parmak izini kaydeder
ama Codex'in yalnız ada göre çalışan silme komutunu çağırmaz. Marketplace hâlâ
aynı checkout ise gösterilen `codex plugin marketplace remove divan --json`
komutunu elle çalıştırın; ardından recovery komutunu yeniden çalıştırın.

En yeni taslak olmayan GitHub Release değişmez kurulum kaynağıdır. Ajan ve
bootstrap `main` dalından kurulum yapmaz.

## İlk gerçek iş

## Divan kuruluysa buradan başla

Paket veya beceri adı bilmeniz gerekmez. Projeyi açıp şunu yazın:

```text
Divan, bu işi devral. Önce mevcut durumu doğrula, kısa plan yap, en küçük doğru
değişikliği uygula, gerçek kontrolleri çalıştır ve kanıtı bana günlük dille
göster: [istediğiniz sonucu yazın]
```

Projeye Divan sözleşmesi eklemek için önce önizleyin, sonra uygulayın:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto
python scripts/divan.py init --project . --profile standard --locale auto --execute
python scripts/divan.py audit --project . --json
```

**İlk kurulum**, eklenti ve proje sözleşmesidir. Günlük kullanım, yukarıdaki
doğal dil isteğidir. **Bakım**, doctor, update, kurtarma veya kaldırmadır;
sıradan görev akışını bölmemelidir.

## Kullanıcı ekranda ne görür?

Divan mevcut sonucu, etkin adımın neden önemli olduğunu ve sırada ne bulunduğunu
kısa biçimde yazar. Teknik komutlar yalnız hatayı açıklıyor veya sonucu
kanıtlıyorsa öne çıkar. Görev durumu ile kanıt durumu birbirinden ayrılır.
Sade ilerleme, kullanıcıya kısa bir hikâye gösterirken ayrıntılı mühendislik
kanıtını arka planda erişilebilir tutar.

### Yerel Seyir ekranı

Seyir; hedef, görev, Git ve kanıt durumunu gösteren salt okunur yerel sayfadır.
Bulut hizmeti veya API anahtarı kullanmaz; yalnız `127.0.0.1` adresine bağlanır.

```powershell
python scripts/divan.py status --project . --open --lang auto
```

Divan boş portu seçer ve çalışan geçici adresi yazar. Sunucuyu `Ctrl+C` ile
durdurun; belgelerdeki örnek portu yeniden kullanmayın.

## Hangi kanıtlar üretilir?

![Ferman'dan canlı yayına Divan kanıt akışı](docs/assets/github/evidence-flow.png)

Göreve göre test özeti, değişen dosya parmak izi, hedef makbuzu, release
checksum'u, SPDX SBOM, attestation ve canlı geri okuma kanıtı üretilir.

```powershell
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası>
python divan-project.pyz goal advance --project . --goal <goal-id> --to verified --evidence <uygulama-dosyası> <test-veya-doğrulama-dosyası> --execute
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex
python divan-project.pyz adoption prove --project . --goal <goal-id> --host codex --execute
python divan-project.pyz adoption verify .divan/adoption/<proof-id>/adoption-receipt.json
```

Bu teknik kapıyı yalnız `valid-clean-room-adoption` karşılar. Sonuç bağımsız
kullanıcı sayısı, tavsiye, pazar benimsemesi veya kalite kazanımı değildir.

## Modüler paketler

| Paket | Ne zaman katılır? |
|---|---|
| `sadrazam` | Uçtan uca sahiplenme, kalıcı karar ve sınırlı görev devri |
| `core-pack` | Planlama, TDD, hata ayıklama, doğrulama ve kaynak inceleme |
| `ui-pack` | Arayüz yönü, host bağımsız yerel tasarım sistemi araması, ürün denetimi ve tarayıcı testi |
| `react-pack` | React, Next.js veya React Native kanıtlandığında |
| `zanaat-pack` | Görsel üretim, MCP ve özel entegrasyon gerektiğinde |

Bütün paketler bu depoda kalır. Divan, forklanmış çalışma zamanı veya ikinci
ürün deposu gerektirmez.

Native Claude Code kurulumunda isteğe bağlı komut kısayolları da bulunur:
`/ferman` sınırlı iş tanımını başlatır, `/sefer` iş sırasını yürütür, `/teftis`
kanıtı kontrol eder, `/defter` kalıcı bağlamı yazar, `/vezir` beceri oluşturur,
`/yayin` yayını hazırlar. Eski `/company` adı v1 uyumluluğu için korunur. Günlük
kullanımda bu adları ezberlemeniz gerekmez.

## Host uyumluluğu ve kanıt düzeyleri

| Düzey | Anlam | Güncel örnek |
|---|---|---|
| Doğrulanmış native | Temiz kurulum, doctor, update ve kaldırma testli | Claude Code, Codex |
| Taşınabilir beceri | Agent Skills dosyaları yüklenebilir; native yaşam döngüsü iddia edilmez | Registry'deki uyumlu hostlar |
| Belgelenmiş hedef | Resmî yetenek biliniyor; Divan kanıtı eksik | Yalnız araştırma kayıtları |

Ayrıntılı kayıt [host uyumluluğu registry'sinde](registry/host-compatibility.json)
hostu, yeteneği, resmî kaynağı ve kanıtı ayrı gösterir.

## Güvenlik ve gizlilik

Değişmez tag kullanın, checksum'u doğrulayın ve yazma işlemini önce önizleyin.
Divan alakasız eklentileri korur, işlem kurtarmasını kaydeder ve kaynak kimliği
kanıtlanamazsa durur. Kamu kanıtından token, e-posta, mutlak yol, müşteri verisi
ve özel remote URL çıkarılır. Açığı public issue yerine
[özel güvenlik bildirimiyle](SECURITY.md) gönderin.

## Topluluk için ücretsiz

Divan MIT lisanslı, ücretsiz ve açık kaynak bir projedir. Bu depoda ücretli
katman yoktur. Model, hosting veya isteğe bağlı entegrasyon sağlayıcılarının
kendi ücretleri olabilir; Divan bu dış maliyetleri gizlemez.

## Topluluğa katılın

Kullanım sorusunu Discussions'a yazın, hatayı yapılandırılmış formla bildirin,
kaynak adayını kurmadan önerin veya bir belgeyi iyileştirin. Doğru ve güvenli
yolu [SUPPORT.md](SUPPORT.md) gösterir.

## Katkı verme

[Türkçe katkı rehberini](CONTRIBUTING.tr.md) ve
[yönetim modelini](GOVERNANCE.md) okuyun. Tek kanonik yerel kapı:

```bash
python scripts/verify.py
git diff --check
```

Yapısal doğrulama 42 becerinin tamamını kapsar.
5 özgün skill için 16 davranış vakası vardır. Gerçek ajan adaptörü ve kör hakem çalışmadan davranış iyileşmesi
iddia edilmez.

## Yol haritası ve proje belgeleri

- [Yol haritası](ROADMAP.md)
- [Ürün yönü ve geçmiş](BLUEPRINT.md)
- [Yazım ve üslup sözleşmesi](docs/Yazim-ve-Uslup.md)
- [Yayın süreci](RELEASE.md)
- [Görsel sistem](docs/Gorsel-Sistem.md)

## Son release ve doğrulama

[GitHub Releases sayfası](https://github.com/trugurpala/divan/releases/latest),
son yayımlanan paketin doğru kaynağıdır. Değişmez v1.3.4 yayın kanıtı
`.divan/evidence/teftis-20260802-v132-release.md` dosyasında kayıtlıdır. Her yeni
sürüm kendi checksum, SPDX SBOM, attestation ve canlı geri okuma kanıtını
eklemelidir.

Hazırlık puanı **8/8**'dir. Bu puan makine destekli teknik kapıları anlatır;
popülerlik veya pazar benimsemesi değildir.

## Görsel sistem ve Figma kaynağı

Görsel yön; gece mavisi, fildişi, firuze, mercan ve altını ölçülü İznik
geometrisiyle birleştirir. [Düzenlenebilir Figma kaynağını](https://www.figma.com/design/Z325Jjy36I7KLdizcaZAnZ)
açabilir veya [üretim dışa aktarım kurallarını](docs/Gorsel-Sistem.md)
okuyabilirsiniz.

## Lisans ve upstream atıfları

Divan [MIT](LICENSE) lisanslıdır. Üçüncü taraf kökenleri, sabit commitler, yerel
uyarlamalar ve lisans sınırları [UPSTREAM.md](UPSTREAM.md) ile
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) içinde kayıtlıdır. Aday
Meclisinde görünmek kurulmuş veya benimsenmiş olmak anlamına gelmez.
