# Divan belge haritası

Bu yapı Divan'ın depo sözleşmesidir; Codex'in zorunlu dosya listesi değildir.
Codex proje talimatlarını kökteki `AGENTS.md` üzerinden keşfeder. Diğer belgeler
oradaki bağlantılarla, yalnız ilgili iş için okunur.

| Dosya | Ne zaman okunur / güncellenir? |
| --- | --- |
| [../AGENTS.md](../AGENTS.md) | Her geliştirme başında kalıcı kurallar ve doğrulama komutları |
| [getting-started.md](getting-started.md) | Kurulum, ilk iş, güncelleme ve günlük kullanım sorunları |
| [compatibility.md](compatibility.md) | Farklı editör ve ajanlarda kurulum, destek sınırı ve kanıt düzeyi |
| [ideas/daily-use.md](ideas/daily-use.md) | Doğal dil ve ilerleme bildirimlerinin ürün kararları |
| [project.md](project.md) | Ürün amacı, kapsam ve tamamlanma ölçütü gerektiğinde |
| [decisions.md](decisions.md) | Mimari veya araç seçimini değiştirirken |
| [development.md](development.md) | Yerel kurulum, test, paketleme ve katkı akışında |
| [capability-map.md](capability-map.md) | Hangi beceri, araç ve uygulama katmanı seçilecek sorusunda |
| [reference-library.md](reference-library.md) | İlgili mühendislik sorusu için kaynak seçerken |
| [launch-kit.md](launch-kit.md) | Tanıtım mesajı, görseller ve dağıtım kanalı durumunda |
| [index.html](index.html) | GitHub Pages üzerindeki statik Divan tanıtım ve kurulum sayfası |
| [../CHANGELOG.md](../CHANGELOG.md) | Kullanıcının gördüğü davranış değiştiğinde |

Makineye özel kurulum kanıtı `.local/setup-status.md` içinde tutulabilir; Git'e ve
plugin ZIP'ine girmez. Bu klasöre de parola, token veya özel anahtar yazılmaz.
Canlı servis ve test sonuçları tarihli gözlemlerdir; sonraki oturumda yeniden
doğrulanır. Çözülmemiş bir işi tamamlandı diye kaydetme.
