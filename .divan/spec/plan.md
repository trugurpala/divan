# Etkin plan — v0.17.0 One Divan / Modular Engine

Kanonik hedef:
`.divan/spec/v0.17.0-one-divan-modular-engine.md`.

1. ADR 0007 ile tek ürün, Hükümdar yetkisi, modül sınırı ve uyumluluk süresini
   sabitle.
2. Çalışan çekirdeği aynı klasör derinliğindeki `divan_runtime` paketine taşı;
   paket-içi importları kullan.
3. Modül grafiği ve Divan Nizamı sözleşmesini fail-closed kernel ile doğrula.
4. Eski `company` Python/JSON yollarını ve `company-validate` takma adını v1
   boyunca davranış eşliğiyle koru.
5. Deterministik project runner, composite action, etki grafiği, mypy, coverage,
   Clean Code ve CI yüzeylerini kanonik pakete geçir.
6. README, kanonik iki dilli rehberler, Wiki, site, CHANGELOG, BLUEPRINT,
   progress ve release manifestini tek ürün diliyle eşitle.
7. Odaklı ve tam testleri çalıştır; bağımsız inceleme bulgularını test-first
   kapat.
8. v0.17 PR'ını aç, bütün CI kapılarını geçir, `main`e birleştir.
9. Kanonik release workflow'undan tag/Release/assets/attestations üret; Pages,
   Wiki ve varlık hash'lerini geri oku.

Issue #34 dış kullanıcı gerektirir. v0.17 yayını bu kanıtı üretmez ve v1,
bağımsız kabul gelene kadar 7/8 kalır.
