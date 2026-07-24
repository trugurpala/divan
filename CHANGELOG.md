# Changelog

All notable changes to Divan are recorded here. The project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses Semantic
Versioning while the public API remains in initial development (`0.y.z`).

## [Unreleased]

### Planned

- Independent adoption evidence and reproducible quality measurements.

## [0.16.0] - 2026-07-24

### Added

- Schema 2 installed-project ownership with immutable Divan source identity,
  project identity, and hashes for every managed whole file or marked block.
- Read-only `project status`, dry-run-first transactional `project update`, and
  intentionally narrow `project repair` commands with fail-closed drift,
  marker, symlink/reparse, stale-plan, and unowned-path handling.
- Verified goal archival with receipt/artifact hash binding, collision checks,
  controlled source removal, and rollback on interrupted application.
- Privacy-bounded JSON and Markdown adoption receipts with explicit
  maintainer/independent declarations and offline verification.

### Changed

- `divan-project.pyz` now carries source metadata schema 2 and the complete
  ownership, lifecycle, archive, and adoption engine while retaining
  deterministic byte-identical builds.
- DCS-007 and the impact graph now cover host lifecycle and installed-project
  lifecycle together. English/Turkish README, Project OS, install, Wiki, and
  publication surfaces distinguish host update, project update, audit, and
  lifecycle status.

### Security

- Project updates run only from the immutable code already executing; they do
  not fetch remote refs or execute target-project code. Install state is written
  last inside the proven locked, journaled, authority-bound transaction.
- Repair never force-overwrites user changes. Adoption exports reject secrets,
  email addresses, usernames, absolute paths, remotes, unrelated plugin
  inventory, and command-output bodies.

### Verified

- The release candidate passed the full local unit suite with 10
  platform-specific skips plus focused lifecycle, archive, adoption,
  reproducible-runner, Unicode, and fail-closed impact tests.
- Five packages and 41 discoverable skills remain unchanged. Owner-operated
  canary evidence is classified separately and cannot close the independent
  adoption gate; v1 readiness remains 7/8.
- This entry records local release preparation only. PR checks, immutable
  `main`, tag, GitHub Release, assets/attestations, Pages, Wiki, canary readback,
  and dual-host global update require separate evidence.

## [0.15.0] - 2026-07-24

### Added

- A portable Project OS contract with deterministic `init`, `inspect`, `audit`,
  `plan`, `impact`, `goal`, `verify`, `release`, and receipt-verification
  routes. Installed projects receive bounded `.divan/` rules, specs, plans,
  tasks, waivers, and append-only evidence without losing existing host text.
- Twelve `DPS-*` installed-project standards, scoped by project type, alongside
  Divan's existing `DCS-*` repository-maintenance standards.
- Unicode-aware English/Turkish intent routing, recursive bounded workspace
  discovery, native package-manager command detection, multi-workflow
  composition, and fail-closed impact classification.
- Provider capability contracts for local, GitHub, Context7, and Vercel
  delivery; a read-only composite action; and a reproducible standalone
  `divan-project.pyz` runner.
- Static public-web SEO contracts covering canonical metadata, robots,
  sitemap, hreflang, social cards, structured data, internal links, and pinned
  Lighthouse CI/Lychee evidence.

### Changed

- Sadrazam can carry a supervised goal from intent through specification,
  planning, verified evidence, preview, release, and live observation while
  keeping provider mutations behind explicit authority.
- English machine interfaces and public technical documentation are canonical;
  Turkish localization remains synchronized and first-class. Existing Turkish
  script names remain bounded compatibility wrappers throughout `0.x`.
- README, Project OS and Company OS guides, Community Standards, Wiki sources,
  Pages/site metadata, install references, and release manifests now share one
  change-impact and publication contract.

### Security

- Project discovery never executes target code, rejects symlink/path escape,
  bounds traversal and input sizes, and reports every unknown changed path as
  `unclassified`.
- Project initialization is dry-run-first, idempotent, transactionally locked,
  atomic, and fail-closed on malformed managed blocks or untrusted recovery
  state.
- Release completion requires provider-native, source-bound evidence and live
  readback. Missing capabilities remain `BLOCKED`; ambient executables,
  environment variables, local JSON, secrets, and hidden reasoning cannot
  establish release authority.

### Verified

- The approved release candidate passed 452 repository tests with 10
  platform-specific skips, Ruff, mypy, the Clean Code debt ratchet, and 71%
  branch coverage against the 64% floor.
- Five packages and 41 discoverable skills remain unchanged. The independent
  adoption gate remains open, so v1 readiness honestly stays 7/8.
- This section records local release preparation only. PR checks, immutable
  `main`, tag, GitHub Release, Pages, Wiki, attestations, and dual-host global
  installation require separate post-merge evidence.

## [0.14.1] - 2026-07-23

### Fixed

- Codex marketplace snapshots now accept Codex's validated, isolated
  `.codex-marketplace-install.json` metadata file even when the CLI reports an
  explicit marketplace ref. Other untracked files, malformed metadata, source
  drift, and ref drift remain fail-closed.

## [0.14.0] - 2026-07-23

### Added

- Company OS contracts for 12 functional roles, 8 delivery workflows,
  evidence-based framework detection, and transitive change-impact analysis.
- A portable `scripts/divan.py` CLI for project inspection, planning, impact
  analysis, contract validation, install, update, doctor, and recovery.
- DCS-011 and a machine-readable naming policy enforcing English canonical
  technical entrypoints with Turkish localization and bounded legacy aliases.
- English and Turkish Company OS guides plus synchronized Pages and Wiki entry.

### Changed

- Sadrazam now routes natural-language intent through Company OS and selects the
  smallest justified combination of Core, UI, React, and Zanaat packs.
- English is the canonical README and contributor surface; Turkish remains
  first-class through `README.tr.md` and `CONTRIBUTING.tr.md`.
- Workflows and maintainer scripts use English canonical names. Pre-v1 Turkish
  script names remain narrow deprecated wrappers to avoid breaking users.

### Security

- Project inspection is bounded, read-only, path-safe, and never executes
  project code.
- Framework packs are selected from manifest evidence; integrations and
  creative tooling are not activated for unrelated tasks.

## [0.13.0] - 2026-07-21

### Added

- A machine-readable registry for DCS-001..DCS-010, narrow expiring
  exceptions, deterministic documentation, and a CI enforcement gate.
- Read-only `--doctor`, dry-run-first `--upgrade`, and ownership-checked
  interrupted-transaction recovery for Claude Code/Desktop Code and Codex.
- Deterministic SPDX 2.3 SBOM generation, OpenSSF Scorecard, pull-request
  dependency review, and release provenance for both ZIP and SBOM assets.
- Bilingual contribution guidance, request-specific support routes, and a
  version-controlled 1280x640 Mühürdar social preview under 1 MB.

### Changed

- New code is ratcheted at McCabe 10, 50 lines per function, and 400 lines per
  module. The enforced branch-coverage floor is the recorded 64% baseline.
- The legacy-debt registry must exactly match current violations; growth is
  rejected and shrinkage/removal requires the same reviewed baseline refresh.
- Host adapters, transaction journals, lock/transition validation, eval
  provenance, and result contracts moved into smaller stdlib modules.
- README, Wiki sources, Pages, install, upgrade, rollback, uninstall, and
  contribution surfaces now share one five-minute first-success path.

### Security

- Upgrade refuses host mutation until it proves a clean pinned source commit,
  catalog digest, full package fingerprints, and a single active transaction.
- Durable intent is written before every external mutation. Verification and
  rollback touch only transaction-owned Divan rows and reject foreign state.
- GitHub Actions remain full-SHA pinned, narrowly permissioned, and release
  assets are never overwritten.
- Social-preview validation traverses every PNG chunk and requires valid CRCs,
  one exact IHDR, at least one IDAT, and a terminal empty IEND.

### Verified

- Local pre-release integration passed 223 tests (2 platform-specific Windows
  skips), Ruff, mypy, Clean Code, actionlint 1.7.10, skills-ref 0.1.1 for all
  41 skills, and Claude Code 2.1.212 for the marketplace and five packages.
- This is local release-candidate evidence. PR/main, repository rules, Pages,
  Wiki, tag, GitHub Release, attestations, and global v0.13.0 host upgrade are
  separate delivery states that remain pending.
- v1 remains 7/8 because no independent non-owner acceptance evidence exists.

## [0.12.2] - 2026-07-20

### Fixed

- `scripts/hijyen.py --clean` artık Windows'ta salt-okunur özniteliği taşıyan
  allowlist cache ağaçlarını, silme sınırını genişletmeden yazılabilir yapıp
  kalıcı kaldırır.
- Windows salt-okunur `__pycache__` regresyonu birim testine bağlandı.

## [0.12.1] - 2026-07-19

### Added

- `scripts/hijyen.py --check/--clean`: UTF-8/BOM/mojibake denetimi, açık
  subprocess kodlaması kuralı ve yalnız yeniden üretilebilir cache'leri silen
  fail-closed repo temizliği.
- UTF-8/LF editor ve Git sözleşmesi ile Ruff C90 McCabe 25 karmaşıklık bütçesi.

### Changed

- Pazar, skill, belge, ajan ve vitrin denetimleri isimli tek-sorumluluk
  fonksiyonlarına ayrıldı; kurulum rollback'i ile v1 kanıt doğrulaması aynı
  public davranışı koruyan aşamalara bölündü.
- Windows sistem locale'ine bırakılan host CLI ve Git metin çıktıları açık
  `encoding="utf-8"` sözleşmesine geçirildi.

### Security

- Temizlik allowlist dışındaki yedek, manifest, kanıt ve kullanıcı dosyalarını
  silmez. Aktif rollback yedekleri korunur; yalnız üretilebilir cache içeriği
  kalıcı kaldırılabilir.

## [0.12.0] - 2026-07-19

### Added

- Native Codex marketplace manifests for the same five packages and 41 skills
  already published through Claude Code, with a cross-host drift validator.
- Dry-run-first transactional installer for Claude Code/Desktop Code and Codex;
  it records pre-state, preserves unrelated plugins, verifies all packages, and
  rolls back only entries created by the failed transaction.
- First-party real-provider evaluation adapters: Claude Code as the bounded
  agent and an ephemeral read-only Codex process as the blinded JSON judge.
- CodeQL, Ruff, mypy, Coverage, actionlint, and immutable GitHub Action pins.

### Changed

- The legacy loose-skill installer is now a compatibility fallback. Release
  archives are SHA-256 verified before extraction and manifests record version,
  ref, source commit, archive hash, per-skill installed hash, install time,
  target, and backup. Migration preflights every row, quarantines owned content,
  preserves changed targets, and reverses every move on failure.
- Site navigation now has a keyboard-visible skip link, one main landmark,
  WCAG AA coral contrast, reduced-motion verification, and mobile/landscape
  overflow checks in real Chromium.
- Root licensing is canonical MIT with separate notices; 15 current upstream
  differences were reviewed and pinned without automatically copying content.

### Security

- Release workflows publish a versioned fallback archive and checksum with its
  source commit; mutable `main` downloads, mutable Action tags, moved release
  tags, and release-asset overwrite attempts are rejected.
- Host mutations are atomically journaled before execution and interrupted
  transactions have an ownership-checked, resumable recovery command. Legacy
  migration and fallback copying use their own durable, reversible journals;
  parent rollback restores even a completed legacy migration before removing
  native packages and fails closed if the recorded legacy journal is missing.
- Eval subprocesses are bounded, do not use dangerous bypass flags, redact
  secrets/PII/home paths, keep per-case A/B outcomes private, and bind publishable
  provenance to a clean Git HEAD plus provider-derived versions. Windows
  provider `.cmd` wrappers are resolved without invoking a shell for other
  commands, adapter JSON I/O is explicitly UTF-8 across platforms, and the
  Codex judge disables plugins while using a strict static score-array schema.

### Verified

- Fixture and repository tests prove host preservation/rollback, checksum
  fail-closed behavior, transactional legacy quarantine, marketplace parity,
  blind judging, and accessibility.
- A publishable first-party comparison ran three `baglam-muhafizi` cases with
  Claude Code 2.1.209 / `claude-sonnet-5` as the bounded agent and Codex CLI
  0.144.4 / `gpt-5.6-terra` as the blinded judge. The skill condition won zero
  cases, baseline won one, and two tied; no release threshold was predeclared,
  so this is auditable run evidence rather than a quality-improvement claim. Independent
  adoption remains pending for v1.
- Public eval evidence uses a commit-reveal boundary with a runner-generated
  256-bit OS-random seed: the raw blinding seed, condition mapping, per-case
  winner, and judge reasons remain in the private
  key while the public provenance records only the seed's SHA-256 commitment.

## [0.11.1] - 2026-07-18

### Added

- Repository-root `CLAUDE.md`, giving Claude Code a native durable handoff
  contract instead of relying on prior chat context.
- `scripts/devral.py --check` and regression tests that reject a missing
  handoff chain or a progress journal without an exact next action.
- GitHub Actions Dependabot configuration and CODEOWNERS coverage for policy,
  automation, release, registry, and project-memory surfaces.

### Changed

- Sadrazam advanced to 0.9.1; SessionStart now surfaces the Claude handoff
  contract before the current progress journal.
- Publication and local audit gates now cover Claude handoff and dependency
  maintenance as release-controlled surfaces.

### Security

- Guidance distinguishes controls stored in Git from GitHub settings requiring
  platform verification: rulesets, required reviews, secret scanning, push
  protection, Dependabot alerts, and CodeQL.

## [0.11.0] - 2026-07-18

### Added

- Publication control plane with a machine-readable surface manifest,
  deterministic version preparation, drift checks, and changelog-derived
  GitHub Release notes.
- Idempotent `main` workflow that waits for matching Pages and Wiki versions,
  then creates the immutable tag/Release or updates notes without moving a tag.
- Clean-host compatibility matrix: official Claude Code marketplace validation
  plus Codex install/discovery/removal on Ubuntu, macOS, and Windows.
- Manifest-driven Codex removal/rollback scripts, independent adoption evidence
  issue form, and a generated machine-readable v1 readiness scorecard.
- `/yayin` command and Sadrazam publication-surface law so future agents do not
  rely on the user to remind them about README, Wiki, site, or Release pages.

### Changed

- Sadrazam advanced to 0.9.0 and the public publication contract now treats
  README, marketplace, Pages, Wiki, changelog, tag, and GitHub Release as one
  ordered but separately verified delivery chain.
- v1 claims are gated by eight explicit evidence records; real-agent comparison
  and independent adoption remain pending instead of being inferred.

### Verified

- Unit coverage rejects stale public surfaces, validates release-note sourcing,
  checks the generated v1 scorecard, and rehearses installer rollback.
- GitHub's official documentation was used for least-privilege
  `contents: write`, non-recursive `GITHUB_TOKEN` behavior, and workflow
  concurrency design.
- PR #12 and all seven post-merge workflows passed. The release workflow
  verified Linux/macOS/Windows rollback, live Pages and Wiki markers, and the
  interactive site in Chromium before publishing tag/Release v0.11.0 at
  commit `5680337a`.

## [0.10.3] - 2026-07-18

### Added

- Deterministic Vezir Catalog generator and exact drift tests over all 41 skill
  frontmatter records.
- Explicit Wiki initialization preflight with the one required `Save Page`
  recovery action instead of an opaque clone failure.

### Changed

- GitHub Actions moved to the current major releases observed from their
  official repositories: checkout v7, setup-python v6, setup-node v7, and
  github-script v9.
- Repository guidance and contribution checks now require catalog validation.

### Fixed

- Multi-line YAML descriptions are rendered correctly; `claude-api` no longer
  appears as the broken `/-…` text in the public catalog and Wiki source.

### Verified

- GitHub repository and workflow state, the live Wiki HTTP 404, failed publish
  job steps, Context7's GitHub Docs result, current Codex manual, and active
  Mühürdar pet were inspected independently.
- The first Wiki page was initialized by the repository owner; raw `Home.md`
  returned HTTP 200 before the full 16-page source sync was triggered.

## [0.10.2] - 2026-07-18

### Added

- **Aday Meclisi:** machine-readable candidate registry with a deterministic
  human catalog and an explicit `never-auto-install` autonomy boundary.
- Structured GitHub source-candidate issue form for user gap, exact license,
  execution surface, and evidence—not popularity alone.
- Weekly read-only GitHub discovery workflow that opens a bounded triage issue,
  excludes known/upstream repositories, and never downloads candidate code.
- Candidate validation for canonical identity, duplicate IDs/URLs, lifecycle
  state, license evidence, decision consistency, review dates, and proof count.

### Changed

- `kaynak-kuratori` now persists discovery into the Meclis lifecycle and keeps
  ADOPT/ADAPT decisions separate from actual installation or vendoring.
- Core pack advanced to 0.5.1; public documentation now exposes how Divan grows
  continuously without turning an “awesome list” into trusted executable code.

### Verified

- The reference audit of `punkpeye/awesome-mcp-servers` records it as a
  MIT-licensed registry/index and explicitly re-audits every downstream item.
- Tests reject duplicate URLs and license-unknown ADOPT decisions and require
  the generated catalog to match the registry exactly.

## [0.10.1] - 2026-07-18

### Added

- Versioned GitHub Wiki manifest, deterministic builder, link/version checks,
  and a generated navigation sidebar.
- Fourteen intent-first Wiki pages covering quick start, current status,
  roadmap, OpenAI/Codex boundaries, and the Mühürdar verification mascot.
- `wiki-sync` Actions workflow: validates Wiki sources on pull requests,
  publishes them to the separate Wiki Git repository after `main`, and reads
  the live `Home.md` back before succeeding.

### Changed

- Sadrazam 0.8.1 now treats enabled Wikis, docs sites, and help centers as
  product surfaces with a canonical source, automated synchronization, and
  explicit live-publication evidence.
- README, English README, landing, roadmap, pull request template, and agent
  guidance now include the Wiki in the same publication contract.
- OpenAI/Codex documentation now distinguishes portable Agent Skills from the
  OpenAI Agents SDK application runtime and links to current official guides.

### Verified

- Wiki compilation is deterministic and rejects missing sources, duplicate
  slugs, broken internal links, and version drift.
- Unit coverage exercises manifest integrity, generated pages/sidebar, and
  version/link consistency.

## [0.10.0] - 2026-07-18

### Added

- Provider-neutral skill-vs-baseline eval runner with 12 cases across four
  original skills.
- JSON stdin/stdout adapter protocol for real agents and optional blind judges.
- A/B blinding, separate reveal keys, timeouts, zero-case failure, and optional
  minimum skill win-rate gates.
- Interactive five-intent decree selector for vibe coders.
- Persistent v0.10 product plan grounded in the official OpenAI agent-evals
  progression from traces to repeatable datasets and eval runs.

### Changed

- Pull-request site CI now tests the proposed `docs/` build locally instead of
  testing the old production page. Every `main` push now waits for the matching
  Pages version and repeats the browser test live; scheduled runs keep watch.
- Product pages now lead from user intent to the smallest pack, a copyable
  decree, and an observable delivery path.
- Marketplace advanced to 0.10.0 and Sadrazam to 0.8.0 with persistent
  intent-first routing and honest eval-evidence rules.

### Verified

- Eval contract discovery reports four skills and 12 non-empty cases.
- Unit tests cover discovery, zero-case failure, A/B blinding, judge mapping,
  threshold behavior, and review-required results.
- Static site JavaScript passes syntax validation; GitHub Actions browser proof
  is recorded with the publication evidence.

## [0.9.0] - 2026-07-18

### Added

- Native-first `ordu-nizami` orchestration and `/sefer` command.
- Evidence-first `arama-ustasi` codebase search.
- `baglam-muhafizi` context-budget and handoff discipline.
- `kaynak-kuratori` repository/license/provenance curation with three eval cases.
- English product README and persistent `.divan/` delivery records.
- Publication Law: a draft PR is not considered a public delivery.
- Version, changelog, roadmap, and public-surface consistency gates.

### Changed

- Marketplace version advanced to 0.9.0 because this release adds public,
  backward-compatible capabilities rather than a patch-only fix.
- Core pack advanced to 0.5.0 and Sadrazam to 0.7.0.
- README now explains why the project exists, how it improves itself, and which
  v1.0 claims are intentionally not made yet.
- Upstream audit now recognizes the original `kaynak-kuratori` workflow instead
  of looking for a nonexistent vendored copy.

### Verified

- Repository unit tests and local audit.
- Official Agent Skills validation for all 41 skills.
- Claude Code strict marketplace and plugin validation.
- GitHub Actions repository audit and Playwright site test.

## [0.7.0] - 2026-07-17

### Added

- 37-skill, five-pack marketplace baseline.
- Curated CC0 rule treasury and original `temkin` engineering prudence.
- Monthly upstream monitoring, community files, GitHub Pages, and local audits.

[Unreleased]: https://github.com/trugurpala/divan/issues
[0.15.0]: https://github.com/trugurpala/divan/releases/tag/v0.15.0
[0.13.0]: https://github.com/trugurpala/divan/releases/tag/v0.13.0
[0.11.0]: https://github.com/trugurpala/divan/releases/tag/v0.11.0
[0.10.3]: https://github.com/trugurpala/divan/tree/main
[0.10.2]: https://github.com/trugurpala/divan/tree/main
[0.10.1]: https://github.com/trugurpala/divan/tree/main
[0.10.0]: https://github.com/trugurpala/divan/tree/main
[0.9.0]: https://github.com/trugurpala/divan/tree/main
[0.7.0]: https://github.com/trugurpala/divan/releases/tag/v0.7.0
