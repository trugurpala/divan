## Ne değişti?

## Teftiş çeklisti
- [ ] `python scripts/validate.py` yerelde temiz
- [ ] Frontmatter standartlara uygun (name ≤64, description ≤1024)
- [ ] Üçüncü taraf içerik varsa lisans izinli + UPSTREAM.md ve
      THIRD_PARTY_LICENSES.md güncellendi
- [ ] Proprietary içerik yok
- [ ] Skill davranışı değiştiyse `python evals/run.py --check` geçti; kalite
      iddiası varsa gerçek adaptör/hakem ve sonuç kanıtı eklendi

## Yayın çeklisti

- [ ] `VERSION`, marketplace ve paket sürümleri SemVer'e uygun
- [ ] Değişiklik kullanıcıya görünüyorsa README/TR, README/EN, CHANGELOG,
      BLUEPRINT, Wiki kaynağı ve site birlikte güncellendi
- [ ] `python scripts/wiki.py --check` geçti; Wiki etkileniyorsa `wiki-sync`
      kontrolü yeşil
- [ ] `python scripts/release.py --check` ve `python scripts/v1.py --check` geçti
- [ ] Dış kaynak/aday değiştiyse `python scripts/candidate_review.py --check` geçti;
      aday olmanın kurulum olmadığı ve lisans kapsamı açık
- [ ] `.divan/progress.md` yapılanı, açığı ve sıradaki kesin adımı kaydediyor
- [ ] PR taslak değil; zorunlu CI kontrolleri yeşil
- [ ] Yetki ve kapsam varsa `main`e birleşme ile varsayılan dal/canlı yüzey
      doğrulaması teslimin parçası
- [ ] Wiki etkinse `main` sonrası Wiki deposu ve canlı `Home.md` doğrulandı
- [ ] `main` sonrası Pages/Wiki aynı sürümde; tag/Release yoksa “release yayımlandı” denmiyor
