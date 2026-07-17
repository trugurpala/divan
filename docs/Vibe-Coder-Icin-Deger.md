# Bunu Kurunca Ne Değişir? (Vibe Coder İçin Değer)

Reponun aklı şudur: **sen "ne" istediğini söylersin (vibe), Divan "nasıl"ı
kıdemli mühendis disipliniyle uygular.** Kurulum öncesi ve sonrası fark:

| Durum | Divan'sız ajan | Divan'lı ajan |
|---|---|---|
| "Şu uygulamayı yap" | Doğrudan kod yazar, yarısı çalışmaz | `/ferman` → önce plan, sonra TDD ile inşa, kanıtla teslim |
| Hata çıktı | Rastgele dener, semptomu yamar | systematic-debugging: 4 fazlı kök-neden analizi |
| Arayüz istedin | Jenerik "AI slop" tasarım | frontend-design + ui-ux-pro-max: özgün estetik yön |
| "Bitti" dedi | Sözüne inanmak zorundasın | verification-before-completion: test çıktısı göstermeden bitti diyemez |
| Fikrin dağınık | Ne sorduğunu unutuyor | brainstorming: seçenekleri tartıp gerekçeli seçer |
| İş büyüdü | Her şeyi aynı bağlamda karıştırır | `/sefer`: tek oturum, sınırları belirli subagent veya izole worktree arasından en küçüğünü seçer |
| Repo yabancı | Her dosyayı okuyup bağlamı doldurur | arama-ustası: dar `rg`, gerekirse doğrulanmış AST araması ve dosya:satır kanıtı |
| Oturum uzadı | Eski loglar hedefi boğar | bağlam-muhafızı: hedefi/hataları korur, tekrarları dışarı alır, ölçemediği kazancı uydurmaz |

Somut bir gün: sabah `/ferman kullanıcı girişi ekle` dersin — ajan planı
yazar, testleri önce yazar, kodu geçirir, tarayıcıda dener (webapp-testing =
Playwright), kanıtı gösterir, sonraki adımları önerir. Sen kahveni içersin.

Birden çok bağımsız parça varsa `/sefer` kullanırsın. Divan sırf “çok ajanlı”
görünmek için swarm kurmaz; çakışan yazımı ayırır, maliyet sınırı koyar ve
birleşik sonucu yeniden test eder.

Yeni vezirler de yalnızca “iyi prompt” oldukları için kabul edilmez. Eval
sözleşmesi gerçek kullanım örneklerini, beklenen çıktıyı ve nesnel beklentileri
tanımlar; mümkünse aynı girdide skill'li/baseline karşılaştırması yapılır.

**Neden ~1.4K token'a mal oluyor da MCP'nin 55K'sına olmuyor?** Skill'ler
aşamalı yüklenir: boşta yalnızca ad+açıklama; gövde tetiklenince okunur.
