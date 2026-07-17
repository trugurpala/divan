# Changelog

All notable changes to Divan are recorded here. The project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses Semantic
Versioning while the public API remains in initial development (`0.y.z`).

## [Unreleased]

### Planned

- Repeatable compatibility and installation matrix across supported hosts.
- Independent adoption evidence and reproducible quality measurements.
- First published comparison using a declared real-agent adapter and judge.

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
  testing the old production page; scheduled runs still inspect GitHub Pages.
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
[0.10.0]: https://github.com/trugurpala/divan/tree/main
[0.9.0]: https://github.com/trugurpala/divan/tree/main
[0.7.0]: https://github.com/trugurpala/divan/releases/tag/v0.7.0
