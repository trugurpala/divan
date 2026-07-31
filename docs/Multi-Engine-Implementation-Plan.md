# Çoklu Motor Uygulama Planı

## Teslim stratejisi

Bu çalışma tek PR içinde bütün motorları kurmaz. Her dilim bağımsız doğrulanabilir ve geri alınabilir olmalıdır.

## Faz 0 — Sözleşme ve kayıt

- [x] Çoklu motor mimari belgesi
- [x] Engine registry JSON Schema
- [x] Backstage, Nx ve Lowdefy için metadata-only örnek kayıtlar
- [x] Şemayı doğrulayan stdlib-only Python komutu
- [x] Mevcut `scripts/validate.py` içine salt-okunur registry kontrolü
- [x] Registry değişiklikleri için fixture testleri

Çıkış ölçütü:

```text
python scripts/divan.py engines validate --registry registry/engines.example.json --json
```

komutu ağ erişimi ve üçüncü taraf paket olmadan deterministik sonuç verir.
`0` gecerli registry, `1` gecersiz registry verisi, `2` okunamayan dosya
anlamina gelir. Komut motor kurmaz, calistirmaz, vendor etmez veya fork'u
onaylamaz.

## Faz 1 — Karar motoru

Yeni çekirdek yüzeyleri:

```text
divan engines list
divan engines inspect <id>
divan engines recommend --project . --intent "..."
```

İlk karar motoru LLM kullanmaz. Girdi sinyalleri:

- proje türü,
- public/internal,
- özel UI,
- SEO,
- gerçek zamanlılık,
- local-first,
- hassas veri,
- bakım kapasitesi,
- host kabiliyeti.

Çıkış:

- seçilen motor,
- güven seviyesi,
- gerekçeler,
- reddedilen adaylar,
- riskler,
- gereken kalite profili,
- kaçış planı.

## Faz 2 — Adapter SDK

Python stdlib-only adapter protokolü:

```python
class EngineAdapter(Protocol):
    def detect(self, project: Path) -> DetectionResult: ...
    def plan(self, project: Path, intent: str) -> EnginePlan: ...
    def validate_environment(self, project: Path) -> CheckResult: ...
    def inspect(self, project: Path) -> InspectionResult: ...
    def verify(self, project: Path) -> VerificationResult: ...
```

İlk adaptörler:

1. `reference`: hiçbir dış komut çalıştırmayan fixture adaptörü.
2. `nextjs`: yalnız tespit, inceleme ve doğrulama planı.

Bu fazda scaffold veya paket kurulumu yapılmaz.

## Faz 3 — Sağlayıcı çalıştırma sözleşmesi

Dış komut güvenliği:

- allowlist,
- timeout,
- cwd sınırı,
- UTF-8 çıktı,
- secret redaction,
- dry-run,
- gerçek yürütme için açık `--execute`,
- process tree sonlandırma,
- stdout/stderr boyut sınırı,
- receipt kaydı.

Windows, Linux ve macOS farkları fixture'larla doğrulanır.

## Faz 4 — Nx sağlayıcısı

Amaç:

- TypeScript monorepo tespiti,
- project graph okuma,
- affected lint/test/build planlama,
- Divan generator sözleşmesi,
- dependency-boundary kontrolü.

Kısıt:

Nx hiçbir zaman Divan Python çekirdeğinin çalışması için zorunlu değildir.

## Faz 5 — Backstage bridge

İlk sürüm salt-okunur projeksiyondur:

- `.divan` ve receipt kayıtlarından `catalog-info.yaml` üretim planı,
- kalite özeti,
- API ve TechDocs bağlantıları,
- şablon kataloğu.

Backstage portalı ayrı process/sidecar olarak çalışır. Portal kapalıyken CLI işlevleri kaybolmaz.

Topluluk pluginleri otomatik kurulmaz. Her plugin ayrı aday ve kabul kaydı gerektirir.

## Faz 6 — Lowdefy sağlayıcısı

İlk güvenli kapsam:

- var olan Lowdefy projesini tespit,
- yapılandırma dosyalarını parse etmeden envanterle,
- paket ve komut planını göster,
- iş mantığı sızıntısı için statik kontroller,
- export ve uninstall planı.

Scaffold ancak bu denetimler fixture projelerde geçtiğinde açılır.

## Faz 7 — Diğer sağlayıcılar

Bağımsız PR'lar:

- Directus
- Activepieces
- Metabase
- Next.js
- NestJS
- Tauri

Her sağlayıcı şu kanıtları taşır:

1. immutable upstream pin,
2. license evidence,
3. clean install fixture,
4. no-write preview,
5. execute test,
6. verify test,
7. uninstall/rollback test,
8. secret redaction test,
9. Claude ve Codex host çıktısı,
10. receipt doğrulaması.

## Faz 8 — Codex ve Claude iş paylaşımı

Ortak kaynak:

```text
AGENTS.md
CLAUDE.md
.divan/
registry/
receipts/
```

Önerilen görev ayrımı:

- planlayıcı: görev riskine göre Claude veya Codex,
- uygulayıcı: ayrı oturum,
- denetçi: uygulayıcı olmayan host/model veya deterministik araç,
- son karar: kullanıcı.

Bir hostun bulunmaması diğer hostu bozmamalıdır.

## Faz 9 — Yerel ürün yüzeyi

İlk ürün yüzeyi mevcut Seyir sunucusunun genişletilmesidir:

- motor kataloğu,
- proje motorları,
- karar gerekçesi,
- kalite kapıları,
- sağlayıcı sağlık durumu,
- receipt geçmişi.

Backstage portalı daha zengin kurumsal görünüm olarak isteğe bağlı kalır.

## Codex ticket kuralı

Her Codex görevi:

- tek fazın tek alt maddesi,
- sınırlı dosya listesi,
- açık kabul ölçütleri,
- çalıştırılacak komutlar,
- değiştirilmeyecek yüzeyler,
- receipt güncellemesi

içermelidir.

Örnek ilk uygulama ticket'ı:

```text
Read AGENTS.md, docs/Multi-Engine-Architecture.md and
registry/engine-registry.schema.json.

Implement only a stdlib-only validator for the engine registry.
Do not add dependencies. Do not install engines. Do not modify host installers.
Add fixtures for valid, duplicate-id, unknown-field and invalid-license records.
Wire the check into scripts/verify.py only after local tests pass.
Return exact commands and outputs; do not claim third-party integration.
```
