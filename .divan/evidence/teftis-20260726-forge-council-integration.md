# Forge Council Current-Main Integration Evidence — 2026-07-26

## Baseline

- Draft PR #28 head `b323c52` was based on `db2b506` and was not mergeable
  with current `main`.
- Its 12 focused Forge registry tests and fail-closed registry validator passed
  on the historical branch.
- Current `main` commit `5f7f088` introduced the canonical hygiene-stable
  verification workflow.

## Integration

- Current `main` was merged in a dedicated integration commit.
- The only textual conflict was `.github/workflows/quality-gate.yml`.
- The current-main single quality step and external cache environment were
  preserved.
- Direct Forge registry validation and the focused Forge test module were added
  inside that canonical quality step.
- No upstream source was vendored, installed, built, or promoted.

## Local verification

- Canonical verification passed 514 tests with 11 expected platform skips.
- Coverage passed at 74% (`10337` statements, `4226` branches).
- Ruff passed.
- Mypy passed across 63 source files.
- Clean Code, release, handoff, Company OS, impact, and final hygiene gates
  passed.
- The impact result had no unclassified paths.
- Release remains v0.16.0 with 94 tracked surfaces.

## Non-claims

- The 18 registered upstream sources still have only pinned identity and license
  evidence unless their `build_evidence` says otherwise.
- No clean clone, Windows build, golden task, materialization, or promotion was
  performed for any upstream source.
- GitHub CI and independent review remain external merge gates.
- Independent-user adoption remains absent; v1 stays 7/8.
