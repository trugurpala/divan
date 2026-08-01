# Divan v1.0.3 Friendly Control Plane Implementation Plan

> **For Codex:** Follow the executing-plans workflow. Keep production behavior
> behind a failing test, recalculate impact after edits, and verify every public
> surface before publication.

**Goal:** Make the installed product immediately understandable: setup once,
use natural language every day, and receive only truthful maintenance actions.

**Architecture:** Preserve the host plugin as the daily interface and the
immutable `divan.pyz` as the maintenance lane. Correct doctor semantics, add
surface-scoped compatibility metadata, then synchronize bilingual onboarding
and public site copy.

**Tech Stack:** Python standard library, JSON, unittest, static HTML, GitHub
Actions, GitHub Pages, Wiki publication checks.

---

### Task 1: Establish the failing doctor contract

**Files:**

- Modify: `tests/test_host_doctor.py`

1. Add a failing assertion that a healthy diagnosis keeps a string
   `next_command` but leaves it empty because no shell action is required.
2. Add a failing human-output test that expects a `READY` message and rejects a
   `NEXT` line for a healthy diagnosis.
3. Preserve attention and unfinished-transaction tests that require exact
   commands.
4. Run `python -m unittest tests.test_host_doctor -v` and record the expected
   failure before production edits.

### Task 2: Correct doctor behavior without weakening recovery

**Files:**

- Modify: `scripts/host_profiles.py`
- Modify: `scripts/host_cli.py`
- Modify only if required: `scripts/host_adapters.py`

1. Return an empty command string only when every requested host is healthy
   and no unfinished transaction overrides it.
2. Render the healthy human result as one readiness instruction.
3. Keep invalid JSON, unavailable CLI, version drift, and recovery commands
   unchanged.
4. Re-run the focused doctor suite until green.

### Task 3: Scope compatibility claims to real host surfaces

**Files:**

- Modify: `tests/test_host_compatibility.py`
- Modify: `scripts/host_compatibility.py`
- Modify: `registry/host-compatibility.json`

1. Add failing tests for missing, duplicate, malformed, and overlapping
   `surfaces` / `excluded_surfaces` values.
2. Run the focused suite and confirm the new tests fail for missing validation.
3. Add the smallest validator rules and declare surfaces for all canonical
   hosts.
4. Limit the verified Codex lifecycle claim to the CLI evidence exercised by
   this repository; keep Desktop, IDE extension, and mobile excluded until
   separate canaries exist.
5. Re-run `python -m unittest tests.test_host_compatibility -v` and
   `python scripts/host_compatibility.py --json`.

### Task 4: Rewrite the golden path around the user's moments

**Files:**

- Modify: `README.md`
- Modify: `README.tr.md`
- Modify: `docs/Kurulum.md`
- Modify: `docs/Host-Uyumlulugu.md`
- Modify: corresponding English compatibility/install docs if present
- Modify: `site/index.html`
- Modify: `docs/index.html`
- Modify: site markup tests where the new contract needs regression coverage

1. Add a top-level choice: “First setup” versus “Already installed.”
2. Make the installed path a plain-language ferman in a fresh agent session.
3. Move doctor/update/recovery under maintenance.
4. Replace no-clone examples that incorrectly use `scripts/divan.py` with the
   verified release bootstrap path.
5. Explain that the bootstrap should be retained for maintenance and that
   Divan does not secretly modify PATH.
6. Add host-surface scope and explicit Codex IDE/mobile exclusions.
7. Keep Turkish and English meanings synchronized.
8. Run community, documentation, host, and site-focused tests.

### Task 5: Record the bounded release decision

**Files:**

- Modify: `CHANGELOG.md`
- Modify: `BLUEPRINT.md`
- Modify: `.divan/progress.md`
- Modify: `docs/Durum-ve-Yol-Haritasi.md` if required by release validation
- Modify: release manifest only when a new permanent surface is introduced

1. State that v1.0.2 remains immutable.
2. Record v1.0.3 as a friction-removal release, not a new runtime.
3. Keep future adaptive profiles and multi-engine adapters as separate,
   evidence-triggered slices.
4. Recalculate `divan impact` for the final path set and ensure no path is
   unclassified.

### Task 6: Verify, review, publish, and read back

**Files:**

- Create: `.divan/evidence/teftis-20260801-v103-friendly-control-plane.md`
- Modify: release/version surfaces required by `scripts/release.py`

1. Run focused doctor, compatibility, CLI, community, and site suites.
2. Run `python scripts/verify.py` and `git diff --check` from a clean-state
   verification flow.
3. Perform an independent review and address actionable findings.
4. Commit on `codex/v110-friendly-control-plane`, push, and open a PR.
5. Wait for all required GitHub checks; fix real failures instead of rerunning
   blindly.
6. Merge only after review and green CI.
7. Prepare v1.0.3 through the repository release workflow; never move or
   rewrite v1.0.2.
8. Download published assets, verify checksums/attestations, and read back
   README, Pages, Wiki, and the exact bootstrap command.
9. Mark the persistent goal complete only after no required work remains.
