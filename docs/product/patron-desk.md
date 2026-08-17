# Patron Masası

Patron Masası, Divan Desktop'ın teknik ayrıntıları bilmek istemeyen kullanıcı için birincil giriş yüzeyidir.

## Ürün sözü

Kullanıcı tek bir yerde:

1. çalışılacak Git projesini seçer veya kaydeder;
2. yapılmasını istediği sonucu normal dille yazar;
3. ferman için salt-okunur Nizâm-ı Sefer planını önizler;
4. iş paketi, iş akışı, sefer, rol, paralellik ve kanıt özetini görür;
5. planı açık onayla kaydeder ve dependency-aware yerel Divan iş paketlerini hazırlar;
6. Codex, Claude Code ve Cursor Agent hazırlığını görür;
7. kaynak kodu değiştirecek execution için mevcut Divan onay kapısına geçer.

Patron Masası ayrı bir orchestration authority değildir. `Divan Core` plan, görev, mandate, execution, review, evidence, approval, merge ve release gerçeğinin tek otoritesi olarak kalır.

## Güvenlik sınırı

Patron Masası planlama aşamasında şu komutları kullanır:

- `project.list`
- `project.register`
- `readiness`
- `goal.preview`
- `goal.create`

TAHT özeti ve SİSTEM/ARŞİV ekranları ek olarak salt okunur
`project.agency.status` ve `doctor` komutlarını okur.

`goal.preview` salt okunurdur; proje içinde plan artifact'ı veya yerel task state yazmaz ve `execution_authority` vermez.

`goal.create` yalnız `approve_plan_write=true` ile çalışır. Onay verildiğinde mevcut goal sözleşmesi üzerinden `spec.md`, `plan.md`, `tasks.md`, `route.json` ve receipt/evidence kayıtları yazılır; receipt-doğrulanmış route aynı anda yerel `planned` Divan iş paketlerine materialize edilir. Bu iş paketlerinin `mandate_id` değeri yoktur ve kaynak kod execution'ı başlamaz.

Bu yüzey doğrudan `task.start`, `task.approve`, merge veya release çağırmaz. Mutating execution mevcut Desktop akışındaki açık `approve_execution=true` onayını gerektirir. Merge de bağımsız review ve açık owner onayı olmadan gerçekleşmez.

## İlk açılış sihirbazı

Divan Desktop ilk açılışta "DİVAN'A HOŞ GELDİNİZ" başlıklı dokuz adımlı bir
sihirbaz gösterir. Her adım Core `doctor` yanıtındaki bir yeteneğe karşılık
gelir: Divan Core, Git, Codex, Claude Code, tarayıcı testi, hafıza (depo ve
geri çağırma), kalite ve kanıt, yerel güvenlik; dokuzuncu adım çalışma
klasörünü seçtirir.

- Satırlar yalnız Core'un `state` ve `code` alanlarından çevrilir:
  `CERTIFIED` → "✓ … hazır.", `DEGRADED` → "⚠ … kurulu ancak …",
  `OFFLINE` → "✗ … bulunamadı.", `INCOMPATIBLE` → "⚠ … uyumsuz sürüm.",
  `BLOCKED` yerel güvenlikte → "⚠ … Windows politikası nedeniyle engelli."
- Patron görünümünde hata kodu, yol veya JSON görünmez; "Teknik ayrıntı"
  düğmesi kodu isteyene gösterir.
- Eksik bir adımda Core `action_hint` göndermişse o cümle aynen gösterilir;
  göndermemişse "Divan bunu kendisi hazırlamayı deneyecek." denir. Sihirbaz
  hiçbir kurulum yapmaz.
- Klasör seçilince kabuk `project.register` çağırır ve "ilk açılış tamam"
  bilgisini kendisi saklar; sihirbaz bu bilgiyi kendi başına yazmaz.

## Yedi durak ve ayrıntı düzeyi

Kenar çubuğu yedi durak sunar: 👑 TAHT (Patron Masası ve proje özeti),
🏛 DİVAN (iş paketleri), ⚔ EKİP (ajanlar ve motorlar), 🕵 TEFTİŞ (kanıtlar),
🧠 ARŞİV (yalnız hafıza yeteneklerinin Doctor satırları), 🧰 CEPHANELİK
(eklentiler ve yönetilen araçlar), 🩺 SİSTEM (Doctor ve sürümler).

Üst çubuktaki "Ayrıntı düzeyi" seçici (Patron / Divan / Teknik) kabuk
genelinde geçerlidir. Patron düzeyi dosya yolu, ham durum kodu, API sürümü ve
SHA-256 gibi teknik ayrıntıları gizler; Divan ve Teknik düzeyleri gösterir.

TAHT özeti yalnız `project.agency.status` yanıtında bulunan alanları
listeler: proje adı, aşama, ilerleme, şu anki etkinlik, çalışan ve durmuş iş
paketi sayısı, sizi bekleyen sayısı, sıradaki adım. Çalışan ajan sayısı,
kritik sorun sayısı, "Divan çözüyor" sayısı ve son olay cümlesi Core
yanıtında henüz yoktur; bu alanlar ancak Core gönderdiğinde görünür,
arayüzde hesaplanmaz.

## Kullanıcı deneyimi

- `Ctrl+K` / `Cmd+K`: Patron Masası'nı açar; aynı masa TAHT ekranında da
  gömülü durur, ikinci bir masa yoktur.
- `Esc`: kapatır.
- Üç hazır ferman başlangıcı sunulur: **Anahtar teslim**, **Hata çöz**, **Özellik ekle**.
- Kullanıcı önce **Planı önizle** ile hiçbir şey yazmadan gerçek Nizâm-ı Sefer kırılımını görür.
- Önizleme; iş paketi, iş akışı, sefer, en fazla paralel çalışma, roller ve kanıt yükümlülüklerini teknik olmayan bir özetle gösterir.
- **Planı kaydet** yalnız plan artifact'larını ve yerel iş paketi durumunu hazırlar; kod çalıştırmaz.
- Araç durumu renk dışında metinle de ifade edilir.
- Proje yolu görünürdür; Divan'ın tüm diski taradığı izlenimi verilmez.
- API anahtarı veya provider credential'ı UI tarafından istenmez ya da kopyalanmaz.
- Plan kaydedildikten sonra kullanıcıya kaç iş paketinin hazır olduğu ve kaynak kodun henüz değiştirilmediği açıkça söylenir.

## Sıradaki ürün dilimleri

Planlama ve dependency-aware work-package kırılımı artık Patron akışına bağlanmıştır. Sonraki genişlemeler hazırmış gibi gösterilmemelidir:

- capability ve provider-health tabanlı Codex / Claude / Cursor worker atama;
- goal seviyesinde açık **Seferi başlat** execution onayı;
- ready work package'larını Nizâm paralellik sınırına göre 1–3 izole worktree'de çalıştırma;
- worker lease, heartbeat, checkpoint ve provider handoff;
- proje profiline göre kalite kapıları;
- tek ekranda workstream ilerlemesi ve teslim fişi.

Bağımsız writer/reviewer ayrılığı mevcut Core review yolunda korunur. Bu genişleme yapılırken renderer yeni bir yetki kaynağına dönüşmez ve Divan'ın fail-closed güvenlik sözleşmeleri zayıflatılmaz.
