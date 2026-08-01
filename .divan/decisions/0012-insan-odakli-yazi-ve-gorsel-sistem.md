# ADR 0012 — İnsan odaklı yazı ve düzenlenebilir görsel sistem

- Durum: Kabul edildi
- Tarih: 2026-08-01
- Sürüm hedefi: v1.2.0

## Bağlam

Divan'ın teknik kanıtları güçlü olsa da ilk kez gelen kullanıcı ürünün ne
yaptığını, ücretsiz olup olmadığını ve ilk komutu bulmak için fazla iç mimari
okuyordu. Yazı ve görseller sohbet kararlarında kalırsa sonraki oturumlarda
yeniden sapma oluşur.

## Karar

Kamuya açık metinlerin kanonik kuralı `docs/Yazim-ve-Uslup.md` olur. Güvenli
mekanik hatalar `scripts/prose.py` ile kapanır; bağlama bağlı dil kararları insan
incelemesinde kalır. Divan kimliği korunur fakat Osmanlıca terimler ilk kullanımda
günlük karşılığıyla açıklanır.

Görsel sistemin düzenlenebilir kaynağı Figma'daki “Divan — Nizamlı Müşterek”
dosyasıdır. Üretim dışa aktarımları bu repoda sürümlenir. Başka repo forklanmaz;
tek repo ve modüler paket yapısı değişmez.

## Sonuçlar

- README, Wiki, site, issue/PR ve sürüm metinleri aynı yazı sözleşmesine uyar.
- Figma kaynak bağlantısı ve export sözleşmesi `docs/Gorsel-Sistem.md` içinde
  tutulur.
- Kanıtsız pazarlama iddiaları ve kullanıcıya rol dayatma reddedilir.
- Her sürümde prose, görsel ölçü, link ve yayın yüzeyi testleri çalışır.
