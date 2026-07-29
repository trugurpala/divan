---
description: Divan reposunu standartlara göre denetle ve raporla
---
`${CLAUDE_PLUGIN_ROOT}` veya host metadata içindeki eşdeğer loaded-plugin root'u
çöz; kullanıcının current working directory yolundan çözme. O kökteki
`skills/sadrazam/references/vibe-progress.md` kanonik Vibe progress protocol
sözleşmesini araçlardan önce ve her meaningful phase değişiminde uygula.

Repo kökünde `python scripts/validate.py` çalıştır. Ham çıktıyı sohbet ekranına
dökme; tam çıktıyı teknik kanıt olarak koru. Hata varsa eyleme dönüşen her
bulguyu tek tek düzelt ve teftişi temiz çıkana kadar tekrar koş. Uyarıları
değerlendir: gerekliyse düzelt, değilse gerekçesini yaz. Sonunda kısa rapor ver:
kaç paket, kaç skill, ne düzeltildi.

Ek olarak hafıza sağlığını denetle: AGENTS.md ve BLUEPRINT.md var ve güncel mi,
.divan/progress.md son oturumu yansıtıyor mu, konuşulmuş kararlar ADR'lenmiş
mi, Teftiş kanıtları .divan/evidence/ altında mı? Eksikleri raporla ve düzelt.
