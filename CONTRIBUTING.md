# Divan'a Katkı

Divan kendini toplulukla geliştirir. Yeni bir vezir (skill) kazandırmak için:

## Yol
1. **Öneri:** "Yeni Vezir" issue şablonuyla fikrini aç — tek cümle amaç +
   hangi ifadelerle tetikleneceği.
2. **Yaz:** `plugins/<paket>/skills/<skill-adi>/SKILL.md`. Kurallar aşağıda.
   İpucu: Claude Code'da `sadrazam` kuruluysa "Divan'a yeni vezir yaz" de —
   `vezir-yetistirme` skill'i seni adım adım yürütür.
3. **Teftiş:** `python scripts/validate.py` yerelde temiz çıkmalı.
4. **PR aç:** Şablondaki çeklisti doldur.

## Skill standartları (Agent Skills — agentskills.io)
- Frontmatter zorunlu: `name` (kebab-case, ≤ 64 karakter) ve `description`
  (≤ 1024 karakter; ne yaptığı + hangi ifadelerde tetikleneceği).
- Gövde: kısa, prosedürel, tek sorumluluk; 500 satırı geçme.
- Dil: Türkçe veya İngilizce; tetikleyici ifadeleri her iki dilde düşün.
- Üçüncü taraf içerik taşıyorsan: lisansı MIT/Apache-2.0/CC0 gibi izinli
  olmalı ve THIRD_PARTY_LICENSES.md + UPSTREAM.md güncellenmeli.
- Proprietary içerik kabul edilmez.

## Sürüm ve onay
Küçük düzeltmeler doğrudan PR; yeni paketler önce issue tartışması ister.
Her PR CI teftişinden geçmeden birleşmez.
