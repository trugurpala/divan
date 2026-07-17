---
description: Divan'a standartlara uygun yeni bir skill (vezir) kazandır
argument-hint: skill-fikri
---
`vezir-yetistirme` skill'ini yükle ve şu fikri Divan'a vezir olarak yetiştir:
$ARGUMENTS

Usulü harfiyen izle: tek cümlelik amaç → tetikleyici ifadeler (TR+EN) →
plugins/<paket>/skills/<ad>/SKILL.md iskeleti (name=klasör adı, ≤64;
description ≤1024; frontmatter'da < > kullanma) → kısa prosedürel gövde →
`python scripts/validate.py` temiz çıkana kadar düzelt → değişen dosyaları
listele ve CONTRIBUTING.md çeklistine göre PR'a hazırla.
