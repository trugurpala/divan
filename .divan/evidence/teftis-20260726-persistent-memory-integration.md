# Persistent Memory Integration Evidence — 2026-07-26

## Baseline

- Draft PR #29 was based on `db2b506` and was not mergeable with current
  `main`.
- Its original 12 memory tests, focused Ruff, and focused mypy checks passed on
  the historical branch.
- Current `main` (`5f7f088`) merged without textual conflicts.

## Review findings

- Mutation functions loaded JSON before acquiring the advertised single-writer
  lock. A second writer could therefore acquire the lock later and overwrite a
  newer state with its stale snapshot.
- Required memory directories were accepted through symlinks. Lesson,
  decision, checkpoint, or history writes could escape the project.
- The runtime and contract were absent from `release-manifest.json`.
- The draft required a Windows smoke but did not carry one.

## Implemented controls

- Execute-mode mutations acquire the lock before validation and state load.
- Required memory paths and evidence reject symlinks and out-of-project
  containment.
- Two red regressions cover stale-state overwrite and symlink escape.
- The memory CLI, store, validator, workflow, contract, and guide are release
  surfaces.
- Decision and lesson records were split into `project_memory_knowledge.py`
  after the hardened workflow exceeded the new-code 400-line module budget.
- Compatibility CI runs the memory module on Linux, macOS, and Windows.

## Local verification

- Canonical hardened integration: 517 tests passed, 11 platform tests skipped,
  opening and closing hygiene checks passed.
- Branch coverage remained 74% (`10937` statements, `4394` branches).
- Focused hardened suite: 14 memory tests and 17 workflow tests passed.
- Ruff, Clean Code, and mypy passed; repository mypy covered 66 source files.
- Release validation passed for v0.16.0 with 101 tracked surfaces.
- GitHub CI and the real Windows matrix remain external merge gates.

## Non-claims

- No Windows result is claimed until GitHub's Windows runner completes.
- No independent review is claimed.
- v0.16.0 assets and immutable tag are unchanged.
- Independent-user adoption remains absent; v1 stays 7/8.
