# Göreve Özel Yetenek Denetimi

**Son güncelleme:** 2026-08-01

Bu protokol "Yapay zekâ yüzde kaç iyi?" sorusunu cevaplamaz. Bir görev için
gereken açık yeteneklerin ne kadarının bu oturumda ve projede kanıtlandığını
ölçer. Payda yazılmadan verilen yüzde geçersizdir.

## 1. Gereksinim defterini kur

Önce somut teslimi yaz, sonra onu en küçük bağımsız gereksinimlere ayır. Her
gereksinime benzersiz bir `id`, durum ve varsa kanıt ekle:

| Durum | Ağırlık | Kullanım |
|---|---:|---|
| `verified` | 1.0 | Mevcut ve bu hostta doğrudan gözlendi |
| `partial` | 0.5 | Var, fakat kapsam veya kalite eksiği var |
| `missing` | 0.0 | Denetlendi ve bulunamadı |
| `unknown` | 0.0 | Kanıt yok ya da envanter çelişkili |

Kanıt örnekleri: okunmuş repo kuralı, araç yardım çıktısı, kurulu skill yolu,
başarılı test komutu, connector yetki çıktısı veya resmi kaynak bağlantısı.
Modelin hatırlaması, eski sohbet özeti ve bir README iddiası tek başına
`verified` değildir.

```json
{
  "requirements": [
    {"id": "repo-rules", "status": "verified", "evidence": ["AGENTS.md read"]},
    {"id": "visual-check", "status": "partial", "evidence": ["desktop only"]},
    {"id": "release-right", "status": "unknown"}
  ]
}
```

## 2. Deterministik ölç

JSON'u dosyadan veya stdin'den ölçücüye ver:

```powershell
python plugins/sadrazam/skills/musavir/scripts/score_capabilities.py audit.json
```

Formüller:

```text
coverage = 100 * (verified + 0.5 * partial) / requirement_count
gap = 100 - coverage
confidence = 100 * (requirement_count - unknown) / requirement_count
```

`coverage` görev kapsamını, `gap` açık işi, `confidence` ise envanter kanıtının
tamlığını anlatır. Bunları model IQ'su, kod kalitesi, güvenlik puanı veya teslim
başarı olasılığı diye adlandırma. Güven düşükse önce araştır, yüzdeyi süsleme.

## 3. Mevcut yeteneği kanıtla

Şu sırayla bak:

1. Repo kuralları, kabul edilmiş ADR/spec ve gerçek bağımlılık dosyaları.
2. Bu oturumda çağrılabilir araçlar, pluginler, connectorlar ve skill listesi.
3. Diskteki kurulum sürümü, komutların `--help` çıktısı ve sağlık kontrolü.
4. Gerekli hesabın veya dış servisin gerçekten bağlı olup olmadığı.

Başlangıç envanteri ile disk çelişirse iki durumu da yaz. Disk güncellense bile
açık oturum eski skill listesini tutabilir; yeni task açılması gerekebilir. Bu
durumu `verified` diye gizleme.

Divan güncellemesinde önce kurulu sürümü ve exact release tag'i doğrula, sonra
`python scripts/divan.py update --ref <exact-release-tag>` ile önizle. Yalnız
açık yetki ve temiz kanıtla `--execute` kullan; ardından aynı tag ile `doctor`
çalıştır. Branch HEAD'ini yayınlanmış release sanma.

## 4. Değişken iddiaları araştır

Sürüm, deprecation, arşiv, lisans, fiyat, güvenlik, uyumluluk ve servis limiti
için resmi doküman, release note veya canonical repository kullan. Teknik
sorularda üçüncü taraf liste yazılarını karar kanıtı yapma. Her kayda gözlem
tarihi koy ve çıkarım yaptığında bunu açıkça belirt.

## 5. Kararı ve teslim modelini ayır

| Karar | Anlamı |
|---|---|
| `KEEP` | Mevcut çözüm gereksinimi karşılıyor |
| `ADD` | Somut boşluğu en küçük yüzeyle kapatıyor |
| `LATER` | Gerçek ihtiyaç olabilir, bugün kurulması gerekmiyor |
| `REPLACE` | Mevcut çözüm bakımsız, riskli veya gereksinime aykırı |
| `REJECT` | Çakışıyor, lisans/güvenlik kapısını geçmiyor veya değer katmıyor |

Her araç için ayrıca bir teslim modeli yaz: runtime dependency, dev dependency,
kaynak-kod bileşeni, harici CI servisi, bağımsız paket veya yalnız referans.
`ADD` kararı bütün marketplace'i ya da repoyu kurma izni değildir.

## 6. Karar ver ve uygula sınırı

Açık ve toplu ön-yetki varsa analizden sonra soru sormadan şu işleri yapabilirsin:

- geri alınabilir yerel dosya düzenlemesi;
- mevcut araçla format, lint, test ve katalog üretimi;
- secretsiz fixture ve belge oluşturma;
- ücretsiz/açık kaynak aday için salt-okunur araştırma.

Şuralarda ayrı onay gerekir: ücretli servis veya kota tüketimi, hesap açma,
secret/credential, erişim kapsamını büyütme, güvenlik veya kimlik politikası,
dış mesaj, gerçek kullanıcı/veri işlemi, yıkıcı komut, commit, push, PR, merge,
tag, paket veya canlı yayın. Yapılmayanı yapılmış gibi raporlama.

## 7. Son rapor

Rapor şu beş parçayı içersin:

1. Ölçülen görev ve gereksinim sayısı.
2. Kapsama, boşluk ve güven yüzdeleri ile ham durum sayıları.
3. Kanıt bağlantıları ve bilinmeyenler.
4. `KEEP | ADD | LATER | REPLACE | REJECT` tablosu.
5. Uygulama ve doğrulama durumları; gerçek eval yapılmadıysa performans artışı
   iddiasının bulunmadığı notu.

