# Divan Community Standards v0.13 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.13.0 with ten enforceable community standards, safer host lifecycle commands, a Clean Code ratchet, supply-chain provenance, protected GitHub delivery, and synchronized public documentation.

**Architecture:** A versioned JSON registry is the single source for DCS-001..DCS-010 and generates the public standards page. Focused stdlib controllers enforce schema, clean-code debt, host diagnosis/upgrade, and SPDX generation; existing publication, host, and GitHub workflows consume those controllers rather than duplicating policy.

**Tech Stack:** Python 3.11+ stdlib, `unittest`, Ruff, mypy, coverage.py, GitHub Actions, GitHub CLI/API, Claude and Codex native plugin CLIs.

## Global Constraints

- The registry contains exactly the stable IDs `DCS-001` through `DCS-010`, all at level `required`.
- New first-party Python functions have McCabe complexity at most 10 and at most 50 logical lines; new first-party Python modules have at most 400 physical lines.
- Existing violations are keyed by exact path and symbol; growth fails, while shrinkage or disappearance requires the baseline to be refreshed to the exact current measurement. The repository-wide McCabe 25 ceiling remains active.
- The branch-coverage configuration floor and measured full-suite result must both remain at least the recorded 64% v0.12.2 baseline.
- Doctor is read-only. Install and upgrade are dry-run by default. Unknown provenance fails before mutation.
- Every external host mutation is journaled first; rollback affects only proven Divan-owned state and never unrelated extensions.
- First-party runtime code uses Python stdlib only; no application framework, telemetry, hosted dashboard, or auto-installing discovery is added.
- GitHub Actions use full 40-character SHA pins and explicit least-privilege permissions.
- README, English README, Wiki source, Pages source, CHANGELOG, BLUEPRINT, package manifests, and release metadata describe the same version.
- v1 independent-adoption status remains pending unless external evidence is supplied by a non-owner user.

## Spec coverage map

- DCS-001: Tasks 3, 4, and 6 — five-minute install, doctor, and recovery path.
- DCS-002: Tasks 3 and 4 — framework-independent host adapters.
- DCS-003: Task 2 — small cohesive code and shrinking debt baseline.
- DCS-004: Tasks 1, 3, and 4 — stable JSON and actionable error contracts.
- DCS-005: Every task — red/green tests, coverage, and evidence gates.
- DCS-006: Task 5 — pinned dependencies, SBOM, analysis, and attestations.
- DCS-007: Task 4 — reversible install/upgrade lifecycle.
- DCS-008: Tasks 1, 6, and 7 — synchronized, discoverable documentation.
- DCS-009: Tasks 6 and 7 — contribution, support, and protected PR flow.
- DCS-010: Tasks 2, 6, and 7 — accessibility, privacy, and honest evidence.

---

### Task 1: Standards registry, renderer, and canonical validation

**Files:** Create `registry/community-standards.json`, `registry/standard-exceptions.json`, `scripts/standartlar.py`, `tests/test_standards.py`, and `docs/Topluluk-Standartlari.md`; modify `scripts/validate.py`, `.github/workflows/teftis.yml`, and `release-manifest.json`.

**Interfaces:** `load_contract(root: pathlib.Path) -> dict[str, Any]`, `validate_contract(root: pathlib.Path) -> list[str]`, `render_markdown(contract: dict[str, Any]) -> str`; CLI modes `--check`, `--render`, `--json`.

- [ ] Write failing tests proving exact DCS-001..DCS-010 IDs, `required` level, duplicate/missing ID rejection, missing check/evidence rejection, expired/duplicate exception rejection, deterministic rendering, stale-document detection, and JSON-only output.
- [ ] Run `python -m unittest tests.test_standards -v`; confirm failure is caused by the absent controller.
- [ ] Implement `REQUIRED_IDS = tuple(f"DCS-{number:03d}" for number in range(1, 11))` and the declared interfaces. Registry rows contain `id`, `title_tr`, `title_en`, `level`, `purpose`, `checks`, `evidence`, and `exception_policy`.
- [ ] Require exception fields `standard_id`, `target`, `reason`, `owner`, `created_on`, `expires_on`, and `evidence`; reject expiry beyond 180 days and wildcard targets.
- [ ] Render `docs/Topluluk-Standartlari.md`, connect the check to `validate.py` and `teftis.yml`, and add all canonical surfaces to `release-manifest.json`.
- [ ] Run `python -m unittest tests.test_standards tests.test_validate tests.test_workflows tests.test_yayin -v`, `python scripts/standartlar.py --check`, `python scripts/validate.py`, and `git diff --check`.
- [ ] Commit as `feat: enforce ten Divan community standards`.

---

### Task 2: Clean Code debt ratchet and focused eval extraction

**Files:** Create `registry/clean-code-baseline.json`, `scripts/clean_code.py`, `tests/test_clean_code.py`, `evals/provenance.py`, and `evals/result_contracts.py`; modify `evals/run.py`, `tests/test_eval_runner.py`, `pyproject.toml`, `.github/workflows/teftis.yml`, and `release-manifest.json`.

**Interfaces:** `measure_python(root: pathlib.Path) -> dict[str, dict[str, int]]`, `compare_baseline(measured: dict, baseline: dict) -> list[str]`; CLI `python scripts/clean_code.py --check [--json]`; all existing importable names in `evals/run.py` remain re-exported.

- [ ] Write failing fixtures for a new 401-line module, 51-line function, new Ruff C901 complexity-11 finding, increased baseline value, deleted/shrunk violation, and silent `except Exception: pass`. Mock only the Ruff subprocess boundary.
- [ ] Run `python -m unittest tests.test_clean_code -v`; confirm the missing checker causes red.
- [ ] Implement schema-1 baseline rows such as `{"kind":"module-lines","target":"evals/run.py","value":640}`. Obtain complexity from `ruff check scripts evals --select C901 --config lint.mccabe.max-complexity=10 --output-format=json`; missing Ruff is an actionable failure.
- [ ] Add characterization tests for `_read_provenance`, `_repository_identity`, `_bind_provenance`, `_sanitize_public`, `_validate_agent_result`, `_validate_judgement`, `_public_candidate`, and `write_results`; verify them against the old module before extraction.
- [ ] Move provenance helpers to `evals/provenance.py` and result/redaction helpers to `evals/result_contracts.py`; re-export them from `evals/run.py`.
- [ ] Set coverage `fail_under = 64`, wire `clean_code.py --check` after Ruff, record only measured legacy violations, and remove entries eliminated by extraction.
- [ ] Run the focused eval/clean-code tests, Ruff, `mypy scripts evals`, full coverage with `--fail-under=64`, the clean-code checker, and `git diff --check`; measured coverage must remain at least 64%.
- [ ] Commit as `refactor: ratchet clean code debt`.

---

### Task 3: Read-only doctor and host adapter boundary

**Files:** Create `scripts/host_adapters.py` and `tests/test_host_doctor.py`; modify `scripts/kur-hostlar.py`, `tests/test_host_install.py`, and `docs/Kurulum.md`.

**Interfaces:** `doctor(options: Options, *, runner: Runner = _subprocess_runner, root: pathlib.Path | None = None) -> dict[str, Any]`; adapter functions normalize marketplace/plugin rows and construct list/add/install/remove commands. CLI accepts mutually exclusive `--doctor` and optional `--json`.

- [ ] Add passing characterization tests for current Claude/Codex list/add/install/remove argv, normalized rows, and UTF-8 subprocess behavior.
- [ ] Write failing doctor tests for missing CLI, healthy pinned install, version drift, disabled package, foreign marketplace, orphaned package, and unfinished transaction. Assert no mutation and JSON keys `status`, `ref`, `hosts`, `issues`, `next_command`.
- [ ] Run `python -m unittest tests.test_host_doctor -v`; confirm red is the absent doctor.
- [ ] Extract host-specific behavior into `host_adapters.py`, keep compatibility imports, and immediately rerun existing installer tests.
- [ ] Implement statuses `healthy`, `attention`, and `unavailable`; human output has one line per host plus an exact next command, while JSON mode writes only JSON.
- [ ] Run focused host tests, clean-code check, Ruff, mypy, and `git diff --check`.
- [ ] Commit as `feat: add read-only dual-host doctor`.

---

### Task 4: Provenance-gated transactional upgrade

**Files:** Create `scripts/host_transactions.py` and `tests/test_host_upgrade.py`; modify `scripts/kur-hostlar.py`, `tests/test_host_install.py`, `docs/Kurulum.md`, and `docs/Kaldirma.md`.

**Interfaces:** extend `Options` with `upgrade: bool`; add `upgrade(options: Options, *, runner: Runner = _subprocess_runner, root: pathlib.Path | None = None) -> dict[str, Any]`; transaction schema 2 records `operation`, `before_rows`, `target`, `pending`, `removed`, `created`, `verified`, and `rollback_errors`; schema-1 rollback remains supported.

- [ ] Write failing tests for dry-run, same-version no-op, dual-host success, untrusted source before mutation, one-host failure, restoration of both prior versions, interruptions around external success, second recovery interruption, and unrelated-row preservation.
- [ ] Run `python -m unittest tests.test_host_upgrade -v`; confirm red is missing upgrade.
- [ ] Extract journal persistence, mutation markers, transaction loading, ownership selection, and recovery primitives into `host_transactions.py`; re-export compatibility names and rerun all existing install tests.
- [ ] Prove ownership only when normalized source equals the requested repository and every installed `@divan` package matches the marketplace/version contract; otherwise raise before journaling a mutation.
- [ ] Journal every remove/add/install before invocation, verify target state, and on failure remove only target rows created by this transaction before reconstructing proven prior state in reverse host order. Persist `rollback-incomplete` with exact recovery command if restoration fails.
- [ ] Add mutually exclusive `--upgrade`; preserve dry-run default and document no-op, refusal, transaction, and recovery behavior.
- [ ] Run focused lifecycle tests, clean-code check, Ruff, mypy, and `git diff --check`.
- [ ] Commit as `feat: add rollback-safe Divan upgrades`.

---

### Task 5: SBOM, Scorecard, dependency review, and artifact provenance

**Files:** Create `scripts/sbom.py`, `tests/test_sbom.py`, `.github/workflows/scorecard.yml`, and `.github/workflows/dependency-review.yml`; modify `.github/workflows/release.yml`, `tests/test_workflows.py`, `release-manifest.json`, `UPSTREAM.md`, and `THIRD_PARTY_LICENSES.md`.

**Interfaces:** `build_spdx(root: pathlib.Path, version: str, source_commit: str) -> dict[str, Any]`; CLI `python scripts/sbom.py --output PATH --source-commit SHA`; release assets ZIP, SHA256, and SPDX JSON.

- [ ] Write failing tests for SPDX 2.3 identity, deterministic namespace/order, five packages, license/provenance relationships, UTF-8 output, invalid commit rejection, Scorecard, dependency review, SBOM, attestations, permissions, and SHA pins.
- [ ] Run `python -m unittest tests.test_sbom tests.test_workflows -v`; confirm missing surfaces cause red.
- [ ] Implement stdlib SPDX generation from both marketplace manifests and existing license/upstream registries using `ensure_ascii=False`, `sort_keys=True`, trailing newline, and no local identity/environment data.
- [ ] Add reviewed full-SHA Scorecard and GitHub dependency-review actions with least privileges; record source, SHA, purpose, and license decision under existing policy.
- [ ] Generate SPDX before release creation, include its SHA in checksum, byte-compare an existing SBOM, upload without `--clobber`, and attest ZIP plus SBOM with GitHub's official action. Limit `id-token: write` and `attestations: write` to publish.
- [ ] Run focused tests, an example SBOM build, Actionlint, validator, and `git diff --check`.
- [ ] Commit as `build: attest Divan release provenance`.

---

### Task 6: Contributor support, discovery, and synchronized surfaces

**Files:** Create `SUPPORT.md`, `CONTRIBUTING.en.md`, `.github/ISSUE_TEMPLATE/config.yml`, and `tests/test_community.py`; modify contribution files, both READMEs, `docs/Home.md`, `docs/Hizli-Baslangic.md`, `docs/Kurulum.md`, `docs/Standartlar-ve-Limitler.md`, `docs/GitHub-Kullanimi.md`, `docs/SSS.md`, `wiki-pages.json`, both site HTML sources, site tests, and `release-manifest.json`.

**Interfaces:** usage questions route to Discussions Q&A, reproducible bugs to the bug form, vulnerabilities to private advisories, capabilities to candidate/skill forms, and independent evidence to the acceptance form. Quick path shows install preview/execute, doctor, upgrade preview/execute, rollback, and uninstall.

- [ ] Write failing tests for bilingual contribution links, all support routes, blank-issue disabling, exact lifecycle commands, DCS links, homepage marker, truthful v1 status, accessibility landmarks, keyboard controls, and matching critical commands in both HTML sources.
- [ ] Run community and site tests; confirm missing support/lifecycle surfaces cause red.
- [ ] Add support and contribution routes without publishing an email or inventing a response promise; keep Turkish and English contracts aligned.
- [ ] Update first-success docs and site. State that Divan is a local skill/plugin distribution, not a model/runtime. Preserve Mühürdar identity, WCAG checks, 41-skill count, and pending v1 evidence.
- [ ] Add `Topluluk-Standartlari` to `wiki-pages.json`, extend release-manifest coverage, render deterministic pages, and run Wiki/publication checks.
- [ ] Run focused community/site/Wiki/publication tests plus standards check and `git diff --check`.
- [ ] Commit as `docs: make Divan contributor and user friendly`.

---

### Task 7: v0.13 integration, repository rules, and public delivery

**Files:** Modify `VERSION`, `CHANGELOG.md`, `BLUEPRINT.md`, `.divan/progress.md`, and every version surface selected by `scripts/yayin.py --prepare 0.13.0`; create `.divan/evidence/teftis-20260721-v013-community-standards.md`, `.divan/evidence/github-ruleset-v013.json`, and `docs/assets/divan-social-preview.png`.

**Interfaces:** repository homepage is `https://trugurpala.github.io/divan/`; ruleset targets `main`, requires PRs and exact observed checks, and permits administrator recovery bypass; public version is v0.13.0 while v1 remains 7/8.

- [ ] Run every focused suite from Tasks 1-6 plus Ruff, mypy, coverage, Actionlint, Agent Skills validation, and Claude plugin validation; fix integration drift before versioning.
- [ ] Run `python scripts/yayin.py --prepare 0.13.0`, then write truthful CHANGELOG, BLUEPRINT, and progress narratives without changing independent-adoption evidence.
- [ ] Create a 1280x640 under-1-MB Mühürdar social preview with strong contrast and minimal text. Set GitHub homepage by API, upload the preview through repository settings, preserve topics, and record readback evidence.
- [ ] Run the complete AGENTS.md gate plus `python scripts/standartlar.py --check`, `python scripts/clean_code.py --check`, Ruff, `mypy scripts evals`, coverage `--fail-under=64`, Actionlint, and `git diff --check`.
- [ ] Request independent whole-branch review of `origin/main..HEAD`; fix all Critical and Important findings with regression tests and obtain clean re-review.
- [ ] Push the branch, open a ready PR, wait for all workflows, and record actual successful check names.
- [ ] Merge only after green CI. Apply/read back a `main` ruleset requiring PRs and the actual checks with administrator recovery bypass; store redacted evidence.
- [ ] Verify `main`, Pages, Wiki, immutable tag, GitHub Release, ZIP/checksum/SPDX assets, and attestations. Run doctor and pinned v0.13.0 global Claude/Codex upgrade lifecycle; verify five packages/41 skills and unchanged unrelated extensions.
- [ ] Record command output, run URLs, merge SHA, ruleset ID, digests, host results, risks, and next step in the evidence/progress/Blueprint ledger. Commit post-release evidence as `docs: record v0.13.0 delivery evidence`.
