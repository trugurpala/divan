---
description: Divan'a standartlara uygun yeni bir skill (vezir) kazandır
argument-hint: skill-fikri
---
`${CLAUDE_PLUGIN_ROOT}` veya host metadata içindeki eşdeğer loaded-plugin root'u
çöz; kullanıcının current working directory yolundan çözme. O kökteki
`skills/sadrazam/references/vibe-progress.md` kanonik Vibe progress protocol
sözleşmesini substantial işlerde araçlardan önce ve her meaningful phase
değişiminde uygula.

`vezir-yetistirme` skill'ini yükle ve şu fikri Divan'a vezir olarak yetiştir:
$ARGUMENTS

Usulü harfiyen izle: tek cümlelik amaç → tetikleyici ifadeler (TR+EN) →
plugins/<paket>/skills/<ad>/SKILL.md iskeleti (name=klasör adı, ≤64;
description ≤1024; frontmatter'da < > kullanma) → kısa prosedürel gövde →
`python scripts/validate.py` temiz çıkana kadar düzelt → değişen dosyaları
listele ve CONTRIBUTING.md çeklistine göre PR'a hazırla.
