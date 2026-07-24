# v0.16.0 Post-Merge Release Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close issue #35 with immutable, independently recomputed v0.16.0 release-asset and attestation evidence while keeping the independent-adoption gate at 7/8.

**Architecture:** Treat GitHub Release `v0.16.0` as the remote source and record a bounded post-merge evidence document in the repository. Cross-check downloaded bytes against both GitHub asset digests and the published checksum manifests, then synchronize only the canonical handoff, changelog, blueprint, and progress surfaces.

**Tech Stack:** GitHub Releases REST API, GitHub Artifact Attestations REST API, SHA-256, SPDX 2.3 JSON, Python zipapp, Markdown.

## Global Constraints

- Do not move or replace tag `v0.16.0` or any existing Release asset.
- Bind every claim to source commit `5513e73d5faa8657a22d813ecfec763a6089bea0`.
- Do not claim owner-canary, global-host update, or independent-user adoption unless reproduced in this execution.
- Keep `registry/v1-gates.json` at 7/8.

---

### Task 1: Recompute immutable Release evidence

**Files:**
- Read: GitHub Release `v0.16.0`
- Create temporarily: `/tmp/divan-v016-assets/*`

- [ ] Download all five published assets from the immutable release URL.
- [ ] Compute SHA-256 for every downloaded byte sequence.
- [ ] Verify `divan-v0.16.0.sha256` binds the ZIP, SPDX SBOM, runner, runner checksum, source commit, and tag.
- [ ] Verify `divan-project.pyz.sha256` against the downloaded runner.
- [ ] Read the runner source envelope and ZIP `VERSION`; require v0.16.0 and the immutable source commit.
- [ ] Query the GitHub attestation endpoint for every asset digest and require both release and SLSA provenance statements.
- [ ] Re-read Pages and Wiki and require `v0.16.0` plus `Fermanını seç`.

### Task 2: Record and synchronize the evidence

**Files:**
- Create: `.divan/evidence/teftis-20260725-v016-release-assets.md`
- Modify: `.divan/evidence/teftis-20260725-v016-publication-handoff.md`
- Modify: `.divan/progress.md`
- Modify: `BLUEPRINT.md`
- Modify: `CHANGELOG.md`

- [ ] Record release identity, exact asset sizes and SHA-256 values, checksum results, SPDX summary, runner source envelope, attestation predicate types, workflow run, and live readbacks.
- [ ] State explicitly that no owner-canary, global-host update, or independent-user adoption was reproduced.
- [ ] Link the new evidence from the canonical handoff and progress records.
- [ ] Convert the v0.16.0 changelog boundary from “local preparation only” to the verified published state without rewriting the immutable GitHub Release notes.
- [ ] Remove issue #35 from the active queue while leaving issues #34 and #33 open.

### Task 3: Verify the repository contract

**Files:**
- Verify: all changed files above

- [ ] Run `python scripts/hygiene.py --check`.
- [ ] Run `python scripts/validate.py`.
- [ ] Run `python scripts/handoff.py --check`.
- [ ] Run `python scripts/catalog.py --check`.
- [ ] Run `python scripts/v1.py --check` and confirm 7/8.
- [ ] Run `python scripts/release.py --check`.
- [ ] Run `python scripts/wiki.py --check`.
- [ ] Run `python evals/run.py --check`.
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `git diff --check` and recalculate Company OS impact from the actual changed paths.
