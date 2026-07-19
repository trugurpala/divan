# Standartlar ve Limitler

Divan, Agent Skills açık standardına (agentskills.io/specification) ve
Claude Code marketplace şemasına uyar. CI'daki `scripts/validate.py` her
push'ta şunları denetler:

## Skill (SKILL.md) kuralları
| Kural | Limit | İhlal sonucu |
|---|---|---|
| `name` uzunluğu | ≤ 64 karakter | hata |
| `name` deseni | küçük harf/rakam/tire; tire ile başlayamaz/bitemez | hata |
| `name` = klasör adı | birebir aynı | **skill hiç yüklenmez** |
| `description` | zorunlu, ≤ 1024 karakter; ne yaptığı + ne zaman | hata |
| Ad çakışması | iki pakette aynı skill adı olamaz | hata |
| Gövde uzunluğu | ≤ 500 satır önerisi; fazlası references/ dosyalarına | uyarı |
| Alanlar | name, description, license, allowed-tools, metadata, compatibility | fazlası uyarı |

## Eval sözleşmesi

Davranışı test edilen skill, `evals/evals.json` taşıyabilir. Divan teftişi
`skill_name` eşleşmesini, en az iki benzersiz örneği, prompt/beklenen çıktı,
nesnel beklentiler ve skill klasöründen dışarı çıkmayan girdi yollarını denetler.
Bu yapısal kontrol performans kanıtı değildir; skill'li/baseline koşuları ayrıca
tamamlanmadan hız veya kalite artışı iddia edilmez.

## Marketplace kuralları
- Katalog `.claude-plugin/marketplace.json` konumunda olmalı; `name`,
  `owner.name` ve her girdide `name`+`source` zorunlu.
- `strict: true` (varsayılan): her paket kendi `plugin.json`'ına sahiptir.
- Girdi sürümü ile plugin.json sürümü uyuşmazsa hata.

## Bağlam bütçesi
Skill'ler aşamalı yüklenir: başlangıçta ad ve açıklama görünür, gövde ancak
tetiklenince okunur. Divan 41 skill içerir; kesin başlangıç bağlamı ve seçme
davranışı istemciye göre değişir. Büyük gövdeler mümkün olduğunda `references/`
altına bölünür ve yalnızca gereken kaynak okunur.

CI üç katmanlıdır: bağımlılıksız `scripts/validate.py`, resmî `skills-ref`
doğrulayıcısı ve Claude Code'un resmî plugin doğrulayıcısı. Açılı ayraçlar Agent
Skills standardında genel olarak yasak değildir; YAML'ın geçerliliği resmî
doğrulayıcıya bırakılır.

## Repo hijyeni ve Clean Code bütçesi

- `.editorconfig` birinci taraf metni UTF-8/LF; `.gitattributes` metin EOL'unu
  LF olarak sabitler.
- `python scripts/hijyen.py --check`, UTF-8/BOM/mojibake ve açık
  `encoding="utf-8"` taşımayan metin subprocess'lerini reddeder.
- `python scripts/hijyen.py --clean`, yalnız `__pycache__`, Ruff/mypy/pytest
  cache'leri, `.coverage` ve `htmlcov` artefaktlarını siler. Yedek, manifest,
  kanıt, worktree veya bilinmeyen dosya allowlist dışındadır.
- Ruff C90 çekirdek Python fonksiyonlarında McCabe karmaşıklığını en çok 25
  kabul eder; daha karmaşık akış isimli tek-sorumluluk adımlarına ayrılır.

## Yayın ve v1 kabul sözleşmesi

`VERSION` tek sürüm kaynağıdır; `release-manifest.json` kamusal yüzeyleri,
`scripts/yayin.py --check` sürüm/not eşliğini denetler. GitHub Release yalnız
CI ve canlı Pages+Wiki eşliğinden sonra oluşur. v1 kapıları
`registry/v1-gates.json` içinde `passed`, `ready` veya `pending` olarak tutulur;
Wiki karnesi deterministik üretilir. Otomasyonu yazılmış ama uzak koşusu geçmemiş
kapı `ready`, dış kullanıcı/gerçek ajan kanıtı olmayan kapı `pending` kalır.
