# Divan — Claude Code devralma sözleşmesi

Bu depo sohbet geçmişinden bağımsız yürütülür. **Agency OS dönüşümünde birinci owner talimatı `DIVAN_AGENCY_OS_MASTER_MANDATE.md` dosyasıdır.**

Bir göreve başlamadan önce şu sırayla oku:

1. `DIVAN_AGENCY_OS_MASTER_MANDATE.md` — Padişah Fermanı, standing technical delegation, hard owner gates ve Agency OS uygulama sırası.
2. `AGENTS.md` — bağlayıcı çalışma, teftiş, güvenlik ve yayın kuralları.
3. `BLUEPRINT.md` — ürün yönü, mimari kararlar ve sürüm geçmişi.
4. `.divan/progress.md` — gerçek mevcut durum ve sıradaki kesin adım.
5. İlgili kod, test, product spec, release/CI sözleşmeleri.
6. Yayında `release-manifest.json` ve `registry/v1-gates.json`.
7. Kamuya açık metin yazarken `docs/Yazim-ve-Uslup.md`.

## Yetki yorumu

Agency OS dönüşümü için owner açıkça geniş, tekrar sormayı gerektirmeyen teknik delegasyon vermiştir. Bu nedenle `AGENTS.md` içindeki “kullanıcı açıkça istemedikçe” koşulu; Ferman kapsamındaki geri alınabilir yerel/repository teknik işler, branch/worktree, commit, doğrulanmış PR ve gerekli entegrasyon açısından sağlanmıştır.

Bunun anlamı:

- rutin framework/kütüphane/refactor/test/migration/skill/agent/plugin/tool kararını kullanıcıya taşıma;
- mevcut kanıtla karar verilebiliyorsa karar ver ve uygula;
- eksik yetenek varsa master mandate'teki Capability Acquisition Pipeline ile araştır, test et, ADOPT/ADAPT/REJECT et;
- worker/tool başarısızsa önce recover/retry/replace/replan et;
- teknik uygulama kapsamı Fermanı doğru ve güvenli bitirmek için büyümek zorundaysa bunu kaydet ve uygula;
- ürün/business niyetini sessizce değiştirme;
- hard owner gate oluşmadıkça yalnız plan yazıp durma.

`DIVAN_AGENCY_OS_MASTER_MANDATE.md` rutin izin döngülerini kaldırır; **AGENTS.md'nin güvenlik, kanıt, kalite, kullanıcı işini koruma, lisans ve fail-closed kurallarını kaldırmaz.** Çelişki görürsen en güvenli, kanıta dayalı yorumu seç ve kararı kalıcı kayda geçir.

## Değişmez emirler

- Kullanıcının eski konuşmaları hatırlatmasını bekleme; karar ve ilerlemeyi aynı turda kalıcı kayıtlara işle.
- README, katalog, Wiki kaynağı, Pages/site, CHANGELOG ve Release ürün yüzeyleridir. Ürünü değiştiren işte `AGENTS.md` kurallarını uygula.
- Lisansı doğrulanmamış içeriği kopyalama; popülerlik güven kanıtı değildir.
- Kanıt görmeden “bitti”, “main'de”, “canlı” veya “release yayımlandı” deme.
- Model/worker self-report'unu kanıt kabul etme.
- `UNKNOWN`, `SKIPPED`, `NOT_INSTALLED` veya timeout'u PASS sayma.
- Kullanıcının başlangıç değişikliklerini silme/sahiplenme.
- Teknik ayrıntı çözülebiliyorsa kullanıcıyı process supervisor yapma.
- README, Wiki, site, release, issue ve PR metnini `docs/Yazim-ve-Uslup.md` sözleşmesine göre yaz ve `scripts/prose.py --check` ile denetle.

Önce mevcut sözleşme hâlâ gerektiriyorsa `python scripts/handoff.py --check` çalıştır. Teslimden önce `AGENTS.md` içindeki güncel doğrulama komutlarını çalıştır. Public release/production promotion master mandate'teki hard owner gate olarak kalır; hazırlık ve kanıtı otomatik tamamla, dış promotion adımında gate'i uygula.
