# Divan v1.3.8 Release Repair Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to
> implement this plan task by task. Use `superpowers:test-driven-development`
> for every behavior change, `superpowers:systematic-debugging` for every
> unexpected failure, and `superpowers:verification-before-completion` before
> any success claim.

**Goal:** Publish an installable `v1.3.8` whose merged `main` commit, immutable
tag, runner metadata, checksum manifest, exact assets, and GitHub evidence all
identify the same verified source.

**Architecture:** Assemble only the four approved deliverables in an isolated
worktree based on the reviewed design commit. Preserve the original dirty
checkout byte-for-byte, prove each behavior with focused tests, prepare the
version only through `scripts/release.py`, merge one green pull request, and
publish from the exact merged `main` commit with fail-closed identity checks.

**Tech Stack:** Python 3, `unittest`, Ruff, mypy, coverage, PowerShell, Git,
GitHub Actions, GitHub CLI/API, Agent Skills Markdown.

---

## Fixed boundaries and acceptance contract

- The source checkout is `C:\Users\User\Desktop\Codex\divan`.
- The isolated checkout is
  `C:\Users\User\Desktop\Codex\divan\.worktrees\v138-release-repair`.
- The isolated branch is `codex/v138-release-implementation`, based on
  `5e1c6f4`.
- Never reset, clean, stash, stage, or rewrite the source checkout.
- Never move, delete, replace, or republish `v1.3.7`.
- Never use a paid API, paid runner, subscription, or new global dependency.
- Stop before publication if GitHub requests billing or a paid runner.
- The release candidate is accepted only if:
  `main == refs/tags/v1.3.8 == divan.pyz source_commit ==
  divan-project.pyz source_commit == checksum source_commit`.
- A failed, missing, skipped, cancelled, or still-running required check is not
  success.

## Task 1: Create the isolated assembly worktree

**Files:**

- Verify: `.gitignore`
- Create: `.worktrees\v138-release-repair` as a Git worktree

- [ ] **Step 1: Record the original checkout evidence**

Run:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git diff --check
```

Expected: branch `codex/v138-recovery-tag-ambiguity`, HEAD `5e1c6f4`, and the
pre-existing dirty paths remain visible. Save the command output in the task
transcript, not in the repository.

- [ ] **Step 2: Prove the worktree container is ignored**

Run:

```powershell
git check-ignore -v .worktrees
```

Expected: an ignore rule matches `.worktrees`. If it does not match, stop and
add only `/.worktrees/` to `.gitignore`, run `git diff --check`, and commit that
single safety change before continuing.

- [ ] **Step 3: Create the isolated branch and worktree**

Run:

```powershell
git worktree add .worktrees/v138-release-repair -b codex/v138-release-implementation 5e1c6f4
git -C .worktrees/v138-release-repair status --short
git -C .worktrees/v138-release-repair rev-parse HEAD
```

Expected: empty status and HEAD `5e1c6f4`.

- [ ] **Step 4: Run the clean baseline**

Run from the isolated worktree:

```powershell
python -B scripts/verify.py --coverage
git diff --check
```

Expected: both pass. If either fails, use systematic debugging and record the
baseline as blocked; do not transfer implementation files until the clean
baseline cause is known.

## Task 2: Implement host install recovery and transaction safety

**Files:**

- Test: `tests/test_bootstrap_runner.py`
- Test: `tests/test_divan_cli.py`
- Test: `tests/test_host_install.py`
- Test: `tests/test_host_upgrade.py`
- Test: `tests/test_host_upgrade_security.py`
- Modify: `scripts/build_bootstrap.py`
- Modify: `scripts/divan.py`
- Modify: `scripts/host_cli.py`
- Modify: `scripts/host_install_authority.py`
- Modify: `scripts/host_install_journal.py`
- Modify: `scripts/host_lifecycle.py`
- Modify: `scripts/host_state.py`
- Modify: `scripts/host_transactions.py`
- Create: `scripts/host_install_marketplace.py`
- Create: `scripts/host_install_recovery.py`

- [ ] **Step 1: Transfer only the host tests**

From the source checkout, copy the five listed test files into the same paths
in the isolated worktree. Use `Copy-Item -LiteralPath`; do not copy directories
or wildcard matches.

- [ ] **Step 2: Run the focused tests and observe RED**

Run:

```powershell
python -B -m unittest tests.test_bootstrap_runner tests.test_divan_cli tests.test_host_install tests.test_host_upgrade tests.test_host_upgrade_security -v
```

Expected: failures or import errors specifically identify the missing recovery,
marketplace, authority, journal, or transaction behavior. If the suite is
already green, compare the transferred tests with HEAD and stop if they do not
exercise new behavior.

- [ ] **Step 3: Transfer the minimal host implementation**

Copy the ten listed script files into the same paths. Review the isolated diff
and remove no pre-existing source-checkout changes.

- [ ] **Step 4: Run the focused tests and observe GREEN**

Run:

```powershell
python -B -m unittest tests.test_bootstrap_runner tests.test_divan_cli tests.test_host_install tests.test_host_upgrade tests.test_host_upgrade_security -v
python -B -m ruff check scripts/build_bootstrap.py scripts/divan.py scripts/host_cli.py scripts/host_install_authority.py scripts/host_install_journal.py scripts/host_install_marketplace.py scripts/host_install_recovery.py scripts/host_lifecycle.py scripts/host_state.py scripts/host_transactions.py tests/test_bootstrap_runner.py tests/test_divan_cli.py tests/test_host_install.py tests/test_host_upgrade.py tests/test_host_upgrade_security.py
```

Expected: all pass without `--fix`.

- [ ] **Step 5: Review and commit the bounded change**

Run:

```powershell
git diff --check
git status --short
git diff --stat
git add scripts/build_bootstrap.py scripts/divan.py scripts/host_cli.py scripts/host_install_authority.py scripts/host_install_journal.py scripts/host_install_marketplace.py scripts/host_install_recovery.py scripts/host_lifecycle.py scripts/host_state.py scripts/host_transactions.py tests/test_bootstrap_runner.py tests/test_divan_cli.py tests/test_host_install.py tests/test_host_upgrade.py tests/test_host_upgrade_security.py
git diff --cached --check
git commit -m "feat: make host installation recoverable"
```

Expected: one commit containing only this task's paths.

## Task 3: Preserve typed plan continuation without execution authority

**Files:**

- Create: `tests/test_planning_continuation.py`
- Modify: `plugins/sadrazam/divan_runtime/cli.py`
- Modify: `plugins/sadrazam/divan_runtime/goals.py`
- Modify: `plugins/sadrazam/divan_runtime/planning.py`

- [ ] **Step 1: Transfer the continuation test and observe RED**

Copy `tests/test_planning_continuation.py`, then run:

```powershell
python -B -m unittest tests.test_planning_continuation -v
```

Expected: the new typed continuation cases fail against the old runtime.

- [ ] **Step 2: Transfer the minimal runtime implementation**

Copy the three listed runtime modules. The implementation must preserve typed
goal/plan state while granting no command execution or host mutation authority.

- [ ] **Step 3: Prove behavior and coverage**

Run:

```powershell
python -B -m coverage run --branch -m unittest tests.test_planning_continuation
python -B -m coverage report --include="plugins/sadrazam/divan_runtime/cli.py,plugins/sadrazam/divan_runtime/goals.py,plugins/sadrazam/divan_runtime/planning.py" --fail-under=90
python -B -m unittest tests.test_divan_cli tests.test_planning_continuation -v
python -B -m ruff check plugins/sadrazam/divan_runtime tests/test_planning_continuation.py
```

Expected: all pass; coverage is at least 90% for the affected runtime files.
Direct coverage artifacts must remain outside the repository or be removed only
if they were created by this task and are ignored.

- [ ] **Step 4: Commit**

Run:

```powershell
git add plugins/sadrazam/divan_runtime/cli.py plugins/sadrazam/divan_runtime/goals.py plugins/sadrazam/divan_runtime/planning.py tests/test_planning_continuation.py
git diff --cached --check
git commit -m "feat: preserve typed plan continuation"
```

## Task 4: Adapt UI/UX Pro Max as a host-neutral, attributed skill

**Files:**

- Create: `plugins/ui-pack/skills/ui-ux-pro-max/LICENSE.txt`
- Modify: `plugins/ui-pack/skills/ui-ux-pro-max/SKILL.md`
- Create: `plugins/ui-pack/skills/ui-ux-pro-max/scripts/color_mode.py`
- Modify: `plugins/ui-pack/skills/ui-ux-pro-max/scripts/design_system.py`
- Create:
  `plugins/ui-pack/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py`
- Create: `tests/test_ui_ux_pro_max.py`
- Modify: `UPSTREAM.md`
- Modify: `THIRD_PARTY_LICENSES.md`
- Modify: `registry/upstream-baselines.json`

- [ ] **Step 1: Transfer tests first and observe RED**

Copy the two new test files and run:

```powershell
python -B -m unittest tests.test_ui_ux_pro_max -v
python -B plugins/ui-pack/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py
```

Expected: missing module, mode selection, provenance, or contract failures.

- [ ] **Step 2: Transfer code, skill contract, licence, and provenance**

Copy the seven implementation/provenance paths listed above, excluding the two
test files already copied. Confirm the licence text and pinned upstream record
agree on repository, commit, and licence.

- [ ] **Step 3: Prove host neutrality and focused behavior**

Run:

```powershell
python -B -m unittest tests.test_ui_ux_pro_max -v
python -B plugins/ui-pack/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py
python -B -m coverage run --branch plugins/ui-pack/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py
python -B -m coverage report --include="plugins/ui-pack/skills/ui-ux-pro-max/scripts/color_mode.py,plugins/ui-pack/skills/ui-ux-pro-max/scripts/design_system.py" --fail-under=90
python -B -m unittest tests.test_upstream -v
python -B -m ruff check plugins/ui-pack/skills/ui-ux-pro-max/scripts tests/test_ui_ux_pro_max.py tests/test_upstream.py
```

Expected: all pass, affected Python coverage is at least 90%, and no paid or
host-specific runtime becomes mandatory.

- [ ] **Step 4: Commit**

Run:

```powershell
git add plugins/ui-pack/skills/ui-ux-pro-max/LICENSE.txt plugins/ui-pack/skills/ui-ux-pro-max/SKILL.md plugins/ui-pack/skills/ui-ux-pro-max/scripts/color_mode.py plugins/ui-pack/skills/ui-ux-pro-max/scripts/design_system.py plugins/ui-pack/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py tests/test_ui_ux_pro_max.py UPSTREAM.md THIRD_PARTY_LICENSES.md registry/upstream-baselines.json
git diff --cached --check
git commit -m "feat: adapt ui ux skill for portable use"
```

## Task 5: Enforce release identity and least-privilege publication

**Files:**

- Create: `scripts/release_guard.py`
- Create: `scripts/release_tag.py`
- Create: `tests/test_release_guard.py`
- Create: `tests/test_release_tag.py`
- Modify: `tests/test_workflows.py`
- Modify: `.github/workflows/release.yml`

- [ ] **Step 1: Transfer release tests first and observe RED**

Copy the three listed test files, then run:

```powershell
python -B -m unittest tests.test_release_guard tests.test_release_tag tests.test_workflows -v
```

Expected: imports and workflow contract assertions fail against the old release
path.

- [ ] **Step 2: Transfer the minimal guard and workflow implementation**

Copy `scripts/release_guard.py`, `scripts/release_tag.py`, and
`.github/workflows/release.yml`. Confirm by review that:

```text
build job: contents: read, persist-credentials: false, no OIDC, no secrets
publish job: no downloaded Python execution, exact artifact ID and digest
tag exists: remote tag == main == bundle source, otherwise fail
tag absent: create only after main == bundle source and all checks pass
release exists: exact names and byte hashes match, otherwise fail
```

- [ ] **Step 3: Prove executable guard behavior**

Run:

```powershell
python -B -m unittest tests.test_release_guard tests.test_release_tag tests.test_workflows -v
python -B -m ruff check scripts/release_guard.py scripts/release_tag.py tests/test_release_guard.py tests/test_release_tag.py tests/test_workflows.py
python -B -m mypy scripts/release_guard.py scripts/release_tag.py
```

Expected: all pass. Source-string assertions in `test_workflows` supplement but
do not replace executable `release_guard` and `release_tag` unit tests.

- [ ] **Step 4: Commit**

Run:

```powershell
git add .github/workflows/release.yml scripts/release_guard.py scripts/release_tag.py tests/test_release_guard.py tests/test_release_tag.py tests/test_workflows.py
git diff --cached --check
git commit -m "fix: bind releases to one verified source"
```

## Task 6: Synchronize candidate, catalog, product, and public surfaces

**Files:**

- Modify: `AGENTS.md`
- Modify: `BLUEPRINT.md`
- Modify: `CHANGELOG.md`
- Modify: `README.en.md`
- Modify: `README.md`
- Modify: `README.tr.md`
- Modify: `RELEASE.md`
- Modify: `docs/Aday-Meclisi.md`
- Modify: `docs/Divan-Engine.md`
- Modify: `docs/Divan-Engine.tr.md`
- Modify: `docs/Hizli-Baslangic.md`
- Modify: `docs/Home.md`
- Modify: `docs/Kaldirma.md`
- Modify: `docs/Kurulum.md`
- Modify: `docs/index.html`
- Modify: `docs/skill-catalog.md`
- Modify: `registry/candidates.json`
- Modify: `registry/clean-code-baseline.json`
- Modify: `release-manifest.json`
- Modify: `site/index.html`
- Modify: `tests/test_meclis.py`
- Modify: `tests/test_verify.py`

- [ ] **Step 1: Transfer product-surface tests first**

Copy `tests/test_meclis.py` and `tests/test_verify.py`, then run:

```powershell
python -B -m unittest tests.test_meclis tests.test_verify tests.test_upstream -v
```

Expected: the old catalog and public surfaces fail the new approved contracts.

- [ ] **Step 2: Transfer the bounded surface set**

Copy the remaining listed files. Do not copy any dirty path outside Tasks 2–6.
Review public prose against `docs/Yazim-ve-Uslup.md`, with the user outcome
first and Divan explained in ordinary language on first use.

- [ ] **Step 3: Run surface and catalogue gates**

Run:

```powershell
python -B scripts/catalog.py --check
python -B scripts/v1.py --check
python -B scripts/handoff.py --check
python -B scripts/prose.py --check
python -B scripts/wiki.py --check
python -B scripts/release.py --check
python -B -m unittest tests.test_meclis tests.test_upstream tests.test_verify -v
```

Expected: all pass before version preparation.

- [ ] **Step 4: Commit**

Run:

```powershell
git add AGENTS.md BLUEPRINT.md CHANGELOG.md README.en.md README.md README.tr.md RELEASE.md docs/Aday-Meclisi.md docs/Divan-Engine.md docs/Divan-Engine.tr.md docs/Hizli-Baslangic.md docs/Home.md docs/Kaldirma.md docs/Kurulum.md docs/index.html docs/skill-catalog.md registry/candidates.json registry/clean-code-baseline.json release-manifest.json site/index.html tests/test_meclis.py tests/test_verify.py
git diff --cached --check
git commit -m "docs: synchronize installation and public surfaces"
```

## Task 7: Prepare version 1.3.8 through the canonical release path

**Files:**

- Modify only the paths emitted by `scripts/release.py --prepare 1.3.8`
- Verify: `VERSION`
- Verify: `.divan/progress.md`
- Verify: `release-manifest.json`

- [ ] **Step 1: Confirm the branch is clean**

Run:

```powershell
git status --short
python -B scripts/release.py --check
```

Expected: empty status and a valid pre-release state.

- [ ] **Step 2: Prepare the version**

Run:

```powershell
python -B scripts/release.py --prepare 1.3.8
git status --short
git diff --stat
git diff
```

Expected: only canonical version/publication surfaces change. Reject unexpected
paths instead of manually editing around them.

- [ ] **Step 3: Validate the prepared release**

Run:

```powershell
python -B scripts/release.py --check
python -B scripts/catalog.py --check
python -B scripts/v1.py --check
python -B scripts/handoff.py --check
python -B scripts/prose.py --check
python -B scripts/wiki.py --check
git diff --check
```

- [ ] **Step 4: Commit canonical version output**

Run:

```powershell
git add -u
git diff --cached --check
git commit -m "chore: prepare divan 1.3.8"
```

Expected: all versioned changes are committed and the worktree is clean.

## Task 8: Run the complete local quality and determinism gates

**Files:**

- Verify: the complete isolated worktree
- Do not modify source files

- [ ] **Step 1: Run focused suites**

Run:

```powershell
python -B -m unittest tests.test_release_guard tests.test_release_tag tests.test_workflows tests.test_bootstrap_runner tests.test_divan_cli tests.test_host_install tests.test_host_upgrade tests.test_host_upgrade_security tests.test_planning_continuation tests.test_ui_ux_pro_max tests.test_meclis tests.test_upstream tests.test_verify -v
python -B plugins/ui-pack/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py
```

Expected: all pass.

- [ ] **Step 2: Run the canonical verifier with enough time**

Run:

```powershell
python -B scripts/verify.py --coverage
git diff --check
git status --short
```

Give the verifier at least 30 minutes. While it runs, inspect live process CPU,
child processes, elapsed time, and newly emitted output at intervals shorter
than 60 seconds. A process with advancing output/CPU is slow, not hung. A
repeated no-progress state must be diagnosed before termination.

Expected: verifier passes, diff check passes, and status is empty.

- [ ] **Step 3: Prove deterministic release assets**

Build the three executable/source assets twice in repository-external temporary
directories using the same source commit and compare names, sizes, and hashes:

```powershell
$sourceCommit = git rev-parse HEAD
$version = (Get-Content -Raw VERSION).Trim()
$determinismRoot = Join-Path ([IO.Path]::GetTempPath()) ("divan-v138-determinism-" + [guid]::NewGuid())
$firstBuild = Join-Path $determinismRoot first
$secondBuild = Join-Path $determinismRoot second
New-Item -ItemType Directory -Path $firstBuild, $secondBuild | Out-Null
foreach ($outputRoot in @($firstBuild, $secondBuild)) {
  git archive --format=zip --prefix="divan-v$version/" --output="$outputRoot/divan-v$version.zip" $sourceCommit
  python -B scripts/build_project_runner.py --root . --output "$outputRoot/divan-project.pyz" --source-commit $sourceCommit
  if ($LASTEXITCODE -ne 0) { throw "Project runner build failed" }
  python -B scripts/build_bootstrap.py --root . --output "$outputRoot/divan.pyz" --source-commit $sourceCommit
  if ($LASTEXITCODE -ne 0) { throw "Bootstrap build failed" }
}
$firstEvidence = Get-ChildItem -LiteralPath $firstBuild -File | Sort-Object Name | ForEach-Object {
  [pscustomobject]@{Name=$_.Name; Length=$_.Length; SHA256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
}
$secondEvidence = Get-ChildItem -LiteralPath $secondBuild -File | Sort-Object Name | ForEach-Object {
  [pscustomobject]@{Name=$_.Name; Length=$_.Length; SHA256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
}
if (Compare-Object $firstEvidence $secondEvidence -Property Name,Length,SHA256) {
  throw "Release assets are not deterministic"
}
$firstEvidence | Format-Table -AutoSize
```

Expected: the archive and two runners have identical names, sizes, and hashes.
The workflow separately constructs and validates the deterministic sidecars,
SBOM, checksum manifest, and release notes from these byte-identical inputs. Do
not publish if the builds differ.

- [ ] **Step 4: Review every commit and final diff**

Run:

```powershell
git log --oneline 5e1c6f4..HEAD
git diff --stat 5e1c6f4..HEAD
git diff --check 5e1c6f4..HEAD
git status --short
```

Expected: only approved deliverables, no secrets, caches, unrelated paths, or
uncommitted changes.

## Task 9: Push one branch and merge one green pull request

**Files:**

- GitHub branch: `codex/v138-release-implementation`
- GitHub pull request target: `main`

- [ ] **Step 1: Re-fetch and prove the base did not move unexpectedly**

Run:

```powershell
git fetch --prune origin
git rev-list --left-right --count origin/main...HEAD
git log --oneline --left-right origin/main...HEAD
```

Expected: the branch is ahead only by the reviewed commits. If `origin/main`
moved, rebase only after reviewing the new commits and rerunning Task 8.

- [ ] **Step 2: Push the implementation branch**

Run:

```powershell
git push -u origin codex/v138-release-implementation
```

Expected: push succeeds without force.

- [ ] **Step 3: Open one pull request**

Create a PR whose body includes root cause, unchanged `v1.3.7`, exact local
verification commands/results, release identity invariant, no-paid boundary,
and rollback behavior.

- [ ] **Step 4: Wait for every required check**

Inspect the PR checks until terminal. Missing, pending, skipped, cancelled, or
failed checks block the merge. If a failure occurs, diagnose it from logs,
apply the smallest TDD-backed correction in the isolated worktree, rerun Task
8, push normally, and wait again.

- [ ] **Step 5: Merge only the green PR**

Merge through the repository's existing allowed merge method. Do not bypass
branch protection, dismiss reviews, use administrator override, or force-push.

- [ ] **Step 6: Re-read merged main**

Run:

```powershell
git fetch origin main
git rev-parse origin/main
```

Store this exact SHA in the PowerShell variable:

```powershell
$mergedMainSha = git rev-parse origin/main
```

Confirm GitHub's default branch and PR merge commit both identify
`$mergedMainSha`.

## Task 10: Publish and independently verify v1.3.8

**Files:**

- GitHub tag: `refs/tags/v1.3.8`
- GitHub Release: `v1.3.8`
- No local source modifications

- [ ] **Step 1: Confirm publication preconditions**

Read GitHub state and prove:

```text
default branch SHA = $mergedMainSha
all required main checks = success
refs/tags/v1.3.8 = absent
release v1.3.8 = absent
v1.3.7 tag and release = unchanged
```

If `v1.3.8` already exists, stop unless its tag and every byte already match
the intended candidate; never overwrite it.

- [ ] **Step 2: Run the repository release workflow from merged main**

Use the workflow's supported trigger with version `1.3.8` and exact merged-main
ref. Do not grant new permissions or supply an unreviewed token. Stop if GitHub
requests billing, a paid runner, or privilege beyond the approved workflow.

- [ ] **Step 3: Wait for terminal GitHub evidence**

Require successful quality, release, CodeQL, Wiki/Pages, and other required
checks for `$mergedMainSha`. Do not report publication while any required
job is non-terminal.

- [ ] **Step 4: Re-read tag, release, and exact assets**

Download metadata and assets into a new repository-external temporary
directory. Prove:

```text
refs/tags/v1.3.8 commit = $mergedMainSha
release target commit = $mergedMainSha
asset names = exact release_guard contract
each manifest SHA-256 = downloaded bytes
divan.pyz source_commit = $mergedMainSha
divan-project.pyz source_commit = $mergedMainSha
checksum source_commit = $mergedMainSha
SBOM and required attestations are present
```

Inspect runner archives without executing them.

- [ ] **Step 5: Run the documented non-mutating installer dry-run**

Use the published `v1.3.8` installer's documented dry-run/inspection mode in a
repository-external temporary host root. Confirm it accepts the tag/source/hash
chain and records no mutation outside that temporary root.

- [ ] **Step 6: Report the final evidence table**

Report exact SHAs, check URLs/statuses, asset names/hashes, local and GitHub
test durations, dry-run result, original checkout status, changed paths,
commits, and remaining risks. The final table must include:

| Gate | Required result |
|---|---|
| GitHub/main equality | Recorded `$mergedMainSha` |
| Ahead/behind after merge | `0/0` for refreshed main |
| Original dirty checkout | Preserved, no cleanup |
| Local canonical verification | Pass with duration |
| PR required checks | All terminal success |
| `v1.3.8` tag/source/bundle | One identical SHA |
| Exact assets and hashes | Complete and matching |
| Installer dry-run | Pass, no host mutation |
| Paid services | None |
| `v1.3.7` | Unchanged |
