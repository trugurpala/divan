# Divan

**Vibe coding, engineered.**

Divan; Codex ile yazılım geliştiren kullanıcıların teknik ayrıntıya boğulmadan, doğal dille daha disiplinli kod üretmesini amaçlayan bir mühendislik eklentisidir.

## Durum

Aktif geliştirme hattı `2.0.0-alpha.1` Codex-native yeniden yazımıdır.

Yayınlanabilir paket:

```text
plugins/divan/
```

Eski Divan uygulaması aktif ağaçtan çıkarılmıştır; Git geçmişi ve eski release'ler korunur.

## Kullanım fikri

Şöyle konuşman yeterlidir:

```text
Divan, bu projeyi incele.
Divan, bu özelliği en küçük doğru değişiklikle yap.
Divan, bu hatanın kök nedenini bul ve düzelt.
Divan, gerçekten bitti mi kontrol et.
```

Divan içeride repo inceleme, planlama, root-cause debugging, kalite review ve completion proof akışlarını kullanır. Kullanıcı bunların teknik isimlerini öğrenmek zorunda değildir.

## V2 alpha sınırı

- tek plugin;
- 7 çekirdek skill;
- gerektiğinde yüklenen engineering-taste referansları;
- standard-library doğrulama ve paketleme;
- MCP yok;
- özel agent runtime yok;
- backend yok;
- UI yok;
- yayınlanan hook yok.

## Doğrulama

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_divan_v2*.py" -v
python scripts/package_divan_v2.py
```

Bu mekanik testler paket bütünlüğünü kanıtlar; model kalitesinde artış iddiası değildir.

## Lisans

MIT
