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
- `goal.tasks`

`goal.preview` salt okunurdur; proje içinde plan artifact'ı veya yerel task state yazmaz ve `execution_authority` vermez.

`goal.preview` ile `goal.create` planı aynı redakte edilmiş ferman metninden çıkarır; önizlemede görülen kırılım, kaydedildiğinde yazılan kırılımın aynısıdır.

`goal.preview` ve `goal.create` yalnız kayıtlı bir projede ya da gerçek bir Git deposu kökünde çalışır; rastgele bir klasöre plan yazmaz.

`goal.tasks` salt okunurdur; kaydedilmiş bir fermanın iş paketlerini ve bağımlılığa göre hazır olanları geri okur. Divan yeniden başlatıldıktan sonra da çalışır.

`goal.create` yalnız `approve_plan_write=true` ile çalışır. Onay verildiğinde mevcut goal sözleşmesi üzerinden `spec.md`, `plan.md`, `tasks.md`, `route.json` ve receipt/evidence kayıtları yazılır; receipt-doğrulanmış route aynı anda yerel `planned` Divan iş paketlerine materialize edilir. Bu iş paketlerinin `mandate_id` değeri yoktur ve kaynak kod execution'ı başlamaz.

Bu yüzey doğrudan `task.start`, `task.approve`, merge veya release çağırmaz. Mutating execution mevcut Desktop akışındaki açık `approve_execution=true` onayını gerektirir. Merge de bağımsız review ve açık owner onayı olmadan gerçekleşmez.

Bağımlılık sırası tavsiye değil, kapıdır: `task.start`, bağımlı olduğu iş paketleri `merged` veya `released` olmayan bir iş paketini `approve_execution=true` verilse bile `DESKTOP_TASK_DEPENDENCIES_PENDING` ile reddeder.

## Kullanıcı deneyimi

- `Ctrl+K` / `Cmd+K`: Patron Masası'nı açar.
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
