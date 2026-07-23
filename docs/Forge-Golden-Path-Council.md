# Forge Golden Path Council

> GitHub büyük bir kaynak havuzudur; Divan'ın görevi bütün kaynakları yüklemek değil,
> doğru tabanı kanıtla seçmek, sabitlemek, materialize etmek ve kalite kapılarıyla
> ürüne dönüştürmektir.

## Amaç

Golden Path Council, boş klasörden uygulama yazdırmak yerine doğrulanmış açık kaynak
başlangıçları ve ürün tabanlarını kullanır. Upstream kaynak kodu Divan reposuna
vendoring yoluyla gömülmez. Divan yalnızca kaynak kimliği, exact commit, lisans
kapsamı, seçim kuralı, profil ve kanıt durumunu tutar.

Makine-okunur tek kaynak: [`registry/forge/sources.json`](../registry/forge/sources.json).

## Kaynak sınıfları

| Sınıf | Anlamı | Örnek |
|---|---|---|
| `GOLDEN_PATH` | Belirli bir ürün/teknoloji ihtiyacı için birincil taban | NextBase, Wave, FastAPI |
| `ALTERNATIVE` | Aynı ailede farklı mimari veya daha dar ihtiyaç | Makerkit Lite, Larament |
| `PRODUCT_BASE` | Starter değil, özelleştirilecek çalışan ürün/motor | Bagisto, Chatwoot, Formance |
| `TOOL` | Oluşturulan projede yetenek sağlayan harici araç | Serena |
| `REFERENCE` | Uyumluluk ve yöntem girdisi; materialize edilmez | Claude Code Best Practice |

`LOCKED`, kaynağın exact commit ve lisans kanıtının kaydedildiği anlamına gelir.
**Yerel build'in geçtiği anlamına gelmez.** `build_evidence` alanı `verified` olmadan
Divan kaynağı üretimde doğrulanmış diye tanıtmaz.

## Seçim haritası

| Kullanıcı ihtiyacı | Birincil taban | Alternatif/Not |
|---|---|---|
| Next.js + Supabase SaaS | NextBase | Makerkit Lite daha küçük alternatif |
| Next.js + Clerk + Drizzle + teams/RBAC | Ixartz SaaS Boilerplate | Supabase tabanlarından farklı profil |
| Laravel + MySQL + cPanel SaaS | DevDojo Wave | cPanel doctor ve rollback Divan patch'i |
| Laravel + Filament admin/CRM | Larament | Canonical license file ve clean build tamamlanana kadar `CANDIDATE` |
| FastAPI + PostgreSQL + React | Full Stack FastAPI Template | Copier veya exact template clone |
| Django + PostgreSQL production | Cookiecutter Django | Generator seçenekleri cevap dosyasıyla sabitlenir |
| ASP.NET Core clean architecture | Jason Taylor CleanArchitecture | Resmî .NET template üretimi |
| Go service | Evrone Go Clean Template | Gereksiz transportlar profil patch'iyle çıkarılabilir |
| Electron masaüstü | Electron React Boilerplate | Secure IPC ve Windows package kapıları eklenir |
| Tauri masaüstü | Create Tauri App | Resmî generator; logo varlıkları alınmaz |
| Expo / React Native mobil | Obytes template | Jest, Maestro ve çoklu ortam profili |
| WordPress tema | Roots Sage | Blade, Vite, Tailwind ve Acorn |
| Laravel e-ticaret | Bagisto | Starter değil product fork; ticari eklentiler kapsam dışı |
| Müşteri destek/inbox ürünü | Chatwoot | `enterprise/` dizini varsayılan olarak kapsam dışı |
| Finansal ledger | Formance Ledger | Generic CRUD tabanı değildir; invariant ve deployment profili gerekir |
| Büyük mevcut kodu anlama/refactor | Serena | Upstream kodu vendoring yapılmaz; resmî kurulum kullanılır |

## Materialization biçimleri

### Template clone

Exact commit detached checkout edilir, kaynak ve lisans blob SHA doğrulanır. Ardından
Divan patch branch'i oluşturulur. Upstream geçmişi korunabilir veya yeni temiz proje
reposuna provenance kaydıyla aktarılabilir.

### Resmî generator

Tauri, Cookiecutter Django ve .NET template gibi kaynaklarda yalnız repoyu kopyalamak
yeterli değildir. Generator exact commit/ref üzerinden çalıştırılır; cevaplar
makine-okunur bir recipe dosyasında tutulur. Üretilen ağacın manifesti kanıta eklenir.

### Product fork

Bagisto, Chatwoot ve Formance zaten çalışan ürünlerdir. Bunlar küçük starter gibi
yeniden şekillendirilmez. Önce ürün sınırı, lisans kapsamı, yükseltme stratejisi,
veri modeli ve upstream sync maliyeti kabul edilir.

### Tool install

Serena gibi araçlar Divan'a kopyalanmaz. Resmî kurulum yöntemi kullanılır, sürüm/commit
kanıtı tutulur ve yalnız ilgili agent/capability için etkinleştirilir.

## Terfi kapıları

Bir kaynak `CANDIDATE` veya yalnız `LOCKED` durumundan gerçek doğrulanmış golden path'e
şu kapılar tamamlanmadan geçemez:

1. Exact commit checkout ve `git rev-parse HEAD` kanıtı.
2. Canonical lisans dosyası ve kapsam incelemesi.
3. Temiz Windows 11 ortamında kurulum.
4. Upstream baseline lint/test/build sonuçları.
5. Secret ve tedarik zinciri taraması.
6. Serena ile mimari/symbol haritası veya eşdeğer kod incelemesi.
7. Divan profil patch'lerinin ayrı committe uygulanması.
8. Gerçek bir vertical-slice golden task.
9. Native kalite kapıları ve gerekiyorsa Playwright/Maestro.
10. Claude uygulaması ve Codex bağımsız review kanıtı.
11. Kurulum, rollback ve upstream sync tatbikatı.
12. `build_evidence: verified` kaydı ve evidence yolu.

Başarısız kaynak otomatik olarak başka bir kaynağa düşmez. Resolver gerekçeyi ve
blocker'ı kullanıcıya gösterir.

## GitHub okyanusu politikası

GitHub keşfi kapatılmaz; iki aşamaya ayrılır:

- **Discovery:** salt okunur arama, lisans ve bakım sinyali toplama. Sonuçlar adaydır.
- **Promotion:** exact commit, temiz build ve golden task. Sonuç kanıtlanmış profildir.

Yıldız sayısı, README iddiası veya popülerlik tek başına terfi ölçütü değildir.
Arşivlenmiş repo varsayılan olarak reddedilir. Açık çekirdek reposunda enterprise,
pro, marketplace veya ayrı lisanslı dizinler otomatik olarak alınmaz.

## Vibe coder deneyimi

Kullanıcı repo isimlerini ezberlemez:

```text
/forge new "cPanel'de çalışacak restoran QR menü ve sipariş sistemi"
```

Divan şu sonucu açıklayarak verir:

```text
Seçilen profil: laravel-mysql-cpanel-saas
Seçilen taban: DevDojo Wave
Neden: Laravel SaaS temeli, MySQL uyumu ve cPanel teslim profili
Exact commit: d5f7ed2...
Durum: LOCKED, yerel build kanıtı henüz yok
Sonraki kapı: clean clone → baseline → cPanel doctor → vertical slice
```

Kullanıcı isterse öneriyi değiştirir; Divan sessizce başka repo seçmez.

## Serena'nın yeri

Serena bir golden path starter değildir. Forge'un semantik kod zekâsıdır:

- starter mimarisini sembol seviyesinde öğrenme,
- referans ve etki analizi,
- cross-file rename/refactor,
- patch sonrası kayıp referans kontrolü.

Küçük metin değişikliklerinde built-in arama yeterlidir. Büyük upstream tabanlarda ve
cross-file değişikliklerde Serena capability router tarafından zorunlu tutulabilir.

## İlk icra sırası

1. Wave 1: NextBase, Wave, Full Stack FastAPI.
2. Wave 2: .NET, Go, Electron, Ixartz, Django, Tauri, React Native, Sage.
3. Alternatifler: Makerkit Lite ve Larament.
4. Wave 3 product bases: Bagisto, Chatwoot, Formance.

Wave numarası kalite sıralaması değil, doğrulama ve uygulama sırasıdır.
