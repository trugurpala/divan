# Etkin plan — v0.17.1 Vibe-friendly Progress

Kanonik hedef: `.divan/spec/v0.17.1-vibe-progress.md`.

1. ADR 0008 ile sade ilerleme dili, kanıt ayrımları, erişilebilir durum dili ve
   host UI sınırını sabitle.
2. Sadrazam altında tek kanonik ilerleme sözleşmesi oluştur; davranışı yeni bir
   runtime veya dış bağımlılık hâline getirme.
3. `/divan`, `/ferman`, `/sefer`, `/teftis` ve `/yayin` girişlerini aynı
   sözleşmeye bağla; kopyalanmış protokol üretme.
4. Vibe coder değer rehberi, README, Wiki, Pages/site kaynağı, paket metadata,
   changelog, blueprint, progress ve release manifestini eşitle.
5. Odaklı testleri, etki grafiğinin istediği kapıları ve tam kanonik teftişi
   çalıştır; bağımsız inceleme bulgularını kapat.
6. v0.17.1 PR'ını aç, zorunlu CI kapılarını geç, korumalı `main`e birleştir.
7. Kanonik release akışından değişmez tag/Release/assets/attestations üret;
   Pages, Wiki ve varlık hash'lerini geri oku.

Issue #34 dış kullanıcı gerektirir. Bu sahip-yürütümlü iletişim sürümü o kanıtı
üretmez ve v1, bağımsız kabul gelene kadar 7/8 kalır.
