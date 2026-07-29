# v0.18.0 local release-candidate evidence

Verified on 2026-07-29 after implementation
[PR #54](https://github.com/trugurpala/divan/pull/54) merged.

## Candidate identity

- Version: v0.18.0
- Implementation merge:
  `7c674874503853216dc8f2abddaa0459811a5ee6`
- Release branch: `agent/v018-release`
- Sadrazam package: `0.10.0`
- Product shape: one Divan repository, one nine-module stdlib-only engine
- v1 readiness: 7/8; independent adoption issue #34 remains open

## Implemented capability

Nizâm-ı Sefer deterministically compiles a Ferman into structural complexity,
risk and context policy, portable model classes, explicit dependency-graph
workstreams, sequential sefer/handoff windows, evidence obligations, and a
goal-bound `route.json`. Planning performs no model call or target-project
mutation.

Unknown or conflicting host identity fails safe to sequential planning. Exact
model identifiers are candidates until the active host confirms availability.
Security, production, release, credential, package-manager-conflict, financial,
destructive, and production-data signals cannot route to the economy class.

## Implementation gates

- 562 tests passed; 11 expected platform-specific tests skipped.
- Branch coverage: 75%.
- Claude Code and Codex compatibility checks passed on Linux, macOS, and
  Windows.
- Quality Gate, CodeQL, dependency review, Playwright, Wiki check, and
  publication surfaces passed.
- Two independent read-only reviews completed. Findings covering selected-team
  ownership, monorepo command identity, legacy-goal idempotency, impact
  classification, risk floors, mandatory independent review, and workstream
  semantics were addressed before merge.

## Versioned candidate gates

- The canonical Windows verifier passed on the clean release commit: 562 tests
  passed and 13 platform-specific tests were skipped.
- Release consistency passed for v0.18.0 and 167 controlled public surfaces.
- Ruff, the Clean Code debt ratchet, and mypy across 86 first-party source
  files passed.
- Repository validation reported 5 packages and 41 skills with synchronized
  Claude and Codex marketplace/plugin versions.
- Handoff, catalog, v1 scorecard, eval contract, final hygiene, and
  `git diff --check` passed.

## Publication boundary

This record establishes a local versioned release candidate. It does not claim
an immutable tag, GitHub Release, published assets, attestations, live
Pages/Wiki convergence, pinned-install success, independent adoption, or a
measured productivity improvement. Those claims require post-merge remote
readback and are recorded separately.
