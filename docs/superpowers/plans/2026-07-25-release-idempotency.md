# Immutable Release Idempotency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make unchanged-version `main` commits verify the existing immutable GitHub Release instead of failing or trying to move its tag.

**Architecture:** The release workflow selects its source before generating assets. A missing version tag uses current `GITHUB_SHA` for new publication; an existing version tag must be an ancestor of current `main`, is checked out into a temporary detached worktree, and is used to deterministically regenerate bytes for comparison with the existing Release. Provenance attestation runs only when the Release does not already exist.

**Tech Stack:** GitHub Actions, Bash, Git worktrees, Python release/SBOM/zipapp builders, `unittest`, actionlint.

## Global Constraints

- Never move or overwrite an existing version tag or Release asset.
- Preserve the new-version path from current `GITHUB_SHA`.
- Fail closed when an existing tag is not an ancestor of current `main`.
- Build verification bytes with the scripts from the tagged source tree.
- Do not mint duplicate attestations for an already-published Release.
- Keep `VERSION=0.16.0` and v1 at 7/8.

---

### Task 1: Pin the two release modes with failing tests

**Files:**
- Modify: `tests/test_workflows.py`

- [x] Add a regression test requiring tagged-source worktree reconstruction, ancestry verification, and tagged build scripts.
- [x] Require the workflow to expose whether the GitHub Release already exists.
- [x] Require the attestation step to skip an already-published Release.
- [x] Retain assertions that a new release uses current `GITHUB_SHA`, never clobbers, and compares every asset.
- [x] Run `python -m unittest tests.test_workflows -v` and observe the new test fail against the current workflow.

### Task 2: Implement tagged-source verification

**Files:**
- Modify: `.github/workflows/release.yml`

- [x] Resolve `source_commit` to current `GITHUB_SHA` when the tag is absent.
- [x] When the tag exists, require it to be an ancestor of current `main`, create a temporary detached worktree, and require the tagged `VERSION` to match.
- [x] Run release notes, runner, and SBOM builders from the selected source tree.
- [x] Set a `published_release` output using authenticated `gh release view`.
- [x] Skip build-provenance attestation only when `published_release=true`.
- [x] Keep byte-for-byte comparison and new Release creation behavior unchanged.
- [x] Run the focused workflow tests and actionlint.

### Task 3: Record and verify the repair

**Files:**
- Create: `.divan/evidence/teftis-20260725-release-idempotency.md`
- Modify: `.divan/progress.md`
- Modify: `BLUEPRINT.md`

- [x] Record failing run 30130364496 and its exact failed step.
- [x] Record focused red/green evidence, complete local gates, PR checks, and the successful post-merge release run.
- [x] Reconfirm tag `v0.16.0` and all five asset digests are unchanged.
- [x] Recalculate Company OS impact with no unclassified paths.
- [x] Keep independent adoption pending and v1 at 7/8.
