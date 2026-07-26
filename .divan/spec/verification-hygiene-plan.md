# Hygiene-Stable Verification Implementation Plan

> **For agentic workers:** Execute inline with the repository's TDD and verification contracts.

**Goal:** Close issue #33 with one POSIX/Windows-compatible verification command that leaves repository hygiene green and never cleans user files.

**Architecture:** Add a small Python controller that owns the canonical core command sequence. It runs every child process with bytecode disabled and Ruff, mypy, coverage, and Python cache locations redirected to a temporary directory outside the repository. `AGENTS.md` and the primary CI workflow call the same controller; `scripts/hygiene.py` remains the only explicit cleanup implementation and keeps its existing fail-closed allowlist.

**Tech Stack:** Python 3.11+, `unittest`, GitHub Actions.

## Global Constraints

- The command must work through `python scripts/verify.py` on POSIX and Windows.
- No dependency may be added.
- The runner must not delete files; cache prevention/redirection is its only hygiene mechanism.
- Existing `scripts/hygiene.py --clean` allowlist and link/junction protections remain unchanged.
- The core command sequence must finish with a second hygiene check.

## Task 1: Freeze the verification contract

**Files:**
- Create: `tests/test_verify.py`
- Create: `scripts/verify.py`

**Interfaces:**
- `verification_environment(root, cache_root) -> dict[str, str]`
- `run(root=ROOT, commands=CORE_COMMANDS, cache_root=None) -> int`

- [x] Add a failing test that requires the canonical runner, its command order, external cache environment, cross-platform `sys.executable` execution, protected-file preservation, and final hygiene check.
- [x] Run `python -m unittest tests.test_verify -v` and confirm it fails because `scripts/verify.py` is absent.
- [x] Implement only the environment builder, command sequence, subprocess loop, CLI, and temporary-cache lifecycle needed by the test.
- [x] Re-run `python -m unittest tests.test_verify -v` and confirm it passes.

## Task 2: Make local and CI verification share the runner

**Files:**
- Modify: `AGENTS.md`
- Modify: `.github/workflows/quality-gate.yml`
- Modify: `tests/test_workflows.py`
- Modify: `release-manifest.json`
- Modify: `tests/test_yayin.py`

- [x] Add a failing workflow/documentation assertion for `python scripts/verify.py`.
- [x] Replace the duplicated core command list in CI with the canonical runner while retaining the additional CI-only quality, deterministic-runner, actionlint, and official-validator gates.
- [x] Replace the maintainer command sequence in `AGENTS.md` with the same one-line entrypoint.
- [x] Track `scripts/verify.py` as a release surface and test the manifest contract.
- [x] Run the focused test modules and confirm they pass.

## Task 3: Record and verify delivery

**Files:**
- Modify: `BLUEPRINT.md`
- Modify: `.divan/progress.md`
- Create: `.divan/evidence/teftis-20260726-verification-hygiene.md`

- [x] Run the canonical verification command from a clean commit and confirm the final hygiene check is green.
- [ ] Run the impact-required workflow, handoff, release, Wiki, Company OS, actionlint, Ruff, mypy, Clean Code, and coverage gates.
- [x] Record exact commands and results without changing the immutable `v0.16.0` tag or claiming v1 completion.
- [ ] Publish a focused PR that closes #33; merge only after every applicable GitHub check is green.
