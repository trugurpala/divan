# Mimari ve çalışma kararları

## Yedi ana beceri ve isteğe bağlı referanslar

Mevcut skills-only mimari korunur. Yeteneğin keşfi `repo-audit`, kalıcı proje
bağlamı `project-contract` içinde geliştirilir. Yeni runtime veya servis gerektirmez.
Kaynak rehberi bir yükleme listesi değildir; yalnız ilgili bölümü okunur.

Kullanıcının hedefi günlük işte güvenilen, sürekli geliştirilen bir üründür.
Plan, uygulama ve doğrulama bu hedefin parçalarıdır; çalışan ürün talebi yalnız
plan veya araç listesiyle kapanmaz. Low-code ve açık kaynak seçimi toplam uyarlama,
test ve bakım maliyetine göre yapılır. Bağımsız uygulama işleri dosya sahipliğiyle
delege edilebilir; son inceleme ve bütünleştirme kanıtını ana ajan sahiplenir.

## Tek kaynakla farklı ajanlara dağıtım

Codex skills-only manifesti `requires_local_executor: true` bildirir. Gerçek
repo inceleme, dosya değişikliği ve test çalıştırma yerel çalışma alanı gerektirir;
resmi dizindeki görünürlük genel web sohbetine dosya erişimi kazandırmaz.
Bu bayrak oturumun komut politikasını gevşetmez. Farklı makine ve ajanlarda
taşınabilir beceriler kendi erişim koşullarıyla ayrıca kurulur.

Codex'in yerel plugin paketi korunur. Aynı yedi `SKILL.md` ve referansları Agent
Skills destekleyen uygulamalara ayrıca kurulabilir. Her editör için ayrı beceri
kopyası, özel runtime veya MCP sunucusu eklenmez. Yardımcı beceriler göreli
bağlantılarla bulunur; bütün yedi beceri birlikte kurulur. Her becerinin lisans
bildirimi bağımsız kopyalamada da korunur ve canonical plugin lisansına karşı denetlenir.

Kurulum için MIT lisanslı Vercel Skills CLI 1.7.4 kullanılır; bu kullanıcı
tarafında isteğe bağlı bir kurucudur, Divan'ın çalışma bağımlılığı değildir.
Dosya yerleşimi testi, editörde algılanma ve gerçek model davranış testi ayrı
kanıtlardır. Kaynaklar ve kapsam [uyumluluk rehberindedir](compatibility.md).

## Kalıcı bağlam Markdown içinde

`AGENTS.md` kısa kuralları ve belge bağlantılarını taşır. Ürün amacı, kararlar ve
geliştirme işlemleri ayrı belgelerde tutulur. Eşdeğer belgeleri olan bir projede
bu adlar zorunlu tutulmaz. Codex'in otomatik belleğine güvenmek yerine gerekli
ekip kuralları sürüm kontrollü kaynakta bulunur; makineye özel durum Git dışında kalır.

## Araç seçimi ihtiyaca ve canlı kanıta dayanır

Kurulu beceri, MCP yapılandırması, oturum aracı ve çalışan servis aynı şey değildir.
Önce mevcut çözüm kullanılır. Eksik bir kurulumun kaynağı, sürümü, lisansı,
bağımlılığı, yetkisi ve doğrulama yöntemi belirlenir; kullanıcının kurulum tercihi
istenir. Sıradan uygulama tercihleri için önceki yetki tekrar sorulmaz.

## Tek doğrulama kümesi

Yerel ve CI akışı `test_*.py` kümesini çalıştırır. Paket üretimi doğrulayıcıdan
bağımsız bir kaçış yolu olmamalıdır. Geçersiz kaynak eski başarılı ZIP'i bozmamalı;
aynı kaynak tekrar paketlendiğinde aynı baytlar çıkmalıdır. `dist/` Git'e girmez.

## Yayın ayrı bir sonuçtur

Yerel kurulum, Git commit'i, uzak dal, PR, CI sonucu ve release ayrı ayrı
raporlanır. Sürüm dosyasının değişmesi yayın yapıldığı anlamına gelmez. Mevcut
GitHub mimarisi korunur; isim benzerliğiyle bir self-host servisine taşınmaz.
