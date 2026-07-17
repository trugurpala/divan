---
name: defterdar
description: Persistent project memory keeper for the USER's project (Ottoman treasurer-scribe). Creates and maintains AGENTS.md, BLUEPRINT.md (vision, ADR decision records, roadmap, status log), a .divan/ progress journal, decision records and a test-evidence log; reads them at every session start and writes after each Divan Protokolu phase and at session end, so work survives restarts, context compaction and machine moves. Use when starting any serious project, when resuming work, or when the user says "hafiza", "kaldigim yerden devam", "defter kur", "BLUEPRINT", "AGENTS.md", "remember this project", "resume where we left off".
---

# Defterdar — Kalıcı Proje Hafızası

İlke: **state ajanın context'inde değil, diskte yaşar.** Context her an
sıfırlanabilir; repoda duran hafıza baki kalır.

## Dosya düzeni (kullanıcı projesinin kökünde)

```
AGENTS.md            # ajan giriş noktası: build/test/konvansiyon/sınırlar
BLUEPRINT.md         # tek gerçek kaynak: Vizyon · ADR özeti · Yol Haritası · Durum Günlüğü
.divan/
  progress.md        # oturum günlüğü: yapıldı / sıradaki adım / bilinen sorunlar
  decisions/         # ADR'ler: 0001-baslik.md (bağlam·seçenekler·karar·sonuç)
  spec/              # spec.md, plan.md, tasks.md (Spec Kit specs/ yapısıyla uyumlu)
  evidence/          # teftis-YYYYMMDD.md: test çıktıları, kanıtlar
  risk-register.md   # (para-dokunan projelerde) risk·olasılık·etki·sahip·azaltım
```

Şablonlar: references/agents-sablonu.md, references/blueprint-sablonu.md,
references/adr-sablonu.md, references/risk-register-sablonu.md — gerektiğinde oku.

## Oturum başı (HER yeni context/restart'ta, işe dokunmadan önce)

1. AGENTS.md → 2. BLUEPRINT.md → 3. .divan/progress.md → 4. `git log --oneline -5`
Sonra tek cümleyle "kaldığımız yer"i söyle ve devam et. Bu dosyalar yoksa
kullanıcının Divan hafızası isteyip istemediğini kontrol et; açık istek yoksa
projeye yeni kayıt dosyaları ekleme.

## Kurulum (ilk ferman / "defter kur")

1. Mevcut dosyaları önce incele; hiçbir dosyanın üzerine yazma. Çakışma varsa
   önerilen farkı göster ve kullanıcı onayı bekle.
2. Yukarıdaki iskeleti yalnızca kullanıcı istediğinde şablonlardan oluştur
   (dolu, yer tutucusuz).
3. Kullanıcı açıkça istemedikçe `git init`, commit veya push yapma. Git kaydı
   istenirse yalnızca bu işin dosyalarını kapsayan kasıtlı bir commit hazırla.
4. AGENTS.md'ye projenin GERÇEK build/test komutlarını yaz (uydurma; yoksa sor).
5. Para-dokunan projeyse (ödeme, borsa, bakiye): risk-register.md zorunlu,
   spec-first zorunlu — spec/spec.md yazılmadan İcra'ya geçilmez.

## Kayıt nizamı (ne, ne zaman yazılır)

| Faz bitti | Dosyaya işle |
|---|---|
| Ferman | hedef → BLUEPRINT vizyon/kapsam |
| Divan | seçilen yaklaşım + gerekçe → .divan/decisions/NNNN-*.md + BLUEPRINT ADR satırı |
| Plan | numaralı plan → .divan/spec/plan.md |
| İcra | progress.md güncelle; commit yalnızca kullanıcı yetki verdiyse |
| Teftiş | kanıt → .divan/evidence/teftis-tarih.md; başarısızlık → risk-register |
| Takdim / oturum sonu | BLUEPRINT durum günlüğüne tarihli satır + progress.md'de net "sıradaki adım" |

## Nizam kuralları

- BLUEPRINT ≤ 200 satır; taşarsa ayrıntıyı .divan/ altına indir.
- Kararı sohbette bırakma: konuşulan her mimari karar ADR olur.
- Kanıtsız "bitti" defterlere geçmez — Teftiş kanıtı evidence/'a yazılmadan
  Takdim yapılmaz.
- Oturumu asla "sıradaki adım" yazmadan kapatma.
- Defter kaydı proje hafızası içindir; kullanıcının kaynak kontrolü kararının
  yerine geçmez.
