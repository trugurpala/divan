---
name: vezir-yetistirme
description: Skill-creation and evaluation coach for the Divan marketplace ("training a new vizier"). Use when the user wants to add, improve, benchmark or test a skill, write a SKILL.md, contribute to the marketplace, compare skill-enabled behavior with a baseline, or says yeni skill yaz, Divan'a vezir ekle, skill nasıl yazılır, skill'i test et, benchmark this skill, evaluate triggering, or create a new skill for Divan. Creates a standards-compliant skill, a bounded eval contract, marketplace wiring and teftiş evidence without inventing performance gains.
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
5. **Eval sözleşmesi.** Davranışı doğrulanabilir vezirde 2–3 gerçek kullanım
   örneğini `evals/evals.json` içine yaz. Her örnekte prompt, beklenen çıktı ve
   nesnel beklentiler bulunur. Şema: `references/eval-protokolu.md`.
6. **Kayıt.** Yeni paketse `marketplace.json`'a ekle; mevcutsa dokunma
   (plugin skills klasörünü otomatik tarar).
7. **Karşılaştır.** Ortam izin veriyorsa aynı girdiyi temiz bağlamlarda skill'li
   ve baseline olarak çalıştır. Girdi ve araç yetkileri aynı olmalı; bir koşunun
   çıktısı diğerine sızmamalı. Çıktıları skill klasörünün dışında tut.
8. **Teftiş.** `python scripts/validate.py` çalıştır — skill ve eval sözleşmesi
   temiz çıkmadan bitti
   deme. Hata varsa düzelt, tekrar koş.
9. **Takdim.** Yapısal doğrulamayı davranış başarısıyla karıştırma. Gerçek koşu
   yapılmadıysa “benchmark geçti” deme; değişen dosyaları ve kanıtı listele.

## Kalite mihengi

- Description'ı okuyan bir ajan, skill'i NE ZAMAN kullanacağını gövdeyi
  açmadan bilmeli.
- Gövde talimatları kanıt ister: "test et", "çıktıyı göster" adımları koy.
- Skill'li/baseline karşılaştırmasında sıfır koşu başarı değildir; eksik sonuç
  açık hata sayılır. Token ve süre yalnızca runtime gerçekten veriyorsa yazılır.
- Öznel tasarım/yazım skill'lerinde sahte sayısal puan yerine kör insan
  değerlendirmesi veya açık rubrik kullanılır.
- Üçüncü taraf içerik taşıyorsan lisansını doğrula (MIT/Apache-2.0/CC0
  izinli; proprietary yasak) ve UPSTREAM.md + THIRD_PARTY_LICENSES.md güncelle.
