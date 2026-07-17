---
description: İşi en küçük güvenli ajan düzeniyle sevk et (tek oturum, subagent veya izole takım)
argument-hint: yapılacak-iş
---
Padişahın sefer fermanı: $ARGUMENTS

`ordu-nizami` ve `sadrazam` skill'lerini yükle. Önce işi bağımlılıklarına ayır,
sonra Ocak / Sefer / Ordu kademelerinden en küçüğünü gerekçesiyle seç.

- Paralellik gerekmiyorsa tek oturumda bitir.
- Bağımsız araştırma, test veya inceleme varsa sınırları belirli subagent kullan.
- Eşzamanlı yazım gerekiyorsa dosya sahipliği ve worktree izolasyonu kur.
- Agent Teams veya harici harness için kullanıcıdan açık yetki almadan ayar,
  ortam değişkeni ya da bağımlılık ekleme.

Sonunda görev-sahip eşlemesini, birleşik test kanıtını ve açık riskleri takdim et.
