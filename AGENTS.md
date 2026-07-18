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
- Katalog teftişi: `scripts/katalog.py --check`
- Yayın yüzeyleri: `release-manifest.json` ve `scripts/yayin.py --check`
- v1 kabul defteri: `registry/v1-gates.json` ve `scripts/v1.py --check`

## Çalışma kuralları

- En küçük yeterli değişikliği yap; üçüncü taraf harness'i veya çalışma zamanı
  bağımlılığını varsayılan yol haline getirme.
- Lisansı doğrulanmamış içeriği kopyalama. Taşınan her içerik için `UPSTREAM.md`
  ve `THIRD_PARTY_LICENSES.md` kayıtlarını güncel tut.
- Dış kaynak keşfini doğrudan kuruluma çevirme. Meclis varsa adayı
  `registry/candidates.json` yaşam döngüsüne işle; ADOPT/ADAPT kararı bile ayrı
  pin+atıf+eval+teftiş uygulaması ister.
- Kullanıcı açıkça istemedikçe repo başlatma, commit, push, release veya mevcut
  proje dosyalarının üzerine sessizce yazma.
- Paralel ajanları yalnızca bağımsız ve sınırları belirli işler için kullan.
  Aynı dosyayı eşzamanlı yazdırma; paralel yazım gerekiyorsa ayrı worktree kullan.
- Ürünü değiştiren işte README, katalog, kurulum belgesi, Wiki kaynağı ve site
  sayılarını aynı değişiklikte eşitle. Wiki etkinse `scripts/wiki.py --check`
  ve `wiki-sync` yayın kanıtını da zorunlu yüzey say.
- Kamusal teslimde taslak PR'ı son durum sayma. Yetki kapsamındaysa CI sonrası
  varsayılan dala birleştir; README/kurulum/canlı sayfayı varsayılan daldan
  yeniden oku. Tag yoksa “release yayımlandı” deme.
- Her sürümde `/yayin`/`scripts/yayin.py` yolunu kullan; `VERSION`, marketplace,
  `CHANGELOG.md`, README'ler, BLUEPRINT, Wiki, site ve kurulum referansını
  eşitle. `.divan/progress.md` sıradaki kesin adımı taşımalı. `main` sonrası
  Pages/Wiki/tag/Release kanıtını ayrı ayrı doğrula.
- Bir skill'in davranışı iyileştirdiğini iddia etmeden önce `evals/README.md`
  protokolünü kullan. Gerçek ajan adaptörü/hakem koşmadıysa yalnız sözleşme veya
  mekanik doğrulama raporla; win-rate, hız ya da kalite artışı uydurma.

## Doğrulama

Teslimden önce en az şunları çalıştır:

```bash
python scripts/validate.py
python scripts/katalog.py --check
python scripts/v1.py --check
python scripts/yayin.py --check
python evals/run.py --check
python -m unittest discover -s tests -v
git diff --check
```

Claude Code veya Agent Skills şemasını etkileyen değişikliklerde CI'daki resmî
doğrulayıcıların yerel karşılıklarını da çalıştır. Kanıt görmeden “bitti” deme.
