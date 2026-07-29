---
description: İşi en küçük güvenli ajan düzeniyle sevk et (tek oturum, subagent veya izole takım)
argument-hint: yapılacak-iş
---
Hükümdarın sefer fermanı: $ARGUMENTS

`ordu-nizami` ve `sadrazam` skill'lerini yükle. Önce işi bağımlılıklarına ayır,
sonra Ocak / Sefer / Ordu kademelerinden en küçüğünü gerekçesiyle seç.
Divan Engine `plan` çıktısındaki `execution_plan` varsa sefer sayısı, görev
bağımlılıkları, model sınıfı, devir eşiği ve paralel iş hattı sınırını uygula.

- Paralellik gerekmiyorsa tek oturumda bitir.
- Bağımsız araştırma, test veya inceleme varsa sınırları belirli subagent kullan.
- Eşzamanlı yazım gerekiyorsa dosya sahipliği ve worktree izolasyonu kur.
- Agent Teams veya harici harness için kullanıcıdan açık yetki almadan ayar,
  ortam değişkeni ya da bağımlılık ekleme.
- Host veya model erişimi belirsizse varmış gibi davranma; eşdeğer kullanılabilir
  model host tarafından doğrulanana kadar planı kapasite sınıfı olarak tut.

`${CLAUDE_PLUGIN_ROOT}` veya host metadata içindeki eşdeğer loaded-plugin root'u
çöz; kullanıcının current working directory yolundan çözme. O kökteki
`skills/sadrazam/references/vibe-progress.md` kanonik Vibe progress protocol
sözleşmesini araçlardan önce ve her meaningful phase değişiminde uygula.

Sonunda görev-sahip eşlemesini, birleşik test kanıtını ve açık riskleri takdim et.
