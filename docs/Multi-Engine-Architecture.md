# Divan Çoklu Motor Mimarisi

## Durum

Önerilen mimari sözleşme. Bu belge tek başına herhangi bir üçüncü taraf projeyi kurmaz, forklamaz veya çalışma zamanı bağımlılığına dönüştürmez.

## Amaç

Divan; Backstage, Nx, Lowdefy, Directus, Activepieces, Metabase, Next.js, NestJS ve Tauri gibi sistemleri kendi içine kontrolsüz biçimde gömen bir dağıtım olmayacaktır.

Divan'ın rolü:

1. Kullanıcı niyetini ve proje bağlamını anlamak.
2. Uygun motoru kanıta dayalı şekilde seçmek.
3. Seçilen motoru sabit bir adaptör sözleşmesi arkasında çalıştırmak.
4. Kod, yapılandırma, test, güvenlik ve yayın kanıtlarını ortak kalite kapılarından geçirmek.
5. Motor değişse veya kaldırılsa bile proje verisi ile iş mantığının taşınabilirliğini korumak.

## Temel ilke

> Divan bir framework koleksiyonu değil; framework'leri seçen, sınırlandıran, doğrulayan ve gerektiğinde değiştiren yerel üretim kontrol düzlemidir.

## Kontrol düzlemi

```text
Kullanıcı / Hükümdar
        |
        v
Niyet ve kapsam sözleşmesi
        |
        v
Karar motoru
        |
        +--> Motor kataloğu
        +--> Kalite profili
        +--> Risk profili
        +--> Host kabiliyeti
        |
        v
Uygulama planı
        |
        +--> Claude Code
        +--> Codex
        +--> Yerel araç sağlayıcıları
        |
        v
Motor adaptörleri
        |
        +--> nextjs
        +--> nestjs
        +--> lowdefy
        +--> directus
        +--> activepieces
        +--> metabase
        +--> backstage
        +--> tauri
        |
        v
Doğrulama + receipt + teslim
```

## Katmanlar

### 1. Divan Core

Stdlib-only çekirdeğin sorumlulukları korunur:

- niyet çözümleme,
- kapsam ve otorite,
- planlama,
- host tespiti,
- kanıt toplama,
- receipt üretimi,
- fail-closed doğrulama.

Çekirdek hiçbir motor SDK'sını doğrudan import etmez.

### 2. Engine Registry

Her motor salt veri manifesti ile tanımlanır.

Zorunlu alanlar:

- `id`
- `decision`
- `status`
- `license`
- `source`
- `host_compatibility`
- `supported_project_types`
- `forbidden_project_types`
- `quality_profiles`
- `installation`
- `escape_plan`
- `portability`
- `business_logic_ownership`
- `frontend_replaceability`
- `when_unavailable`

Bu fazdaki registry yalniz metadata kapisidir. `category`, `capabilities`,
`constraints`, `adapter_contract_version` ve gercek adapter protokolu sonraki
fazlarda ayri testlerle eklenir; Faz 0 validator bunlari kabul edip sessizce
yok saymaz.

### 3. Engine Adapter

Her motor aynı davranış sözleşmesini uygular:

```text
detect(project)
plan(project, intent)
validate_environment(project)
scaffold(project, request)
inspect(project)
verify(project)
migrate(project, from, to)
doctor(project)
uninstall(project)
```

Adaptörün görevleri:

- yalnız ilgili motor yüzeyini yönetmek,
- önizleme ile gerçek yazımı ayırmak,
- dış komutları allowlist üzerinden çalıştırmak,
- mutlak yolları ve sırları receipt içine sızdırmamak,
- motor yoksa sahte başarı yerine `BLOCKED` üretmek.

### 4. Backstage Bridge

Backstage Divan'ın beyni değildir. İsteğe bağlı portal ve katalog görünümüdür.

İlk kapsam:

- Software Catalog projeksiyonu,
- Software Templates projeksiyonu,
- TechDocs bağlantısı,
- API Docs bağlantısı,
- kalite ve receipt özetleri.

Backstage olmadan Divan CLI ve host eklentileri çalışmaya devam etmelidir.

### 5. Nx Bridge

Nx zorunlu çalışma zamanı değildir. TypeScript monorepo projelerinde generator, executor, migration ve dependency-boundary sağlayıcısıdır.

Divan'ın kendi Python çekirdeği Nx'e bağımlı olmayacaktır.

### 6. Knowledge Registry

Tek ve dev bir teknik kitap yerine makine tarafından okunabilen küçük kayıtlar tutulur:

- karar ağaçları,
- motor yetenekleri,
- kalite profilleri,
- güvenlik kuralları,
- mimari sınırlar,
- anti-pattern kayıtları,
- ADR'ler,
- upstream provenance,
- doğrulama tarifleri.

İnsan belgeleri bu kayıtların projeksiyonu olabilir; kaynak gerçek tek yerde tutulur.

## Motor seçimi

Motor seçimi LLM'in serbest yorumuna bırakılmaz. Karar motoru şu girdileri puanlar:

- public web / internal tool / desktop / API / automation,
- SEO,
- özgün UI gereksinimi,
- gerçek zamanlılık,
- veri hassasiyeti,
- offline/local-first gereksinimi,
- ölçek,
- bakım kapasitesi,
- lisans,
- motorun export ve kaldırılabilirlik durumu,
- host ve işletim sistemi kabiliyeti.

Seçim çıktısı en az şunları içerir:

```yaml
selected_engine: lowdefy
confidence: medium
reasons:
  - internal CRUD application
  - limited custom interaction
rejected:
  nextjs:
    - unnecessary custom-code cost
escape_plan:
  database_owned_by_project: true
  business_logic_outside_engine: true
  export_test_required: true
```

## Kaçış planı

Bir motor ancak şu koşullarla üretim adayı olabilir:

- proje verisi dışa aktarılabilir,
- iş mantığı motor UI'sına gömülmez,
- kimlik ve sır yönetimi ayrıştırılmıştır,
- adaptör kaldırılabilir,
- migration ve rollback planı vardır,
- motor olmadan veri okunabilir kalır.

## Fork politikası

Varsayılan karar sırası:

1. `REFERENCE`: fikir ve karşılaştırma girdisi.
2. `ADAPT`: sözleşme veya yaklaşım Divan'a özgün uygulanır.
3. `ADOPT`: pinli bağımlılık veya araç sağlayıcısı olarak kullanılır.
4. `FORK`: yalnız zorunlu ürün kontrolü, upstream uyumsuzluğu veya sürdürülebilir yama ihtiyacı kanıtlanırsa.

Bir fork için zorunlu kayıtlar:

- upstream repo ve commit,
- lisans ve notice,
- fork gerekçesi,
- upstream sync politikası,
- taşınan değişiklik listesi,
- güvenlik sahibi,
- kaldırma planı,
- bakım bütçesi.

## Host sözleşmesi

Claude Code ve Codex aynı gerçek kaynağı kullanır:

- `CLAUDE.md`: Claude giriş yüzeyi,
- `AGENTS.md`: Codex giriş yüzeyi,
- `.divan/`: ortak proje sözleşmesi,
- Divan CLI: deterministik işlemler,
- MCP veya host-native plugin: araç köprüsü,
- receipt: ortak kanıt.

Host hiçbir zaman tek başına kalite hakemi değildir.

## İlk teslim dilimi

İlk sürüm yalnız şu parçaları uygular:

1. engine manifest şeması,
2. engine registry okuyucusu,
3. salt-okunur motor seçimi,
4. `reference` adaptörü,
5. `nextjs` örnek adaptörü,
6. kalite profili bağlantısı,
7. receipt genişletmesi,
8. Codex ve Claude için aynı plan çıktısı.

Backstage portalı, Lowdefy, Directus, Activepieces, Metabase ve Tauri daha sonra bağımsız, geri alınabilir sağlayıcılar olarak eklenir.

## Kabul ölçütleri

- Divan çekirdeği üçüncü taraf runtime import etmez.
- Motor seçimi JSON olarak tekrarlanabilir sonuç üretir.
- Bilinmeyen motor fail-closed davranır.
- Önizleme yazma yapmaz.
- Motor kaldırıldığında Divan'ın temel komutları çalışır.
- Claude ve Codex aynı plan ve kalite profilini görür.
- Her gerçek entegrasyon pin, lisans, doğrulama ve receipt kanıtı taşır.
