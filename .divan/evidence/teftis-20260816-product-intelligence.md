# Ürün zekâsı — teslim sonrası öneriler

- Tarih: 2026-08-16
- Kaynak: Heavy Campaign II boyunca gözlenen gerçek kanıt
- Kapsam: Divan Agency OS platformu

## Neden bu kapsam

AgencyBench-01 `TURNKEY_BLOCKED` ile durdu; teslim edilmiş bir müşteri
uygulaması yok, dolayısıyla o uygulama hakkında kullanım kanıtı da yok.
Uydurma öneri üretmek yerine, bu kampanyada fiilen gözlenen kanıta dayalı
platform önerileri çıkarıldı. Her öneri gerçek bir olaya bağlıdır.

## V1.1 — gözlenen acıyı gideren

### 1. Kurulu çalışan yoksa Divan bunu Ferman anında söylesin

- **Problem**: Benchmark, iş paketi grafiği üretildikten sonra çalışan
  atama adımında durdu. Sahip bunu ancak plan hazırlandıktan sonra öğrendi.
- **Kanıt**: `teftis-20260816-agencybench-01.md`, `stage_reached:
  worker-assignment`, `blocked_capabilities: codex, claude`.
- **Kullanıcı faydası**: Sahip, planlama emeği harcanmadan önce tek
  eksiğini görür.
- **Risk**: Düşük. Deep Doctor okuması zaten mevcut; yalnız Ferman
  girişine bağlanır.
- **Efor**: Küçük.
- **Öncelik**: Yüksek.

### 2. Kanonik doğrulama koşarken çalışma ağacını kilitle

- **Problem**: Doğrulama koşarken aynı worktree düzenlendiğinde
  deterministik runner testi fixture'ı tutarsız kopyaladı ve beş sahte hata
  üretti. Bu bir kez bu oturumda gerçekten oldu.
- **Kanıt**: `.divan/progress.md`, PASS 6-8 kaydındaki süreç dersi.
- **Kullanıcı faydası**: Sahte hata avına harcanan zaman ortadan kalkar.
- **Risk**: Düşük; kilit yalnız doğrulama süresince tutulur.
- **Efor**: Küçük.
- **Öncelik**: Yüksek.

### 3. Yeni runtime modülü eklemeyi tek adıma indir

- **Problem**: Bir modül eklemek `modules.json`, katman bağımlılığı ve
  `RUNTIME_FILES` listesini ayrı ayrı güncellemeyi gerektiriyor. Bu
  kampanyada üç kez unutuldu ve her seferinde sözleşme kapısı yakaladı.
- **Kanıt**: `agency_status.py` runner fixture eksikliği; doctor
  modüllerinin bildirilmemesi; `desktop_state` üzerinden kernel-project
  katman ihlali.
- **Kullanıcı faydası**: Kapılar zaten koruyor, ama tekrarlanan sürtünme
  kaldırılır.
- **Risk**: Orta. Otomatik kayıt, sözleşmenin bilinçli olma niteliğini
  zayıflatmamalı; öneri kontrol eden bir yardımcı, sessizce yazan değil.
- **Efor**: Orta.
- **Öncelik**: Orta.

## V1.2 — yeteneği genişleten

### 4. Gerçek tarayıcı kabul kanıtı

- **Problem**: `browser-e2e` ve `accessibility` kapıları kalite modelinde
  tanımlı ama bu makinede hiçbir tarayıcı yeteneği kurulu değil, dolayısıyla
  `WEB_STANDARD` profili hiçbir zaman tam `READY` üretemez.
- **Kanıt**: `quality_factory` profil tanımı; Deep Doctor'da tarayıcı QA
  yeteneği bulunmuyor.
- **Kullanıcı faydası**: Web projeleri için teslim kararı gerçek etkileşim
  kanıtına dayanır.
- **Risk**: Orta. Proje-kapsamlı ve pinli kurulmalı; global kurulum
  yapılmamalı.
- **Efor**: Orta.
- **Öncelik**: Orta.

### 5. Bağlam paketini gerçek ölçümle kalibre et

- **Problem**: Token sayısı bugün yalnız `estimated`. Benchmark 4 paket
  için 207 token tahmin etti; bu sayının gerçekle ilişkisi ölçülmedi.
- **Kanıt**: `teftis-20260816-agencybench-01.md`, `token_confidence:
  estimated`.
- **Kullanıcı faydası**: Bütçe kararları tahmine değil ölçüme dayanır.
- **Risk**: Düşük. Ölçüm yoksa `unknown` demeye devam edilir; sahte
  kesinlik üretilmez.
- **Efor**: Orta.
- **Öncelik**: Orta.

### 6. Hafızayı iş kapanışının ötesine bağla

- **Problem**: Ders yalnız teftişten kalıp sonra merge olan görevde
  yazılıyor. Reddedilen, iptal edilen veya çalışan değişimiyle biten
  denemelerden ders çıkarılmıyor.
- **Kanıt**: `task_learning.capture_merge_lesson` yalnız `approve_merge`
  yolundan çağrılıyor; attempt modelinde `REPLACED` ve `FAILED` durumları
  hafızaya bağlı değil.
- **Kullanıcı faydası**: Aynı çalışan hatası ikinci projede tekrarlanmaz.
- **Risk**: Orta. Defteri gürültüyle doldurmamak için yalnız sınıflandırılmış
  başarısızlıklar yazılmalı.
- **Efor**: Orta.
- **Öncelik**: Orta.

## Sınır

Bu öneriler platform gözlemine dayanır. Teslim edilmiş bir müşteri
uygulamasının kullanım verisi yoktur ve bu kayıt öyle bir veri varmış gibi
davranmaz.
