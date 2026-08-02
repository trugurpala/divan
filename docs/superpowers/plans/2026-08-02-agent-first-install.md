# Agent-First Install Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make a Codex or Claude desktop agent able to install Divan from this repository through an immutable release, prove `READY`, and give a short restart-and-use message without changing unrelated plugins.

**Architecture:** Keep the existing stdlib-only host lifecycle and fallback authority. Add a small machine-readable install contract at the repository root, normalize native and fallback records through one result adapter, and make the human CLI render only the outcome while retaining detailed JSON for agents and tests.

**Tech Stack:** Python standard library, deterministic JSON, existing host adapters/journals, Markdown documentation, unittest.

## Global Constraints

- Use the latest immutable GitHub Release; never resolve `main`, `master`, or `latest` as an install source.
- Preview must be write-free; execute must preserve unrelated marketplaces and plugins.
- A successful install requires a real doctor result with `status: healthy` (`READY`).
- Native and `verified-skill-fallback` capabilities must remain distinct.
- Do not modify PATH, shell profiles, or unrelated extensions.
- Keep runtime dependency-free and preserve checksum, source-ref, source-commit, and transaction authority.

### Task 1: Inspect and lock the existing contracts

**Files:** `scripts/host_lifecycle.py`, `scripts/host_profiles.py`, `scripts/host_cli.py`, `scripts/host_adapters.py`, `scripts/host_install_journal.py`, `tests/test_host_install.py`, `tests/test_host_doctor.py`, README surfaces.

- Record the current native transaction and fallback manifest shapes.
- Reuse existing package and skill counters instead of creating a second catalog.
- Use the existing doctor aggregator as the only `READY` authority.

### Task 2: Add the agent install contract

**Files:** Create `INSTALL_FOR_AGENTS.md`, `divan-install.json`; modify `scripts/host_lifecycle.py`, `scripts/host_profiles.py`, `scripts/host_cli.py`, `scripts/host_install_journal.py`.

- Add versioned schema fields for product, hosts, release resolution, preview/execute/doctor templates, success marker, restart requirement, and natural-language daily use.
- Add normalized fields to every install result: `status`, `version`, `source_ref`, `source_commit`, `host`, `profile`, `package_count`, `skill_count`, `doctor_status`, `restart_required`, `next_action`, `recovery_command`.
- Keep `status` non-success until doctor is healthy; preserve rollback metadata on failure.
- Render a short human result with version, host/profile, doctor state, and restart instruction.

### Task 3: Add regression tests first, then implementation

**Files:** Create `tests/test_agent_install.py`; modify existing host tests only where the normalized contract is intentionally asserted.

- Validate required manifest keys and deterministic serialization.
- Validate native and fallback result normalization and capability boundaries.
- Reject `READY` claims when doctor is missing, unhealthy, or absent.
- Require `restart_required: true` for a verified fresh install.
- Verify human output omits command dumps on success and includes one recovery action on failure.

### Task 4: Make the public entrypoint agent-first

**Files:** Modify `README.md`, `README.en.md`, `README.tr.md`; add references from `docs/Kurulum.md` if required.

- Put the natural-language repository-install request before technical commands.
- Explain that the agent selects the immutable release, previews, executes, runs doctor, and asks for a full restart.
- Keep native/fallback differences and CLI details in secondary sections.
- State that daily use is natural language in a new Codex or Claude session.

### Task 5: Verify and report host gaps

- Run focused agent-install tests, prose/catalog/release checks, then `scripts/verify.py` and `git diff --check`.
- Verify the manifest is included in release surfaces.
- Report remaining Windows 11/Codex/Claude gaps honestly; do not claim a post-restart canary without a fresh session.
