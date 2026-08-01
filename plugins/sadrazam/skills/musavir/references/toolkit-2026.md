# 2026 Uygulama Araçları Karar Matrisi

**Son gözlem:** 2026-08-01

Bu tablo kurulum listesi değildir. Karar, projenin kabul edilmiş mimarisine ve
somut boşluğuna göre verilir. "Yerel OSS" yazması barındırma, bulut, destek veya
API kullanımının da ücretsiz olduğu anlamına gelmez.

## Web arayüzü ve deneyim

| Araç | Teslim modeli | Varsayılan karar | Ne zaman / sınır |
|---|---|---|---|
| Tailwind CSS | runtime build dependency | `KEEP` | Mevcut tasarım diliyse koru; ikinci CSS sistemi ekleme |
| shadcn/ui | source-owned component | `ADD` | Seçili bileşenleri kaynak olarak al; registry içeriğini çalıştırmadan önce incele |
| Radix Primitives | runtime dependency | `ADD` | Erişilebilir headless davranış boşluğu varsa |
| React Hook Form | runtime dependency | `ADD` | Büyük ve durumlu formlarda render/validation ergonomisi için |
| TanStack Table | runtime dependency | `ADD` | Operasyon tablolarında sorting, filtering ve controlled state için |
| TanStack Virtual | runtime dependency | `ADD` | Ölçülmüş büyük liste maliyeti varsa; Table sanallaştırmayı kendi içinde sağlamaz |
| Lucide | runtime dependency | `KEEP/ADD` | Tek ikon dili; elle SVG çoğaltma |
| i18next | runtime dependency | `ADD` | Türkçe varsayılan ve gerçek çok-dil yol haritası varsa |
| Recharts | runtime dependency | `ADD` | Basit React yönetim grafikleri; finansal gerçeği grafikten türetme |
| Material UI | runtime design system | `REJECT` | shadcn/headless tasarım sistemi olan projeye ikinci temel sistem olarak ekleme |

## Sözleşme, veri ve alan yardımcıları

| Araç | Teslim modeli | Varsayılan karar | Ne zaman / sınır |
|---|---|---|---|
| openapi-typescript | dev dependency | `ADD` | OpenAPI sözleşmesinden TS tipleri üretilecekse |
| openapi-fetch | runtime dependency | `ADD` | Üretilmiş tiplerle hafif Fetch istemcisi gerekiyorsa |
| Ajv | runtime/dev dependency | `ADD` | JSON Schema runtime doğrulaması somut sınırda gerekiyorsa |
| csv-parse | runtime/dev dependency | `ADD` | Finansal/veri içe aktarmada ad hoc split yerine yapılandırılmış parse için |
| decimal.js | runtime dependency | `LATER` | Oran/hassas matematik için; para saklama kuralı yine integer minor unit |
| libphonenumber-js | runtime dependency | `ADD` | Uluslararası telefon parse/format/validation ihtiyacı varsa |
| schwifty | ayrı Python paketi veya referans | `REFERENCE` | Python servisinde IBAN/BIC parse ve doğrulama için düşünülebilir; TS projeye doğrudan runtime değildir |
| Türkiye IBAN veri paketi | bağımsız veri/paket | `ADD` | TCMB kaynaklı kuruluş kodları için; gerçek IBAN içermez, dil bağımsız JSON/CSV/SQL sağlar |

`schwifty` ülkeye özgü IBAN biçimini ve checksum'u doğrulayabilir, bileşenleri
çıkarabilir ve elle küratörlü registry'den bazı banka/BIC eşlemelerini sunar.
Türkiye kuruluş verisinin doğruluğu yine TCMB kaynakları, gözlem tarihi ve ayrı
veri yaşam döngüsüyle yönetilmelidir. Kütüphaneyi fork etmek, resmi Türkiye veri
paketi üretmenin yerine geçmez.

## Test ve kalite

| Araç | Teslim modeli | Varsayılan karar | Ne zaman / sınır |
|---|---|---|---|
| Storybook | dev dependency | `ADD` | Tekrarlanan UI durumları ve tasarım sistemi denetimi için |
| MSW | dev dependency | `ADD` | Tarayıcı/Node ağ davranışını aynı mock modeliyle test etmek için |
| Playwright | dev dependency | `KEEP/ADD` | Rol kabukları ve kritik akışların gerçek tarayıcı testi için |
| axe-core / Playwright | dev dependency | `ADD` | Otomatik erişilebilirlik kapısı; manuel WCAG denetiminin yerine geçmez |
| fast-check | dev dependency | `ADD` | IBAN, para, izin ve durum makinesi invariant'larında property test için |
| Testcontainers | dev dependency | `ADD` | PostgreSQL/RLS entegrasyonunu gerçek servisle test etmek için; cloud ürünü opsiyoneldir |

## Sunucu, gözlemlenebilirlik ve güvenlik

| Araç | Teslim modeli | Varsayılan karar | Ne zaman / sınır |
|---|---|---|---|
| NestJS + Fastify | runtime foundation | `KEEP` | Kabul edilmiş API çatısıysa Express ekleme |
| Pino | runtime dependency | `KEEP/ADD` | Yapılandırılmış ve redakte edilmiş log; hassas veri sınırları zorunlu |
| OpenTelemetry JS | runtime/dev dependency | `LATER` | İz/metric ihtiyacı olduğunda; JS log sinyali ve browser desteğinin olgunluğunu güncel doğrula |
| Socket.IO | runtime dependency | `LATER` | Kanıtlanmış çift yönlü realtime gerekirse; tek yön için SSE/polling değerlendir |
| Express | runtime foundation | `REJECT` | Nest/Fastify yanında ikinci HTTP çatısı olmasın |
| MongoDB + Mongoose | runtime data foundation | `REJECT` | PostgreSQL/RLS finansal çekirdeğine paralel ikinci gerçeklik kaynağı kurma |
| Browser JWT yönetimi | auth yaklaşımı | `REJECT` | OIDC + BFF session mimarisinde token'ı tarayıcıya taşıma |

## CI, bağımlılık ve topluluk yönetişimi

| Araç | Teslim modeli | Varsayılan karar | Ne zaman / sınır |
|---|---|---|---|
| dependency-cruiser | dev dependency | `ADD` | Modül sınırlarını import grafiğinde mekanik korumak için |
| Trivy | harici CI aracı | `ADD` | Dependency, image, IaC ve secret taraması için; CI izinlerini sınırla |
| Semgrep Community Edition | harici CI/yerel araç | `ADD` | Kural tabanlı SAST için; bulgular insan incelemesi ister |
| Renovate | GitHub app veya self-hosted servis | `ADD` | Kontrollü dependency PR'ları; en az ayrıcalık ve config incelemesiyle |
| Changesets | dev dependency | `ADD/LATER` | Çok paketli yayımlanan kütüphanelerde; tek uygulama deploy'u için şart değil |

## Mobil yol

| Araç | Teslim modeli | Varsayılan karar | Ne zaman / sınır |
|---|---|---|---|
| Expo + React Native | ayrı uygulama foundation | `LATER` | Gerçek mobil ürün onaylandığında; web paneline paket olarak ekleme |
| Expo Router | mobile runtime dependency | `ADD` | Expo uygulamasında dosya tabanlı routing gerekirse |
| Expo Camera | mobile runtime dependency | `ADD` | Genel kamera/barkod ihtiyacı ve Expo uyumu için |
| VisionCamera | mobile runtime dependency | `LATER` | Yüksek performanslı frame processing gibi özel ihtiyaç varsa |

## Modernizasyon kararları

| Eski/çakışan seçim | Karar | Yol |
|---|---|---|
| Moment.js | `REPLACE` | Yeni kodda platform `Intl`, Temporal uyumlu çözüm veya dar bir tarih kütüphanesi |
| NativeBase | `REPLACE` | Resmi deprecation notuna göre gluestack veya güncel Expo uyumlu sistem |
| React Native Camera | `REPLACE` | Expo Camera veya ihtiyaca göre VisionCamera |
| React Virtualized | `REPLACE` | Yeni yüzeyde TanStack Virtual ya da dar ihtiyaçta react-window |
| Axios + openapi-fetch birlikte | `KEEP` tekini | Axios yalnız interceptor/non-OpenAPI ihtiyacı kanıtlıysa |
| Material UI + shadcn birlikte | `REJECT` ikinciyi | Tek tasarım sistemi ve ortak tokenlar |
| Socket.IO "belki lazım olur" | `LATER` | Somut gecikme ve yön gereksinimini ölç |

## Resmi kaynak izi

- shadcn/ui kurulum ve registry: https://ui.shadcn.com/docs/installation/manual
  ve https://ui.shadcn.com/docs/registry/github
- TanStack Table/Virtual: https://tanstack.com/table/latest/docs/overview ve
  https://tanstack.com/virtual/latest/docs/introduction
- openapi-fetch: https://openapi-ts.dev/openapi-fetch/
- MSW: https://mswjs.io/docs/
- Storybook: https://storybook.js.org/docs
- Playwright erişilebilirlik: https://playwright.dev/docs/accessibility-testing
- OpenTelemetry JS olgunluk durumu: https://opentelemetry.io/docs/languages/js/
- Testcontainers: https://testcontainers.com/
- Renovate güvenlik/izinler: https://docs.renovatebot.com/security-and-permissions/
- Semgrep CE: https://semgrep.dev/products/community-edition
- Moment proje durumu: https://momentjs.com/docs/
- NativeBase deprecation: https://github.com/GeekyAnts/NativeBase
- React Native Camera deprecation: https://github.com/react-native-camera/react-native-camera
- React Native yeni uygulama rehberi: https://reactnative.dev/docs/environment-setup
- schwifty dokümantasyonu ve paket kaydı: https://schwifty.readthedocs.io/en/latest/
  ve https://pypi.org/project/schwifty/

