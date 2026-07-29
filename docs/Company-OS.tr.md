# Divan Company OS

Divan, doğal dilde verdiğin işi kodlama ajanının çevresinde küçük ve kanıt
odaklı bir yazılım şirketine dönüştürür. Onlarca sahte persona ya da ikinci bir
ajan çalışma zamanı kurmaz; yalnız proje ve hedef için gereken rolleri,
paketleri, framework kurallarını ve kalite kapılarını seçer.

## Nasıl çalışır?

1. **Inspect**, proje kodunu çalıştırmadan sınırlı manifestleri okur.
2. **Plan**, işi ve framework'ü belirler; uygun akışı ve en küçük ekibi seçer.
3. **Nizâm-ı Sefer**, işin tahmini çalışma yükünü hesaplar; host tarafından
   bildirilen veya güvenli varsayım olarak kullanılan bağlam kapasitesine göre
   işi oturumlara böler, paralellik sınırını ve devir eşiğini belirler.
4. **Deliver**, mühendislik için Core Pack'i; arayüz için UI Pack'i; yalnız
   React/Next.js kanıtı varsa React Pack'i; yaratıcı veya entegrasyon işi varsa
   Zanaat Pack'i kullanır.
5. **Impact**, düzenlenmesi planlanan ve gerçekten değişen dosyaları bağımlılık
   grafiğinde genişletir; katalog, README, Wiki, site, eval ve yayın yüzeylerinin
   unutulmasını engeller.
6. **Verify**, tamamlandı demeden önce güncel test, kalıcı makbuz ve bağımsız
   inceleme ister.

Normal kullanımda skill adlarını ezberlemen gerekmez. Hedefi yazman yeterlidir.
Bakım ve entegrasyon için kanonik komutlar:

```powershell
python scripts/divan.py inspect --project .
python scripts/divan.py plan --project . --intent "Kayıt ekranını erişilebilir yap"
python scripts/divan.py plan --project . --intent "Sürümü yayınla" --target released --host-profile codex --context-window 128000 --json
python scripts/divan.py impact README.md plugins/sadrazam/skills/sadrazam/SKILL.md
python scripts/divan.py company-validate
```

`--context-window`, hostun veya operatörün bildirdiği kesin token kapasitesidir.
Bu değer yoksa `host-profiles.json` yalnız planlama için temkinli bir varsayım
kullanır. Bu varsayım model, abonelik veya ürün limiti iddiası değildir; plan
kapasitenin kaynağını ve uyarısını açıkça döndürür.

## Nizâm-ı Sefer sözleşmesi

Genişletilmiş rota şema 3'tür ve şunları üretir:

- deterministik karmaşıklık puanı ve tahmini çalışma yükü;
- kullanılabilir bağlam bütçesi, güvenlik payı ve devir eşiği;
- önerilen oturum sayısı ve güvenli paralel iş şeridi sınırı;
- teknik olarak İngilizce-kanonik `single-expedition`,
  `sequential-expeditions` veya `bounded-army` çalışma yolu;
- makine tarafında `campaigns` dizisi, kullanıcı tarafında `Sefer 01`,
  `Sefer 02` gibi Osmanlı düzenini koruyan görünen adlar;
- bağımlılıkları, görev sahibi paşası ve kanıt şartı belirlenmiş işler;
- İngilizce-kanonik `command_structure` alanları içinde Padişah ve Sadrazam
  görünen adları;
- kalıcı hafıza ve yayın yüzeyi yükümlülükleri.

Bir hedef başlatıldığında eski insan-okunur sözleşme korunur:
`.divan/specs/<goal-id>/{spec.md,plan.md,tasks.md}`. Makine rotası ayrıca
`.divan/routes/<goal-id>.json` dosyasına yazılır ve SHA-256 özeti `spec.md`
içine mühürlenir. Böylece eski Project OS makbuzları bozulmaz; yeni oturum ise
işe tam olarak nereden devam edeceğini bilir. Host ve context kapasitesi hedef
kimliğinden çıkarıldığı için aynı proje ve ferman Claude ile Codex'te aynı
`goal_id` değerini korur.

```powershell
python scripts/divan.py goal start --project . --intent "API'yi sertleştir ve yayınla" --target released --host-profile auto --json
python scripts/divan.py goal start --project . --intent "API'yi sertleştir ve yayınla" --target released --host-profile auto --execute --json
```

Her sefer; checkpoint, karar/progress güncellemesi, kanıt ve tek bir kesin sonraki
adımla kapanmalıdır. Paralel çalışma yalnız `safe_parallel_workstreams`
sınırına kadar açılır. Bağlam kapasitesi bilinmiyorsa Divan daha serbest değil,
daha temkinli davranır.

## Bilgi ve yayın yüzeyi yükümlülüğü

Planlama zekâsı rastgele metinlerin üzerine körlemesine yazmaz. Yükümlülüğü
makine-okunur ve fail-closed hâle getirir:

1. düzenlemeden önce etki hesabı yap;
2. gerçek değişen dosyalardan etkiyi yeniden hesapla;
3. sınıflandırılmamış dosya varsa işi tamamlanmış sayma;
4. kanonik kaynağı ve ona bağlı README/Wiki/site/release yüzeylerini aynı
   değişiklik içinde güncelle;
5. `released` veya `observed` hedeflerinde uzak yüzeyi geri okuyup doğrula.

Etki grafiği; planlama motoru, host profilleri, hedef oluşturma sistemi, CLI ve
odak testlerindeki değişiklikleri Company OS, dokümantasyon ve yayın işi olarak
sınıflandırır. Beyni güncelleyip kitabı eski bırakan bir PR zorunlu kontrolleri
geçmemelidir.

Project OS bu seçimi kurulu projede kalıcı sözleşmeye dönüştürür:

```powershell
python scripts/divan.py init --project . --profile standard --locale auto
python scripts/divan.py audit --project . --format json
```

Repo düzeyindeki `DCS-*` kuralları Divan'ın bakım sözleşmesidir. Kurulu projede
yalnız uygulanabilir `DPS-*` kuralları ve kanıt zinciri çalışır:
[Project OS](../docs/Project-OS.tr.md).

Kurulu plugin, standart kütüphane tabanlı çekirdeği
`plugins/sadrazam/company/` altında taşır; proje verisini dışarı göndermez.

| Paket | Seçildiği işler | Seçilmediği işler |
|---|---|---|
| Core Pack | planlama, test, hata ayıklama, review ve doğrulama | ürün değişikliklerinde atlanmaz |
| UI Pack | arayüz, UX, erişilebilirlik ve tarayıcı doğrulaması | yalnız backend işleri |
| React Pack | kanıtlanmış React, Next.js veya React Native projeleri | ilgisiz frameworkler |
| Zanaat Pack | MCP/API entegrasyonu ve özgün yaratıcı içerik | sıradan özellik geliştirme |

Çekirdek sözleşmeler `roles.json`, `workflows.json`, `frameworks.json`,
`impact-graph.json` ve `host-profiles.json` dosyalarıdır. `planning.py`,
Nizâm-ı Sefer rotasını üretir. Teknik dosya ve komut adları küresel katkıcılar
için İngilizce, kullanıcı metinleri Türkçe kalabilir. Ayrıntılar:
[English](Company-OS.md).
