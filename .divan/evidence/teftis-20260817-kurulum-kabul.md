# Teftiş — kurulum adayı ve kabul testi

Date: 2026-08-17
Artifact: `Divan_1.3.8_x64-setup.exe`, 11.5 MB
Built from: `apps/desktop` with the existing Tauri and NSIS pipeline, no second
installer architecture

## Neden yeniden derlendi

Kurulum adayı üretilmeden önce sidecar deneme derlemesine alındı ve arşivi
açılıp içindeki gerçek modül listesi okundu. İkili, çalışma zamanının
bildirdiği 93 modülden **59'unu** taşıyordu. Eksik olanlar arasında çalışan
yürütme, bağımsız denetim, doğrulama kilidi ve başarısızlıktan öğrenme vardı.

PyInstaller yalnız giriş noktasından erişilebilen modülleri paketler; hiçbir
yerden içe aktarılmayan bir modül sessizce dışarıda kalır. Bu haliyle üretilen
bir kurulum, bu kampanyada kanıtlanan yeteneklerin çoğunu taşımayan bir ürün
paketlerdi.

Derleme artık `modules.json` sözleşmesini okuyup her bildirilen modülü zorunlu
içe aktarım olarak veriyor. Yeniden derlendi ve arşivden okundu: **93 bildirilen,
93 pakette**.

## Kabul testi

Kurulumun var olması geçmek değildir. Aday, atılabilir bir dizine sessizce
kuruldu, taşıdığı Core sidecar'ı çalıştırıldı, kaldırıldı ve kullanıcı işine ne
olduğuna bakıldı. Sahibin gerçek Divan durumuna dokunulmadı; kullanıcı işinin
yerine sentetik bir depo kondu.

| Kontrol | Sonuç |
|---|---|
| Kurulum ürünü var | 11.5 MB |
| Sessiz kurulum tamamlanır | çıkış 0, `Divan.exe` yerinde |
| Core sidecar paketle gelir | `Divan.exe`, `divan-core.exe`, `uninstall.exe` |
| Core kurulumdan sonra cevap verir | doctor 15 yetenek döndürdü |
| Doctor bütün yetenekleri bildirir | 15 yetenek |
| Doctor durumları ayırt eder | 15'in 10'u CERTIFIED; görülen durumlar BLOCKED, CERTIFIED, DEGRADED, INCOMPATIBLE, OFFLINE |
| Çalışma alanı yeniden başlatmayı atlatır | ayrı bir süreçte kaydedilip listelendi |
| Kaldırma uygulamayı siler | dizinde çalıştırılabilir kalmadı |
| **Kaldırma kullanıcı projesini korur** | sentetik proje dosyası yerinde |
| **Kaldırma proje kanıtını korur** | projenin `.divan` kanıtı yerinde |

**10/10.**

Doctor'ın durum çeşitliliği burada asıl kanıttır. Hepsi CERTIFIED dönseydi
kontrolün bir şey ölçtüğünü söyleyemezdik; beş ayrı durum, kurulumun makinenin
gerçek halini okuduğunu gösteriyor. Eksik bir isteğe bağlı yetenek ürünü
bütünüyle çökük saymıyor.

## Kendi hatalarım

İlk üç koşuda dört kontrol düştü ve dördü de ölçüm aracımdandı:

- `project.register` argümanlarını `params` içine koymuştum; Core en üst
  seviyeden okuyor.
- Sentetik kullanıcı projesini düz klasör yapmıştım; Divan yalnız sürüm
  kontrolü altındaki klasörü benimsiyor. Bu kasıtlı bir ürün kuralı, kusur
  değil.
- `project.list` listenin kendisini döndürüyor, sarmalanmış bir nesne değil.
- Yetenek durumlarını küçük harfle karşılaştırmıştım, Core büyük harf gönderiyor.

Uygulamaya hiçbir düzeltme yapılmadı. Bunlar burada duruyor çünkü kampanyada
düşen kapıların önemli bir bölümünün sebebi ürün değil ölçüm aracı oldu ve bunu
saymamak raporu bozar.

## Sınırlar

- İmzalama yapılandırılmadı; aday imzasızdır.
- Güncelleyici bu derlemede etkin değil, dolayısıyla kendi kendini
  güncellemesi bu kanıtın kapsamında değil.
- Kaldırma sonrası uygulamaya ait geçici veri politikası ayrıca ölçülmedi;
  ölçülen, kullanıcı işinin ve proje kanıtının korunmasıdır.
- Yayımlanmadı, etiketlenmedi, dağıtılmadı. Yerel adaydır.
