# Divan'a Katkı

**Türkçe** · [English](CONTRIBUTING.en.md) · [Destek yolları](SUPPORT.md) ·
[Topluluk standartları](docs/Topluluk-Standartlari.md)

Divan yerel bir skill/plugin dağıtımıdır; model veya ajan runtime'ı değildir.
Katkılar 41 skill'lik kataloğu taşınabilir, lisansı açık, geri alınabilir ve
kanıta dayalı tutmalıdır.

## Doğru yolu seç

- Kullanım soruları için [SUPPORT.md](SUPPORT.md) içindeki Q&A yolunu kullan.
- Tekrar üretilebilir hataları hata formuyla bildir.
- Güvenlik açıklarını yalnız özel güvenlik bildirimiyle paylaş.
- Mevcut bir repo/yetenek için kaynak-adayı formunu kullan.
- Özgün bir Divan yeteneği için yeni-vezir formunu kullan.
- Bağımsız v1 kanıtını kabul-kanıtı formuyla gönder.

## Katkı yolu

1. Düzenlemeden önce `BLUEPRINT.md`, `UPSTREAM.md`,
   `THIRD_PARTY_LICENSES.md` ve ilgili paket talimatlarını oku.
2. En küçük tutarlı birimi değiştir. Kaynak keşfini kuruluma çevirme; lisansı
   ve kökeni kanıtlanmamış içeriği kopyalama.
3. Davranış değişikliğine kırmızı testle başla. Host politikasını Claude/Codex
   adaptörlerinden bağımsız tut ve alakasız kullanıcı eklentilerini koru.
4. Yerel kapıların tamamını çalıştır:

```bash
python scripts/hygiene.py --check
python scripts/validate.py
python scripts/handoff.py --check
python scripts/catalog.py --check
python scripts/v1.py --check
python scripts/release.py --check
python evals/run.py --check
python -m unittest discover -s tests -v
git diff --check
```

5. Tek amaçlı bir pull request aç. Kullanıcı sonucunu, riski, geri alma yolunu
   ve tam doğrulama kanıtını yaz. Gerçek ajan adaptörü ve kör hakem protokolü
   olmadan davranış iyileşmesi iddia etme.

## Yeni skill ekleme

Özgün bir skill'i gerçek paket yolunda oluştur:

```text
plugins/<paket>/skills/<skill-adi>/SKILL.md
```

`SKILL.md` YAML frontmatter'ında klasörle birebir aynı, kebab-case `name`
(en çok 64 karakter) ve ne yaptığıyla ne zaman tetikleneceğini anlatan
`description` (en çok 1024 karakter) zorunludur. Gövde prosedürel ve tek
sorumluluklu olmalı; 500 satırı aşan ayrıntıyı `references/` altına böl.
Sonra katalog ve teftişi eşitle:

```bash
python scripts/catalog.py --render
python scripts/catalog.py --check
python scripts/validate.py
python scripts/candidate_review.py --check
```

Bir dış kaynağın aday defterine girmesi benimsenmesi değildir. Kaynak önce
kimlik, lisans, köken, hook/script/yetki ve mevcut yetenek çakışması açısından
incelenir. `ADOPT` veya `ADAPT` kararı bile kurulum sayılmaz; sabit pin, atıf,
eval ve teftiş ayrı uygulama değişikliğinde tamamlanır.

Ürünü değiştiren katkı README, katalog, kurulum belgesi, Wiki kaynağı, site,
yayın manifesti ve lisans/köken kayıtlarını aynı değişiklikte eşitlemelidir.
`DCS-001` ile `DCS-011` arasındaki on bir zorunlu kuralı doğrulamak için:

```bash
python scripts/standards.py --check
```
