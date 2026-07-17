---
name: ordu-nizami
description: Native-first agent orchestration for Claude Code and Codex. Use when a task may benefit from subagents, parallel research, isolated worktrees, dynamic agent workflows, or experimental Agent Teams, and when the user asks for orchestration, multiple agents, a team, swarm-like execution, or faster parallel delivery. Chooses the smallest safe coordination lane, assigns clear ownership, limits cost, and requires independent verification without installing an external harness.
license: MIT
compatibility: Claude Code and Codex; Agent Teams remains an explicit experimental opt-in
---

# Ordu Nizamı

Amaç çok ajan kullanmak değil, işi en az koordinasyon maliyetiyle doğru
bitirmektir. Önce tek oturum; yalnızca iş gerçekten bölünebiliyorsa ordu.

## Üç kademe

| Kademe | Ne zaman | Düzen |
|---|---|---|
| **Ocak** | Tek hedef, ortak dosyalar, sıralı bağımlılık | Ana ajan işi baştan sona yürütür |
| **Sefer** | En az iki bağımsız araştırma, inceleme veya test hattı | Sınırları belirli subagent'lar; ana ajan sonuçları birleştirir |
| **Ordu** | Bağımsız uygulama parçaları gerçekten eşzamanlı ilerleyebilir | Ayrı worktree ve dosya sahipliği; gerekirse açıkça etkinleştirilmiş Agent Teams |

Kararsızsan daha düşük kademeyi seç. Ajan sayısı bir başarı ölçütü değildir.

## Sevkten önce

1. Fermanı tek cümleye indir ve teslim ölçütlerini yaz.
2. İşleri bir bağımlılık grafiği gibi ayır: bağımsız olmayanları paralelleştirme.
3. Her görev için tek sahip, açık girdi, açık çıktı ve doğrulama komutu belirle.
4. Varsayılan üst sınır üç yardımcı ajandır. Daha fazlası için kullanıcıya
   maliyet ve koordinasyon gerekçesini söyle.
5. İki ajan aynı dosyayı yazacaksa planı değiştir veya ayrı worktree kullan.

## Kademe seçimi

### Ocak — varsayılan

- Küçük ve orta işleri tek bağlamda bitir.
- `sadrazam` ile planla, uygula ve `mufettis` ile kanıtı denetle.
- Sırf araç mevcut diye subagent başlatma.

### Sefer — sınırları belirli subagent

- Keşif, doküman tarama, test, log analizi ve bağımsız kod incelemesi için uygundur.
- Her subagent'a tek somut görev ver; ham çıktı yerine bulgu özeti iste.
- Yazma işi veriyorsan dosya sahipliğini çakışmayacak biçimde böl.
- Ana ajan tüm sonuçları bekler, uyuşmazlıkları çözer ve tek karar üretir.

### Ordu — izole paralel uygulama

- Her çalışma hattına ayrı branch/worktree ve ayrı dosya sınırı ver.
- Entegrasyon sırasını uygulamadan önce belirle; birleştirmeyi tek sahip yapsın.
- Claude Code Agent Teams deneysel bir yoldur. Kullanıcı açıkça istemeden ortam
  bayrağını veya ayar dosyasını değiştirme; ekip kurmadan önce planı ve tahmini
  token maliyetini göster.
- Agent Teams kullanılırsa ekip arkadaşları arasında görev sınırı ve posta
  kutusu disiplini kur; oturum sürdürmenin ekip üyelerini geri getirmeyebileceğini
  hesaba kat.

## Emniyet sınırları

- Ruflo, Gastown, Claude Squad veya başka bir harici harness'i kendiliğinden
  kurma. Açık kullanıcı talebi, lisans kontrolü, güncel güvenlik incelemesi ve
  kimlik doğrulama/maliyet kararı olmadan bağımlılık ekleme.
- Ajanlara sır, üretim anahtarı veya ihtiyaç dışı yazma yetkisi verme.
- Bağımsız denetçi uygulama kodunu düzeltmez; kusuru ana ajana raporlar.
- Durma koşulu koy: aynı hata iki kez tekrarlanırsa paralelliği durdur, kök
  nedeni ana bağlamda çöz.

## Teftiş ve takdim

Teslimde şu kanıtları birlikte ver:

- görev → sahip → değişen dosya eşlemesi,
- her çalışma hattının doğrulama sonucu,
- birleşik test/lint/build sonucu,
- açık kalan risk veya uygulanmayan deneysel yol.

Paralellik hız kazandırmadıysa bunu kaydet ve sonraki sefer daha düşük kademeyi
öner. Ordu Nizamı kendi karmaşıklığını da teftiş eder.
