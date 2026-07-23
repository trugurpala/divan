# Divan Company OS

Divan, doğal dilde verdiğin işi kodlama ajanının çevresinde küçük ve kanıt
odaklı bir yazılım şirketine dönüştürür. Onlarca sahte persona ya da ikinci bir
ajan çalışma zamanı kurmaz; yalnız proje ve hedef için gereken rolleri,
paketleri, framework kurallarını ve kalite kapılarını seçer.

1. **Inspect**, proje kodunu çalıştırmadan sınırlı manifestleri okur.
2. **Plan**, işi ve framework'ü belirler; uygun akışı ve en küçük ekibi seçer.
3. **Deliver**, mühendislik için Core Pack'i; arayüz için UI Pack'i; yalnız
   React/Next.js kanıtı varsa React Pack'i; yaratıcı veya entegrasyon işi varsa
   Zanaat Pack'i kullanır.
4. **Impact**, değişen dosyaları bağımlılık grafiğinde genişletir; katalog,
   README, Wiki, site, eval ve yayın yüzeylerinin unutulmasını engeller.
5. **Verify**, tamamlandı demeden önce güncel test ve bağımsız inceleme ister.

Normal kullanımda skill adlarını ezberlemen gerekmez. Hedefi yazman yeterlidir.
Bakım ve entegrasyon için kanonik komutlar:

```powershell
python scripts/divan.py inspect --project .
python scripts/divan.py plan --project . --intent "Kayıt ekranını erişilebilir yap"
python scripts/divan.py impact README.md plugins/sadrazam/skills/sadrazam/SKILL.md
python scripts/divan.py company-validate
```

Teknik dosya ve komut adları küresel katkıcılar için İngilizce, kullanıcı
metinleri Türkçe kalabilir. Ayrıntılar: [English](Company-OS.md).
