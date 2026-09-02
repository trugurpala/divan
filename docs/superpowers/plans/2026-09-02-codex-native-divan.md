# Codex-native Divan V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a mechanically validated, skills-only Divan `2.0.0-alpha.1` package on an isolated rewrite branch without deleting legacy history.

**Architecture:** Add `plugins/divan` as the only new publishable package. Seven skills provide workflow routing and use references for deep engineering guidance. Standard-library Python validators and unit tests enforce the package contract; hooks and MCP stay out of the alpha.

**Tech Stack:** OpenAI plugin manifest, Agent Skills markdown, Python 3 standard library, unittest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-02-codex-native-divan-design.md`

## Global Constraints

- Preserve Git history and existing releases.
- Do not merge to `main` until validation and acceptance evidence exist.
- V2 alpha is skills-only: no MCP, apps, UI, or published hooks.
- Keep exactly seven high-signal top-level skills in the alpha.
- Use repository evidence before generic engineering preferences.
- Never claim completion without observed verification.

---

### Task 1: Plugin package and local marketplace

**Files:**
- Create: `plugins/divan/.codex-plugin/plugin.json`
- Create/update: `.agents/plugins/marketplace.json`

- [x] Add a stable `divan` plugin manifest at version `2.0.0-alpha.1`.
- [x] Point `skills` to `./skills/`.
- [x] Exclude MCP/app/hook fields from the alpha manifest.
- [x] Wire the repo marketplace to `./plugins/divan`.

### Task 2: Core skills and engineering references

**Files:**
- Create: `plugins/divan/skills/*/SKILL.md`
- Create: `plugins/divan/skills/quality-review/references/*.md`

- [x] Add seven narrowly triggered skills.
- [x] Put deep naming/types/architecture/database/reliability/security/testing/frontend guidance in references.
- [x] Keep heavy workflow out of trivial prose or general-explanation cases.

### Task 3: Validator with TDD

**Files:**
- Test: `tests/test_divan_v2.py`
- Create: `scripts/divan_v2_validate.py`

- [x] Write failing validator tests.
- [x] Confirm RED because the validator does not exist.
- [x] Implement the minimum validator.
- [x] Confirm all validator tests pass.

### Task 4: Routing eval contract

**Files:**
- Test: `tests/test_divan_v2_evals.py`
- Create: `evals/divan-v2-routing.json`

- [x] Write the contract test first.
- [x] Confirm RED because the eval file does not exist.
- [x] Add five positive and three negative cases.
- [ ] Run the full suite and confirm GREEN.

### Task 5: CI and branch acceptance

**Files:**
- Create: `.github/workflows/divan-v2-quality.yml`

- [ ] Run validator directly.
- [ ] Run all Divan V2 unittests.
- [ ] Add the same commands to GitHub Actions.
- [ ] Push only to `rewrite/codex-native`.
- [ ] Inspect branch diff and CI state.
