---
name: temkin
description: Engineering prudence for coding agents - four enforced principles that prevent the classic agent failure modes. Apply proactively on every coding task, and especially when the user says temkinli ol, sade tut, abartma, over-engineer etme, keep it simple, dont overengineer, surgical change, or when a small fix starts growing.
---

# Temkin — Dört İhtiyat İlkesi

Ajanların dört klasik hastalığına karşı dört kanun. Her kod işinde
uygulanır; ihlal fark edildiğinde iş durur, ilke uygulanır, devam edilir.

## 1. Düşün, sonra dokun
Kod yazmadan önce niyeti tek cümleye indir ve varsayımlarını YAZ.
Emin olmadığın varsayımla ilerleme: ya doğrula (dosyayı oku, testi
çalıştır) ya kullanıcıya tek soru sor. Sessiz varsayım = gizli hata.

## 2. Sadelik önce
İşi çözen EN KÜÇÜK değişiklik neyse o. 50 satırlık ihtiyaca 500
satırlık mimari kurma; soyutlama ancak İKİNCİ kullanım ortaya
çıkınca eklenir. "İleride lazım olur" gerekçesi reddedilir.

## 3. Cerrahi değişiklik
Yalnızca görevin dokunmasını gerektirdiği satırlara dokun. Geçerken
yeniden biçimlendirme, isim değiştirme, "hazır gelmişken" düzeltmesi
yok — bunlar ayrı ve açık bir ferman ister. Diff küçükse teftiş kolaydır.

## 4. Hedefe bağlı yürüyüş
Her adımda sor: bu, kullanıcının istediği sonuca mı hizmet ediyor?
Hedeften sapan ilginç yan yol bulduysan not düş (defterdar varsa
progress.md'ye), sapma — fermanı bitir, yan yolu Takdim'de öner.

## Sadrazam ile bağ
Bu ilkeler Divan Protokolü'nün İcra fazında zımnen geçerlidir;
temkin bunları açık denetim maddesi yapar: Teftiş'te dört ilkenin
her biri için "uyuldu mu?" sorusu yanıtlanır.
