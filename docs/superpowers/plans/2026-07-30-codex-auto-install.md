# Codex Desktop Auto-Install Implementation Plan

> **For Codex:** Follow the executing-plans workflow, keep every production
> change behind a failing test, and verify each task before continuing.

**Goal:** Make one explicit Divan install command diagnose Codex CLI execution
and choose the strongest honest installation route.

**Architecture:** A new host probe classifies process launch failures. Host
doctor exposes the diagnosis. The lifecycle CLI adds an opt-in `auto` profile
that preserves the native path when healthy and delegates only eligible
failures to the existing verified skill installer.

**Tech Stack:** Python standard library, PowerShell, POSIX shell, unittest,
GitHub Actions.

---

### Task 1: Specify process-launch diagnoses

**Files:**

- Create: `scripts/host_probe.py`
- Modify: `tests/test_host_install.py`

1. Add failing tests for executable missing, access denied, invalid executable,
   and normal UTF-8 execution.
2. Run the focused tests and confirm the new cases fail for the expected
   missing behavior.
3. Implement stable probe markers and OS error classification.
4. Re-run the focused tests and confirm they pass.
5. Commit the diagnosis boundary.

### Task 2: Expose honest doctor results

**Files:**

- Modify: `scripts/host_adapters.py`
- Modify: `scripts/host_lifecycle.py`
- Modify: `tests/test_host_doctor.py`

1. Add failing tests for all five `cli_status` values.
2. Add failing tests that invalid JSON blocks while launch failures recommend
   the auto profile.
3. Run the focused doctor tests and confirm red.
4. Map probe results and JSON parsing into the public doctor contract.
5. Re-run focused tests and confirm green.
6. Commit the doctor contract.

### Task 3: Add the opt-in auto profile

**Files:**

- Modify: `scripts/host_lifecycle.py`
- Modify: `scripts/divan.py`
- Modify: `tests/test_host_install.py`
- Modify: `tests/test_divan_cli.py`

1. Add failing parser and routing tests for `--profile auto`.
2. Add failing selection tests for native, fallback, and blocked decisions.
3. Add a failing test proving plain install remains native and unchanged.
4. Run focused tests and confirm red.
5. Implement `native|auto` parsing and Codex-only validation.
6. Implement dry-run decision output.
7. Re-run focused tests and confirm green.
8. Commit the profile and decision engine.

### Task 4: Execute and verify the canonical fallback

**Files:**

- Modify: `scripts/host_lifecycle.py`
- Modify: `tests/test_host_install.py`
- Modify: `tests/fixtures/host_runtime/**` only if a new fixture is required

1. Add a failing test that auto execution calls the platform installer.
2. Add failing tests for manifest verification, capability declaration,
   rollback command, and failed installer propagation.
3. Run focused tests and confirm red.
4. Delegate to `install_codex.ps1` or `install_codex.sh`.
5. Read and validate the resulting fallback manifest.
6. Emit one exact next command and one exact rollback command.
7. Re-run focused tests and confirm green.
8. Commit fallback execution.

### Task 5: Synchronize user-facing documentation

**Files:**

- Modify: `README.md`
- Modify: `README.tr.md`
- Modify: `docs/Kurulum.md`
- Modify: `docs/Installation.md`
- Modify: `docs/Host-Uyumlulugu.md`
- Modify: `docs/Host-Compatibility.md`
- Modify: `site/index.html`
- Modify: `site/tr/index.html`
- Modify: `CHANGELOG.md`
- Modify: `BLUEPRINT.md`
- Modify: `.divan/progress.md`
- Modify: `release-manifest.json`

1. Add the one-command auto profile to Turkish and English installation docs.
2. Add a clear native-versus-fallback capability table.
3. Update host compatibility without raising the Codex tier before canary
   evidence exists.
4. Register every new permanent release surface.
5. Run documentation, manifest, and site validations.
6. Commit the synchronized product surface.

### Task 6: Inspect, canary, and release

**Files:**

- Modify: `.divan/evidence/**`
- Modify: release metadata required by the repository release workflow

1. Run focused unit tests.
2. Run the canonical full verification suite.
3. Perform an independent code review and address actionable findings.
4. Run a clean Windows skill-fallback install/uninstall canary and prove
   unrelated skills survive.
5. Record privacy-filtered evidence.
6. Open the pull request and wait for every required GitHub check.
7. Merge only after green checks and review evidence.
8. Prepare and publish v0.18.1 if the repository release policy requires a
   release for installer changes.
9. Download release assets again and verify checksums, provenance, Pages, Wiki,
   and the exact install command.

