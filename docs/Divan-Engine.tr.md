# Divan Engine ve Divan Nizamı

[English](Divan-Engine.md)

Divan tek ürün ve tek repodur: Hükümdarın fermanını sınırları belli uzman
çalışmasına ve doğrulanmış yayına dönüştüren, yerel öncelikli ve gözetimli
yazılım teslim framework'üdür. Divan Engine, yalnız Python standart
kütüphanesiyle çalışan çekirdektir. Divan Nizamı ise yetkinin bu çekirdekte
nasıl devredildiğini belirleyen yönetişim modelidir; ikinci bir ürün veya repo
değildir.

## Yetki Hükümdardan başlar

| Sıra | Makine kimliği | İngilizce | Türkçe |
|---:|---|---|---|
| 0 | `owner` | Owner | Hükümdar |
| 1 | `mandate` | Mandate | Ferman |
| 2 | `orchestrator` | Orchestrator | Sadrazam |
| 3 | `council` | Council | Divan |
| 4 | `specialist` | Specialist | Uzman |
| 5 | `provider` | Provider | Sağlayıcı |

Kapsamı yalnız `owner/Hükümdar` genişletebilir. Her alt katman yetkisini üst
katmandan daha dar alır. Bir sağlayıcının bağlı olması ona kendiliğinden işlem
yetkisi vermez; yalnız fermanda zaten izin verilmiş işlemi yapabilir. Değişiklik
açık yetki, tamamlanma iddiası kanıt ister.

Bu sınır, yerel iş akışı yönetişimidir; kullanıcı kimlik doğrulaması değildir.
Kimlik ve erişim sınırı host işletim sistemi hesabı ile repo izinleridir. Genel
CLI her değişikliğin tam argümanlarını deterministik bir Ferman kimliğine
bağlar, `--execute` bayrağını açık yerel Hükümdar yetkisi sayar ve devredilmiş
bir `--actor` ile değişiklik isteğini reddeder. Doğrudan dahili Python API'leri
ayrı bir güvenlik sandbox'ı değil, güvenilen uygulama yüzeyleridir.

## Dokuz çalışma zamanı modülü

Kanonik paket `plugins/sadrazam/divan_runtime/` yolundadır.

| Modül | Sorumluluk |
|---|---|
| `kernel` | modül grafiğini ve mimari sözleşmeyi doğrular |
| `governance` | yetki devrini doğrular, genel CLI değişikliğini yetkilendirir |
| `council` | projeyi keşfeder, niyeti yönlendirir, etkiyi hesaplar |
| `evidence` | maskelenmiş kanıt makbuzlarını üretir ve doğrular |
| `project` | proje sözleşmesini kurar, sahiplenir, denetler ve günceller |
| `records` | hedef, arşiv ve kabul kaydı |
| `providers` | sınırlı local, GitHub, Context7 ve Vercel yetenekleri |
| `release` | kaynağa bağlı yayın kanıtı ve canlı geri okuma |
| `api` | kararlı CLI, maskelenmiş JSON çıktısı ve v0.17 öncesi takma adlar |

`modules.json` bağımlılık grafiğinin, `governance.json` iki dilli yetki
sözleşmesinin tek kaynağıdır. `python scripts/divan.py architecture --json`
ikisini birlikte doğrular ve gösterir. Bağımlılıklar döngü kuramaz. Çekirdek
başka bir repoya veya harici agent runtime'ına bağlı değildir.

## Kullanım

Normal kullanıcı yalnız sonucu söyler. CLI, bakım ve entegrasyon yüzeyidir:

```powershell
python scripts/divan.py architecture --json
python scripts/divan.py inspect --project .
python scripts/divan.py plan --project . --intent "Kayıt ekranını erişilebilir yap"
python scripts/divan.py impact README.md plugins/sadrazam/skills/sadrazam/SKILL.md
python scripts/divan.py validate
python scripts/divan.py init --project . --profile standard
python scripts/divan.py init --project . --profile standard --actor owner --execute
python scripts/divan.py audit --project .
```

Eski `Company OS` adı ve `plugins/sadrazam/company/` yolu v1 boyunca
uyumluluk yüzeyi olarak kalır ve v2'den önce kaldırılmaz. Eski
`company-validate` takma adı kanonik `validate` ile aynı sözleşmeyi döndürür.
Mevcut `.divan/` verileri, DCS/DPS kimlikleri, makbuzlar, hash'ler ve genel CLI
komutları değişmez.

Hedef repoya kurulan gözetimli katman için
[Divan Proje Sözleşmesi](Project-Contract.tr.md) belgesine bak.
