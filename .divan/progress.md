# Divan İlerleme Defteri

## Agency OS kampanyası III — worker'lar sahaya indi (2026-08-16)

Dal: `feat/agency-os-turnkey-v1` · PR #165 · head `bd9ae2f`

### Kurulum tamam

| Bileşen | Sürüm | Yöntem |
|---|---|---|
| Claude Code | 2.1.229 | `winget install Anthropic.ClaudeCode` |
| Codex CLI | 0.147.0 | `npm install -g @openai/codex` |
| Playwright | 1.61.0 + chromium | CI ile aynı pin |

Yeni tarayıcı çatısı kurulmadı; repoda zaten kullanılan sürüm hizalandı.

### Codex sertifikalı

Tek kullanımlık bir git deposunda sınırlı headless `codex exec` çalıştırıldı
ve beklenen belirteci döndürdü; model ve token kullanımı raporlandı. Bu,
kimliği doğrulanmış ve çağrılabilir bir çalışandır — yalnız kurulu değil.

`codex login status` mevcut ChatGPT oturumunun kullanılabilir olduğunu
gösterdi; yeni bir giriş akışı başlatılmadı.

### Claude oturum açmadı

`claude doctor` kurulum sorunu bulmuyor, ancak "Not logged in" diyor.
Headless çağrı `Please run /login` döndürüyor. Giriş sahibin hesabını
gerektirir; **tek kalan kapı budur** ve etrafından dolaşılmadı.

### Keşifte iki gerçek kusur bulundu ve düzeltildi

1. **winget köprüsü**: winget her paketi kendi dizinine kurar ve yalnız
   kullanıcı PATH'ini değiştirir; daha önce başlamış bir süreç bunu göremez.
   Keşif ne bu kökü ne de bir kademe altını arıyordu, bu yüzden Claude
   kurulu olduğu hâlde eski PATH'li süreçte `TOOL_NOT_INSTALLED` okunuyordu.
   Artık winget paket kökü ve bir kademe altı aranıyor; yürüyüş sınırlıdır.
2. **Windows launcher tercihi**: arama uzantısız dosyayı tercih ediyordu;
   Codex için bu çalışmayan bir shell script'tir, ayrıca `.ps1` shim'i de
   kabul edilebiliyordu. Artık gerçek launcher'lar önce gelir.

### Deep Doctor şimdi

| Yetenek | Önce | Şimdi |
|---|---|---|
| codex | OFFLINE / TOOL_NOT_INSTALLED | DEGRADED / AUTH_NOT_VERIFIED |
| claude | OFFLINE / TOOL_NOT_INSTALLED | DEGRADED / AUTH_NOT_VERIFIED |
| browser-qa | OFFLINE | **CERTIFIED** |
| local-state-security | BLOCKED | BLOCKED (değişmedi, ACL'e dokunulmadı) |

Binary bulunması hâlâ CERTIFIED değildir.

### Açık kapı

`HARD_OWNER_AUTH_GATE`: Claude Code oturumu. Codex authenticated olduğu
için tek worker ile ilerlenebilir, ancak bağımsız hakem ayrımı
(writer ≠ reviewer) iki farklı sağlayıcı ister.

### Sıradaki kesin adım

1. Claude oturumu açıldığında Doctor'ı yeniden koş; iki worker da
   sertifikalanmalı.
2. Worker sertifikasyon sözleşmesi ve routing politikasını tamamla.
3. AgencyBench-02'yi gerçek attempt'larla koş.

## Agency OS kampanyası III — worker keşfi (2026-08-16)

Dal: `feat/agency-os-turnkey-v1` · PR #165 · head `ccc865e`

### Engelin gerçek nedeni kanıtlandı

Önceki koşum Codex ve Claude'u yalnız PATH aramasına dayanarak `OFFLINE`
bildirmişti. "PATH'te yok" ile "kurulu değil" farklı bulgulardır.

Bu oturumda kesin arama yapıldı: PATH, `where.exe`, npm global kökü ve bin
dizini, scoop shims, chocolatey bin, Program Files, `LOCALAPPDATA\Programs`
ve kullanıcı profili kökleri. **Hiçbirinde `codex` veya `claude`
çalıştırılabiliri yok.**

`C:\Users\User\.claude`, `.codex` ve `AppData\Roaming\claude` dizinleri var
ama bunlar Claude Desktop uygulamasının ve Codex'in yapılandırma/durum
dizinleridir; CLI kurulumu değildir.

Sonuç değişmedi ama artık varsayım değil kanıt: **worker'lar gerçekten
kurulu değil.**

### `worker_discovery`

Bulgu kalıcı yeteneğe çevrildi. Mevcut resolver önce kullanılır, sonra
belgelenmiş kurulum kökleri taranır. `ABSENT` sonucu **aranan her konumu
taşır**, böylece iddia kontrol edilebilir. PATH dışında bulunan bir worker
"environment sınırı" notuyla `RESOLVED` bildirilir.

Kimlik dosyası hiçbir zaman açılmaz; bir test probe'un credential dizinine
girmediğini doğrular.

### Tarayıcı yeteneği

Doctor'da eksikti ama **repoda zaten vardı**: `site-tests` workflow'u
`playwright==1.61.0` ve chromium kuruyor, `ui-pack` altında
`webapp-testing` skill'i mevcut. Yeni araç eklenmedi; Doctor aynı yeteneği
yokluyor. Yoklama alt süreçte çalışır çünkü çekirdek stdlib-only'dir —
ilk denemede playwright'ı doğrudan import ettiğimde sözleşme doğrulayıcısı
bunu yakaladı.

Bu makinede tarayıcı yeteneği `OFFLINE` / `BROWSER_NOT_INSTALLED`; CI
hattında kuruludur.

### Açık hard gate

AgencyBench hâlâ `TURNKEY_BLOCKED` / `WORKERS_OFFLINE`. Tek engel budur ve
sahip kararıdır: ücretli kodlama CLI'ını kurmak ve oturum açmak kimlik
işlemidir. Divan bunu kendi başına yapmaz.

Kurulum yapılsa bile oturum açılmadan Doctor `DEGRADED` /
`AUTH_NOT_VERIFIED` bildirir ve benchmark yine bloke kalır.

### Sıradaki kesin adım

Kampanya III'ün 2-15 arası bölümleri (worker sertifikasyonu, routing,
gerçek attempt yürütme, gerçek fault injection, tarayıcı/güvenlik kampanyası,
AgencyBench-02, onarım döngüsü, final teftiş) kurulu bir worker olmadan
kanıtlanamaz. Worker sağlandığında sıra budur.

Worker'sız yapılabilecek kalan işler: worker sertifikasyon sözleşmesi ve
routing politikası modelleri, Ferman öncesi worker hazırlık uyarısı,
doğrulama sırasında worktree mutation guard.

## Agency OS kampanyası II — PASS 9 ve 10 (2026-08-16)

Dal: `feat/agency-os-turnkey-v1` · PR #165 · head `df17551`

### PASS 9 — Deep Doctor

Tek kanonik Core sağlık modeli üretildi; CLI ve Desktop aynı modeli okur,
ikinci bir sağlık gerçeği yoktur. On dört yetenek denetlenir ve binary
varlığı asla hazırlık sayılmaz: çekirdek kendi sözleşmesini geri okur, spec
derleyici örnek bir ferman derler, hafıza deposu açılıp analitiğini
raporlar. Çözümlenen bir çalıştırılabilir `AUTH_NOT_VERIFIED` koduyla
`DEGRADED` bildirilir, çünkü `codex.exe` bulmak oturumun çalıştığını
kanıtlamaz.

Her yetenek, sertifikalı değilken sahibin neyi kaybettiğini yazmak
zorundadır; `CERTIFIED` olmayan her durum neden kodu taşımak zorundadır.
Çöken bir probe `BLOCKED` bulguya dönüşür ve asla kullanılabilir sayılmaz.

Bu makinedeki AppData capability SID'i tam istendiği gibi raporlanır:
`BLOCKED`, kod `LOCAL_STATE_DACL_POLICY`, ve yalnız yerel kanıtın son
doğrulamasını engellediği, geliştirmeyi durdurmadığı açıkça yazılır. ACL'e
dokunulmadı, kapı zayıflatılmadı.

Panel üç derinlik render eder; Padişah varsayılandır. Test, Padişah
görünümüne hiçbir neden kodunun veya DACL sözcüğünün ulaşmadığını ve
engelli bir yeteneğin asla hazır gösterilmediğini doğrular.

Bu iş sırasında üç mimari kural gerçek hatalarımı yakaladı ve üçü de
çözüldü: bildirilmemiş modüller, sınırsız dinamik import, ve kernel-project
katman ters çevrimi. Doctor artık ait olduğu `api` katmanındadır.

### PASS 10 — AgencyBench-01

Sonuç: **TURNKEY_BLOCKED**, neden `WORKERS_OFFLINE`.

Divan kendi hattını Ferman'dan iş paketi grafiğine kadar gerçekten yürüttü:
ürün sözleşmesi, UX kabul sözleşmesi, mimari kararlar ve dört iş paketi
üretildi, paket başına sınırlı bağlam derlendi. Çalışan atama adımında
durdu; bu makinede ne Codex ne Claude kurulu.

**Uygulama elle yazılmadı.** Yazılsaydı arkasında ölçüm olmayan bir `READY`
üretilirdi; bu sınav Divan'ın ne yapabildiğini ölçer. Ücretli bir kodlama
CLI'ını kurup oturum açmak kimlik işlemidir ve hard gate'tir.

On yedi kabul kapısının tamamı `BLOCKED` ve her biri nedenini taşır.
`HUMAN_INTERVENTION_COUNT` sıfırdır: koşu yardım isteği yüzünden değil
makine gerçeği yüzünden durdu.

Kanıt: `.divan/evidence/teftis-20260816-agencybench-01.md`.

### Teslim sonrası ürün zekâsı

Teslim edilmiş uygulama olmadığı için kullanım verisi yoktur ve öyleymiş
gibi davranılmadı. Altı öneri bu kampanyada fiilen gözlenen kanıta
dayandırıldı: çalışanların geç fark edilmesi, doğrulama sırasında worktree
düzenlemenin ürettiği beş sahte hata, yeni modül kaydının tekrarlanan
sürtünmesi, eksik tarayıcı yeteneği, kalibre edilmemiş token tahmini ve
yalnız merge yolunda tetiklenen öğrenme.

Kanıt: `.divan/evidence/teftis-20260816-product-intelligence.md`.

### Ölçüm

| | Test | Başarısız | Yeni regresyon |
|---|---|---|---|
| `main` | 1020 | 87 | — |
| PASS 10 head | **1181** | 84 | **0** |

Frontend 20/20 render testi. validate, ruff, mypy, clean-code, naming,
prose, standards, candidates, hijyen — hepsi yeşil.

### Sıradaki kesin adım

AgencyBench'i `TURNKEY_READY`'ye taşımak için tek engel kurulu ve kimliği
doğrulanmış bir kodlama çalışanıdır. Bu sahip kararıdır. Çalışan
sağlandığında benchmark aynı komutla yeniden koşulur ve kapı matrisi gerçek
sonuçlarla dolar.

## Agency OS kampanyası II — PASS 6, 7 ve 8 (2026-08-16)

Dal: `feat/agency-os-turnkey-v1` · PR #165 · head `514e15e`

PR #165 CI'ı bu oturuma girerken temizdi: 0 hata, 11 başarılı.

### PASS 6 — Worker güvenilirliği

`AttemptRecord` artık first-class. Task ile Attempt kesin ayrıdır: Task
ajansın verdiği söz, Attempt bir çalışanın o söze tek denemesidir. Mevcut
retry/recovery kodu yeniden yazılmadı, üzerine inşa edildi.

Canlılık ile ilerleme ayrı sinyaldir. Bir süreç canlı olup takılabilir, bu
yüzden atmaya devam eden ama hiçbir şey ilerletmeyen bir heartbeat yine
stall sayılır. PID de sağlık değildir: kayıtlı process start token, PID
yeniden kullanımına karşı korur.

Stall politikası sıralıdır ve yavaş çalışan asla ölü sanılmaz. Ölü süreç
zamanlayıcıdan bağımsız `ORPHANED`; canlı ama sessiz olan önce
`SUSPECTED_STALLED`, ancak stall sınırını aşınca `RECOVERY_PENDING` olur.

Kurtarma önce sınıflandırır. Esasen reddedilmiş iş körlemesine tekrar
denenmez; checkpoint'i olan kayıp çalışan resume, olmayan replace edilir;
attempt bütçesi sonsuz döngüyü keser.

**Fault injection gerçek**: test tek kullanımlık bir alt süreç başlatır,
çalışırken öldürür ve zinciri kanıtlar — attempt gerçekten çalışıyordu,
kill "sessizlik" değil "süreç yok" olarak algılandı, `ORPHANED` →
`RECOVERY_PENDING`, aynı task altında farklı sağlayıcıyla yeni attempt, ve
öldürülen attempt evidence/failure class/history'sini korudu. Canlılık
kontrolü devre dışı bırakılınca iki fault injection testi de kırmızıya
döner, yani totolojik değildir.

### PASS 7 — Context Compiler

Bütün repo ve bütün hafıza gönderilmiyor. Paket öncelik sırasıyla dolar:
önce task contract, kabul ölçütleri, güncel hata ve diff; sonra ürün/UX
sözleşmesi, mimari kararlar, hafıza, olaylar, testler ve kaynak sembolleri.

**Hiçbir şey sessizce düşmez**: her aday ya pakette ya da gerekçesi ve
tahmini maliyetiyle omission listesinde; testler iki kümenin adayları tam
olarak böldüğünü doğrular. Hiçbir şeyin sığmadığı bütçe yarım paket
göndermek yerine `budget_exceeded` olarak bildirilir.

Token sayısı güveniyle taşınır: tahmin `estimated`, ölçüm `exact`, kullanım
bildirmeyen sağlayıcı `unknown`. Uydurma sayı yok.

Dış bağımlılık eklenmedi. Mevcut project inspector, Agency Memory ve Spec
Compiler tüm girdileri sağladığı için Serena/Repomix spike'ı çalıştırılmadı
ve yapılmamış bir inceleme aday defterine yazılmadı.

### PASS 8 — Teftiş Factory

`QualityProfile` first-class. Altı profil modellendi, hepsi baseline
kapıları devralır ve profil yalnız yükümlülük ekleyebilir.

**Çalışmayan kapı asla geçmiş sayılmaz**: `SKIPPED`, `TIMEOUT`, `UNKNOWN`,
`NOT_INSTALLED` ve `BLOCKED` fail-closed'dır; hiç raporlanmamış kapı
"eksik" sayılır, "geçti" değil. İki kez raporlanan kapı en kötü sonucunu
korur. `PASS`/`FAIL` dışındaki her durum nedenini kaydetmek zorundadır.

`EvidenceManifest` sonucu yeniden kurulabilir kılar: proje, ferman, task,
attempt, çalışan, sağlayıcı, base/result commit, worktree, değişen
dosyalar, diff digest, komutlar ve çıkış kodları, kapı sonuçları, hakem ve
kararı, raporlar, politika kararları, hafıza gözlemleri, zaman damgaları ve
güveniyle token kullanımı. `delivery_state` kapı kararından türer, yani
çalışanın kendine "başarılı" demesi tek başına asla `READY` üretemez.

### Ölçüm

| | Test | Başarısız | Yeni regresyon |
|---|---|---|---|
| `main` | 1020 | 87 | — |
| PASS 6+7+8 head | **1164** | 84 | **0** |

Yerel quality-gate adımlarının tamamı yeşil: validate, ruff, mypy,
clean-code, naming, prose, standards, candidates, hijyen. Frontend 14/14.

### Süreç dersi

Bir doğrulama koşarken aynı worktree düzenlenmemeli. Deterministik runner
testi fixture ağacını canlı çalışma ağacından kopyaladığı için, koşu
sırasında yapılan düzenleme 5 sahte hata üretti. Temiz commit üzerinde
yeniden koşulunca sıfır regresyon çıktı.

### Sıradaki kesin adım

PASS 9 (Deep Doctor) ve PASS 10 (AgencyBench-01) yapılmadı. Deep Doctor
tek Core read modelini CLI ve UI'a vermeli; bu makinedeki AppData DACL
sorunu `BLOCKED` / `LOCAL_STATE_DACL_POLICY` olarak dürüst gösterilmeli ve
ACL değiştirilmemelidir.

## Agency OS kampanyası II — integration head (2026-08-16)

### Tek integration head

`feat/agency-os-turnkey-v1` artık tüm Agency OS yeteneklerini tek dalda
taşıyor. Zincir: `#158` → `#160` → spec compiler → Agency Memory →
Plugin Trust.

Bütün çakışmalar semantik çözüldü, taraf seçilmedi: iki protokol çakışması
da iki dalın aynı satıra ayrı yüzey eklemesiydi, ikisi de korundu;
`modules.json` modül bazında birleştirildi; progress defteri iki kaydı da
tuttu. Dispatcher 29 komut taşıyor ve hiçbiri kaybolmadı — bu varsayılmadı,
test edildi.

Üç handler tablosunun birleşmesi `desktop_protocol.py`'yi 409 satıra
çıkardı. Yine sıkıştırmak yerine `plugin.inspect` kendi
`plugin_protocol.py` modülüne alındı; `knowledge_protocol.py` zaten aynı
deseni kullanıyordu.

### CI hatası sınıflandırması

PR #162 iki kırmızı check ile geldi. **İkisinin de tek kök nedeni vardı**:
aday defterini güncelleyip `tests/test_meclis.py` içindeki sabit pin'i
güncellememiştim. `verify.py` tüm süiti koştuğu için quality-gate de aynı
testten düştü. Pin'ler tam da sessiz kaymayı önlemek için var; bilinçli
güncellendi. Coverage sorun değildi: %68, taban %64.

### Patron Masası gerçek ürün UX'i

`humanStatus.ts` saf bir sunum katmanıdır ve Core'un karar vermediği hiçbir
şeyi türetmez. Sahibin altı sorusunu insan diliyle yanıtlar.

"Kod yazıldı" ile "Hazır" artık karıştırılamaz iki durumdur. Hazır yalnız
Core `DELIVERY_READY` veya `RELEASED` dediğinde çıkar. Bütün iş paketleri
tamamlanmış ama hâlâ `IMPLEMENTATION` olan proje "Yapılıyor" görünür;
`BLOCKED` proje asla "Hazır" görünemez. İkisi de test edilmiştir.

`ProjectStatusCard` üç derinlik render eder ve varsayılan Padişah'tır.
Padişah görünümünde hiç teknik kelime yoktur; test worktree yolu veya çıkış
kodunun orada görünmediğini doğrular.

### Gerçek frontend testleri

Kaynak metni grep'i bırakıldı. Vitest 4.1.10 (Vite 8 destekli),
`@testing-library/react` 16.3.2 (React 19 destekli) ve jsdom
proje-kapsamlı ve lockfile'a pinli kuruldu; global kurulum yapılmadı.
14 test gerçek render edilmiş DOM üzerinde çalışır, etkileşim `fireEvent`
ile tetiklenir ve derinlik seçicinin klavye/etiket sözleşmesi doğrulanır.

### Ölçüm

| | Test | Başarısız | Yeni regresyon |
|---|---|---|---|
| `main` | 1020 | 87 | — |
| integration head | 1128 | 84 | **0** |

Frontend: 14/14. Yerel quality-gate adımlarının tamamı yeşil.

### Sıradaki kesin adım

PASS 6'dan devam: attempt modelini first-class yapmak, ardından fault
injection ile kontrollü worker kill kanıtı. Sonra Context Compiler,
Teftiş Factory, Deep Doctor ve AgencyBench-01.

## Agency OS kampanyası — durum (2026-08-16)

Bu kayıt kampanyanın nerede kaldığını sonraki oturuma taşır. Hiçbir merge,
tag veya release yapılmadı; force push kullanılmadı.

### Canlı zincir

| Dal | Head | CI |
|---|---|---|
| `main` | `68e91fd` | — |
| `feat/patron-goal-plan-flow` (#158) | `7277186` | yeşil |
| `feat/agency-project-lifecycle-v1` (#160) | `4343cae` | yeşil |
| `feat/spec-compiler-v1` | `fac0fed` | yeni |
| `feat/agency-memory-current` | `414ef79` | yeni |
| `feat/plugin-sdk-current` | `8ee8fe0` | yeni |

`#158`, `#160`'ın atasıdır. `#161` Ottoman kimlik hattıdır ve Agency OS
kanonik yönü sayılmamıştır.

### Tamamlanan

1. **Spec Kit kararı kanıta bağlandı.** v0.16.4 izole tek seferlik spike ile
   incelendi, kurulmadı. Karar ADAPT olarak kaldı; aday kaydı yeni commit ve
   kanıtla tazelendi. `spec_compiler` bir Fermanı PROJECT_CONTRACT,
   UX_ACCEPTANCE_CONTRACT, ARCHITECTURE_DECISIONS, WORK_PACKAGE_DAG ve
   QUALITY_REQUIREMENTS sözleşmelerine derler; execution yetkisi vermez.
2. **Memory-first gerçek.** `memory_first.recall` sınırlı bir paket döndürür,
   cevaplayamadığını açıkça bildirir; yalnız bu boşluklar araştırma tetikler.
3. **Projeksiyon ve yeniden-kullanım bağlandı.** `knowledge.book`,
   `knowledge.recall` ve `knowledge.observe` komutları canlı; Markdown yalnız
   projeksiyon, SQLite otorite. Yeniden kullanım sayısı terfi yetkisi değil.
4. **Çelişkiler açık durum.** `SUPERSEDED`, `QUARANTINED`, `STALE` eklendi;
   `resolve_contradiction` hiçbir tarafı silmez, karantinadaki iddia
   planlayıcıya verilmez.
5. **Plugin girdisi sınırlandı.** Manifest 64 KB, capability 32, hata listesi
   sınırlı; yinelenen JSON anahtarı fail-closed reddediliyor.

### Açık kalanlar

- Plugin Trust Center gerçek render/component testi (kaynak metni grep'i
  yetersiz). Vitest gibi bir test koşucusu değerlendirilmeli.
- Worker güvenilirliği: attempt kimliği, heartbeat, stall, replacement ve
  kontrollü process kill testleri.
- Context Compiler ve token bütçesi.
- Teftiş Factory profil bağlama ve browser QA yeteneği.
- Deep Doctor tek okuma yüzeyi.
- Patron Masası'nın `project.agency.status` verisini üç derinlikli insan
  diline bağlaması.
- AgencyBench-01 uçtan uca kanıtı.

### Bilinen engel

Kanonik `scripts/verify.py` bu makinede engellidir. 87 hata `main` ile
birebir aynıdır ve tek nedeni `C:\Users\User\AppData` üzerindeki
capability-SID'in tüm ağaca tam yetki vermesidir. PASS sayılmamıştır ve ACL
değiştirilmemiştir.

`scripts/verify.py` tek başına CI değildir: ruff, mypy, clean-code, naming,
prose ve standards ayrı quality-gate adımlarıdır ve her PASS'ta ayrıca
çalıştırılmalıdır.
## Agency OS: Agency Memory portu (2026-08-16)

- PR #121 ve #123 main'den 20 commit geride kalmıştı. #123, #121'in üst
  kümesi olduğu için ikisi tek tutarlı değişiklik olarak current main'e
  port edildi; bayat yığın merge edilmedi. Port çakışmasız uygulandı.
- Portlanan kod Windows'ta çalışmıyordu. `KnowledgeStore._connect`
  bağlantıyı hiç kapatmıyordu; `sqlite3.Connection.__exit__` yalnız
  transaction'ı bitirir. 13 knowledge testinden 12'si `WinError 32` ile
  düşüyordu. POSIX açık dosyayı silebildiği için Linux CI'da görünmüyordu.
- Bağımsız teftiş üç P1 buldu ve BLOCK verdi. İkisi kapatıldı:
  - yakalanan metin redaksiyondan geçmiyordu; `OPENAI_API_KEY=...` ve tam
    ev yolu deftere ham giriyordu. Artık `receipts.redact_text` uygulanıyor
    ve redaksiyon digest'ten önce olduğu için `item_id` makineden bağımsız.
  - `upsert` küratörlüğü siliyordu; aynı hatayı tekrar yakalamak
    `validated`/0.95 kaydını `candidate`/0.5'e düşürüyor ve `created_at`
    ilk-görülme geçmişini yok ediyordu. Artık kimlik, ilk-görülme ve
    küratörlük sütunlarına dokunmuyor; terfi için ayrı `curate()` var.
- Üçüncü P1 de kapatıldı: yakalama yolunun test dışı çağıranı yoktu, yani
  defter üretimde boş kalırdı. Artık görev kapanışına bağlıdır. `review()`
  her reddin nedenini kaydeder; `approve_merge()` bu geçmişi, sonunda
  merge olan diff ile birleştirip tek bir bilgi kaydına çevirir.
- İlk seferde teftişi geçen görev hiçbir şey yazmaz: hiç başarısız olmamış
  işte ders yoktur ve temiz koşumlar defteri doldurup gerçek hataları
  gömerdi.
- Hafıza yazımı, bütün kapıları geçmiş bir merge'i asla düşüremez. Defter
  bozuksa hata yakalanır ve başarısız `knowledge` kanıt kaydına dönüşür;
  sonuç iki yönde de dürüst kalır ve kanıttan yeniden kurulabilir.
- `modules.json` artık yalnız kodun karşıladığını ilan eder.
  `cross_project_reuse_analytics` ve `generated_knowledge_projection`
  kaldırıldı: `observe()` üretimde hiç çağrılmıyor ve `render_book`
  ulaşılabilir değil. Modüller test edildiği ve projeksiyon yüzeyi
  geldiğinde gerekeceği için silinmedi.
- Regresyon farkı: main 1020 test / 87 başarısız, bu dal 1043 test / 87
  başarısız. Yeni regresyon yok.
- Açık kalan: projeksiyon yüzeyi (`render_book`) ve yeniden-kullanım
  sinyali (`observe()`) hâlâ bağlı değil. Bunlar sonraki dilimdir.

## Agency OS: Plugin SDK portu (2026-08-16)

- PR #119 main'den 22 commit geride kalmıştı; current main'e çakışmasız
  port edildi. `App.tsx` iki hattın da dokunduğu tek dosya olduğu için
  sonuç doğrulandı: `main.tsx` App'i hâlâ PatronDesk ile sarıyor, App
  hâlâ PluginTrustCenter render ediyor; iki yüzey birlikte yaşıyor.
- Plugin SDK, desktop protokol, Trust Center UI ve reflow testleri geçti;
  frontend iki yüzeyle birlikte derlendi (23 modül).
- Regresyon farkı: 1044 test / 87 başarısız; yeni regresyon yok.
- Bu port henüz bağımsız teftişten geçmedi; "hazır" değil, "portlandı ve
  derleniyor" olarak kayıtlıdır.
## Agency OS: Plugin SDK portu ve teftişi (2026-08-16)

- PR #119 main'den 22 commit geride kalmıştı; current main'e çakışmasız port
  edildi. `App.tsx` iki hattın da dokunduğu tek dosyaydı, sonuç doğrulandı:
  `main.tsx` App'i hâlâ PatronDesk ile sarıyor, App hâlâ PluginTrustCenter
  render ediyor.
- Bağımsız teftiş BLOCK verdi, P0 yok. Güvenlik çekirdeği sağlam çıktı:
  eklenti kodu hiçbir zaman import edilmiyor veya çalıştırılmıyor, hiçbir
  şey aktive edilemiyor, ve teftişin kurduğu hiçbir manifest doğrulamadan
  kaçamadı.
- P1 kapsam boşluğuydu: 32 ret nedeninden 24'ünün testi yoktu; kaçışı
  önleyen iki kontrolün ikisi de kapsamsızdı. Artık her ret nedeninin
  negatif testi var.
- Üç kontrol fazla kabul ediyordu ve üçü de düzeltilmeden önce koşularak
  doğrulandı: yalnız boşluktan oluşan SPDX ifadesi geçerli lisans olarak
  gösteriliyordu; `schema_version` ve `api_version` `True` kabul ediyordu
  (`bool`, `int` alt sınıfı); executable deseni `.`, `..` ve `CON`, `COM1`
  gibi Windows aygıt adlarını kabul ediyordu.
- İki ret kodu f-string ile üretiliyordu, bu yüzden grep'lenemiyordu ve
  teftişin ilk kapsam sayımından da bu yüzden kaçmışlardı; literal oldular.
- `modules.json` `bounded_plugin_discovery` ve `hash_bound_plugin_approval`
  yeteneklerini ilan ediyordu ama `approve_candidate`, `validate_activation`
  ve `discover_plugins` üretimde çağrılmıyor; tek canlı giriş
  `plugin.inspect`. İddialar kaldırıldı, modüller korundu.
- Regresyon farkı: main 1020 test / 87 başarısız, bu dal 1059 test / 87
  başarısız. Yeni regresyon yok.
- Açık kalan: reflow işi bu porta yapışmış durumda ve kendi değişikliğine
  ait; Trust Center UI testleri render yerine kaynak metni arıyor; manifest
  okuması ve hata listesi sınırsız; yinelenen JSON anahtarları sessizce son
  değeri alıyor.

## Hedef Güncellemesi (2026-08-04)

- `v1.3.8` adayı host recovery, typed continuation, host-bağımsız
  `ui-ux-pro-max` ve tek kaynaklı release kimliği değişikliklerini taşır.
- Temiz baseline `python -B scripts/verify.py --coverage` ile 777 testte,
  451 saniyede geçti; önceki uzun koşum takılma değil test süresiydi.
- Yeni release guard/tag testleri, UI davranış testleri, recovery testleri ve
  provenance kapıları yerelde geçti.
- `v1.3.7` etiketi ve Release kaydı tarihsel kanıt olarak değişmeden kalır;
  yeni yayın onun üzerine yazmaz veya etiketi taşımaz.
- Sıradaki kesin adım: `v1.3.8` adayının kanonik doğrulamasını tamamlamak,
  tek PR ile `main`e taşımak ve yalnız tüm zorunlu GitHub kontrolleri yeşilse
  değişmez tag/Release kimliğini yayımdan sonra yeniden okumaktır.

## Hedef Güncellemesi (2026-08-03)

- `python scripts/verify.py` 776 test ile geçti; `git diff --check` temiz.
- `python scripts/prose.py --check --json` temiz, `scripts/release.py --check` yüzeylerini doğruladı.
- `python scripts/divan.py doctor --host codex --ref v1.3.4 --json` `healthy` döndürdü.
- `BLUEPRINT.md`da sadece bir satır düzeltmesi kaldı; süreç ve kanıt kapıları kapanmamış durumda.
- Bir sonraki adım: bu dalın PR/merge hattını açıp main'e taşıyarak yeni bir `release` adımı sonrası canlı doğrulama ile kapanışı yapmak.

## Güncel çalışma: v1.3.4 yayımlanan topluluk bakımı

`main`, dağıtılan skill'lerdeki kanıtlanmış güvenlik/doğruluk açıklarını,
public komut örneklerini, bağımlılık gözlemini, nested skill impact
sınıflandırmasını ve Quality Gate'in tekrarlanan test işini zaten kapattı.
Windows eski-host checksum yolu artık PowerShell modül komutuna bağlı değildir.
v1.3.3 etiketi ve release varlıkları değişmez kalır. v1.3.4, bu sınırlı
topluluk bakım düzeltmelerinin ayrı, doğrulanabilir yayını olarak yayımlandı.

## Ajan kurulum canary'si

Yeni kurulum sözleşmesi temiz bir Windows 11 Codex ve Claude oturumunda
canary olarak yeniden çalıştırılabilir. Bu, yayımlanmış v1.3.4 kanıtını
genişletecek bakım çalışmasıdır; release'in varlığı için ön koşul değildir.

Son güncelleme: 2026-08-02

## Yayın durumu

- Latest published release: v1.3.4
- Published commit: 0fe544124daab90de9c4600349d411f79946857b
- Publication evidence: .divan/evidence/teftis-20260802-v134-release.md
- Release asset evidence: seven checksummed and attested v1.3.4 assets
- Release idempotency evidence: .divan/evidence/teftis-20260725-release-idempotency.md

## Güncel hedef

Divan v1.3.4 is the current immutable publication. It carries the portable
Windows checksum repair and the bounded risk-hardening work; tag, assets,
checksums, attestations, Pages, Wiki and README readbacks passed in the release
workflow.

Divan v1.3.1 closes the publication-truth gap left after v1.3.0: onboarding
surfaces now name the current immutable release, and the prose gate fails when
a public page presents a published release as a candidate.

## Sıradaki kesin iş

Maintain the community path: triage a real bug, documentation correction,
source candidate, or first contribution only when it arrives; keep the v1.3.4
tag and assets immutable, and use the same evidence-first release path for any
future change.

## Son yayımlanan durum

The latest published release is immutable v1.3.4 at commit
`0fe544124daab90de9c4600349d411f79946857b`. PR #106 published the portable
Windows checksum repair and current community surfaces after all PR checks
passed. The release workflow published seven assets; downloaded hashes, SBOM,
attestations, Pages, Wiki and README readbacks are recorded in
`teftis-20260802-v134-release.md`. Nöbet issue #85 remains closed with zero
review debt.

Divan remains one product and one repository. Divan Engine is the canonical
stdlib-only modular core; Divan Nizamı is the owner-first governance model; the
installed layer is Divan Project Contract / Divan Proje Sözleşmesi. Hükümdar is
the final authority and only `owner` may expand scope. Legacy Company OS,
Project OS, `/company`, `company-validate`, and Python/JSON paths remain bounded
compatibility surfaces through v1. The released v0.18.5 runner completed one
machine-verifiable clean-room adoption on Windows 11, Codex `0.146.0`, and a
real project distinct from Divan. One bounded test passed; the privacy-reviewed
schema-2 JSON and Markdown receipts re-verified offline as
`valid-clean-room-adoption`. The v1 readiness score is now 8/8. This is not an
independent-user count, endorsement, market-adoption, speed, or quality claim.

v1.0.3 preserves the Seyir wait-state UX and quiet workspace discovery, then
removes control-plane friction: a healthy doctor stops at READY, unhealthy
journals include an exact recovery command, and setup, daily use, and
maintenance are separate user journeys.

## Yapıldı

- Schema-1 adoption receipts remain verifiable with explicit non-v1 statuses.
  Schema-2 adds an immutable-release, distinct-project, verified-goal,
  observed-host, bounded-check, source-stability, privacy, and offline-digest
  contract. `adoption prove` previews without writes/processes; `--execute`
  runs the fixed host probe and safe checks once before atomically sealing
  evidence. Maintainer/external role does not affect eligibility.
- Issue #57 adds safe process probing,
  explicit profile selection, canonical fallback execution, exact 41-skill
  manifest verification, per-skill installed SHA-256 verification, a rollback
  command, and user-facing native/fallback limits. Plain native installation
  remains unchanged and invalid host JSON fails closed. Host parsing, output,
  diagnosis, profile policy, and lifecycle execution are separate modules; the
  registered install-function complexity and length debt was removed. PR #58
  merged at `f367de92e09b4f56e205d7e2883d988b3b4d2797`; release workflow
  `30500376337`, all required workflows, immutable assets, strict SLSA
  verification, and the isolated remote Windows lifecycle canary passed.
- PR #55 merged the v0.18.0 release preparation to `main` at
  `3bbbd95881a7c33f64e3e9f8d23824e3eef8977e`. Release workflow
  `30493811167` published immutable tag/Release v0.18.0. All five downloaded
  asset digests matched GitHub and both checksum manifests; the ZIP reports
  0.18.0, the SBOM is SPDX 2.3, and the portable runner validates. Every asset
  has one verified SLSA provenance record and API-visible release/v0.2 plus
  SLSA provenance/v1 attestations. All eight main/publication workflows passed.
- PR #54 merged Nizâm-ı Sefer to `main` at
  `7c674874503853216dc8f2abddaa0459811a5ee6`. Its required CI passed 562 tests
  with 11 expected platform skips and 75% coverage plus the cross-platform
  compatibility matrix, CodeQL, dependency review, Playwright, and Wiki/Pages
  checks. Two independent read-only reviews were completed and every reported
  P1/P2 finding was addressed before merge.
- Nizâm-ı Sefer now compiles intent into a deterministic dependency graph,
  structural risk, an explicit context-budget authority, portable model
  classes, at most three bounded sefers, durable handoff, and goal-bound
  `route.json`. Unknown or conflicting hosts fail safe to sequential work;
  environment values are not persisted and exact model availability requires
  host confirmation. Focused tests, public guides, skills, impact obligations,
  and release surfaces are synchronized in the published release.
- ADR 0008 and the v0.17.1 specification define one Vibe Progress Protocol.
  Sadrazam and all seven public chat commands point to the same loaded-plugin
  root contract. README, Wiki, Pages/site source, and the vibe-coder guide
  explain the user benefit and the contract-only evidence boundary. The clean
  Windows candidate passed the canonical verifier with 544 tests and 14
  platform-specific skips; 5 packages, 41 skills, and 151 release surfaces
  matched. Independent whole-change review reported no open P0-P3 findings and
  approved the local release gate. The nine-module runtime, Hükümdar authority
  order, compatibility paths, and v1 7/8 status remain unchanged.
- PR #49 merged v0.17.0 to `main` as
  `8b711b6f0ebb696ce971d83c90833bb59acf3c34`. Seven PR workflows and nine
  main/publication workflows completed successfully. Release workflow
  `30453034011` published immutable tag/Release `v0.17.0`; all five downloaded
  asset digests, both checksum manifests, SPDX 2.3 metadata, the schema-2 runner
  envelope, and two attestations per asset matched. Pages returned HTTP 200 and
  Wiki exposed the Divan Engine and Hükümdar-first contract. Exact evidence is
  `.divan/evidence/teftis-20260729-v017-release.md`.
- The v0.17.0 implementation passed 538 tests with 7 platform-specific skips and
  76% coverage. Ruff, mypy, Clean Code, 41/41 Agent Skills, the root
  marketplace plus five plugins under Claude Code 2.1.212 strict validation,
  local Chromium site verification, and two byte-identical project-runner
  builds passed. Independent review findings for ambient module-cache spoofing,
  pre-resolve runtime path identity, and dynamic imports were addressed
  test-first. Final independent re-review reported no open P0-P3 findings and
  approved the local release gate.
- Issue #33 was closed by merged PR #46 at `5f7f088`. The canonical verifier
  keeps generated caches outside the checkout and ends with a clean hygiene
  check on Windows as well as CI hosts.
- PR #39 merged the issue #38 release-idempotency repair as `da5c2a7c`.
  Main release run `30131579254` passed all three clean hosts, skipped duplicate
  attestation, and verified all five v0.16.0 assets byte-for-byte from the
  immutable tag. The tag, five SHA-256 digests, and two attestations per asset
  remained unchanged. Evidence is tracked in
  `.divan/evidence/teftis-20260725-release-idempotency.md`.
- PR #31 merged v0.16.0 to `main`; tag `v0.16.0` points to
  `5513e73d5faa8657a22d813ecfec763a6089bea0`. The Release page returned HTTP
  200 and live Pages/Wiki readbacks contained v0.16.0. Bounded evidence is
  tracked in `.divan/evidence/teftis-20260725-v016-publication-handoff.md`.
- All five v0.16.0 Release assets were downloaded again and their SHA-256
  values matched the GitHub asset digests and published checksum manifests.
  The SPDX 2.3 SBOM, runner source envelope, release/SLSA attestations, release
  workflow, Pages, and Wiki readbacks are tracked in
  `.divan/evidence/teftis-20260725-v016-release-assets.md`.
- The post-merge evidence branch passed 495 tests with 11 platform skips, 74%
  branch coverage, Ruff, mypy across 61 source files, Clean Code, release,
  handoff, Wiki, Company OS, and eval contract checks. v1 remains 7/8.
- Schema 2 config and install state bind immutable version/ref/commit, project
  identity, and managed whole-file/marked-block payload hashes.
- `project status` is read-only; `project update` and `project repair` are
  dry-run-first and reuse the proven lock, ACL, journal, authority, marker,
  rollback, and recovery transaction boundary.
- Verified goals archive with bound hashes and controlled source removal.
  Adoption export writes redacted JSON/Markdown and distinguishes
  `valid-owner-canary` from `valid-independent-declaration`.
- The deterministic project runner, impact graph, DCS-007, README, Project OS,
  install, Wiki, changelog, blueprint, and publication manifest include the new
  lifecycle while 5 packages/41 skills and v1 at 7/8 remain unchanged.
- Ruff, mypy, coverage, and Clean Code now measure the first-party Company OS
  runtime; previously invisible exact module/function/complexity debt is pinned
  in the ratchet and cannot increase without failing CI.
- Whole-branch review approved the Project OS candidate at `1a94b61` after
  provider, SEO, initialization, recovery, and mutation-authority findings were
  closed test-first.
- Portable Project OS now provides dry-run-first initialization, deterministic
  goals/specs/plans/tasks, append-only receipts, `DPS-001..DPS-012`, bounded
  monorepo discovery, Unicode English/Turkish routing, multi-workflow planning,
  fail-closed impact classification, and provider-native release evidence.
- Public-web projects receive scoped SEO/accessibility policy, static metadata
  checks, pinned Lighthouse CI/Lychee plans, and provider-bound live evidence;
  irrelevant web standards are not forced on libraries or services.
- English canonical Project OS, Company OS, Community Standards, README, Wiki,
  Pages/site, install, workflow, and release surfaces are synchronized with
  first-class Turkish localization.
- `python scripts/release.py --prepare 0.15.0` updated only deterministic version
  surfaces. Preflight passed 452 tests with 10 platform-specific skips, Ruff,
  mypy, Clean Code, and 71% coverage; five packages/41 skills and v1 at 7/8
  remain unchanged.
- The failed v0.14.0 dual-host upgrade rolled back automatically and both hosts
  were re-proven healthy at v0.12.2 before development continued.
- Codex's isolated native metadata file is now accepted through its existing
  schema, source, ref, revision, UTF-8, and symlink checks even when Codex also
  reports the marketplace ref. Additional dirt remains rejected.
- Company OS now maps natural-language intent to 12 functional roles, 8
  workflows, detected frameworks, the smallest justified pack set, and
  transitive documentation/Wiki/site/release effects.
- `scripts/divan.py` is the canonical English CLI. Existing Turkish script
  names are narrow deprecated compatibility aliases until v1.
- DCS-011, naming policy, English canonical README/contribution surfaces,
  Turkish locale files, Company OS docs, Pages, Wiki, CI, and release manifest
  are synchronized.

- v0.13.0 introduced DCS-001..DCS-010 as a machine-readable contract, a Clean
  Code debt ratchet, dual-host doctor/transactional upgrade, SPDX supply-chain
  evidence, and synchronized community/public documentation.
- Final local integration passed 223 tests with 2 platform-specific Windows skips;
  Ruff, mypy, Clean Code, actionlint 1.7.10, 41 skills via skills-ref 0.1.1, and
  the Claude marketplace plus five packages via Claude Code 2.1.212 passed.
- The generated 1280x640 RGB social preview is 908422 bytes and is now checked
  by the release manifest without adding an image runtime dependency.

- PR #21 bütün CI kapılarından geçti ve `c226dccf` ile `main`e birleşti.
  Release workflow `29705195263`; tag/Release, ZIP+SHA-256, Pages, Wiki ve canlı
  Chromium doğrulamasını başarıyla tamamladı.
- Sabit v0.12.2 kaynağı Claude ve Codex'e global kuruldu. Her host 5 paket/41
  skill ve doğru source/ref döndürdü; alakasız eklentiler korundu. Doğrulanmış
  işlem: `install-20260719T215712Z-c9095665.json`.
- Windows salt-okunur `__pycache__` hatası gerçek worktree'de üretildi;
  yalnız hata veren gerçek yolu yazılabilir yapıp junction/symlink üzerinde
  fail-closed kalan düzeltme iki Windows regresyonuyla test-first uygulandı.
- PR #19 bütün CI kapılarından geçti ve `4125c31e` ile `main`e birleşti.
  Release workflow `29704548820`; v0.12.1 tag/Release, ZIP+SHA-256, Pages, Wiki
  ve canlı Chromium doğrulamasını başarıyla tamamladı.
- Sabit v0.12.1 kaynağı Claude ve Codex'e global kuruldu. Her host 5 paket/41
  skill ve doğru source/ref döndürdü; alakasız eklentiler korundu. Doğrulanmış
  işlem: `install-20260719T213732Z-5a357853.json`.
- v0.12.1 hijyen kapsamı test-first tamamlandı: UTF-8/BOM/mojibake taraması,
  locale-bağımsız text subprocess kuralı, allowlist cache temizliği,
  `.editorconfig`/`.gitattributes` ve Ruff C90 McCabe 25 kapısı eklendi.
- `validate.denetle`, `rollback_transaction` ve v1 gerçek-kanıt doğrulaması
  aynı davranışı koruyan isimli sorumluluklara ayrıldı; 99 test yeşile geldi.
- Bağımsız kod incelemesindeki LF, subprocess alias/kodlama, hijyen
  entegrasyonu ve atomik yayın bulguları test-first kapatıldı; repo dışı
  symlink ve gereksiz worktree yürüyüşü de sertleştirildi.
- İkinci bağımsız incelemede önemli bulgu kalmadı. Tek küçük geri bildirim olan
  başarısız rollback yedeğinin tam kurtarma yolu da test-first rapora eklendi.
- Açık PR bulunmadığı doğrulandı; birleşmiş PR'lara ait 15 artık uzak `codex/*`
  dalı kalıcı silindi. Sahipliği belirsiz `claude/*`, `main` ve aktif dal korundu.
- Kapanmış PR #17/#16'nın yerel ve uzak dalları kaldırıldı. Ana repo ve aktif
  rollback yedeğindeki yalnız `__pycache__` içeriği kalıcı silindi; manifestin
  işaret ettiği gerçek kullanıcı skill yedeği korundu.
- Yayın hazırlayıcının geçmiş sürüm kayıtlarını kör replace etmesi regresyon
  testiyle düzeltildi. v0.12.1 güncel yüzeyleri değişirken v0.12.0 gerçek eval
  provenance'ı tarihsel olarak kalır.
- v0.12.0 ürün kapsamı tamamlandı: Claude ve Codex için aynı 5 paket/41 skill'i
  sunan yerel pazarlar, dry-run-first işlemsel kurucu, yalnız kendi kayıtlarını
  geri alan rollback ve alakasız eklentileri koruyan fixture testleri eklendi.
- Eski kopyalama fallback'i değişmez release varlığı + SHA-256 doğrulamasına
  geçirildi; manifest sürüm/ref/commit/hash/zaman/hedef/yedek kaydeder. Release
  workflow'u arşiv, checksum ve source commit yayınlayacak şekilde hazırlandı.
- Bütün GitHub Actions tam commit SHA'sına sabitlendi; CodeQL, Ruff, mypy,
  Coverage ve actionlint kapıları eklendi. Yerel taban 46 test ve %61 branch
  dahil coverage ölçümüdür; bu bir davranış kalite artışı iddiası değildir.
- Site skip link, tek main landmark, 4.5:1+ mercan kontrastı, reduced-motion ve
  mobil/yatay taşma kontrolleriyle gerçek Chromium'da geçti.
- Kök lisans kanonik MIT oldu; NOTICE ayrıldı. Güncel upstream HEAD'lerinde
  bulunan 15 fark tek tek commit + yerel ağaç SHA-256 + KEEP gerekçesiyle
  `registry/upstream-baselines.json` defterine işlendi; nöbet yeniden temizdir.
- Claude Code gerçek ajan ve read-only/ephemeral kör Codex hakem adaptörleri
  eklendi. Fixture'lar izolasyon, körlük, JSON şeması ve sır maskelemeyi kanıtlar;
  gerçek model koşusu ayrıca yayımlanabilir provenance ile tamamlandı.
- Claude Code 2.1.209 ajanı ve Codex CLI 0.144.4 kör hakemiyle üç
  `baglam-muhafizi` vakası sabit modellerle gerçek çalıştırıldı. Kamu sonucunda
  skill 0, baseline 1 kazandı, 2 beraberlik çıktı; önceden eşik tanımlanmadığı ve
  skill galibiyeti bulunmadığı için kalite artışı iddiası yapılmadı.
  `evals/results/claude-codex-baglam-muhafizi-v012.json` kanıtıyla v1 karnesi
  7/8'e çıktı.
- PR #17 bütün kontrollerden geçti ve `e9a2642e` ile `main`e birleşti. Ana-dal
  teftişi, CodeQL, üç işletim sistemi uyumluluk matrisi, Pages, Wiki ve canlı
  Chromium testi yeşildir. v0.12.0 etiketi aynı commit'e bağlı; GitHub Release
  arşivi ile checksum'u yayımlandı ve SHA-256 yeniden eşleşti.
- Sabit `v0.12.0` kaynağı dry-run sonrasında Claude Code/Desktop Code ve Codex'e
  global native marketplace olarak kuruldu. İki hostta 5 paket/41 skill enabled;
  önceki 2 Claude ve 11 Codex eklentisi ile bütün eski marketplace'ler korundu.
  Tam kayıt `.divan/evidence/teftis-20260719-v012-release-install.md` dosyasındadır.
- v0.11.1 için kök `CLAUDE.md` devralma sözleşmesi eklendi; Claude Code sohbet
  geçmişi olmadan AGENTS, BLUEPRINT, progress ve yayın/v1 kayıtlarına gider.
- `scripts/devral.py --check` ve regresyon testleri hafıza zincirini denetler;
  Sadrazam SessionStart hook'u sözleşmeyi ve defteri gösterir.
- GitHub Actions Dependabot ve CODEOWNERS eklendi. Ruleset/branch protection,
  secret scanning, push protection ve CodeQL platform doğrulaması bekler.
- PR #14 `teftis`, `uyumluluk`, `wiki-sync` ve `site-testi` kapılarından geçti;
  `731db9d7` ile `main`e birleşti. Canlı Pages/Wiki v0.11.1, tag aynı commit ve
  GitHub Release HTTP 200 olarak yeniden okundu.
- Yayın sonrasında durum sayfasında kalan eski v0.11.0 commit SHA'sı yakalandı;
  v0.11.1 gerçek SHA'sı `731db9d7` ile düzeltildi ve kanıt kaydı eklendi.

- Canlı `main` README'sinin 37 skill/v0.7 döneminde kaldığı doğrulandı.
- PR #1'in önce v0.8.2/41 skill içerdiği, yeşil fakat taslak olduğu doğrulandı;
  yayın düzeltmelerinin SemVer karşılığı yeni işlev nedeniyle v0.9.0 oldu.
- Eksik teslimin kök nedeni “PR hazır = yayın tamam” varsayımı olarak belirlendi.
- Yayın tamamlama planı ve ADR kaydı başlatıldı.
- Türkçe README ürün değeri, öz-gelişim döngüsü ve dürüst durumla genişletildi.
- İngilizce README, CHANGELOG ve VERSION eklendi.
- BLUEPRINT geçmiş/gelecek yol haritası ve sıradaki kesin adımla düzeltildi.
- Sadrazam Yayın Kanunu hem Divan paketine hem Work skill'ine işlendi.
- CI; sürüm, iki README, CHANGELOG, BLUEPRINT, kurulum ve progress kaydını
  birlikte denetleyecek şekilde güçlendirildi; yeni regresyon testi geçti.
- PR #1 taslaktan çıkarıldı; `teftis` #29 ve `site-testi` #8 başarıyla geçti.
- PR #1 squash ile `main`e birleşti (`6893e8043518f55f014a61765fc17b7c657ae295`).
- Varsayılan dalda README/TR, README/EN, VERSION, CHANGELOG ve BLUEPRINT
  yeniden okundu; GitHub Pages üzerinde v0.9.0, 41 vezir ve Yayın Kanunu görüldü.
- v0.10.0 vibe coder planı yazıldı; beş niyetli ferman seçici ürün yüzeyine
  eklendi.
- Dört özgün skill'deki 12 vakayı keşfeden; baseline/skill koşusu, A/B körleme,
  opsiyonel hakem/eşik ve JSON kanıt üreten sağlayıcı-bağımsız eval koşucusu
  eklendi.
- Aday Meclisi güvenlik davranışıyla güncel eval toplamı 4 skill / 13 vakadır.
- PR site testi eski canlı sayfa yerine dalın `docs/` önizlemesini test edecek
  şekilde düzeltildi; haftalık canlı nöbet korundu.
- Sadrazam 0.8.0'a niyetten en küçük yola geçiş ve gerçek adaptör olmadan kalite
  iddiasını reddeden Eval Kanunu eklendi; Work skill'i aynı metinle eşitlendi.
- PR #3'te `teftis` #37 ve dalın yerel önizlemesini Chromium'da tıklayan
  `site-testi` #13 başarıyla geçti.
- PR #3 squash ile `main`e birleşti (`361a6d672b9db2519a3e21d5c71ec95db7663b1e`).
- Varsayılan dalda VERSION, iki README, eval koşucusu, site kaynağı, Sadrazam ve
  BLUEPRINT yeniden okundu; v0.10.0 kayıtları eşleşti.
- Site workflow'u her `main` push'ında Pages'in repo `VERSION`ına gelmesini
  bekleyip canlı etkileşimi Chromium'da yeniden tıklayacak şekilde güçlendirildi.
- Boş/varsayılan GitHub Wiki ayrı bir teslim yüzeyi olarak kayda alındı.
- `wiki-pages.json` ve `scripts/wiki.py`, 14 Wiki sayfası ile `_Sidebar.md`yi
  repodaki sürümlü `docs/*.md` kaynaklarından deterministik üretecek şekilde
  eklendi; eksik kaynak, yinelenen slug, kırık Wiki bağlantısı ve sürüm farkı
  teftişi kuruldu.
- `wiki-sync` PR'da kaynağı denetleyecek, `main` sonrası ayrı Wiki Git deposuna
  yazacak ve canlı `Home.md` üzerinde sürümü yeniden okuyacak şekilde eklendi.
- Context7 ve OpenAI'nin güncel resmi rehberleriyle portable Agent Skills ile
  OpenAI Agents SDK runtime'ı arasındaki sınır Wiki'de açıklandı.
- Mühürdar'ın Wiki rolü belgelendi; mevcut ChatGPT Work Mühürdar etkinleştirildi.
- Sadrazam 0.8.1'e Bilgi Yüzeyleri Kanunu eklendi; proje ve Work kopyaları
  aynı metinle eşitlendi.
- `punkpeye/awesome-mcp-servers` bugünkü repo, CONTRIBUTING, MIT lisansı,
  `check-glama.yml`, son commitler ve açık katkı kuyruğuyla incelendi; 3.012
  GitHub girişli bir registry/index olarak `REFERENCE` kararı aldı.
- `registry/candidates.json` Aday Meclisi tek doğru kaynağı; kimlik, mükerrerlik,
  yaşam döngüsü, lisans kanıtı, karar/durum ve inceleme tarihi kapılarıyla kuruldu.
- `scripts/meclis.py`, insan-okunur `docs/Aday-Meclisi.md` dosyasının defterden
  ayrılmasını engelliyor; mükerrer URL ve lisanssız ADOPT regresyon testleri eklendi.
- GitHub kaynak-adayı issue formu ve haftalık salt-okunur keşif workflow'u
  eklendi. Keşif aday kodunu indirmiyor/çalıştırmıyor; yalnız bounded issue açıyor.
- Kaynak Küratörü Meclis yaşam döngüsüyle proje ve Work'te eşitlendi.
- PR #6'da `meclis` #1, `teftis` #46, `site-testi` #22 ve `wiki-sync` #3
  başarıyla geçti; squash commit `70cde8960438840153a47880571e269d37c9abbf`
  ile `main`e birleşti.
- `main` sonrası `meclis` #2, `teftis` #47, `site-testi` #23 ve Pages #17
  başarıyla geçti. `wiki-sync` #4 ilk Wiki sayfası kaydedilmediği için beklenen
  `Repository not found` engelini yeniden doğruladı; canlı Wiki iddiası yok.
- GitHub/Context7/OpenAI/Mühürdar ortak teftişinde canlı Wiki'nin HTTP 404 olduğu,
  kaynak check'inin geçtiği ve publish clone adımının `divan.wiki.git` yokluğunda
  kırıldığı doğrulandı; ilk sayfa şartı GitHub Docs'tan yeniden okundu.
- “Otomatik üretilir” yazdığı halde üreticisi olmayan Vezir Kataloğu için
  `scripts/katalog.py` ve regresyon testleri eklendi. Çok satırlı frontmatter
  yüzünden `claude-api` açıklamasını `/-…` gösteren kullanıcı hatası düzeltildi.
- GitHub Actions checkout/setup-python/setup-node/github-script kullanımları
  resmî depolardaki güncel major sürümlere taşındı; Wiki eksikliği artık tek
  `Save Page` iyileştirme yolunu doğrudan Actions hata mesajında veriyor.
- PR #8'de `wiki-sync` #5, `meclis` #3, `teftis` #52 ve `site-testi` #25 geçti;
  squash commit `6706952ccb9e4c8874593299cda4d1fdd7c2efd7` ile `main`e birleşti.
- Ana dalda `teftis` #53, `site-testi` #26, `meclis` #4 ve Pages #19 geçti.
  `wiki-sync` #6, ilk Home sayfası eksikliğini doğrudan `Save Page` talimatıyla
  durdurdu. Katalog main'den yeniden okunarak 41 kayıt ve doğru `claude-api`
  açıklaması doğrulandı.
- Repo sahibi ilk Wiki Home sayfasını kaydetti. Raw `Home.md` HTTP 200 verdi ve
  varsayılan karşılama metni okundu; `divan.wiki.git` başlangıç engeli kalktı.
  16 sayfalık kaynak paketini yayımlamak için README/Wiki durum değişikliğiyle
  `wiki-sync` yeniden tetikleniyor.
- PR #10'da `wiki-sync` #7, `teftis` #58 ve `site-testi` #28 geçti; squash
  commit `b19e6ccaee534d77a8ca3f0e52e28d38381e0a0d` ile `main`e birleşti.
- Ana dal `wiki-sync` #8, Wiki commit `ebbbf66` ile 16 dosyada 652 satır
  yayımladı ve canlı `Home.md` üzerinde v0.10.3 + “Fermanını seç” readback'ini
  geçti. `teftis` #59, `site-testi` #29 ve Pages #21 de başarılıdır.
- `release-manifest.json` ve `scripts/yayin.py`; tek komutla deterministik sürüm
  yüzeylerini hazırlar, CHANGELOG anlatısını insan sorumluluğunda bırakır ve
  sapmayı CI hatasına çevirir.
- `release` workflow'u yerel/resmî teftişlerden sonra Pages ile Wiki'nin aynı
  sürüme gelmesini bekler; CHANGELOG'dan not üretip tag/Release oluşturur. Mevcut
  etiketi taşımadan yalnız release sayfasını eşitleyerek tekrarlı çalışır.
- Claude Code resmî doğrulaması ve Codex Linux/macOS/Windows kurulum, 41 skill keşfi,
  kayıtlı kaldırma/geri yükleme tatbikatı `uyumluluk` matrisine bağlandı.
- Sekiz kapılı `registry/v1-gates.json`, deterministik Wiki karnesi, bağımsız
  kabul issue formu ve Sadrazam `/yayin` emri eklendi.
- PR #12'nin `teftis` #64, `site-testi` #31, `wiki-sync` #9, `meclis` #5 ve
  yeni `uyumluluk` #1 kapıları geçti; squash commit `5680337a` ile `main`e birleşti.
- Ana dalda `teftis` #65, `uyumluluk` #2, `wiki-sync` #10, `site-testi` #32,
  `meclis` #6, Pages #23 ve `release` #1 başarıyla tamamlandı.
- `release` akışı Linux/macOS/Windows kur-kaldır, bütün yerel/resmî teftiş,
  canlı Pages/Wiki readback ve Chromium tıklamasından sonra v0.11.0 etiketini
  değişmez biçimde `5680337a` commit'ine bağladı ve GitHub Release'i yayımladı.
- Canlı Pages ile Wiki `v0.11.0` + “Fermanını seç” döndürdü; Wiki v1 karnesi
  kayıt sonrası 6/8 geçen kapıyı gösterecek şekilde yeniden üretildi.

## Devam ediyor

- PR #62 merged the multi-engine foundation into `main` at
  `0b0efca5369c690b5830de76e4b0df0874ab1958`. The change stayed inside one
  repository and added a read-only engine registry validator, schema, example
  registry, CLI route, tests, and bilingual Divan Engine documentation. GitHub
  Actions for the merge commit passed `quality-gate`, `compatibility`,
  `codeql`, `site-tests`, `wiki-sync`, `scorecard`, `candidate-review`,
  `release`, and Pages deployment. Local canonical verification on Windows
  passed 705 tests with 14 platform-specific skips.
- v1.0.1 remains the latest immutable public release at
  `62f30f39d78be6b15e39f6e2aa9b7c19e7fb0949`. The multi-engine foundation is
  source-ready on `main`, but it is not a newly tagged public release. Prepare a
  future v1.1.0 or bounded patch release only through `scripts/release.py` after
  CHANGELOG, BLUEPRINT, README, Wiki, site, and release-manifest surfaces are
  synchronized.
- PR #72 merged the pinned-action refresh into `main` at
  `954202492723bb1b4174a51d2b1fd41ef76f6a35`. It superseded Dependabot PRs
  #41-#45 as one coherent policy update, kept every GitHub Action pinned to a
  full commit SHA, synchronized `UPSTREAM.md`, tests, workflows, and the release
  manifest, and passed main `quality-gate`, `release`, `compatibility`,
  `codeql`, `site-tests`, `scorecard`, `wiki-sync`, and Pages.
- PR #73 merged the Hükümdar-first public copy repair into `main` at
  `fc4f734bb662500a1f24319b8b8ff4582499b28c`. It superseded stale PR #51,
  preserved Divan/Ferman/Hükümdar identity, clarified that Divan is one repo
  with modular packs rather than a separate runtime, external model, or forked
  project, and verified README, Pages, and Wiki live readbacks. Main CI passed
  `quality-gate`, `codeql`, `site-tests`, `scorecard`, `wiki-sync`, and Pages.
- The observed CI/user-wait benchmarks for this development line are now known:
  local Windows `python scripts/verify.py` took about 307 seconds, main
  `quality-gate` took 7m43s after PR #72 and 8m02s after PR #73, release took
  3m56s after PR #72, and PR validation took roughly 8-9 minutes on the
  public-copy branch. Future Seyir/timeout work should surface these waits to a
  vibe coder as friendly progress states instead of silent waiting.
- Draft PR #29 durable project memory and draft PR #28 Forge Golden Path Council
  were audited and closed instead of merged. PR #29 would have introduced a
  parallel `memory` lifecycle beside the current Project Contract, goal,
  receipt, and Seyir state. PR #28 would have introduced a parallel Forge
  registry beside the canonical Aday Meclisi. Their useful ideas remain
  historical design input only; future work must extend the existing canonical
  modules rather than adding a second brain. No pull requests remain open.
- Automated Meclis discovery issues #47 and #23 were triaged on branch
  `codex/triage-meclis-discovery`. Seven candidates were promoted into the
  canonical candidate registry with pinned observed commits, license evidence,
  execution review, risk notes, source issue links, and bounded
  ADAPT/REFERENCE rationales: Cherry Studio, PortOS, Notebrain CLI, Engramory,
  Majordomo, Macher Agent, and Vivarium. This is metadata-only curation:
  nothing was installed, forked, vendored, or treated as a Divan runtime
  dependency. The other discovered repositories remain rejected from the
  registry because they are too narrow, unrelated, empty/noisy, license-unclear,
  duplicate-purpose, or outside Divan's one-repo modular product boundary.
- PR #76 merged the Meclis backlog triage into `main` at
  `20332a0386374d18eeef51a2b590366eb2d38fee`. Main `quality-gate`,
  `candidate-review`, `codeql`, `site-tests`, `scorecard`, `wiki-sync`, and
  Pages all completed successfully; `quality-gate` took 7m32s. Discovery issues
  #47 and #23 were closed with promoted/rejected candidate summaries. No pull
  requests or issues remain open.
- Branch `codex/seyir-wait-state-ux` turns the recorded CI wait problem into a
  small post-v1 product slice. The timeout benchmark now includes the latest 20
  trusted `main` `quality-gate.yml` runs from GitHub Actions, so `verify`
  resolves from 25 samples to p95 480s and a bounded 720s configured wait.
  Seyir snapshots expose this as `wait_state`, and the local UI explains the
  normal wait window plus attention threshold in English and Turkish. No external
  runtime, forked code, or second repository was added.
- PR #78 merged the Seyir wait-state UX slice into `main` at
  `7092544f5fbac2a0ac6bbb12cfa4412f28308294`. Local canonical verification
  passed 706 tests with 14 expected platform skips; main `quality-gate`,
  `release`, `compatibility`, `codeql`, `site-tests`, `scorecard`, `wiki-sync`,
  `candidate-review`, and Pages all passed. Raw GitHub source, README, live
  Pages, and live Wiki readbacks expose the new wait guidance. Latest immutable
  release remains v1.0.1 at `62f30f39d78be6b15e39f6e2aa9b7c19e7fb0949`.
- PR #80 merged the v1.0.2 release preparation into `main` at
  `f227e2d30ab1a6f010a3d5acf18740f6eab09e70`. Local canonical verification
  passed 707 tests with 14 expected platform skips and `git diff --check`
  passed. PR validation, main `quality-gate`, release, compatibility, CodeQL,
  site-tests, Scorecard, Wiki sync, candidate review, Pages deployment, release
  asset checksum verification, and seven GitHub attestations all passed.
  v1.0.2 is now the latest immutable public release.
- PR #82 merged the v1.0.3 friendly control plane into `main` at
  `ce0c87103a1e96f62ccabdf63dc6df9ee9b195fb`. Canonical local verification
  passed 715 tests with 14 expected skips; PR and main publication workflows,
  seven downloaded asset hashes, both checksum sidecars, strict attestations,
  and a real Windows/Codex CLI upgrade readback passed. v1.0.3 is now the
  latest immutable public release.

## Tarihsel devam kayıtları

The following entries are retained as dated pre-release snapshots. They are not
the current execution queue.

- 2026-07-19: v0.12.1 yüzeyleri hazır. Tam yerel teftiş, bağımsız code review,
  PR/main/Release/Pages/Wiki ve çift-host global kurulum kanıtı sıradadır.
- 2026-07-19: ADR 0003 ve test-first v0.12.1 uygulama planı yazıldı. Sıradaki
  parça hijyen testlerini kırmızıya getirip allowlist temizleyiciyi uygulamaktır.
- Proje sahibi dışındaki bağımsız kullanıcıdan tekrar üretilebilir kurulum ve
  görev kanıtı.
- 2026-07-19: v0.12 kanıt zinciri için tasarım onaylandı. İlk parça Windows
  kurulum–yedek–kaldırma test eşliği ve gerçek eval koşularının provenance
  sözleşmesidir; dış v1 kapıları bu mekanik çalışmayla kapanmayacaktır.
- 2026-07-19: Windows PowerShell kur–yedekle–kaldır–geri yükle tatbikatı gerçek
  geçici dizinlerde 41 skill ile geçti. Eval sonuçları için redakte edilmiş
  provenance sözleşmesi eklendi; 33 test geçti, tam teftiş kanıtı
  `evidence/teftis-20260719-v012-evidence-chain.md` altındadır.

## Bilinen açıklar

- Eski Codex loose skill kopyaları veri kaybını önlemek için korundu. Eski
  manifest sahiplik hash'i taşımadığından güvenli otomatik migration uygulanmadı;
  native Divan paketleri ayrıca kurulu ve doğrulanmıştır.
