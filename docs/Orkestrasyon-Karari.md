# Orkestrasyon Kararı — v0.8

**Karar:** Divan, üçüncü taraf bir agent harness'e bağlanmaz. Varsayılan yol
Claude Code ve Codex'in yerel skill, subagent ve worktree yetenekleridir.
Deneysel Agent Teams yalnızca açık kullanıcı tercihiyle, bağımsız işlerde ve
maliyet sınırıyla kullanılır.

Karar akışı: [Divan v0.8 Yerel Orkestrasyon — FigJam](https://www.figma.com/board/Jfpg0ASsVHOuCQeFFRladZ).

## Neden

Temmuz 2026 anlık görüntüsünde adaylar altı ölçütle puanlandı: yerel/abonelik
uyumu %25, güvenlik ve köken %20, vibe-coder sadeliği %20, bakım canlılığı %15,
kabiliyet %10, taşınabilirlik %10. Her ölçüt 1–5 arası değerlendirilip 100'e
ölçeklendi. Puanlar nesnel gerçek değil, Divan'ın hedef kitlesine göre şeffaf
ürün kararıdır.

| Sıra | Yol | Puan | Divan'daki rolü |
|---:|---|---:|---|
| 1 | Claude Code yerel | 94 | Varsayılan temel |
| 2 | wshobson/agents | 90 | Seçici upstream ve uyumluluk referansı |
| 3 | gstack | 82 | Süreç ilhamı; zorunlu bağımlılık değil |
| 4 | ccpm | 73 | Spec/GitHub Issues deseni gerektiğinde |
| 5 | Claude Squad | 62 | Teknik çok-terminal kullanıcılarına |
| 6 | Gastown | 57 | Endüstriyel ölçekte, Divan kapsamı dışında |
| 7 | Ruflo | 55 | Güçlü ama varsayılan için fazla geniş yüzey |

Tam veri: [`data/orkestrasyon-adaylari.csv`](data/orkestrasyon-adaylari.csv).

## Güncel bulgular

- Claude Code'un güncel yerel yolu yalnızca klasik subagent'lardan ibaret
  değildir: paralel agent görünümü, dinamik iş akışları, worktree izolasyonu ve
  deneysel Agent Teams aynı ürün içinde farklı kademeler sunar.
- Agent Teams ayrı bağlamlar ve takım içi mesajlaşma sağlar fakat deneysel,
  daha pahalı ve oturum sürdürme sınırlarına sahiptir. Otomatik açılmaz.
- wshobson/agents deposu Temmuz 2026 README'sinde 94 eklenti, 203 ajan, 175
  skill ve 109 komut bildiriyor. Divan buradan toplu kopya yapmaz; lisansı ve
  dosya kökeni tek tek doğrulanan boşlukları seçici olarak değerlendirir.
- Ruflo'nun kendi ADR-166 kaydı, Docker ile gelen MCP köprüsünde doğrulamasız
  uzaktan komut çalıştırma yüzeyini ve sonradan eklenen loopback/auth
  sertleştirmesini belgeliyor. Bu, harici çalışma zamanı yüzeyinin bakım
  maliyetine somut bir örnektir; “kötü proje” hükmü değildir.
- 15 Haziran 2026 için duyurulan Claude Agent SDK kredi ayrımı duraklatıldı.
  Bugünkü politika gelecekte değişebileceği için Divan mimarisini fiyat veya
  geçici kimlik doğrulama boşluğuna bağlamaz.

## Divan'ın üç kademesi

1. **Ocak:** Tek oturum + ilgili skill'ler. Varsayılan.
2. **Sefer:** Bağımsız keşif, test ve inceleme için sınırları belirli
   subagent'lar. Yazma çakışması yok.
3. **Ordu:** Bağımsız uygulama hatları için worktree izolasyonu; kullanıcı
   açıkça isterse deneysel Agent Teams.

`/sefer` komutu ve `ordu-nizami` skill'i bu kararı uygulanabilir hale getirir.
Harici harness kurulumu her zaman ayrı bir kullanıcı kararı, güncel güvenlik
incelemesi ve lisans/kimlik doğrulama kontrolü gerektirir.

## Kaynaklar ve anlık görüntü

GitHub sayıları 17 Temmuz 2026'da GitHub REST API'den alındı; yıldız sayıları
kararın kendisi değil, bakım/popülerlik bağlamıdır. Ürün davranışı için birincil
kaynaklar Claude Code'un resmî agents/agent-teams belgeleri, Anthropic destek
duyurusu ve adayların kendi README, LICENSE ve güvenlik ADR'leridir.

Bu karar üç ayda bir veya şu eşiklerden biri gerçekleşince yeniden açılır:
Agent Teams genel kullanıma çıkarsa, abonelik/SDK politikası değişirse ya da
Divan'ın gerçek işleri düzenli olarak üçten fazla bağımsız yazma hattı isterse.
