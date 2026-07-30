# Divan İlerleme Defteri

Son güncelleme: 2026-07-30

## Yayın durumu

- Latest published release: v0.18.4
- Published commit: 2eb36bdd24e383c90e1e62e53ad1c6c5d5730000
- Publication evidence: .divan/evidence/teftis-20260730-v0184-release.md
- Release asset evidence: .divan/evidence/teftis-20260730-v0184-release.md
- Release idempotency evidence: .divan/evidence/teftis-20260725-release-idempotency.md

## Güncel hedef

The latest published release is v0.18.4 at immutable commit `2eb36bd`.
PR #64 published real VERIFIED evidence binding, plan-only proof rejection,
distinct-project policy v2, and focused bug-fix routing. All nine required
main/publication workflows passed. Seven release assets were downloaded again,
their SHA-256 values matched, strict attestations passed, and Pages plus Wiki
returned v0.18.4.

Divan remains one product and one repository. Divan Engine is the canonical
stdlib-only modular core; Divan Nizamı is the owner-first governance model; the
installed layer is Divan Project Contract / Divan Proje Sözleşmesi. Hükümdar is
the final authority and only `owner` may expand scope. Legacy Company OS,
Project OS, `/company`, `company-validate`, and Python/JSON paths remain bounded
compatibility surfaces through v1. Issue #34 now targets machine-verifiable
clean-room evidence rather than operator identity. The schema-2 mechanism is
published, but no reviewed receipt from the released mechanism is committed,
so v1 remains 7/8.

The first released-runner clean-room attempt reached the real goal and bounded
test plan, then failed closed while observing the Codex version. Windows found
an extensionless npm shim that returned access denied even though the adjacent
`codex.cmd --version` command passed. v0.18.5 resolves the runnable Windows
command shim explicitly before retrying the same released-runner proof.

## Yapıldı

- Schema-1 adoption receipts remain verifiable with explicit non-v1 statuses.
  Schema-2 adds an immutable-release, distinct-project, verified-goal,
  observed-host, bounded-check, source-stability, privacy, and offline-digest
  contract. `adoption prove` previews without writes/processes; `--execute`
  runs the fixed host probe and safe checks once before atomically sealing
  evidence. Maintainer/external role does not affect eligibility.
- Issue #57 adds safe process probing,
  explicit profile selection, canonical fallback execution, exact 41-skill
  manifest verification, per-skill installed SHA-256 verification, a rollback
  command, and user-facing native/fallback limits. Plain native installation
  remains unchanged and invalid host JSON fails closed. Host parsing, output,
  diagnosis, profile policy, and lifecycle execution are separate modules; the
  registered install-function complexity and length debt was removed. PR #58
  merged at `f367de92e09b4f56e205d7e2883d988b3b4d2797`; release workflow
  `30500376337`, all required workflows, immutable assets, strict SLSA
  verification, and the isolated remote Windows lifecycle canary passed.
- PR #55 merged the v0.18.0 release preparation to `main` at
  `3bbbd95881a7c33f64e3e9f8d23824e3eef8977e`. Release workflow
  `30493811167` published immutable tag/Release v0.18.0. All five downloaded
  asset digests matched GitHub and both checksum manifests; the ZIP reports
  0.18.0, the SBOM is SPDX 2.3, and the portable runner validates. Every asset
  has one verified SLSA provenance record and API-visible release/v0.2 plus
  SLSA provenance/v1 attestations. All eight main/publication workflows passed.
- PR #54 merged Nizâm-ı Sefer to `main` at
  `7c674874503853216dc8f2abddaa0459811a5ee6`. Its required CI passed 562 tests
  with 11 expected platform skips and 75% coverage plus the cross-platform
  compatibility matrix, CodeQL, dependency review, Playwright, and Wiki/Pages
  checks. Two independent read-only reviews were completed and every reported
  P1/P2 finding was addressed before merge.
- Nizâm-ı Sefer now compiles intent into a deterministic dependency graph,
  structural risk, an explicit context-budget authority, portable model
  classes, at most three bounded sefers, durable handoff, and goal-bound
  `route.json`. Unknown or conflicting hosts fail safe to sequential work;
  environment values are not persisted and exact model availability requires
  host confirmation. Focused tests, public guides, skills, impact obligations,
  and release surfaces are synchronized in the published release.
- ADR 0008 and the v0.17.1 specification define one Vibe Progress Protocol.
  Sadrazam and all seven public chat commands point to the same loaded-plugin
  root contract. README, Wiki, Pages/site source, and the vibe-coder guide
  explain the user benefit and the contract-only evidence boundary. The clean
  Windows candidate passed the canonical verifier with 544 tests and 14
  platform-specific skips; 5 packages, 41 skills, and 151 release surfaces
  matched. Independent whole-change review reported no open P0-P3 findings and
  approved the local release gate. The nine-module runtime, Hükümdar authority
  order, compatibility paths, and v1 7/8 status remain unchanged.
- PR #49 merged v0.17.0 to `main` as
  `8b711b6f0ebb696ce971d83c90833bb59acf3c34`. Seven PR workflows and nine
  main/publication workflows completed successfully. Release workflow
  `30453034011` published immutable tag/Release `v0.17.0`; all five downloaded
  asset digests, both checksum manifests, SPDX 2.3 metadata, the schema-2 runner
  envelope, and two attestations per asset matched. Pages returned HTTP 200 and
  Wiki exposed the Divan Engine and Hükümdar-first contract. Exact evidence is
  `.divan/evidence/teftis-20260729-v017-release.md`.
- The v0.17.0 implementation passed 538 tests with 7 platform-specific skips and
  76% coverage. Ruff, mypy, Clean Code, 41/41 Agent Skills, the root
  marketplace plus five plugins under Claude Code 2.1.212 strict validation,
  local Chromium site verification, and two byte-identical project-runner
  builds passed. Independent review findings for ambient module-cache spoofing,
  pre-resolve runtime path identity, and dynamic imports were addressed
  test-first. Final independent re-review reported no open P0-P3 findings and
  approved the local release gate.
- Issue #33 was closed by merged PR #46 at `5f7f088`. The canonical verifier
  keeps generated caches outside the checkout and ends with a clean hygiene
  check on Windows as well as CI hosts.
- PR #39 merged the issue #38 release-idempotency repair as `da5c2a7c`.
  Main release run `30131579254` passed all three clean hosts, skipped duplicate
  attestation, and verified all five v0.16.0 assets byte-for-byte from the
  immutable tag. The tag, five SHA-256 digests, and two attestations per asset
  remained unchanged. Evidence is tracked in
  `.divan/evidence/teftis-20260725-release-idempotency.md`.
- PR #31 merged v0.16.0 to `main`; tag `v0.16.0` points to
  `5513e73d5faa8657a22d813ecfec763a6089bea0`. The Release page returned HTTP
  200 and live Pages/Wiki readbacks contained v0.16.0. Bounded evidence is
  tracked in `.divan/evidence/teftis-20260725-v016-publication-handoff.md`.
- All five v0.16.0 Release assets were downloaded again and their SHA-256
  values matched the GitHub asset digests and published checksum manifests.
  The SPDX 2.3 SBOM, runner source envelope, release/SLSA attestations, release
  workflow, Pages, and Wiki readbacks are tracked in
  `.divan/evidence/teftis-20260725-v016-release-assets.md`.
- The post-merge evidence branch passed 495 tests with 11 platform skips, 74%
  branch coverage, Ruff, mypy across 61 source files, Clean Code, release,
  handoff, Wiki, Company OS, and eval contract checks. v1 remains 7/8.
- Schema 2 config and install state bind immutable version/ref/commit, project
  identity, and managed whole-file/marked-block payload hashes.
- `project status` is read-only; `project update` and `project repair` are
  dry-run-first and reuse the proven lock, ACL, journal, authority, marker,
  rollback, and recovery transaction boundary.
- Verified goals archive with bound hashes and controlled source removal.
  Adoption export writes redacted JSON/Markdown and distinguishes
  `valid-owner-canary` from `valid-independent-declaration`.
- The deterministic project runner, impact graph, DCS-007, README, Project OS,
  install, Wiki, changelog, blueprint, and publication manifest include the new
  lifecycle while 5 packages/41 skills and v1 at 7/8 remain unchanged.
- Ruff, mypy, coverage, and Clean Code now measure the first-party Company OS
  runtime; previously invisible exact module/function/complexity debt is pinned
  in the ratchet and cannot increase without failing CI.
- Whole-branch review approved the Project OS candidate at `1a94b61` after
  provider, SEO, initialization, recovery, and mutation-authority findings were
  closed test-first.
- Portable Project OS now provides dry-run-first initialization, deterministic
  goals/specs/plans/tasks, append-only receipts, `DPS-001..DPS-012`, bounded
  monorepo discovery, Unicode English/Turkish routing, multi-workflow planning,
  fail-closed impact classification, and provider-native release evidence.
- Public-web projects receive scoped SEO/accessibility policy, static metadata
  checks, pinned Lighthouse CI/Lychee plans, and provider-bound live evidence;
  irrelevant web standards are not forced on libraries or services.
- English canonical Project OS, Company OS, Community Standards, README, Wiki,
  Pages/site, install, workflow, and release surfaces are synchronized with
  first-class Turkish localization.
- `python scripts/release.py --prepare 0.15.0` updated only deterministic version
  surfaces. Preflight passed 452 tests with 10 platform-specific skips, Ruff,
  mypy, Clean Code, and 71% coverage; five packages/41 skills and v1 at 7/8
  remain unchanged.
- The failed v0.14.0 dual-host upgrade rolled back automatically and both hosts
  were re-proven healthy at v0.12.2 before development continued.
- Codex's isolated native metadata file is now accepted through its existing
  schema, source, ref, revision, UTF-8, and symlink checks even when Codex also
  reports the marketplace ref. Additional dirt remains rejected.
- Company OS now maps natural-language intent to 12 functional roles, 8
  workflows, detected frameworks, the smallest justified pack set, and
  transitive documentation/Wiki/site/release effects.
- `scripts/divan.py` is the canonical English CLI. Existing Turkish script
  names are narrow deprecated compatibility aliases until v1.
- DCS-011, naming policy, English canonical README/contribution surfaces,
  Turkish locale files, Company OS docs, Pages, Wiki, CI, and release manifest
  are synchronized.

- v0.13.0 introduced DCS-001..DCS-010 as a machine-readable contract, a Clean
  Code debt ratchet, dual-host doctor/transactional upgrade, SPDX supply-chain
  evidence, and synchronized community/public documentation.
- Final local integration passed 223 tests with 2 platform-specific Windows skips;
  Ruff, mypy, Clean Code, actionlint 1.7.10, 41 skills via skills-ref 0.1.1, and
  the Claude marketplace plus five packages via Claude Code 2.1.212 passed.
- The generated 1280x640 RGB social preview is 908422 bytes and is now checked
  by the release manifest without adding an image runtime dependency.

- PR #21 bütün CI kapılarından geçti ve `c226dccf` ile `main`e birleşti.
  Release workflow `29705195263`; tag/Release, ZIP+SHA-256, Pages, Wiki ve canlı
  Chromium doğrulamasını başarıyla tamamladı.
- Sabit v0.12.2 kaynağı Claude ve Codex'e global kuruldu. Her host 5 paket/41
  skill ve doğru source/ref döndürdü; alakasız eklentiler korundu. Doğrulanmış
  işlem: `install-20260719T215712Z-c9095665.json`.
- Windows salt-okunur `__pycache__` hatası gerçek worktree'de üretildi;
  yalnız hata veren gerçek yolu yazılabilir yapıp junction/symlink üzerinde
  fail-closed kalan düzeltme iki Windows regresyonuyla test-first uygulandı.
- PR #19 bütün CI kapılarından geçti ve `4125c31e` ile `main`e birleşti.
  Release workflow `29704548820`; v0.12.1 tag/Release, ZIP+SHA-256, Pages, Wiki
  ve canlı Chromium doğrulamasını başarıyla tamamladı.
- Sabit v0.12.1 kaynağı Claude ve Codex'e global kuruldu. Her host 5 paket/41
  skill ve doğru source/ref döndürdü; alakasız eklentiler korundu. Doğrulanmış
  işlem: `install-20260719T213732Z-5a357853.json`.
- v0.12.1 hijyen kapsamı test-first tamamlandı: UTF-8/BOM/mojibake taraması,
  locale-bağımsız text subprocess kuralı, allowlist cache temizliği,
  `.editorconfig`/`.gitattributes` ve Ruff C90 McCabe 25 kapısı eklendi.
- `validate.denetle`, `rollback_transaction` ve v1 gerçek-kanıt doğrulaması
  aynı davranışı koruyan isimli sorumluluklara ayrıldı; 99 test yeşile geldi.
- Bağımsız kod incelemesindeki LF, subprocess alias/kodlama, hijyen
  entegrasyonu ve atomik yayın bulguları test-first kapatıldı; repo dışı
  symlink ve gereksiz worktree yürüyüşü de sertleştirildi.
- İkinci bağımsız incelemede önemli bulgu kalmadı. Tek küçük geri bildirim olan
  başarısız rollback yedeğinin tam kurtarma yolu da test-first rapora eklendi.
- Açık PR bulunmadığı doğrulandı; birleşmiş PR'lara ait 15 artık uzak `codex/*`
  dalı kalıcı silindi. Sahipliği belirsiz `claude/*`, `main` ve aktif dal korundu.
- Kapanmış PR #17/#16'nın yerel ve uzak dalları kaldırıldı. Ana repo ve aktif
  rollback yedeğindeki yalnız `__pycache__` içeriği kalıcı silindi; manifestin
  işaret ettiği gerçek kullanıcı skill yedeği korundu.
- Yayın hazırlayıcının geçmiş sürüm kayıtlarını kör replace etmesi regresyon
  testiyle düzeltildi. v0.12.1 güncel yüzeyleri değişirken v0.12.0 gerçek eval
  provenance'ı tarihsel olarak kalır.
- v0.12.0 ürün kapsamı tamamlandı: Claude ve Codex için aynı 5 paket/41 skill'i
  sunan yerel pazarlar, dry-run-first işlemsel kurucu, yalnız kendi kayıtlarını
  geri alan rollback ve alakasız eklentileri koruyan fixture testleri eklendi.
- Eski kopyalama fallback'i değişmez release varlığı + SHA-256 doğrulamasına
  geçirildi; manifest sürüm/ref/commit/hash/zaman/hedef/yedek kaydeder. Release
  workflow'u arşiv, checksum ve source commit yayınlayacak şekilde hazırlandı.
- Bütün GitHub Actions tam commit SHA'sına sabitlendi; CodeQL, Ruff, mypy,
  Coverage ve actionlint kapıları eklendi. Yerel taban 46 test ve %61 branch
  dahil coverage ölçümüdür; bu bir davranış kalite artışı iddiası değildir.
- Site skip link, tek main landmark, 4.5:1+ mercan kontrastı, reduced-motion ve
  mobil/yatay taşma kontrolleriyle gerçek Chromium'da geçti.
- Kök lisans kanonik MIT oldu; NOTICE ayrıldı. Güncel upstream HEAD'lerinde
  bulunan 15 fark tek tek commit + yerel ağaç SHA-256 + KEEP gerekçesiyle
  `registry/upstream-baselines.json` defterine işlendi; nöbet yeniden temizdir.
- Claude Code gerçek ajan ve read-only/ephemeral kör Codex hakem adaptörleri
  eklendi. Fixture'lar izolasyon, körlük, JSON şeması ve sır maskelemeyi kanıtlar;
  gerçek model koşusu ayrıca yayımlanabilir provenance ile tamamlandı.
- Claude Code 2.1.209 ajanı ve Codex CLI 0.144.4 kör hakemiyle üç
  `baglam-muhafizi` vakası sabit modellerle gerçek çalıştırıldı. Kamu sonucunda
  skill 0, baseline 1 kazandı, 2 beraberlik çıktı; önceden eşik tanımlanmadığı ve
  skill galibiyeti bulunmadığı için kalite artışı iddiası yapılmadı.
  `evals/results/claude-codex-baglam-muhafizi-v012.json` kanıtıyla v1 karnesi
  7/8'e çıktı.
- PR #17 bütün kontrollerden geçti ve `e9a2642e` ile `main`e birleşti. Ana-dal
  teftişi, CodeQL, üç işletim sistemi uyumluluk matrisi, Pages, Wiki ve canlı
  Chromium testi yeşildir. v0.12.0 etiketi aynı commit'e bağlı; GitHub Release
  arşivi ile checksum'u yayımlandı ve SHA-256 yeniden eşleşti.
- Sabit `v0.12.0` kaynağı dry-run sonrasında Claude Code/Desktop Code ve Codex'e
  global native marketplace olarak kuruldu. İki hostta 5 paket/41 skill enabled;
  önceki 2 Claude ve 11 Codex eklentisi ile bütün eski marketplace'ler korundu.
  Tam kayıt `.divan/evidence/teftis-20260719-v012-release-install.md` dosyasındadır.
- v0.11.1 için kök `CLAUDE.md` devralma sözleşmesi eklendi; Claude Code sohbet
  geçmişi olmadan AGENTS, BLUEPRINT, progress ve yayın/v1 kayıtlarına gider.
- `scripts/devral.py --check` ve regresyon testleri hafıza zincirini denetler;
  Sadrazam SessionStart hook'u sözleşmeyi ve defteri gösterir.
- GitHub Actions Dependabot ve CODEOWNERS eklendi. Ruleset/branch protection,
  secret scanning, push protection ve CodeQL platform doğrulaması bekler.
- PR #14 `teftis`, `uyumluluk`, `wiki-sync` ve `site-testi` kapılarından geçti;
  `731db9d7` ile `main`e birleşti. Canlı Pages/Wiki v0.11.1, tag aynı commit ve
  GitHub Release HTTP 200 olarak yeniden okundu.
- Yayın sonrasında durum sayfasında kalan eski v0.11.0 commit SHA'sı yakalandı;
  v0.11.1 gerçek SHA'sı `731db9d7` ile düzeltildi ve kanıt kaydı eklendi.

- Canlı `main` README'sinin 37 skill/v0.7 döneminde kaldığı doğrulandı.
- PR #1'in önce v0.8.2/41 skill içerdiği, yeşil fakat taslak olduğu doğrulandı;
  yayın düzeltmelerinin SemVer karşılığı yeni işlev nedeniyle v0.9.0 oldu.
- Eksik teslimin kök nedeni “PR hazır = yayın tamam” varsayımı olarak belirlendi.
- Yayın tamamlama planı ve ADR kaydı başlatıldı.
- Türkçe README ürün değeri, öz-gelişim döngüsü ve dürüst durumla genişletildi.
- İngilizce README, CHANGELOG ve VERSION eklendi.
- BLUEPRINT geçmiş/gelecek yol haritası ve sıradaki kesin adımla düzeltildi.
- Sadrazam Yayın Kanunu hem Divan paketine hem Work skill'ine işlendi.
- CI; sürüm, iki README, CHANGELOG, BLUEPRINT, kurulum ve progress kaydını
  birlikte denetleyecek şekilde güçlendirildi; yeni regresyon testi geçti.
- PR #1 taslaktan çıkarıldı; `teftis` #29 ve `site-testi` #8 başarıyla geçti.
- PR #1 squash ile `main`e birleşti (`6893e8043518f55f014a61765fc17b7c657ae295`).
- Varsayılan dalda README/TR, README/EN, VERSION, CHANGELOG ve BLUEPRINT
  yeniden okundu; GitHub Pages üzerinde v0.9.0, 41 vezir ve Yayın Kanunu görüldü.
- v0.10.0 vibe coder planı yazıldı; beş niyetli ferman seçici ürün yüzeyine
  eklendi.
- Dört özgün skill'deki 12 vakayı keşfeden; baseline/skill koşusu, A/B körleme,
  opsiyonel hakem/eşik ve JSON kanıt üreten sağlayıcı-bağımsız eval koşucusu
  eklendi.
- Aday Meclisi güvenlik davranışıyla güncel eval toplamı 4 skill / 13 vakadır.
- PR site testi eski canlı sayfa yerine dalın `docs/` önizlemesini test edecek
  şekilde düzeltildi; haftalık canlı nöbet korundu.
- Sadrazam 0.8.0'a niyetten en küçük yola geçiş ve gerçek adaptör olmadan kalite
  iddiasını reddeden Eval Kanunu eklendi; Work skill'i aynı metinle eşitlendi.
- PR #3'te `teftis` #37 ve dalın yerel önizlemesini Chromium'da tıklayan
  `site-testi` #13 başarıyla geçti.
- PR #3 squash ile `main`e birleşti (`361a6d672b9db2519a3e21d5c71ec95db7663b1e`).
- Varsayılan dalda VERSION, iki README, eval koşucusu, site kaynağı, Sadrazam ve
  BLUEPRINT yeniden okundu; v0.10.0 kayıtları eşleşti.
- Site workflow'u her `main` push'ında Pages'in repo `VERSION`ına gelmesini
  bekleyip canlı etkileşimi Chromium'da yeniden tıklayacak şekilde güçlendirildi.
- Boş/varsayılan GitHub Wiki ayrı bir teslim yüzeyi olarak kayda alındı.
- `wiki-pages.json` ve `scripts/wiki.py`, 14 Wiki sayfası ile `_Sidebar.md`yi
  repodaki sürümlü `docs/*.md` kaynaklarından deterministik üretecek şekilde
  eklendi; eksik kaynak, yinelenen slug, kırık Wiki bağlantısı ve sürüm farkı
  teftişi kuruldu.
- `wiki-sync` PR'da kaynağı denetleyecek, `main` sonrası ayrı Wiki Git deposuna
  yazacak ve canlı `Home.md` üzerinde sürümü yeniden okuyacak şekilde eklendi.
- Context7 ve OpenAI'nin güncel resmi rehberleriyle portable Agent Skills ile
  OpenAI Agents SDK runtime'ı arasındaki sınır Wiki'de açıklandı.
- Mühürdar'ın Wiki rolü belgelendi; mevcut ChatGPT Work Mühürdar etkinleştirildi.
- Sadrazam 0.8.1'e Bilgi Yüzeyleri Kanunu eklendi; proje ve Work kopyaları
  aynı metinle eşitlendi.
- `punkpeye/awesome-mcp-servers` bugünkü repo, CONTRIBUTING, MIT lisansı,
  `check-glama.yml`, son commitler ve açık katkı kuyruğuyla incelendi; 3.012
  GitHub girişli bir registry/index olarak `REFERENCE` kararı aldı.
- `registry/candidates.json` Aday Meclisi tek doğru kaynağı; kimlik, mükerrerlik,
  yaşam döngüsü, lisans kanıtı, karar/durum ve inceleme tarihi kapılarıyla kuruldu.
- `scripts/meclis.py`, insan-okunur `docs/Aday-Meclisi.md` dosyasının defterden
  ayrılmasını engelliyor; mükerrer URL ve lisanssız ADOPT regresyon testleri eklendi.
- GitHub kaynak-adayı issue formu ve haftalık salt-okunur keşif workflow'u
  eklendi. Keşif aday kodunu indirmiyor/çalıştırmıyor; yalnız bounded issue açıyor.
- Kaynak Küratörü Meclis yaşam döngüsüyle proje ve Work'te eşitlendi.
- PR #6'da `meclis` #1, `teftis` #46, `site-testi` #22 ve `wiki-sync` #3
  başarıyla geçti; squash commit `70cde8960438840153a47880571e269d37c9abbf`
  ile `main`e birleşti.
- `main` sonrası `meclis` #2, `teftis` #47, `site-testi` #23 ve Pages #17
  başarıyla geçti. `wiki-sync` #4 ilk Wiki sayfası kaydedilmediği için beklenen
  `Repository not found` engelini yeniden doğruladı; canlı Wiki iddiası yok.
- GitHub/Context7/OpenAI/Mühürdar ortak teftişinde canlı Wiki'nin HTTP 404 olduğu,
  kaynak check'inin geçtiği ve publish clone adımının `divan.wiki.git` yokluğunda
  kırıldığı doğrulandı; ilk sayfa şartı GitHub Docs'tan yeniden okundu.
- “Otomatik üretilir” yazdığı halde üreticisi olmayan Vezir Kataloğu için
  `scripts/katalog.py` ve regresyon testleri eklendi. Çok satırlı frontmatter
  yüzünden `claude-api` açıklamasını `/-…` gösteren kullanıcı hatası düzeltildi.
- GitHub Actions checkout/setup-python/setup-node/github-script kullanımları
  resmî depolardaki güncel major sürümlere taşındı; Wiki eksikliği artık tek
  `Save Page` iyileştirme yolunu doğrudan Actions hata mesajında veriyor.
- PR #8'de `wiki-sync` #5, `meclis` #3, `teftis` #52 ve `site-testi` #25 geçti;
  squash commit `6706952ccb9e4c8874593299cda4d1fdd7c2efd7` ile `main`e birleşti.
- Ana dalda `teftis` #53, `site-testi` #26, `meclis` #4 ve Pages #19 geçti.
  `wiki-sync` #6, ilk Home sayfası eksikliğini doğrudan `Save Page` talimatıyla
  durdurdu. Katalog main'den yeniden okunarak 41 kayıt ve doğru `claude-api`
  açıklaması doğrulandı.
- Repo sahibi ilk Wiki Home sayfasını kaydetti. Raw `Home.md` HTTP 200 verdi ve
  varsayılan karşılama metni okundu; `divan.wiki.git` başlangıç engeli kalktı.
  16 sayfalık kaynak paketini yayımlamak için README/Wiki durum değişikliğiyle
  `wiki-sync` yeniden tetikleniyor.
- PR #10'da `wiki-sync` #7, `teftis` #58 ve `site-testi` #28 geçti; squash
  commit `b19e6ccaee534d77a8ca3f0e52e28d38381e0a0d` ile `main`e birleşti.
- Ana dal `wiki-sync` #8, Wiki commit `ebbbf66` ile 16 dosyada 652 satır
  yayımladı ve canlı `Home.md` üzerinde v0.10.3 + “Fermanını seç” readback'ini
  geçti. `teftis` #59, `site-testi` #29 ve Pages #21 de başarılıdır.
- `release-manifest.json` ve `scripts/yayin.py`; tek komutla deterministik sürüm
  yüzeylerini hazırlar, CHANGELOG anlatısını insan sorumluluğunda bırakır ve
  sapmayı CI hatasına çevirir.
- `release` workflow'u yerel/resmî teftişlerden sonra Pages ile Wiki'nin aynı
  sürüme gelmesini bekler; CHANGELOG'dan not üretip tag/Release oluşturur. Mevcut
  etiketi taşımadan yalnız release sayfasını eşitleyerek tekrarlı çalışır.
- Claude Code resmî doğrulaması ve Codex Linux/macOS/Windows kurulum, 41 skill keşfi,
  kayıtlı kaldırma/geri yükleme tatbikatı `uyumluluk` matrisine bağlandı.
- Sekiz kapılı `registry/v1-gates.json`, deterministik Wiki karnesi, bağımsız
  kabul issue formu ve Sadrazam `/yayin` emri eklendi.
- PR #12'nin `teftis` #64, `site-testi` #31, `wiki-sync` #9, `meclis` #5 ve
  yeni `uyumluluk` #1 kapıları geçti; squash commit `5680337a` ile `main`e birleşti.
- Ana dalda `teftis` #65, `uyumluluk` #2, `wiki-sync` #10, `site-testi` #32,
  `meclis` #6, Pages #23 ve `release` #1 başarıyla tamamlandı.
- `release` akışı Linux/macOS/Windows kur-kaldır, bütün yerel/resmî teftiş,
  canlı Pages/Wiki readback ve Chromium tıklamasından sonra v0.11.0 etiketini
  değişmez biçimde `5680337a` commit'ine bağladı ve GitHub Release'i yayımladı.
- Canlı Pages ile Wiki `v0.11.0` + “Fermanını seç” döndürdü; Wiki v1 karnesi
  kayıt sonrası 6/8 geçen kapıyı gösterecek şekilde yeniden üretildi.

## Devam ediyor

- v0.18.5 must publish the Windows host-probe launcher fix. After publication,
  the separate clean-room canary can be initialized with the released runner
  and re-proven with bounded checks. Only a privacy-reviewed
  `valid-clean-room-adoption` receipt may move v1 from 7/8 to 8/8.

## Tarihsel devam kayıtları

The following entries are retained as dated pre-release snapshots. They are not
the current execution queue.

- 2026-07-19: v0.12.1 yüzeyleri hazır. Tam yerel teftiş, bağımsız code review,
  PR/main/Release/Pages/Wiki ve çift-host global kurulum kanıtı sıradadır.
- 2026-07-19: ADR 0003 ve test-first v0.12.1 uygulama planı yazıldı. Sıradaki
  parça hijyen testlerini kırmızıya getirip allowlist temizleyiciyi uygulamaktır.
- Proje sahibi dışındaki bağımsız kullanıcıdan tekrar üretilebilir kurulum ve
  görev kanıtı.
- 2026-07-19: v0.12 kanıt zinciri için tasarım onaylandı. İlk parça Windows
  kurulum–yedek–kaldırma test eşliği ve gerçek eval koşularının provenance
  sözleşmesidir; dış v1 kapıları bu mekanik çalışmayla kapanmayacaktır.
- 2026-07-19: Windows PowerShell kur–yedekle–kaldır–geri yükle tatbikatı gerçek
  geçici dizinlerde 41 skill ile geçti. Eval sonuçları için redakte edilmiş
  provenance sözleşmesi eklendi; 33 test geçti, tam teftiş kanıtı
  `evidence/teftis-20260719-v012-evidence-chain.md` altındadır.

## Bilinen açıklar

- Yayımlanmış runner ile tamamlanan doğrulanmış temiz-proje makbuzu henüz yok;
  başarı veya v1 8/8 iddiası yapılamaz.
- Eski Codex loose skill kopyaları veri kaybını önlemek için korundu. Eski
  manifest sahiplik hash'i taşımadığından güvenli otomatik migration uygulanmadı;
  native Divan paketleri ayrıca kurulu ve doğrulanmıştır.

## Sıradaki kesin adım

Publish v0.18.5, download and verify both portable runners, then rerun
`adoption prove` against the separate clean-room canary. Commit only the
privacy-reviewed schema-2 receipt and re-verify it before changing the v1
score from 7/8 to 8/8.
