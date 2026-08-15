# Patron Masası

Patron Masası, Divan Desktop'ın teknik ayrıntıları bilmek istemeyen kullanıcı için birincil giriş yüzeyidir.

## Ürün sözü

Kullanıcı tek bir yerde:

1. çalışılacak Git projesini seçer veya kaydeder;
2. yapılmasını istediği sonucu normal dille yazar;
3. Codex, Claude Code ve Cursor Agent hazırlığını görür;
4. fermanı Divan Core'a görev olarak kaydeder;
5. görevin planlanmasını başlatır;
6. kaynak kodu değiştirecek execution için mevcut Divan onay kapısına geçer.

Patron Masası ayrı bir orchestration authority değildir. `Divan Core` görev, mandate, execution, review, evidence, approval, merge ve release gerçeğinin tek otoritesi olarak kalır.

## İlk dilimin güvenlik sınırı

Patron Masası şu komutları kullanabilir:

- `project.list`
- `project.register`
- `readiness`
- `task.create`
- `task.plan`

Bu yüzey doğrudan `task.start`, `task.approve`, merge veya release çağırmaz. Mutating execution mevcut Desktop akışındaki açık `approve_execution=true` onayını gerektirir. Merge de bağımsız review ve açık owner onayı olmadan gerçekleşmez.

## Kullanıcı deneyimi

- `Ctrl+K` / `Cmd+K`: Patron Masası'nı açar.
- `Esc`: kapatır.
- Üç hazır ferman başlangıcı sunulur: **Anahtar teslim**, **Hata çöz**, **Özellik ekle**.
- Araç durumu renk dışında metinle de ifade edilir.
- Proje yolu görünürdür; Divan'ın tüm diski taradığı izlenimi verilmez.
- API anahtarı veya provider credential'ı UI tarafından istenmez ya da kopyalanmaz.
- Görev planlandıktan sonra kullanıcıya kaynak kodun henüz değiştirilmediği açıkça söylenir.

## Sonraki ürün dilimleri

Patron Masası ileride şu Core yeteneklerine bağlanabilir; bunlar hazırmış gibi gösterilmemelidir:

- fermanı PRD / kabul kriterleri / bağımlı iş paketlerine ayırma;
- capability tabanlı Codex / Claude / Cursor worker atama;
- writer ve reviewer ayrılığı;
- worker heartbeat, lease, checkpoint ve handoff;
- proje profiline göre kalite kapıları;
- teslim fişi ve tek ekranda kanıt özeti.

Bu genişleme yapılırken renderer yeni bir yetki kaynağına dönüşmez ve Divan'ın fail-closed güvenlik sözleşmeleri zayıflatılmaz.
