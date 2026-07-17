---
name: vezir-yetistirme
description: Skill-creation coach for the Divan marketplace ("training a new vizier"). Use when the user wants to add a new skill to Divan, write a SKILL.md, contribute to the marketplace, or says things like "yeni skill yaz", "Divan'a vezir ekle", "skill nasıl yazılır", "create a new skill for Divan". Scaffolds a standards-compliant skill, wires it into a plugin and marketplace.json, and runs the teftiş validator before finishing.
---

# Vezir Yetiştirme — Divan'a Yeni Skill Kazandırma

Divan kendini böyle geliştirir: her yeni vezir bu usulle yetişir.

## Usul

1. **Amaç.** Tek cümle: bu vezir ne yapar? Tek sorumluluk — iki iş yapan
   vezir, iki vezir olmalıdır.
2. **Tetikleyiciler.** Kullanıcı hangi ifadelerle çağırır? En az 3-5 gerçekçi
   ifade yaz (Türkçe + İngilizce). Bunlar description'a girecek.
3. **İskelet.** `plugins/<paket>/skills/<skill-adi>/SKILL.md` oluştur:
   - `name`: kebab-case, ≤ 64 karakter
   - `description`: ≤ 1024 karakter; üçüncü şahıs; ne yaptığı + ne zaman
     tetikleneceği (tetikleyici ifadeler dahil)
4. **Gövde.** Kısa ve prosedürel yaz: numaralı adımlar, somut örnekler,
   "yapma" listesi. 500 satırı geçme; uzarsa `references/` dosyalarına böl.
5. **Kayıt.** Yeni paketse `marketplace.json`'a ekle; mevcutsa dokunma
   (plugin skills klasörünü otomatik tarar).
6. **Teftiş.** `python scripts/validate.py` çalıştır — temiz çıkmadan bitti
   deme. Hata varsa düzelt, tekrar koş.
7. **Takdim.** Değişen dosyaları listele; katkı PR'ıysa CONTRIBUTING.md'deki
   çekliste göre hazırla.

## Kalite mihengi

- Description'ı okuyan bir ajan, skill'i NE ZAMAN kullanacağını gövdeyi
  açmadan bilmeli.
- Gövde talimatları kanıt ister: "test et", "çıktıyı göster" adımları koy.
- Üçüncü taraf içerik taşıyorsan lisansını doğrula (MIT/Apache-2.0/CC0
  izinli; proprietary yasak) ve UPSTREAM.md + THIRD_PARTY_LICENSES.md güncelle.
