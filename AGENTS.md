# Divan çalışma sözleşmesi

## Amaç

Divan, Claude Code için yerel bir eklenti pazarı ve Agent Skills uyumlu bir
skill derlemesidir. Değişiklikler vibe coder için düşük bilişsel yükü,
taşınabilirliği, lisans açıklığını ve kanıtlı teslimi korumalıdır.

## Önce oku

- Ürün yönü ve kararlar: `BLUEPRINT.md`
- Upstream kökenleri ve yamalar: `UPSTREAM.md`
- Lisans envanteri: `THIRD_PARTY_LICENSES.md`
- Yerel teftiş: `scripts/validate.py`

## Çalışma kuralları

- En küçük yeterli değişikliği yap; üçüncü taraf harness'i veya çalışma zamanı
  bağımlılığını varsayılan yol haline getirme.
- Lisansı doğrulanmamış içeriği kopyalama. Taşınan her içerik için `UPSTREAM.md`
  ve `THIRD_PARTY_LICENSES.md` kayıtlarını güncel tut.
- Kullanıcı açıkça istemedikçe repo başlatma, commit, push, release veya mevcut
  proje dosyalarının üzerine sessizce yazma.
- Paralel ajanları yalnızca bağımsız ve sınırları belirli işler için kullan.
  Aynı dosyayı eşzamanlı yazdırma; paralel yazım gerekiyorsa ayrı worktree kullan.
- Ürünü değiştiren işte README, katalog, kurulum belgesi ve site sayılarını aynı
  değişiklikte eşitle.
- Kamusal teslimde taslak PR'ı son durum sayma. Yetki kapsamındaysa CI sonrası
  varsayılan dala birleştir; README/kurulum/canlı sayfayı varsayılan daldan
  yeniden oku. Tag yoksa “release yayımlandı” deme.
- Her sürümde `VERSION`, marketplace, `CHANGELOG.md`, README'ler, BLUEPRINT ve
  kurulum referansını eşitle. `.divan/progress.md` sıradaki kesin adımı taşımalı.

## Doğrulama

Teslimden önce en az şunları çalıştır:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
git diff --check
```

Claude Code veya Agent Skills şemasını etkileyen değişikliklerde CI'daki resmî
doğrulayıcıların yerel karşılıklarını da çalıştır. Kanıt görmeden “bitti” deme.
