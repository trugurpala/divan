# v0.11.0 yayın adayı yerel teftişi · 2026-07-18

## Kaynak kararı

- Context7 `/github/docs`: GitHub Release oluşturmak için ilgili job'da
  `contents: write`; `GITHUB_TOKEN` kaynaklı olaylar varsayılan olarak yeni
  workflow zinciri başlatmaz; workflow/ref concurrency grubu kullanılabilir.
- Repo gerçeği: v0.10.3'te sürüm bilgisi README, marketplace, Wiki, site,
  CHANGELOG, BLUEPRINT ve ilerleme defterine dağılmış; GitHub Release otomasyonu
  ve temiz-host matrisi yoktu.

## Yerel kapılar

| Kapı | Sonuç |
|---|---|
| Unit test | 28/28 geçti |
| `scripts/validate.py` | Temiz: 5 paket, 41 skill; iki belgeli uzunluk uyarısı |
| `scripts/yayin.py --check` | 11 kamusal yüzey v0.11.0 ile eşleşti |
| `scripts/v1.py --check` | 8 kapılı karnenin üretilmiş sayfayla eşliği geçti |
| Eval sözleşmesi | 4 skill / 13 vaka geçerli |
| Wiki | v0.11.0, 17 çıktı ve bağlantılar geçerli |
| Aday Meclisi / katalog | 1 aday ve 41 skill deterministik eşleşti |
| Shell sözdizimi / YAML | kur-kaldır betikleri ve bütün workflow/form YAML'ları geçti |
| Agent Skills resmî doğrulayıcı | 41/41 geçti (`skills-ref==0.1.1`) |
| Claude Code resmî doğrulayıcı | marketplace + 5/5 paket geçti (`2.1.212`) |
| `git diff --check` | Geçti |

## Dürüst sınır

Bu dosya yerel yayın-adayı kanıtıdır. Linux/macOS/Windows uzak matris koşuları,
PR kontrolleri, `main`, Pages, Wiki ve v0.11.0 GitHub Release henüz bu kayıtta
geçmiş sayılmaz. Gerçek ajan/hakem karşılaştırması ile bağımsız kullanıcı kanıtı
v1 için ayrıca bekler.
