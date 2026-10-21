# Divan ürün sözleşmesi

Divan, kullanıcının doğal dille anlattığı yazılım işini repo inceleme, küçük uygulama
adımları ve güncel tamamlanma kanıtına taşıyan, Codex eklentisi ve taşınabilir Agent
Skills olarak dağıtılan bir mühendislik yardımcısıdır. Kullanıcının
her seferinde beceri, araç veya servis adı seçmesini gerektirmemelidir.

Ürün hedefi gerçek günlük geliştirmede kullanılan, bakımı sürdürülen bir yardımcıdır.
Kullanıcı bu hedefin bir MVP veya demo kapsamına indirgenmesini istemiyor. İşin küçük
adımlara bölünmesi; gerçek veri akışını, hata davranışını, entegrasyonu veya doğrulamayı
atlama gerekçesi değildir. Mevcut ön sürüm etiketi geçmiş paket sürümünü ifade eder;
ölçülmemiş bir kararlılık garantisi vermek için değiştirilmez.

## Kapsam

- `plugins/divan/`: dağıtılan plugin, yedi ana beceri ve gerektiğinde okunan referanslar.
- `scripts/`: Python standart kütüphanesiyle doğrulama ve deterministik ZIP üretimi.
- `tests/` ve `evals/`: mekanik sözleşmeler, paket davranış testleri, yönlendirme senaryoları.
- `.github/workflows/`: pull request ve ana dal için kalite kontrolleri.
- `docs/`: ürün kararları, katkı akışı ve seçilmiş kaynaklar.

Divan'ın kendi HTTP sunucusu, veritabanı, MCP sunucusu, UI'ı veya özel ajan
çalıştırıcısı yoktur. Başka projelerde mevcut MCP ve servisleri gerektiğinde
kullanabilmesi, bunları Divan paketine eklemeyi gerektirmez.

## Bu geliştirme diliminin sonucu

1. Yerel checkout, çalıştırılabilir doğrulama ve Codex plugin kurulumu.
2. Araçların gerçek erişim durumunu ayıran ve eksik kurulum için somut seçenek sunan akış.
3. Kısa `AGENTS.md`, bağlantılı proje belgeleri ve gerektiğinde okunan 50 maddelik rehber.
4. Tüm testleri kapsayan CI ve geçersiz/istenmeyen dosyaları dışlayan paketleme.
5. Yeniden kullanım, API/eklenti, low-code ve özel kod kararını toplam bakım maliyetine
   göre veren; bağımsız işleri kısa kanıtlarla delege eden çalışma rehberi.
6. Kendi diliyle istek veren kullanıcı için ilk kullanım, ilerleme bildirimi,
   durum sorusu ve devam etme akışı; ayrıntılar [günlük kullanım kararında](ideas/daily-use.md).
7. Belirli bir Git ağacını ayrı çalışma alanında doğrulayan tekrar üretilebilir komut.
8. Tek beceri kaynağından farklı kodlama ajanlarına kurulum; editör erişimi ve
   davranış başarımıyla dosya kurulumunu ayıran [uyumluluk rehberi](compatibility.md).

Tamamlanma ölçütü: yeni ağaç üzerinde validator, tüm testler ve paketleme geçmeli;
kurulumun algılandığı ayrıca doğrulanmalı. Yerel test, uzak CI veya model başarımı
kanıtı yerine geçmez. Bir sonraki ürün davranışı kullanıcı ihtiyacı ve bu kanıtla
seçilir; belirsiz bir “her şeyi geliştir” kapsamı açılmaz.

## Sonraki geliştirmeler

- Yönlendirme senaryolarını izinli gerçek Codex oturumlarında karşılaştırmalı ölçmek.
- Paket biçimini değiştirirken Codex uyumluluğunu resmi plugin belgelerine göre sınamak.
- Yeni kullanıcı geri bildiriminden tekrar eden bir boşluk çıkarsa mevcut beceriyi
  düzeltmek; her boşluk için yeni ana beceri veya bağımlılık eklememek.
