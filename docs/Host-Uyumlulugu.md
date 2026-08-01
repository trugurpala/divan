# Host Uyumluluğu

Divan tek repo ve tek üründür. Claude Code, Codex, Cursor, Antigravity CLI,
Gemini CLI, GitHub Copilot, Kiro IDE/CLI, OpenCode, Windsurf ve diğer ajanlar
için ayrı Divan forkları tutulmaz. Host farkları küçük adaptörlerle çözülür;
41 beceri ve Divan Engine aynı kanonik kaynaktan gelir.

## “Uyumlu” ne demek?

| Seviye | Dürüst anlamı |
|---|---|
| `experimental` | Resmî yüzey bulundu; Divan yaşam döngüsü henüz kanıtlanmadı |
| `skill-compatible` | Agent Skills veya eşdeğer beceri dosyaları host tarafından okunabilir |
| `native` | Hostun kendi plugin/extension/power yüzeyi için Divan adaptörü vardır |
| `verified` | Temiz hostta kurulum, keşif, güncelleme ve kaldırma canary testi geçti |

Bir alt seviyedeki destek üst seviyeyi kendiliğinden kanıtlamaz. Örneğin
`SKILL.md` okuyan bir host için hook, alt ajan, MCP veya güvenli güncelleme
çalışıyor denmez.

## Güncel doğruluk matrisi

| Host | Kanıtlanan yüzey | Bugün | Hedef | Dağıtım | Resmî kaynak |
|---|---|---|---|---|---|
| Claude Code | CLI | `verified` | `verified` | Plugin | [Plugins reference](https://code.claude.com/docs/en/plugins-reference) |
| Codex | CLI | `verified` | `verified` | Plugin | [Codex plugins](https://developers.openai.com/codex/plugins) |
| Cursor | IDE | `skill-compatible` | `verified` | Plugin | [Plugins reference](https://cursor.com/docs/reference/plugins) |
| Antigravity CLI | CLI | `experimental` | `verified` | Plugin | [Plugins & Skills](https://antigravity.google/docs/cli/plugins) |
| Gemini CLI | CLI | `experimental` | `verified` | Extension | [Extension reference](https://geminicli.com/docs/extensions/reference/) |
| GitHub Copilot | IDE + CLI + coding agent | `skill-compatible` | `verified` | Yüzeye göre | [Customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet) |
| Kiro IDE | IDE | `experimental` | `native` | Power | [Powers](https://kiro.dev/docs/powers/) |
| Kiro CLI | CLI | `experimental` | `verified` | Adaptör | [Agent Skills](https://kiro.dev/docs/cli/skills/) |
| OpenCode | CLI | `skill-compatible` | `verified` | Adaptör | [Agent Skills](https://opencode.ai/docs/skills/) |
| Windsurf | IDE | `skill-compatible` | `verified` | Adaptör | [Cascade Skills](https://docs.windsurf.com/windsurf/cascade/skills) |
| Diğer ajanlar | Agent Skills yüzeyi | `skill-compatible` | `skill-compatible` | Agent Skills | [Agent Skills specification](https://agentskills.io/specification) |

Bu tablo elle verilmiş bağımsız bir vaat değildir. Kanonik kayıt
`registry/host-compatibility.json`, kapısı ise
`python scripts/host_compatibility.py` komutudur. `verified` yazabilmek için
repoda gerçek kanıt yolu bulunmak zorundadır.

Codex satırındaki `verified` iddiası yalnız repodaki tekrarlanabilir canary'nin
çalıştırdığı CLI yaşam döngüsü içindir. OpenAI'nin güncel plugin sözleşmesi
Desktop desteğini belgelese de Divan henüz ayrı bir Desktop UI canary kaydı
taşımadığı için Desktop, IDE extension ve mobil yüzeyler bu iddianın dışındadır.
Bu sınır kanonik kayıtta `excluded_surfaces` olarak makinece doğrulanır. Benzer
biçimde her satırdaki yetenekler yalnız `surfaces` alanında yazan yüzeyler için
geçerlidir.

## Codex Desktop kurulum sonucu

Codex'in genel `verified` seviyesi, temiz hostta kanıtlanmış yerel plugin yaşam
döngüsünü anlatır. Tek bir Windows kurulumundaki AppX/ACL veya PATH durumu ise
yerel sonucu değiştirebilir. Bu nedenle Divan aşağıdaki açık profili sunar:

```powershell
python scripts/divan.py install --host codex --profile auto --ref v1.0.2 --execute
```

Komut `missing`, `not-executable`, `access-denied`, `invalid-json` ve `healthy`
tanılarını ayrı tutar. İlk üç tanıda checksum-backed skill fallback seçilebilir;
`invalid-json` gerçek bir protokol uyumsuzluğu olarak durur. Fallback sonucu
`skill-compatible` yetenek verir: 41 skill ve talimat vardır, fakat yerel
komutlar, ajanlar, hook'lar, MCP ve host yaşam döngüsü varmış gibi gösterilmez.

## Host kimliği ile model kapasitesi aynı şey değildir

Nizâm-ı Sefer plan üretirken hostu açık `--host-profile`, `DIVAN_HOST` veya
yalnız adı bilinen resmî ortam işaretlerinden algılar. Birden fazla işaret
çakışırsa host `ambiguous`, hiçbir kanıt yoksa `unknown` olur ve çalışma tek
seferlik güvenli hatta düşer. Ortam değişkenlerinin değerleri plana veya
makbuza yazılmaz.

Hostun Codex olarak algılanması belirli bir modelin hesapta açıldığı anlamına
gelmez. Divan yalnız risk düzeyine göre `economy`, `balanced` veya `frontier`
model sınıfı ve muhakeme bütçesi önerir. Tam model adı ancak kanıtlı bir aday
olarak gösterilir; seçilmeden önce host tarafından doğrulanması gerekir.
Bağlam penceresi de hosttan kanıtlanamıyorsa ürün limiti diye sunulmaz,
işaretlenmiş bir planlama varsayımı kullanılır.

## Neden hepsinde bugün tam güç değil?

Hostlar aynı eklenti sözleşmesini kullanmıyor. Dizinler, manifest biçimleri,
komutlar, hook olayları, alt ajanlar, MCP yapılandırması, izin modeli ve
güncelleme davranışı değişiyor. Divan bu farkı kullanıcıdan saklamak yerine
adaptör katmanında sınırlar ve eksik yeteneği açıkça gösterir.

Hedef, “her yere dosya kopyalandı” demek değil; şu yaşam döngüsünü gerçekten
kanıtlamaktır:

```text
hostu algıla → güvenli önizleme → kur → becerileri keşfet
→ çalıştır → güncelle → kaldır → geride sahiplenilmemiş dosya bırakma
```

## Modülerlik sınırı

- Divan Engine, görev sırası, hafıza ve kanıt kuralları bu repoda kalır.
- Host adaptörleri yalnız paketleme ve host yeteneği çevirisi yapar.
- GitHub, Figma, Gmail, Slack ve benzeri uygulamalar isteğe bağlı el ve gözlerdir;
  Divan'ın beyni veya zorunlu kurulum bağımlılığı değildir.
- MCP sunucuları varsayılan olarak açılmaz; görev ve izin gerektiğinde seçilir.
- Yeni bir host “verified” seviyesine yalnız tekrarlanabilir canary kanıtıyla çıkar.
- Model, bağlam ve alt ajan kapasitesi host desteğinden ayrı kanıtlanır.

Bu model kurulum paketini gereksiz büyütmeden daha çok hosta ulaşmayı ve bir
host değiştiğinde bütün Divan'ı çatallamadan yalnız ilgili adaptörü güncellemeyi
sağlar.
