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
- The first PR Quality Gate exposed an integration gap after all 501 tests and
  static gates had passed: the CI-only Ruff, mypy, and coverage commands wrote
  `.ruff_cache`, `.mypy_cache`, and `.coverage` into the checkout before the
  canonical runner's opening hygiene check. A regression test now requires all
  CI tool caches to use `${{ runner.temp }}`.

## Implemented contract

- `python scripts/verify.py` is the canonical local and CI core command.
- Child Python uses `sys.executable` and `-B`.
- `PYTHONDONTWRITEBYTECODE`, `PYTHONPYCACHEPREFIX`, `RUFF_CACHE_DIR`,
  `MYPY_CACHE_DIR`, and `COVERAGE_FILE` keep generated state outside the repo.
- The Quality Gate applies the same external-cache contract to its additional
  CI-only Ruff, mypy, coverage, and Python invocations. The `${{ runner.temp }}`
  expressions live on the executable step, where the `runner` context exists,
  rather than at job scope.
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
| Focused CI-cache regression | PASS, 21 workflow/runner tests |

The Work execution surface imposes an approximately 30-second process window,
so the 501 tests were also executed as bounded per-module subprocesses. Every
module returned zero; coverage was collected in parallel data files outside the
repository and combined afterward.

## GitHub verification

- PR #46 was opened from the focused delivery branch.
- The first Quality Gate run failed only at the canonical runner's opening
  hygiene check after the preceding CI-only commands created local cache
  paths. The cache-path regression was reproduced locally and fixed
  test-first.
- The first replacement commit put `runner.temp` at job scope, so GitHub did
  not create a Quality Gate run. A second red test narrowed the contract to the
  `Local quality gates` step, and the expressions were moved to that supported
  context. The next replacement CI run is the merge gate.

## Non-claims

- The immutable v0.16.0 tag and Release assets were not changed.
- No independent-user adoption evidence was produced; v1 remains 7/8.
