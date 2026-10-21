# Kurulum ve geliştirme

## Gereksinimler

Git ve plugin destekleyen Codex yeterlidir. Kaynak doğrulaması için Python 3.12+
gerekir; CI Python 3.13 kullanır. Python paket bağımlılığı yoktur. Node/npx,
Docker, veritabanı veya yeni MCP sunucusu bu repo için gerekli değildir.

## Yerel checkout'u kur

Repo kökünde, mevcut marketplace kayıtlarını önce kontrol et:

```powershell
codex plugin marketplace list
codex plugin marketplace add .
codex plugin add divan@divan --json
codex plugin list --marketplace divan --json
```

Aynı adlı marketplace zaten varsa kaynağını kontrol et; başka bir kaydı sessizce
değiştirme. Yerel marketplace checkout'u gösterir, kurulum plugin içeriğini önbelleğe
alır. Kaynak değişiklikleri sonrası testleri çalıştırıp `codex plugin add divan@divan`
ile yeniden kur ve yeni bir Codex sohbeti aç. Eski sohbetin beceri kataloğunun
kendiliğinden yenilendiğini varsayma.

Kaynak checkout kurulumuyla GitHub `main` sürümünün kurulumu farklıdır. GitHub'daki
yayınlanmış ağaç için kök README komutlarını kullan.

## Doğrula

Windows PowerShell:

```powershell
./scripts/check.ps1
# İsteğe bağlı açık yorumlayıcı seçimi:
./scripts/check.ps1 -Python 'C:/path/to/python.exe'
```

Yardımcı, mevcut Python'u veya varsa Codex'in hazır ortamını kullanır. Python
yoksa kurulumu gizlice başlatmaz, eksikliği bildirir. Diğer platformlarda:

```bash
python3 scripts/divan_v2_validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/package_divan_v2.py
git diff --check
```

ZIP `dist/` içinde oluşturulur. `dist/` ve `.local/` Git dışında kalır. Lisans
bildirimleri paketle taşınır. Paketleyici beklenmeyen dosya veya geçersiz sözleşme
bulursa başarısız olur; hassas dosyaları yalnız `.gitignore` ile koruduğunu varsayma.
Skill Markdown içindeki basit yerel inline bağlantıların hedefleri ve paket sınırı
denetlenir; bu kontrol tam Markdown ayrıştırması veya dış web bağlantısı testi değildir.

## Git ve CI

Belirli bir Git sürümünü ayrı geçici çalışma alanında sınamak için:

```sh
git fetch origin
python scripts/isolated_check.py --ref origin/main
```

Bu komut seçilen commit'i değişmez SHA'ya çözer; validatorı, tam test kümesini ve
paketlemeyi o ağacın düzenlenmemiş kopyasında çalıştırır. JSON çıktısı kaynak ve
ağaç SHA'sını, komutların sonuçlarını ve ZIP hashini içerir. Kirli veya izlenmeyen
çalışma dosyaları dahil edilmez. İncelenmiş index görüntüsünü sınamak için
`git write-tree` çıktısını `--ref` olarak ver; önce yalnız amaçlanan dosyaları stage et.
Sonuç dosyasını örneğin `.local/isolated-check.json` içinde saklayabilirsin.

Çalışma dosyaları ve devralınan kullanıcı yapılandırması ayrılır; bu bir işletim
sistemi/ağ güvenlik sandbox'ı değildir. Yalnız güvendiğin kaynakta çalıştır.
Komut Codex modelini çağırmaz; gerçek beceri davranışı ayrı görev denemesi gerektirir.
Git arşivinin dosyaları eksiltmesi (`export-ignore`) veya içerik değiştirmesi kabul
edilmez; symlink/submodule bu kaynak doğrulama yolunda desteklenmez.

Kısa ömürlü bir dalda küçük, doğrulanmış değişiklikler yap. Commit öncesi son
diff'i ve dışarı gidecek dosyaları incele. GitHub eklentisi ile `gh`/Git kimlik
doğrulaması farklıdır; birinin bağlı olması diğerini kanıtlamaz. Push/PR sonrasında
uzak SHA ve ilgili CI sonuçlarını ayrıca kontrol et. Release ve main'e birleştirme
kullanıcının kapsamı açıkça içeriyorsa yapılır.

CI validatorı, tam test kümesini, farkların whitespace kontrolünü ve paketlemeyi
çalıştırır. Yapısal eval senaryoları model üzerinde otomatik kalite ölçümü değildir.
[Sipariş eşzamanlılığı görevi](../evals/order-concurrency/README.md) başlangıç kodu
ve bağımsız davranış kontrolü sunar; gerçek ajan karşılaştırması için aynı ortamda
ayrı denemeler ve sonuç kayıtları gerekir.

## İşletim

Bu skills-only plugin için HTTP health endpoint, Coolify dağıtımı veya Kuma
monitörü uygulanmaz. Aynı adı taşıyan servisleri repo kimliği doğrulanmadan Divan'ın
çalışan uygulaması sayma. Başka bir projede servis kullanıldığında o projenin
işletim belgesinde URL, health endpoint, kaynak ve monitor eşleşmesi tutulur.
