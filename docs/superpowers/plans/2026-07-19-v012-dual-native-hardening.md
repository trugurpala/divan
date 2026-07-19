# Divan v0.12 Dual-Native Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task by task. Apply `test-driven-development` for behavior changes, `systematic-debugging` for failures, `requesting-code-review` before publication, and `verification-before-completion` before completion claims.

**Goal:** Ship Divan v0.12 as a verified native marketplace for both Claude Code/Desktop Code and Codex, harden the legacy fallback installer and supply chain, add real cross-provider evaluation adapters, publish the release, and install it globally without removing unrelated user plugins.

**Architecture:** Keep the existing Claude marketplace canonical, add a generated/validated Codex marketplace beside it, and expose a Python host installer that delegates to official host CLIs with dry-run, backup, verification, and rollback semantics. Preserve the direct-copy installer only as a checksum-pinned fallback. Extend existing registry/release/eval controllers instead of creating a parallel product model.

**Tech Stack:** Python 3.11+, unittest, JSON, PowerShell/POSIX shell, GitHub Actions, Claude CLI, Codex CLI, Playwright.

## Global Constraints

- Work only in the isolated worktree and preserve the user's unrelated main-checkout line-ending change.
- Every behavior change begins with a failing test; keep commits small and independently reviewable.
- Never remove an unrelated Claude or Codex plugin. Back up any colliding Divan entry before replacement.
- Do not copy changed upstream content until its license, pinned revision, attribution, evaluation, and adoption decision are recorded.
- Keep `real-agent-comparison` and `independent-adoption` pending until their actual evidence contracts are satisfied.
- Run the repository's complete `AGENTS.md` verification set before publication.

## Task 1: Add the native Codex marketplace and cross-host validator

**Files:**
- Create: `.agents/plugins/marketplace.json`
- Create: `plugins/*/.codex-plugin/plugin.json`
- Create: `scripts/host_marketplaces.py`
- Create: `tests/test_host_marketplaces.py`
- Modify: `scripts/validate.py`

1. Add tests that load both host marketplaces and assert the same five package names, versions, source directories, and 41 total skills.
2. Run `python -m unittest tests.test_host_marketplaces -v` and confirm RED because the Codex marketplace/validator is absent.
3. Implement a standard Codex marketplace with local package sources and one `.codex-plugin/plugin.json` per package.
4. Implement `scripts/host_marketplaces.py --check` with actionable drift errors and call it from `scripts/validate.py`.
5. Run the focused tests and `python scripts/host_marketplaces.py --check` to GREEN.
6. Commit as `feat: add native Codex marketplace`.

## Task 2: Add a transactional dual-host installer

**Files:**
- Create: `scripts/kur-hostlar.py`
- Create: `tests/test_host_install.py`
- Modify: `docs/Kurulum.md`
- Modify: `docs/Kaldirma.md`

1. Write subprocess-fixture tests for dry-run defaults, host selection, explicit `--execute`, existing-plugin preservation, collision backup, verification, and rollback of only entries created by the current run.
2. Run `python -m unittest tests.test_host_install -v` and confirm RED.
3. Implement `--host claude|codex|both`, `--ref`, `--execute`, `--migrate-legacy`, and a JSON transaction log. Use official commands:
   - `claude plugin marketplace add <source>#<ref>` and `claude plugin install <package>@divan --scope user`
   - `codex plugin marketplace add <source> --ref <ref>` and `codex plugin add <package>@divan`
4. Verify every installed package before optional legacy migration. On failure, undo only the transaction's newly created Divan registrations and restore collision backups.
5. Document dry-run, execution, migration, uninstall, and recovery paths.
6. Run focused tests to GREEN and commit as `feat: add transactional host installer`.

## Task 3: Harden the legacy fallback installer

**Files:**
- Modify: `scripts/kur.ps1`
- Modify: `scripts/kur.sh`
- Modify: `scripts/kaldir.ps1`
- Modify: `scripts/kaldir.sh`
- Modify: `tests/test_validate.py`
- Modify: `.github/workflows/release.yml`

1. Add failing tests requiring immutable release references, archive SHA-256 verification, fail-closed mismatch behavior, and manifest provenance fields.
2. Extend the install manifest with `skill`, `hedef`, `yedek`, `surum`, `ref`, `source_commit`, `archive_sha256`, and `installed_at`.
3. Make release installs download a versioned archive plus checksum, validate it before extraction, and retain explicit local-source mode for development.
4. Ensure uninstall restores only recorded backups and never deletes unrelated skills.
5. Publish the archive and checksum as release assets.
6. Run installer tests on PowerShell and syntax/static checks for shell; commit as `fix: pin and verify fallback installs`.

## Task 4: Raise the code and supply-chain quality gate

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`
- Create: `.github/workflows/codeql.yml`
- Create: `tests/test_workflows.py`
- Modify: `.github/workflows/*.yml`

1. Add failing tests that reject mutable action tags and require CodeQL, lint, type-check, coverage, and actionlint gates.
2. Pin official actions to full commit SHAs with readable version comments.
3. Configure Ruff, mypy, and Coverage with honest baselines; pin development tool versions.
4. Add CodeQL and extend CI to run the new local quality checks.
5. Run `ruff check .`, `mypy scripts`, coverage, workflow tests, and actionlint; commit as `ci: harden quality and supply chain`.

## Task 5: Fix site accessibility and test it

**Files:**
- Modify: `docs/site/index.html`
- Modify: `docs/site/styles.css`
- Modify: `scripts/site_testi.py`
- Create: `tests/test_site_markup.py`

1. Add failing markup/browser tests for a keyboard-visible skip link, one `<main id="main-content">` landmark, logical focus order, and WCAG AA contrast for small coral text.
2. Add the skip link and main landmark, then change the coral token to `#E06450` or a darker tested equivalent that reaches at least 4.5:1 on its actual background.
3. Extend the Playwright smoke test to exercise keyboard focus and landmark discovery.
4. Run the focused unit and site tests; commit as `fix: improve site accessibility`.

## Task 6: Normalize licensing and review upstream drift

**Files:**
- Modify: `LICENSE`
- Create: `NOTICE.md`
- Create: `registry/upstream-baselines.json`
- Create: `tests/test_upstream.py`
- Modify: `scripts/upstream_watch.py`
- Modify: `UPSTREAM.md`
- Modify: `THIRD_PARTY_LICENSES.md`

1. Add failing tests requiring a canonical root MIT license, separate notices, immutable upstream revisions, licenses, and explicit decisions for every detected upstream change.
2. Move third-party explanatory material from `LICENSE` to `NOTICE.md` without removing attribution.
3. Record the 15 changed upstream skills and classify each as `KEEP`, `ADAPT`, `ADOPT`, `REFERENCE`, or `REJECT`, with rationale and pinned revision.
4. Update the watcher so drift opens a review item rather than modifying installed content.
5. Run upstream/license validation; commit as `docs: normalize license and upstream review`.

## Task 7: Add real Claude-agent and Codex-judge adapters

**Files:**
- Create: `evals/adapters/common.py`
- Create: `evals/adapters/claude_agent.py`
- Create: `evals/adapters/codex_judge.py`
- Create: `tests/test_real_adapters.py`
- Modify: `evals/run.py`
- Modify: `evals/README.md`
- Modify: `tests/test_evals.py`

1. Add fixture-CLI tests that prove timeout handling, structured output parsing, prompt separation, ablation behavior, blinded judging, and secret-safe logs.
2. Implement the Claude adapter so baseline disables Divan customization while the treatment exposes only the selected package plugin directory.
3. Implement the Codex judge through non-interactive `codex exec` with a read-only sandbox, no approvals, and a strict JSON schema. The judge must not receive treatment labels.
4. Integrate adapters with the current controller and preserve deterministic mechanical `--check` mode.
5. Run focused fixture tests; do not claim quality improvement from them. Commit as `feat: add cross-provider eval adapters`.

## Task 8: Synchronize v0.12 release surfaces

**Files:**
- Modify: `VERSION`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `plugins/*/.claude-plugin/plugin.json`
- Modify: `plugins/*/.codex-plugin/plugin.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `BLUEPRINT.md`
- Modify: `docs/Kurulum.md`
- Modify: `docs/wiki/*`
- Modify: `docs/site/*`
- Modify: `release-manifest.json`
- Modify: `registry/v1-gates.json`
- Modify: `.divan/progress.md`
- Modify: `scripts/yayin.py`
- Modify: tests covering publication surfaces

1. Add/adjust failing publication tests for v0.12, both native hosts, counts, asset/checksum references, and exact progress evidence.
2. Use `scripts/yayin.py` as the publication controller to synchronize all versioned surfaces.
3. Keep `independent-adoption` pending. Keep `real-agent-comparison` pending until Task 11 produces qualifying real evidence.
4. Run all publication controllers and tests; commit as `chore: prepare v0.12 release`.

## Task 9: Request and resolve code review

1. Record `BASE_SHA=5b5b3e5` and the current feature `HEAD_SHA`.
2. Dispatch the required code-review agent with the design, this plan, base, head, and explicit attention to destructive install behavior, rollback scope, subprocess safety, secret handling, and truthful evidence gates.
3. Reproduce every Critical or Important finding locally.
4. Fix accepted findings with a failing regression test first; document any rejected finding with concrete evidence.
5. Re-run focused tests and commit review fixes.

## Task 10: Run the full local verification gate

Run from repository root and save exact evidence:

```powershell
python scripts/validate.py
python scripts/devral.py --check
python scripts/katalog.py --check
python scripts/v1.py --check
python scripts/yayin.py --check
python evals/run.py --check
python -m unittest discover -s tests -v
ruff check .
mypy scripts
coverage run -m unittest discover -s tests
coverage report
actionlint
git diff --check
```

Then run installer dry-runs for Claude, Codex, and both hosts. Any failure returns to the relevant task via `systematic-debugging`; do not weaken a gate merely to make it pass.

## Task 11: Publish, verify, globally install, and hand over

1. Push the feature branch and create a ready pull request.
2. Enable GitHub branch protection/rulesets, required CI/CodeQL checks, Dependabot vulnerability alerts, and security updates without disabling existing secret scanning or push protection.
3. Wait for CI, fix failures with evidence, merge to the default branch, and re-read README, installation docs, marketplace metadata, and site from `main`.
4. Tag v0.12.0 through the repository's release path. Verify the tag, GitHub Release, archive, SHA-256 asset, Pages, and Wiki independently before saying they are published.
5. Run one bounded real Claude-agent/Codex-judge comparison. Close `real-agent-comparison` only if the stored artifact satisfies the registry contract; otherwise leave it pending with the exact blocker. Never close `independent-adoption` without external user evidence.
6. Back up current user-level host state. Execute `scripts/kur-hostlar.py --host both --ref v0.12.0 --execute`, verify all five packages/41 skills in both hosts, then migrate only Divan's legacy loose-copy entries. Confirm unrelated Codex skills and existing Claude plugins remain installed.
7. Reload Claude Desktop Code through supported UI controls if needed; do not interrupt the user's unrelated running Claude task.
8. Run Defterdar to update `.divan/progress.md` with release/install evidence, unresolved gates, and the next exact action. Commit/push any evidence-only follow-up through the same verification path.

## Completion Contract

Completion means v0.12 is merged, tagged, released, remotely verified, and installed natively in both user hosts with rollback evidence. If the independent-adoption gate remains pending, report the release as complete but the v1 acceptance program as still open; never conflate the two.
