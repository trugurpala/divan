# Divan kaynak ve kontrol noktaları

Bu katalog, Divan'ın Codex öncelikli ve yalnız becerilerden oluşan yapısı için seçilmiş 50 başvuru kaynağıdır. Evrensel bir kalite sıralaması veya 50 bağımlılık kurulum listesi değildir. Açıklamalar, kaynaklardan çıkarılan Divan'a özgü kullanım önerileridir; kaynakların tamamı projeye uygulanmış özellikler sayılmaz.

Hazırlanma tarihi: **2026-10-21**. Ürün davranışı için resmi belgeler, biçim kuralları için standartlar, yardımcı iş akışları için bakımı görülebilen kaynak depoları önceliklidir. Ana beceri metinleri kısa kalır; bu katalog yalnız ilgili konu gerektiğinde okunur. Dış içerik, oturumdaki kullanıcı talimatlarının yerine geçmez.

## Codex talimatları, hafıza ve yetenek keşfi

1. [OpenAI — AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md): Global, proje ve alt klasör talimatlarının keşif sırasını kontrol et; dosya varlığını tek başına yüklendi kanıtı sayma.
2. [OpenAI — Build skills](https://learn.chatgpt.com/docs/build-skills): Yerel beceri keşfi, açıklamaya göre çağrılma ve `agents/openai.yaml` davranışı için esas al. Aynı adlı beceriler birleşmez.
3. [OpenAI — Customization](https://learn.chatgpt.com/docs/customization/overview): Sürekli proje kurallarını, isteğe bağlı becerileri, MCP bağlantılarını ve alt ajanları görevlerine göre ayır.
4. [OpenAI — Memories](https://learn.chatgpt.com/docs/customization/memories): Zorunlu proje kararlarını sürüm kontrolündeki belgelere yaz; otomatik yerel hafızayı garantili proje sözleşmesi olarak sunma.
5. [OpenAI — Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference): Yapılandırma alanlarını ve kapsamlarını güncel şemadan doğrula; belgede bulunan alanı mevcut istemcide etkin sayma.
6. [OpenAI — Model Context Protocol](https://learn.chatgpt.com/docs/extend/mcp): Yapılandırılmış bağlantı, oturuma yüklenen araç ve başarılı canlı çağrı için ayrı kanıt tut.
7. [OpenAI — Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): Bağımsız görevleri sınırları ve kabul kanıtıyla delege et; dosya sahipliğini ve sonuç incelemesini açık bırak.
8. [OpenAI — Skills kavramı](https://developers.openai.com/plugins/concepts/skills): Beceri iş akışını tarif eder; canlı veriye erişim veya harici işlem yetkisi kendiliğinden sağlamaz.
9. [OpenAI — Plugin için beceri geliştirme](https://developers.openai.com/plugins/build/skills): Her becerinin tetikleyicisini, girdisini ve teslimini daralt; kullanıcı talimatının beceri rehberinden öncelikli olduğunu koru.
10. [OpenAI — Plugin paketleme](https://developers.openai.com/plugins/build/plugins): Taşınabilir kök manifest ile Codex uyumluluk manifestini ayırt et; kullanılan biçimin yollarını ve paket sınırını doğrula.
11. [OpenAI — Plugin bağlantı ve testi](https://developers.openai.com/plugins/deploy/connect-chatgpt): Paket denetimi ile gerçek kullanıcı iş akışının doğrulanmasını ayrı kabul koşulları yap.
12. [OpenAI — Submission errors](https://developers.openai.com/plugins/deploy/submission-errors): İsim, metadata ve paket doğrulama hatalarında resmi hata sözlüğüne başvur; yerel geçişi yayın kabulü sayma.

## Beceri biçimi ve davranış değerlendirmesi

13. [Agent Skills — Specification](https://agentskills.io/specification): `SKILL.md`, frontmatter, isim ve açıklama sınırlarını temel biçim sözleşmesi olarak kullan.
14. [Agent Skills — Best practices](https://agentskills.io/skill-creation/best-practices): Genel nasihatleri azalt; gerçek proje kararlarını, varsayılanları ve hata durumlarını kısa, uygulanabilir adımlara dönüştür.
15. [Agent Skills — Description optimization](https://agentskills.io/skill-creation/optimizing-descriptions): Doğru çağrılmanın yanında benzer kelimeler içeren yanlış çağrılma örneklerini de değerlendir.
16. [Agent Skills — Output quality evals](https://agentskills.io/skill-creation/evaluating-skills): Gerçekçi kullanıcı istemi, beklenen sonuç ve gerekiyorsa örnek dosyalarla karşılaştırılabilir davranış senaryoları hazırla.
17. [Agent Skills — Scripts](https://agentskills.io/skill-creation/using-scripts): Tekrarlanabilir doğrulama gereken yerde küçük betik kullan; betiğin girdisini, çıktısını ve bağımlılık ihtiyacını açıkla.
18. [Agent Skills — Client implementation](https://agentskills.io/client-implementation/adding-skills-support): Katalog metadata'sı, tam talimatlar ve ek kaynakları aşamalı yüklemenin neden ayrı olduğunu anla; Divan'a yeni runtime ekleme gerekçesi sayma.
19. [Agent Skills — Quickstart](https://agentskills.io/skill-creation/quickstart): Yeni beceri örneklerini küçük ve bağımsız başlat; gösterimde kullanılan editörü veya kurulumu proje zorunluluğu yapma.
20. [OpenAI — Testing Agent Skills with Evals](https://developers.openai.com/blog/eval-skills): Başarı ölçütünü önce tanımla; koşu izi ve çıktılarla ölçmeden kalite, doğruluk veya hız artışı iddia etme.

## Standart Python ile doğrulama ve paketleme

21. [Python — unittest](https://docs.python.org/3/library/unittest.html): Doğrulayıcıların kabul ve ret davranışlarını gerçek dosya örnekleriyle test et; test keşfinin gerçekten test çalıştırdığını denetle.
22. [Python — unittest.mock](https://docs.python.org/3/library/unittest.mock.html): Gerekli dış sınırları kontrollü taklit et; paket okuma ve içerik kontrollerini yalnız taklitlere dayandırma.
23. [Python — pathlib](https://docs.python.org/3/library/pathlib.html): Windows ve POSIX yollarını açıkça ele al; paket kökünün dışına çıkan referansları çözülmüş yol üzerinden kontrol et.
24. [Python — json](https://docs.python.org/3/library/json.html): Manifest okuma hatalarını anlaşılır raporla; geçerli JSON ile geçerli ürün sözleşmesini ayrı doğrula.
25. [Python — argparse](https://docs.python.org/3/library/argparse.html): Yardım metni, argüman hatası ve çıkış kodlarını kararlı tut; mevcut küçük CLI için yeni çatı ekleme.
26. [Python — zipfile](https://docs.python.org/3/library/zipfile.html): Üretilen arşivi yeniden açıp üye yollarını, zorunlu dosyaları ve istenmeyen içerikleri kontrol et.
27. [Python — tempfile](https://docs.python.org/3/library/tempfile.html): Paket ve doğrulama testlerini geçici dizinlerde çalıştır; gerçek kullanıcı dosyalarını test fikstürü olarak değiştirme.
28. [Python — tomllib](https://docs.python.org/3/library/tomllib.html): TOML okuma ihtiyacı oluşursa desteklenen Python sürümünü kontrol et; biçimi düzenli ifadelerle tamamen ayrıştırdığını varsayma.
29. [Python — subprocess](https://docs.python.org/3/library/subprocess.html): Dış komut gerektiğinde argüman, zaman aşımı ve dönüş kodunu açık yönet; shell metnine güvenilmeyen içerik ekleme.
30. [Python — hashlib](https://docs.python.org/3/library/hashlib.html): Paket kimliği gerektiğinde içerik özeti üret; aynı hash'i davranış kalitesinin veya kaynak güvenilirliğinin kanıtı sayma.

## Git, CI ve dağıtım kanıtı

31. [GitHub — Building and testing Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python): Yerel doğrulama, test ve paket komutlarını CI'da çalıştır; örnekteki PyPI yayın adımını Divan'a otomatik taşıma.
32. [GitHub — Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax): Tetikleyici, çalışma dizini, izin ve iş bağımlılıklarını depodaki gerçek akışla eşleştir.
33. [GitHub Actions — setup-python](https://github.com/actions/setup-python): Desteklenen Python sürümünü açık seç; kullanılan action sürümünün README ve runtime koşullarını değişiklik sırasında yeniden kontrol et.
34. [GitHub Actions — checkout](https://github.com/actions/checkout): Test edilen checkout'u bil; tarihçe gerektiren kontrollerde varsayılan sığ klon davranışını dikkate al.
35. [GitHub — Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows): Gerçek tekrar oluşursa ortak akış çıkar; küçük tek bir pipeline için gereksiz soyutlama ekleme.
36. [GitHub — Workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data): Test çıktısı ve ZIP'i aynı koşunun kanıtlarıyla ilişkilendir; artifact üretimini herkese açık yayınla karıştırma.
37. [GitHub — Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository): Sürüm notu, tag ve paket eşleşmesini incele; yayın yalnız görevdeki açık yetki kapsamında yapılır.
38. [Git — status](https://git-scm.com/docs/git-status): İşe başlarken ve teslimde çalışma ağacını kontrol et; kullanıcı değişiklikleriyle görev değişikliklerini ayırt et.
39. [Git — diff](https://git-scm.com/docs/git-diff): İnceleme kapsamını doğru tabana göre kur; yalnız yeni dosyaya değil son farkın tamamına bak.

## Belge düzeni, köken ve ekosistem

40. [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/): Başlık, liste, bağlantı ve kod bloklarını taşınabilir yaz; belgeyi belirli bir görüntüleyicinin tesadüfi davranışına bağlama.
41. [Semantic Versioning 2.0.0](https://semver.org/): Dışarıdan kullanılan sözleşmeyi tanımla; uyumsuz değişiklikleri ve ön sürüm durumunu sürüm numarasına yansıt.
42. [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/): Kullanıcının göreceği değişiklikleri tarih ve sürümle kaydet; ham commit listesini açıklama yerine kullanma.
43. [GitHub — Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository): Kaynak ve alt dosya lisanslarını incele; herkese açık depoyu kendiliğinden yeniden dağıtılabilir sayma.
44. [SPDX License List](https://spdx.org/licenses/): Lisans adlarını standart kimlikle kaydet; otomatik tespit sonucu belirsizse özgün lisans dosyasına bak.
45. [REUSE Specification 3.3](https://reuse.software/spec-3.3/): Üçüncü taraf dosya alınırsa dosya kökenini ve lisans kapsamını koru; yalnız bağlantı verilen kaynağı vendored içerik sayma.
46. [Vercel Labs — skills](https://github.com/vercel-labs/skills): Beceri keşfi ve dağıtım araçları için kaynak depo; keşif sonucunu kurulum veya çalışırlık kanıtından ayır.
47. [Jesse Vincent — Superpowers](https://github.com/obra/superpowers): Hata ayıklama, gözden geçirme ve doğrulama yöntemlerine başvur; mevcut Divan akışını ikinci bir süreçle gereksiz çoğaltma.
48. [Matt Pocock — skills](https://github.com/mattpocock/skills): Ajanların okuyacağı belgeler ve kod inceleme yöntemleri için aday kaynak; runtime ve görev kapsamına uyumu değerlendirmeden içeri aktarma.
49. [prompts.chat — kaynak depo](https://github.com/f/prompts.chat): İstem ve beceri keşif ekosistemini incelemek için kaynak; kod lisansı ile kullanıcı istemi/veri lisansını ayrı kaydet.
50. [OpenAI — Docs MCP](https://developers.openai.com/resources/docs-mcp): Resmi belge erişimi için isteğe bağlı bağlantı kaynağı; kurulu beceri, MCP yapılandırması, yüklü araç ve canlı erişimi ayrı doğrula.

## Sınırlı ekosistem önerileri

Bu tablo yeni kurulum yapmaz. **Mevcut**, bu hazırlama oturumunun beceri kataloğunda bulunup yerel `SKILL.md` dosyası doğrulanan yeteneği belirtir; Divan paketine gömülü olduğu anlamına gelmez. **Aday**, bu oturumda kurulu olduğu doğrulanmayan dış kaynaktır. Kurulum sayısı beceriye, yıldız sayısı depoya aittir; kullanım başarısını ölçmez.

Veriler **2026-10-21** tarihinde skills.sh sayfaları ve GitHub'ın herkese açık depo API'sinden okundu. `K` bin, `M` milyon anlamındadır. Sayfalar farklı önbellek zamanları nedeniyle küçük farklar gösterebilir.

| Beceri / kaynak sahibi | Durum ve Divan için kullanım | Görülen kurulum | Depo yıldızı | Lisans kapsamı |
| --- | --- | ---: | ---: | --- |
| [find-skills — Vercel Labs](https://www.skills.sh/vercel-labs/skills/find-skills) | Mevcut; eksik yetenekte kaynak keşfi | 4.0M | 35.962 | `vercel-labs/skills` depo lisansı MIT |
| [systematic-debugging — Jesse Vincent](https://www.skills.sh/obra/superpowers/systematic-debugging) | Mevcut; doğrulayıcı veya paket hatasında kök neden incelemesi | 302.7K | 303.092 | `obra/superpowers` depo lisansı MIT |
| [verification-before-completion — Jesse Vincent](https://www.skills.sh/obra/superpowers/verification-before-completion) | Mevcut; teslimden önce güncel komut kanıtı | 248.3K | 303.092 | `obra/superpowers` depo lisansı MIT |
| [requesting-code-review — Jesse Vincent](https://www.skills.sh/obra/superpowers/requesting-code-review) | Mevcut; anlamlı değişiklikte bağımsız inceleme | 259.6K | 303.092 | `obra/superpowers` depo lisansı MIT |
| [writing-skills — Jesse Vincent](https://www.skills.sh/obra/superpowers/writing-skills) | Mevcut; tetikleyici ve davranış senaryosu tasarımı | 215.4K | 303.092 | `obra/superpowers` depo lisansı MIT |
| [writing-for-agents — Matt Pocock](https://www.skills.sh/mattpocock/skills/writing-for-agents) | Aday; belge işaretçileri ve bağlam bütçesi için yöntem karşılaştırması | 453.3K | 299.724 | `mattpocock/skills` depo lisansı MIT |
| [code-review — Matt Pocock](https://www.skills.sh/mattpocock/skills/code-review) | Aday; gereksinim ve depo standardını ayrı inceleme yaklaşımı | 775.8K | 299.724 | `mattpocock/skills` depo lisansı MIT |

İlk tercih mevcut, göreve uygun becerileri kullanmaktır. Matt Pocock'un `code-review` becerisinde sabit karşılaştırma tabanı ve issue tracker hazırlığı gibi ön koşullar bulunur; Divan'a doğrudan eklenmesi gerekli değildir. Aynı iş için birden çok inceleme/planlama becerisini aynı anda zorunlu kılma.

Bu ortamda ayrıca `sak` (seç, araştır, kur) becerisi okunarak yeniden kullanım,
uyarlama ve özel geliştirme kararları değerlendirildi. İçindeki 20 uzmanlık
başlığı birer isteğe bağlı referanstır; çalışan 20 ajan değildir. Kaynak deposu
[Addy Osmani agent-skills](https://github.com/addyosmani/agent-skills), MIT lisansını
ve uzmanlık listesini yayımlar. Divan'a bu dış beceriler kopyalanmadı; mevcut
yetenek uygunsa çağırma ve toplam bakım maliyetini değerlendirme yöntemi kullanılır.

Bakım göstergesi olarak GitHub API'sinde `vercel-labs/skills` son push tarihi 2026-10-19, `obra/superpowers` ve `mattpocock/skills` son push tarihi 2026-10-21 idi; üçü de arşivlenmemişti. Bu, her becerinin ayrı denetlendiği veya mevcut yerel kopyanın son upstream sürümü olduğu anlamına gelmez. Bu kaynakların `LICENSE` dosyaları ayrıca okundu.

Lisans örneği: [prompts.chat LICENSE](https://github.com/f/prompts.chat/blob/main/LICENSE), kaynak kodu/site içeriğini MIT ve istem içeriği/verisini CC0-1.0 olarak ayırır. [Anthropic skills README](https://github.com/anthropics/skills) de depo içindeki lisansların tek tip olmadığını belirtir; örneğin `frontend-design` dosya lisansı Apache-2.0 iken belge becerileri ayrı koşullara sahiptir. Bu katalog üçüncü taraf beceri, istem veya betik kopyalamaz.

## Kaynak bağlantıları ve doğrulama kapsamı

### Farklı ajanlara erişim ve README araştırması

2026-10-21 tarihinde [AgenticSkills.io](https://agenticskills.io/) yerel Firecrawl
ile okundu. Bir keşif dizinidir; [Agent Skills standardı](https://agentskills.io/specification)
ile aynı kaynak değildir. Kurulum kararında resmi, sürümlenmiş
[Vercel Skills 1.7.4 belgeleri](https://github.com/vercel-labs/skills/blob/v1.7.4/docs/commands.md)
ve uygulamaların kendi belgeleri esas alındı. Kurulum ve gerçek davranış kanıtı
[uyumluluk rehberinde](compatibility.md) ayrı tutulur.

Find Skills yaklaşımıyla güncel resmi dağıtım aracı değerlendirildi; prompts.chat
aramasında [Skill Maintenance Audit](https://prompts.chat/prompts/cmuwbt3p80004qs06iif6z1q1_skill-maintenance-audit)
ve [Markdown Accessibility and Alt Text Checker](https://prompts.chat/prompts/cmv22tciz0009ig06vv06246n_markdown-accessibility-and-alt-text-checker)
bulundu. İlk adayın içeriği okundu ve mevcut kalite akışıyla örtüştüğü görüldü.
İkincisinde yalnız arama metadatası elde edildi. Hiçbiri kurulmadı veya kopyalanmadı;
bireysel yeniden dağıtım lisansı doğrulanmadan içerik alınmaz. README'nin amaç,
kurulum, ilk iş, destek, katkı ve lisans sırası
[GitHub'ın README rehberine](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
göre sadeleştirildi.

### Mindrally karşılaştırması (2026-10-22)

[Mindrally/skills](https://github.com/Mindrally/skills) deposu, Cursor kurallarından
dönüştürülmüş 265'ten fazla konu becerisi sunuyor. İncelenen README ve depo verisi:
Apache-2.0, 281 yıldız, arşivlenmemiş durum, son commit 2026-10-08.
[README best practices](https://github.com/Mindrally/skills/blob/main/readme-best-practices/SKILL.md)
becerisindeki ilk ekranda değeri ve çalışır başlangıç örneğini gösterme fikri,
Divan'ın mevcut README'sine uygun. `python-testing` becerisi `pytest` merkezli;
Divan'ın standart kütüphane `unittest` hattını değiştirmek için gerekçe sağlamıyor.
Tekil becerinin kurulum sayısı doğrulanmadı. Mindrally paketi kurulmadı veya
içeriği kopyalanmadı; 265 beceriyi Divan'ın yedi çekirdek becerisine eklemek
keşif ve bakım yükünü artırır. Gerektiğinde projeye uygun tekil aday yeniden
değerlendirilir.

### Önceki kaynak doğrulamasının kapsamı

Numaralı maddelerdeki bağlantılar başvuru listesidir. Açılan ve ilgili bölümleri okunan kaynak grupları: OpenAI'nin AGENTS.md, Build skills, Memories, plugin paketleme/beceri yazımı ve eval rehberleri; Agent Skills biçim, yazım, tetikleme, script ve eval belgeleri; Python `unittest`, `unittest.mock`, `pathlib`, `json`, `zipfile`; Git/GitHub CI, artifact, release ve lisans sayfaları; CommonMark, SemVer, Changelog, SPDX, REUSE; seçilen ekosistem sayfaları, depo metadata'sı ve lisans dosyaları.

[Agent Skills belge indeksi](https://agentskills.io/llms.txt), [ChatGPT/Codex belge indeksi](https://learn.chatgpt.com/llms.txt) ve [OpenAI plugin belge indeksi](https://developers.openai.com/plugins/llms.txt) de okundu. Diğer maddeler bu kaynak gruplarının tamamlayıcı başvuru noktalarıdır; bütün 50 URL için ayrı içerik denetimi veya uçtan uca çalışma testi yapıldığı iddia edilmez. Açılan belge bir kurulumun, eklenti erişiminin ya da canlı servisin doğrulaması değildir.

Bir kaynak uygulamada kullanılacağı zaman ilgili sayfa ve kullanılan sürüm yeniden kontrol edilir. Özellikle Python `/3/` belgeleri ilerleyen sürüme işaret edebilir; Divan'ın desteklediği sürümde bulunmayan API'ler yalnız güncel belgede yer aldığı için kullanılmaz. İşlem kanıtı; çalıştırılan komut, ilgili sürüm/commit, tarih ve gözlenen sonuçla proje kayıtlarına eklenir.
