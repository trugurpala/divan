# Nizâm-ı Sefer planning intelligence teftişi

Tarih: 2026-07-29
Issue: #48
Branch: `codex/nizami-sefer-planning-intelligence`
Durum: implementation complete; remote CI pending

## Uygulanan sözleşme

- Temkinli ve kaynağı açık host planlama profilleri eklendi.
- Kesin kapasite için `--context-window` override eklendi.
- Company OS planı; karmaşıklık, çalışma yükü, bağlam bütçesi, oturum sayısı,
  paralellik sınırı, campaign/task ayrımı, görev sahipliği, kanıt şartı,
  hafıza ve yayın yükümlülükleriyle genişletildi.
- Teknik rota şeması İngilizce-kanonik tutuldu; Padişah, Sadrazam ve Sefer
  adları görünen ürün dili olarak korundu.
- Goal kimliği host/context planından ayrıldı; aynı proje/ferman/hedef Claude ve
  Codex'te aynı `goal_id` üretir.
- Makine rotası `.divan/routes/<goal-id>.json` altında, SHA-256 bağı
  `spec.md` içinde saklanır.
- Eski DPS-005 üçlü spec/plan/tasks makbuz sınırı değiştirilmedi.
- Portable Project OS runner yeni planlama modülü ve profilleri paketler.
- Impact graph, Sadrazam kanunu, iki dilli Company OS belgeleri ve release
  manifesti aynı değişiklikte güncellendi.

## Yerel doğrulama sınırı

Bu çalışma ortamının genel container ağı GitHub DNS çözümleyemediği için dalı
container içinde yeniden clone edip yerel test çalıştırmak mümkün olmadı.
Bu bir PASS iddiası değildir. Doğrulama GitHub pull-request iş akışlarında ve
GitHub'ın commit/check kanıtlarıyla tamamlanacaktır.

## Bekleyen kapılar

- [ ] Focused planning tests
- [ ] Company OS and Project OS regression tests
- [ ] Release manifest check
- [ ] Complete `scripts/verify.py`
- [ ] Official Agent Skills / Claude plugin validation
- [ ] CodeQL and dependency review where applicable
- [ ] Independent review

## Dürüst yayın sınırı

Dal henüz `main` üzerinde değildir. VERSION, tag, GitHub Release, Pages, Wiki
ve kurulu Claude/Codex paketleri değişmemiştir. CI yeşil olsa bile merge ve
canlı geri okuma tamamlanmadan özellik yayımlanmış sayılmaz.
