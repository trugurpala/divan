# Divan — Blueprint

> Tek gerçek kaynak. Bu dosyayı okuyan herhangi bir ajan veya insan,
> projeyi kaldığı yerden sürdürebilir. Sohbet geçmişine bağımlılık yoktur.

## Vizyon
Padişah (kullanıcı) fermanı verir; Divan (skill paketleri) işi baştan sona,
kanıtıyla bitirir. Hedef kitle: AI ajanlarıyla üretim yapan vibe coder'lar.

## Mimari Kararlar (ADR)
1. **Neden skill/plugin, neden MCP değil:** Ürün prosedürel bilgidir (nasıl
   yapılır). Skill'ler progressive disclosure ile token-verimlidir ve Agent
   Skills açık standardı sayesinde Claude Code, Cursor, Codex ve 30+ ajanda
   çalışır. MCP canlı veri/aksiyon içindir; ihtiyaç doğduğunda (v2) eklenir.
2. **Neden uygulama değil (henüz):** Dağıtım GitHub + `/plugin` komutuyla
   sıfır altyapı maliyetiyle çalışır. Hosted web uygulaması, ödeme ve premium
   içerik v2'nin işidir.
3. **Lisans stratejisi:** Derleme ve özgün skill'ler MIT. Üçüncü taraf
   skill'ler kendi lisanslarını korur (THIRD_PARTY_LICENSES.md). Anthropic'in
   proprietary document-skills'i (docx/pdf/pptx/xlsx) ASLA dahil edilmez.
4. **Orkestrasyon stratejisi:** Divan üçüncü taraf bir harness'e bağımlı olmaz.
   Varsayılan tek oturumdur; bağımsız işler yerel subagent'larla, eşzamanlı
   yazım worktree izolasyonuyla yürür. Agent Teams deneysel ve açık tercihtir.
   Gerekçe ve aday karnesi `docs/Orkestrasyon-Karari.md` içindedir.
5. **Repo hijyeni:** Üretilmiş dosya temizliği allowlist ve fail-closed çalışır;
   kullanıcı yedeği ile yayın kanıtı çöp sayılmaz. Birinci taraf metin UTF-8/LF,
   çekirdek Python karmaşıklık bütçesi 25'tir. Ayrıntı ADR 0003'tedir.
6. **Topluluk standartları kod olarak:** DCS-001..DCS-011 makine-okunur tek
   registry'den doğrulanır; framework/host ayrıntıları adaptör sınırında kalır,
   istisnalar dar ve süreli olur. Ayrıntı ADR 0004'tedir.
7. **Company OS ve küresel teknik dil:** Kullanıcı hedefi doğal dilde verir;
   Sadrazam rol, akış, framework, paket ve geçişli etki sözleşmelerinden en küçük
   yetkin ekibi seçer. Teknik girişler İngilizce kanoniktir, Türkçe yerelleştirme
   birinci sınıftır. Ayrıntı ADR 0005'tedir.

## Standartlar
- Agent Skills açık standardı (agentskills.io): SKILL.md frontmatter,
  name ≤ 64, description ≤ 1024 karakter.
- Her push'ta CI teftişi: `scripts/validate.py` (JSON geçerliliği, frontmatter,
  proprietary sızıntı, placeholder kontrolü).
- Tarayıcı testi kullanıcı tarafında: ui-pack'teki `webapp-testing` skill'i
  (Playwright) ile.

## v0.6 Vendoring Hedef Listesi (keşif raporu, 2026-07-17)
Öncelik sırasıyla; her biri alınmadan önce LICENSE dosyası bizzat okunacak:
1. Karpathy-skills (100K+ yıldız fenomen, tek CLAUDE.md, 4 ilke) — lisans DOĞRULANACAK
2. VoltAgent/awesome-agent-skills'ten seçme (20K yıldız, 1000+ skill; tek tek lisans bak)
3. Remotion best-practices (video üretimi — vibe coder talebi yüksek)
4. Caveman (çıktı-token kısıcı; fatura dostları için)
5. android/skills + Expo skill (mobil ordu)
YASAK: sızdırılmış system-prompt depoları (x1xhlol vb.) — lisanssız + etik dışı, popülerliği fark etmez.

## Yol Haritası

### Yayımlanan temel

- **v0.14.0 ✓** Company OS; 12 rol, 8 akış, framework kanıtı ve geçişli etki
  grafiği; Core/UI/React/Zanaat paketlerinin gerekçeli seçimi; İngilizce kanonik
  CLI, workflow ve katkı yüzeyleri; süreli Türkçe uyumluluk sarmalayıcıları

- **v0.1–v0.7 ✓** 5 paket, 37 skill, landing, CI, hafıza, lisans/köken
  kayıtları, topluluk ve güvenlik dosyaları
- **v0.9.0 ✓** 41 skill; yerel orkestrasyon, kanıtlı arama, bağlam disiplini,
  kaynak kürasyonu, İngilizce vitrin, CHANGELOG ve Yayın Kanunu
- **v0.10.0 ✓** niyetten pakete/fermana giden etkileşimli vibe coder yüzeyi;
  4 skill/12 vaka için sağlayıcı-bağımsız, kör A/B davranış eval koşucusu
- **v0.10.1 ✓** 14 sayfalık sürümlü GitHub Wiki kaynağı, deterministik
  derleyici/bağlantı teftişi ve `main` sonrası ayrı Wiki Git deposuna yayın +
  canlı `Home.md` doğrulama kapısı; Sadrazam Bilgi Yüzeyleri Kanunu
- **v0.10.2 ✓** yapılandırılmış kaynak-adayı formu, makine-okunur Aday Meclisi,
  haftalık salt-okunur GitHub keşfi ve otomatik kurulum yapmayan
  PENDING→ADOPT/ADAPT/REFERENCE/REJECT yaşam döngüsü
- **v0.10.3 ✓** 41 skill frontmatter'ından deterministik Vezir Kataloğu,
  Wiki ilk-sayfa preflight'ı ve Node 24 tabanlı güncel GitHub Actions zinciri
- **v0.11.0 ✓** tek komutlu yayın yüzeyi hazırlığı ve sapma kapısı; Pages +
  Wiki canlı eşliğinden sonra CHANGELOG kaynaklı otomatik tag/GitHub Release;
  Linux/macOS/Windows Codex kur-kaldır matrisi, Claude Code resmî doğrulaması,
  makine-okunur v1 karnesi ve bağımsız kabul kanıtı akışı
- **v0.11.1 ✓** Claude Code kök devralma sözleşmesi, makinece denetlenen
  sohbetten bağımsız devam zinciri, CODEOWNERS ve Actions Dependabot kapısı
- **v0.12.0 ✓** ürün kapsamı: Claude + Codex yerel pazar eşliği, dry-run-first
  işlemsel çift-host kurucu, checksum/provenance kontrollü fallback, gerçek
  Claude ajanı + kör Codex hakemi adaptörleri, CodeQL ve tam-SHA Action pinleri,
  erişilebilir site ile 15 kayıtlı upstream drift kararı. PR #17 `e9a2642e`
  ile `main`e birleşti; v0.12.0 tag/Release, Pages, Wiki ve çift global native
  kurulum ayrı kanıtlarla doğrulandı.
- **v0.12.1 ✓** ürün kapsamı: UTF-8/LF repo sözleşmesi, allowlist tabanlı
  güvenli hijyen komutu, McCabe 25 bütçesi ve üç kritik akışta davranış-korumalı
  tek-sorumluluk refactor'ü. Bu satır kod kapsamını gösterir; PR/main/Release ve
  global kurulum kanıtı tamamlanmadan sürüm yayımlandı sayılmaz.
- **v0.12.2 ✓** Windows bakım kapsamı: salt-okunur öznitelikli allowlist cache
  yollarını yalnız silme hatası anında ve junction/symlink reddiyle düzelten
  dayanıklı silme ile regresyon testleri.

- **v0.13.0 ✓** product scope ready: ten machine-enforced community standards,
  read-only dual-host doctor, provenance-gated transactional upgrade, Clean
  Code debt ratchet, SPDX/Scorecard/dependency-review/attestation controls, and
  synchronized support/contribution/public surfaces. This check marks local
  scope completion only; PR/main, repository rules, public release, and global
  host delivery remain separate pending states.

### Sıradaki ürün kanıtı — v1 kabulü

1. ✓ v0.12.0 birleştirme/tag/Release/Pages/Wiki ve global kurulum kanıtı.
2. ✓ Gerçek Claude ajanı + kör Codex hakemiyle ilk yayımlanabilir A/B kanıtı.
3. Sabitlenmiş release'i deneyen bağımsız kullanıcı kabul kanıtı.
4. Bağımsız kanıt geldikten sonra eşik, başarısızlık ve tekrar koşu politikasını
   v1 sözleşmesine sabitleme.

### v1.0 kabul kapıları

- Kararlı ve belgelenmiş public skill/command sözleşmesi.
- Otomatik davranış eval'leri; başarısız eval'de yayın engeli.
- En az bir bağımsız kullanıcıdan tekrar üretilebilir kurulum ve görev kanıtı.
- Sürüm etiketi, release notes, kurulum ve geri alma tatbikatı.

Makine-okunur ayrıntı `registry/v1-gates.json`, insan/Wiki görünümü
`docs/V1-Hazirlik.md` dosyasındadır. Bütün kapılar `passed` olmadan v1 denmez.

### Uzun vade

- **v2.0:** Talep ve güvenlik gerekçesi oluşursa isteğe bağlı hosted ürün/MCP;
  çekirdek açık ve yerel kalır.

## Durum Günlüğü
- 2026-07-21: v0.13.0 local release candidate prepared after 223 tests (2
  platform-specific skips), Ruff, mypy, Clean Code, actionlint 1.7.10,
  skills-ref 0.1.1 validation of 41 skills, and Claude Code 2.1.212 validation
  of the marketplace plus five packages. The 1280x640 social preview is
  release-tracked and under 1 MB. No PR/main/ruleset/tag/Release/global-host
  claim is made yet; v1 remains 7/8.
- 2026-07-20: v0.12.1 sonrası yeni worktree'de Windows salt-okunur dizin
  özniteliği `shutil.rmtree` son adımını engelledi. Hata gerçek ortamda
  üretildi. İlk tüm-ağaç yaklaşımının junction üzerinden kök dışına çıkabildiği
  bağımsız incelemede gerçek testle yakalandı ve reddedildi. Son çözüm yalnız
  `rmtree` hatası veren gerçek yolu düzeltir; symlink/junction üzerinde fail-closed
  kalır. İki Windows regresyon testi v0.12.2'ye eklendi.
- 2026-07-19: Clean Code denetimi başlatıldı. Başlangıçta 87 test/Ruff/mypy
  temizdi; repo kodlama sözleşmesi ve cache kapısı yoktu, üç çekirdek fonksiyon
  McCabe 25'i aşıyordu. ADR 0003; güvenli allowlist temizliği, UTF-8/LF ve
  davranış-korumalı sınırlı parçalama yaklaşımını seçti. Aktif rollback yedeği
  kullanıcı verisi kabul edilerek korunacaktır.
- 2026-07-19: Hijyen uygulaması 99 teste çıktı; UTF-8/BOM/mojibake, LF, metin
  subprocess encoding'i ve allowlist cache temizliği otomatik kapıya bağlandı.
  McCabe 25'i aşan validate/rollback/v1 akışları tek-sorumluluk adımlarına
  ayrıldı. Sürüm hazırlayıcının tarihsel v0.12.0 eval kaydını körlemesine
  v0.12.1'e çevirdiği yakalandı; `version_patterns` regresyon sözleşmesi güncel
  yüzeyi yükseltirken tarihsel provenance'ı koruyor. Bağımsız ilk incelemenin
  LF, subprocess alias/kodlama, ana doğrulayıcı entegrasyonu ve atomik yayın
  bulguları test-first kapatıldı; depo dışı symlink ile `.worktrees` taraması da
  sertleştirildi. İkinci incelemenin örtük subprocess metin modu ve bozuk Python
  kaynağında çökmeden raporlama bulguları da regresyon sözleşmesine dönüştü.
  Rollback'in kendisi başarısız olursa korunan kurtarma yedeğinin tam yolu hata
  raporuna yazılır.
- 2026-07-19: v0.12 kanıt zinciri adayı Windows/Codex kurulum sözleşmesini gerçek
  PowerShell yaşam döngüsü testiyle eşitledi: 41 skill kuruldu, çakışan skill
  yedeklendi, kayıtla kaldırıldı ve kullanıcı dosyası geri yüklendi. Gerçek eval
  sonuçları artık redakte edilmiş ajan/hakem/sürüm/commit/ortam provenance'ını
  kamu sonucuna yazabiliyor; kör eşleme ayrı kalıyor ve `sk-` benzeri değerler
  reddediliyor. Bu mekanik iyileştirme dış v1 kapılarını kapatmaz; gerçek
  ajan+hâkim ve bağımsız kullanıcı kanıtı beklemeye devam eder.
- 2026-07-18m: v0.11.1 PR #14 dört kapıdan geçti ve `731db9d7` ile `main`e
  birleşti. Pages ile Wiki canlıda v0.11.1 döndürdü; değişmez tag aynı commit'e
  bağlı ve GitHub Release HTTP 200 verdi. Yayın sonrası teftiş, sürüm hazırlama
  sırasında durum sayfasında kalan eski v0.11.0 SHA'sını yakaladı; gerçek
  v0.11.1 SHA'sıyla düzeltildi ve kanıt `.divan/evidence/` altına işlendi.
- 2026-07-18l: Claude Code devralma açığı kapatıldı. Kök `CLAUDE.md`, ajanı
  AGENTS→BLUEPRINT→progress→yayın/v1 kayıtlarına bağladı; `scripts/handoff.py`
  ve regresyon testleri eksik zinciri reddeder. SessionStart aynı sözleşmeyi
  gösterir. CODEOWNERS ile Actions Dependabot eklendi; ruleset, secret scanning,
  push protection ve CodeQL'nin GitHub ayarı olduğu dürüstçe açık bırakıldı.
  v0.11.1 sağlamlaştırması dış kanıt isteyen iki v1 kapısını değiştirmez.
- 2026-07-18k: v0.11.0 yayın kontrol düzlemi uçtan uca kendini kanıtladı. PR #12
  üzerinde beş workflow; yeni `uyumluluk` matrisinde Claude Code + Ubuntu,
  macOS ve Windows Codex kur-keşfet-kaldır işleri geçti. PR `5680337a` ile
  `main`e birleşti. Ana dalda yedi iş akışı yeşil oldu; `release` #1 bütün
  doğrulayıcılar, canlı Pages/Wiki readback ve Chromium tıklamasından sonra
  v0.11.0 tag/GitHub Release'i aynı commit'te yayımladı. Public API etiketi,
  release'in draft/prerelease olmadığını ve canlı yüzeylerin v0.11.0 olduğunu
  yeniden doğruladı. v1 karnesi 6/8'e çıktı; yalnız gerçek ajan/hakem ile
  bağımsız kullanıcı kanıtı kaldı.
- 2026-07-18j: Kullanıcının “kitap/Release dahil her yeri her seferinde ben mi
  hatırlatacağım?” itirazı kalıcı ürün gereksinimine çevrildi. GitHub Docs
  üzerinden `GITHUB_TOKEN` en az yetki ve recursion davranışı doğrulandı.
  `release-manifest.json` + `scripts/release.py` tek komutlu sürüm hazırlığı,
  yüzey sapma kapısı ve CHANGELOG kaynaklı release notu kurdu. `release`
  workflow'u `main` sonrası Pages/Wiki sürümünü bekleyip tag/Release oluşturur;
  etiketi asla taşımaz. Claude Code doğrulaması ile Linux/macOS/Windows Codex
  kur-keşfet-kaldır tatbikatı ayrı uyumluluk matrisine bağlandı. Sekiz kapılı
  v1 defteri ve Wiki karnesi, bağımsız kabul formu ve `/yayin` eklendi. Gerçek
  ajan/hakem ile dış kullanıcı kanıtı dürüstçe açık bırakıldı.
- 2026-07-18i: Repo sahibi ilk Wiki Home sayfasını kaydetti; canlı raw adres
  HTTP 200 ve varsayılan “Welcome to the divan wiki!” içeriğiyle okundu. Böylece
  `divan.wiki.git` başlangıç kapısı açıldı. README canlı Wiki bağlantısına geçti;
  PR #10 üç yeşil kapı sonrası `b19e6cca` ile `main`e birleşti. `wiki-sync` #8,
  Wiki commit `ebbbf66` ile 16 dosya/652 satır yayımladı; canlı readback v0.10.3
  ve “Fermanını seç” metnini doğruladı. `teftis` #59, `site-testi` #29 ve Pages
  #21 de geçti; Wiki artık canlıdır.
- 2026-07-18h: GitHub, Wiki, Context7, güncel Codex kılavuzu ve Mühürdar birlikte
  teftiş edildi. Canlı Wiki 404 ve `divan.wiki.git` yokluğu yeniden doğrulandı;
  GitHub'ın ilk sayfa şartı birincil dokümandan bulundu. Katalogda `claude-api`
  açıklamasını `/-…` gösteren çok satırlı YAML hatası ve gerçekte var olmayan
  “otomatik üretilir” iddiası düzeltildi. 41 kaydı deterministik üreten ve farkı
  CI'da kıran katalog kapısı eklendi; Actions major sürümleri güncellendi. PR #8
  dört yeşil kapı sonrası `6706952c` ile `main`e birleşti. Ana dalda `teftis` #53,
  `site-testi` #26, `meclis` #4 ve Pages #19 geçti; `wiki-sync` #6 eksik ilk
  sayfayı yeni açıklayıcı hata mesajıyla doğru biçimde durdurdu.
- 2026-07-18g: `punkpeye/awesome-mcp-servers` karşılaştırması Divan'ın asıl
  eksiğini gösterdi: güçlü kürasyon vardı fakat kamusal ve sürekli aday üretim
  çarkı yoktu. 3.012 GitHub girdili indeksin katkı/otomasyon fikri REFERENCE
  kararıyla alındı; downstream içerik alınmadı. Aday Meclisi defteri, formu,
  doğrulayıcısı ve haftalık salt-okunur keşif nöbeti kuruldu. Kaynak Küratörü
  hiçbir adayı otomatik kurmayan kalıcı yaşam döngüsünü aldı. PR #6'nın dört
  kapısı yeşil geçti; squash commit `70cde896` ile `main`e birleşti. Ana dalda
  `meclis` #2, `teftis` #47, `site-testi` #23 ve Pages #17 başarılı oldu.
  `wiki-sync` #4 ise önceden kayıtlı ilk-Wiki-sayfası engelini yeniden yakaladı.
- 2026-07-18f: Varsayılan “Welcome to the divan wiki!” yüzeyi teslim açığı
  sayıldı. `docs/*.md` tek doğru kaynağından 14 sayfa + kenar çubuğu üreten
  manifest/derleyici, PR teftişi ve `main` sonrası Wiki Git deposuna yazıp canlı
  sürümü yeniden okuyan `wiki-sync` kuruldu. OpenAI/Codex runtime-skill sınırı
  güncel resmi kaynaklarla belgelendi; Mühürdar Wiki'nin kanıt bekçisi olarak
  tanımlandı. Sadrazam aynı hatayı önleyen Bilgi Yüzeyleri Kanunu'nu aldı.
  `main` sonrası yayın kapısı Wiki Git deposunun ilk sayfa UI'da kaydedilmediğini
  `Repository not found` ile yakaladı; canlı Wiki bu tek seferlik adıma kadar
  doğrulanmış sayılmıyor.
- 2026-07-18e: v0.10.0 yayın zinciri — PR #3'te `teftis` #37 ve dalın `docs/`
  önizlemesini gerçek Chromium'da tıklayan `site-testi` #13 geçti; squash commit
  `361a6d67` ile `main`e birleşti. İlk site koşusunun yakaladığı geniş protokol
  seçicisi aynı PR'da daraltıldı. Site CI her `main` push'ında Pages sürümünü
  bekleyip canlı etkileşimi yeniden tıklayacak şekilde kalıcılaştırıldı.
  Etiketli GitHub release oluşturulmadı.
- 2026-07-18d: v0.10.0 vibe coder yüzeyi ve eval koşucusu — beş yaygın
  niyetten en küçük paket, kopyalanabilir ferman ve teslim akışına giden seçici
  eklendi. Dört özgün skill'deki 12 vaka; aynı promptlu baseline/skill koşusu,
  A/B körleme, opsiyonel hakem/eşik ve makine-okunur kanıt üreten sağlayıcı-
  bağımsız koşucuya bağlandı. PR site testi artık eski canlı yerine dalın
  `docs/` önizlemesini gerçek Chromium'da denetliyor.
- 2026-07-18c: v0.9.0 yayın zinciri tamamlandı — PR #1 taslaktan çıkarıldı;
  `teftis` #29 ve `site-testi` #8 geçti; squash commit `6893e804` ile `main`e
  birleşti. Varsayılan dal ve GitHub Pages yeniden okunarak v0.9.0/41 vezir
  vitrini doğrulandı. GitHub tag/release olmadığı açıkça kaydedildi.
- 2026-07-18b: v0.9.0 yayın disiplini — canlı `main`in v0.7'de kaldığı ve
  v0.8.2 işinin taslak PR'da beklediği doğrulandı. PR'ı teslim sayan varsayım
  kaldırıldı; Türkçe+İngilizce vitrin, CHANGELOG, VERSION, kalıcı plan/ADR ve
  Yayın Kanunu eklendi. Yeni özellik nedeniyle SemVer minor sürüme geçildi.
- 2026-07-18: v0.8.2 — “100 Claude Repos” paylaşımındaki sağlanan 40 bağlantı
  çözüldü; 6 bulunamayan, 2 arşivli ve 1 yinelenen kanonik hedef belgelendi.
  Toplu kurulum reddedildi; özgün `kaynak-kuratori` ve üç eval eklendi. 41 vezir.
- 2026-07-17p: v0.8.1 — kanıtlı repo araması, bağlam bütçesi/maskeleme ve
  skill'li-baseline eval protokolü eklendi. 40 vezir.
- 2026-07-17o: v0.8 yerel orkestrasyon — Claude Code, Codex ve yedi aday
  birincil kaynaklarla yeniden incelendi; ağırlıklı puan kartı oluşturuldu.
  Harici harness bağımlılığı reddedildi. `ordu-nizami` ve `/sefer` ile Ocak →
  Sefer → Ordu kademeleri, worktree sahipliği ve deneysel Agent Teams sınırları
  ürüne işlendi. 38 vezir.
- 2026-07-17n: v0.7.1 sağlamlaştırması — Agent Skills resmî doğrulayıcısının bulduğu 1024+ açıklama düzeltildi; 37 skill üç katmanlı CI'a alındı; otomatik git init/commit ve sessiz üzerine yazma kaldırıldı; Codex kurucuları yedek+manifestli yapıldı; upstream nöbeti SHA-256 ve simetrik karşılaştırmaya geçti; belge/lisans/site sayıları eşitlendi.
- 2026-07-17m: PADİŞAH DÜZELTMESİ — vitrin (README/katalog/landing) v0.3te kalmıştı, v0.7 gerçeğine eşitlendi. Bir daha olamaz: teftiş v4 vitrin tutarlılığını denetliyor (katalog sayısı, paket adları, komutlar READMEde yoksa CI KIRILIR); sadrazama Vitrin Kanunu eklendi.
- 2026-07-17l: Kural Hazinesi seferi — awesome-cursorrules (CC0, lisans bizzat okundu) hazinesinden kürasyonla kural-hazinesi veziri; Karpathy-skills LİSANSSIZ çıktığı için REDDEDİLDİ, yerine özgün temkin veziri (4 ihtiyat ilkesi) yazıldı. 37 vezir.
- 2026-07-17k: Keşif raporu işlendi — MÜŞAVİR veziri (stack danışmanı: proje türüne göre 2026 varsayılanları + tazelik protokolü) ve AYLIK NÖBET (upstream değişim bekçisi: cron + otomatik issue) eklendi. v0.6 vendoring hedef listesi BLUEPRINTe girdi. 35 vezir.
- 2026-07-17j: SEFERBERLİK — ordu 15ten 34 vezire çıktı: core-pack +7 (superpowers MIT), yeni zanaat-pack 7 (Anthropic Apache, Ehl-i Hiref), react-pack +5 (Vercel MIT). İki name/klasör uyumsuzluğu giderildi; o tarihte yapılan gereksiz açılı-ayraç yamaları v0.7.1'de upstream'e döndürüldü. 5 paket.
- 2026-07-17i: Codex tek-komut kurulum scriptleri (kur-codex.ps1 Windows / kur-codex.sh unix) eklendi; git gerektirmez (zip indirir). Kurulum belgesi güncellendi.
- 2026-07-17h: Canlı upstream denetimi — 12 taşınan vezirin 12si bugünkü kaynaklarla birebir (tek fark bilinçli spec yaması, UPSTREAM.md tablosunda belgeli). Komut/subagent çakışması yok. docs/Kaldirma.md (komple kaldırma rehberi) eklendi.
- 2026-07-17g: 8-katman karnesine göre eksikler kapandı - subagents (kâşif: keşif öncüsü, müfettiş: bağımsız denetçi) ve hooks (SessionStart: defteri otomatik oku) eklendi; teftiş v3 bunları da denetliyor; docs uyumluluk matrisi. Sadrazam v0.4.0.
- 2026-07-17f: Hafıza katmanı geldi — defterdar skill'i (AGENTS.md+BLUEPRINT+.divan/ nizamı, 4 şablon), /defter komutu, Sadrazam'a zorunlu kayıt nizamı, para-dokunan işlere spec-first+risk-register kuralı. Sadrazam v0.3.0. Dünya standardı boşluk analizi raporuna dayanır.
- 2026-07-17e: Akıl sayfaları (Değer, GitHub Kullanımı, Test ve Teftiş) docs/ altına; gerçek Playwright testi tests/site_testi.py yazıldı, canlıda TEMİZ geçti; haftalık site-testi CI eklendi. Wiki push GitHub kısıtı yüzünden bekliyor (ilk sayfa UI ister).
- 2026-07-17d: İlk vizyondaki komutlar tamamlandı (/ferman, /vezir, /teftis); GitHub Pages, Discussions, issue etiketleri açıldı. Upstream tamlık doğrulandı (birebir).
- 2026-07-16: v0.1 derlendi (vibeforge → Divan rebrand, Sadrazam yazıldı,
  landing yayında). GitHub push token bekliyor.
- 2026-07-17c: Teftiş v2 iki gerçek Vercel skill klasör-ad uyuşmazlığı yakaladı. Aynı turdaki açılı-ayraç yasağı varsayımının Agent Skills standardında olmadığı v0.7.1'de resmî doğrulayıcıyla teyit edilip düzeltildi. Wiki içeriği docs/ altında; GitHub wiki ilk sayfa açılınca aynalanacak.
- 2026-07-17b: Topluluk dosyaları (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, şablonlar), UPSTREAM.md ve vezir-yetistirme meta-skill eklendi.
- 2026-07-17: Teftiş script'i + CI + BLUEPRINT eklendi. SEO güncellemesi
  site/index.html'de hazır; push sonrası canlıya alınacak.

## Sıradaki Kesin Adım

Run an independent whole-branch review, fix every Critical and Important
finding, then deliver v0.13.0 through a green PR/main/public-release chain.
Only after main checks are observed may the main ruleset be applied. Keep v1 at
7/8 until a non-owner submits reproducible acceptance evidence.
