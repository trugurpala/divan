# Divan neyi ne zaman kullanır?

Kullanıcı amacı anlatır; Divan mevcut projeyi okuyup gerekli katmanı seçer. Bu tablo
bir çalışma haritasıdır. Dış beceri ve servisler Divan'ın zorunlu bağımlılıkları
değildir; her ortamda erişimleri ayrıca doğrulanır.

| İhtiyaç | Divan'ın seçimi | Dış yetenek gerekirse |
| --- | --- | --- |
| Projeyi tanımak | `repo-audit` | Git, mevcut README/manifest/testler |
| Açık kaynak mı, low-code mu, özel kod mu? | `repo-audit` içindeki yeniden kullanım rehberi | SAK veya eşdeğer keşif yöntemi; resmi kaynak, GitHub, varsa Context7 |
| Ürün özelliğini geliştirmek | `implementation-plan`, ardından gerçek uygulama | Projeye uygun frontend/API/veritabanı becerisi ve mevcut araçlar |
| Dış uygulamadaki veriyi okumak/değiştirmek | Gerekli yeteneği ve işlemi doğrulamak | Yetkili eklenti/MCP/API/CLI; okuma yetkisi yazma yetkisi sayılmaz |
| Form, yönetim paneli, iç iş akışı | Mevcut framework veya low-code seçeneğini karşılaştırmak | Gerçek veri, yetki, taşıma/ihraç, test ve işletim maliyeti uygunsa kullanmak |
| Yeni servis gereksinimi | Mevcut kaynakla eşleştirmek | Mevcut hosting, sağlık ve kapasite kanıtı; gerekiyorsa somut kurulum seçimi |
| Hata/regresyon | `root-cause-debug` | Başarısız akışın yeniden üretimi, ilgili log/test |
| Kalite ve kullanıcı deneyimi | `quality-review` | Gerektiğinde tarayıcı/erişilebilirlik, tasarım veya ilgili uzmanlık |
| Gerçekten tamamlandı mı? | `completion-proof` | Güncel test/build, gerekiyorsa kullanıcı akışı, CI ve canlı ortam |
| Yarın kaldığımız yerden devam | `project-contract` | Mevcut AGENTS ve proje belgelerine kısa durum/karar/kanıt |

## Ana ve alt ajanlar

Ana ajan sonucu ve entegrasyonu sahiplenir. Araştırma, ayrı dosyalardaki uygulama ve
bağımsız inceleme işleri uygun olduğunda alt ajanlara ayrılır. Her görev hedef,
dosya sınırı, yetki ve kabul kanıtıyla gider. Sonuçlar kısa değişiklik/kanıt/engel
mesajlarıyla döner; ana ajan diff'i inceler ve güncel testi kendisi çalıştırır.

Bu, Codex'in mevcut ajan araçlarının kullanımıdır. Yeni agent sunucusu veya sürekli
arka plan hizmeti kurmaz. Büyük değişiklikte bağımsız üst düzey inceleme, ilk kullanıcı
amacının kaybolup kaybolmadığını ve gerçek akışın tamamlanıp tamamlanmadığını kontrol eder.

## Low-code seçiminde kalite eşiği

Hazır çözüm; uyarlama, test, dağıtım ve bakımın toplamını iyileştiriyorsa seçilir.
Kısa görünen kurulum komutu tek başına yeterli gerekçe değildir. Veri sahipliği,
yetkilendirme, hata durumları, yedekleme, taşınabilirlik ve gereken özelleştirme
doğrulanır. Sadece maket veya sahte veriyle çalışan bağlantı teslim edilmez.

Yöntemin paket içindeki kaynakları:
[yetenek keşfi](../plugins/divan/skills/repo-audit/references/capabilities.md),
[yeniden kullanım kararı](../plugins/divan/skills/repo-audit/references/reuse-decisions.md),
[iş bölümü](../plugins/divan/skills/implementation-plan/references/delegation.md),
[proje hafızası](../plugins/divan/skills/project-contract/references/project-memory.md).
