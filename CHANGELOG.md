# Changelog

All notable changes to Divan are recorded here. The project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses Semantic
Versioning while the public API remains in initial development (`0.y.z`).

## [Unreleased]

### Planned

- Independent adoption evidence and reproducible quality measurements.

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
- Fixture tests prove contracts only. A real cross-provider comparison remains
  a separate evidence step and independent adoption remains pending for v1.

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
[0.11.0]: https://github.com/trugurpala/divan/releases/tag/v0.11.0
[0.10.3]: https://github.com/trugurpala/divan/tree/main
[0.10.2]: https://github.com/trugurpala/divan/tree/main
[0.10.1]: https://github.com/trugurpala/divan/tree/main
[0.10.0]: https://github.com/trugurpala/divan/tree/main
[0.9.0]: https://github.com/trugurpala/divan/tree/main
[0.7.0]: https://github.com/trugurpala/divan/releases/tag/v0.7.0
