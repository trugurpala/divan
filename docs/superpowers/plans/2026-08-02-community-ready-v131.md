# Divan v1.3.1 Topluluk Hazırlığı Uygulama Planı

**Goal:** Güncel v1.3.1 ana dalını tek repo, modüler paket ve kanıtlı topluluk
bakımı sözleşmesiyle korumak; ilk temas yüzeylerinde sürüm gerçeği driftini
kalite kapısında yakalamak.

## Task 1: Güncel temel doğrulaması

- [x] v1.3.1 release, `main`, açık issue/PR ve son Actions durumunu oku.
- [x] Eski v1.3.0 çalışma dalını güncel `origin/main` ile değiştirme.
- [x] Mevcut topluluk dosyaları, issue formları ve görsel sistem kaynaklarını denetle.

## Task 2: Kamuya açık sürüm gerçeğini koru

- [x] Türkçe README rozetindeki eski 1.2.0 metnini v1.3.1 ile eşitle.
- [x] `scripts/prose.py` içine İngilizce/Türkçe kaynak satırı ve rozet kapısı ekle.
- [x] Drift için regresyon testi yaz.
- [x] Kararı `.divan/decisions/0013-community-ready-public-truth.md` içinde kaydet.

## Task 3: Kanıtlı teslim

- [ ] Odak testleri, katalog, release, prose ve tam `scripts/verify.py` çalıştır.
- [ ] Temiz dalı GitHub PR'ı olarak sun; CI yeşil değilse merge/release iddiasında bulunma.
- [ ] Merge sonrası `main`, Pages, Wiki, README ve release yüzeylerini geri oku.

## Kapsam dışı

Yeni runtime, başka repo fork'u, otomatik plugin kurulumu, Figma dosyasını
yeniden üretme ve kanıtsız kalite/hız iddiası bu bakım işine dahil değildir.
