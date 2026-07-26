# Verification Hygiene Evidence — 2026-07-26

## Scope

Issue #33 required the documented local verification sequence to leave a clean
checkout hygiene-green on POSIX and Windows without touching user files.

## Red evidence

- `tests.test_verify` initially produced four failures because
  `scripts/verify.py` did not exist.
- The documentation/CI integration assertion failed until `AGENTS.md`,
  `quality-gate.yml`, and `release-manifest.json` shared the same runner.
- The first clean-commit full suite exposed seven Goal Archive errors:
  the initial receipt event used the current date while later events were
  forced to `2026-07-24`. The fixture now freezes the whole receipt lifecycle
  to one date.

## Implemented contract

- `python scripts/verify.py` is the canonical local and CI core command.
- Child Python uses `sys.executable` and `-B`.
- `PYTHONDONTWRITEBYTECODE`, `PYTHONPYCACHEPREFIX`, `RUFF_CACHE_DIR`,
  `MYPY_CACHE_DIR`, and `COVERAGE_FILE` keep generated state outside the repo.
- The first and last commands are `scripts/hygiene.py --check`.
- The runner never calls `--clean`; the existing fail-closed cleanup allowlist
  and Windows link/junction protections are unchanged.

## Local verification

| Gate | Result |
|---|---|
| Test discovery | 501 tests |
| Isolated module execution | 36/36 modules exited 0 |
| Branch coverage | 74% (`10222` statements, `4178` branches) |
| Ruff 0.15.22 | PASS |
| mypy 2.3.0 | PASS, 62 source files |
| Clean Code ratchet | PASS |
| Release validation | PASS, v0.16.0 / 94 surfaces |
| Catalog | PASS, 41 skills / 5 packages |
| v1 registry | PASS, target 1.0.0; readiness remains 7/8 |
| Eval contract | PASS, 4 skills / 13 cases |
| Final hygiene | PASS |
| Company OS impact | PASS, no unclassified changed paths |

The Work execution surface imposes an approximately 30-second process window,
so the 501 tests were also executed as bounded per-module subprocesses. Every
module returned zero; coverage was collected in parallel data files outside the
repository and combined afterward.

## Non-claims

- GitHub PR and CI results are not local evidence and remain pending here.
- The immutable v0.16.0 tag and Release assets were not changed.
- No independent-user adoption evidence was produced; v1 remains 7/8.
