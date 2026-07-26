# v0.16.0 Publication Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the canonical handoff reject stale instructions that attempt to
republish the latest immutable Divan release.

**Architecture:** `scripts/handoff.py` parses a small publication-state section
from `.divan/progress.md`, binds it to a tracked Markdown evidence record, and
compares it with the exact next-step section. Company OS classifies these
memory paths so the same validation is selected by impact analysis.

**Tech Stack:** Python 3.11+ standard library, `unittest`, Markdown, Company OS
JSON contracts.

## Global Constraints

- Do not change `VERSION` or immutable v0.16.0 release assets.
- Do not claim asset-byte, attestation, canary, dual-host, or independent-user
  evidence that was not reproduced.
- Keep all paths repository-relative and reject traversal.
- Write tests before production code.

---

### Task 1: Publication-state handoff contract

**Files:**
- Modify: `tests/test_devral.py`
- Modify: `scripts/handoff.py`

**Interfaces:**
- Consumes: `.divan/progress.md`, `VERSION`, and one repository-relative
  publication evidence path.
- Produces: `denetle(kok: pathlib.Path) -> list[str]` errors for malformed,
  contradictory, or escaping publication state.

- [ ] **Step 1: Write the failing tests**

Add fixture helpers that write:

```text
## Yayın durumu
- Latest published release: v0.16.0
- Published commit: 5513e73d5faa8657a22d813ecfec763a6089bea0
- Publication evidence: .divan/evidence/v016.md
```

Cover a valid state, an evidence mismatch, a stale v0.16.0 push/PR instruction,
and an allowed v0.16.1 candidate instruction.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_devral -v
```

Expected: the stale-state and evidence-binding assertions fail because the
current validator checks only file presence.

- [ ] **Step 3: Implement the minimal parser and validator**

Add strict regexes for SemVer, commit SHA, and evidence path; extract Markdown
sections; reject traversal; compare the evidence version/commit; compare SemVer
tuples; and reject push/open-PR/publish verbs only when the next step also names
the latest-published version.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_devral -v
```

Expected: all handoff tests pass.

### Task 2: Company OS impact classification

**Files:**
- Modify: `tests/test_company_engine.py`
- Modify: `plugins/sadrazam/company/impact-graph.json`

**Interfaces:**
- Consumes: canonical repository memory/evidence Markdown paths.
- Produces: no `unclassified_paths` and the company/documentation/release
  validation checks.

- [ ] **Step 1: Write the failing impact test**

Call `calculate_impact` with:

```python
[
    "AGENTS.md",
    "CLAUDE.md",
    "BLUEPRINT.md",
    ".divan/progress.md",
    ".divan/evidence/v016.md",
]
```

Assert that `unclassified_paths` is empty and the required checks are present.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  tests.test_company_engine.ImpactTests.test_project_memory_markdown_has_complete_impact -v
```

Expected: the Markdown memory paths are reported as unclassified.

- [ ] **Step 3: Add the exact impact rule**

Add `project-memory` patterns for the three root handoff documents plus
`.divan/*.md` and `.divan/**/*.md`, with `company-validation`,
`documentation`, and `release-validation` effects.

- [ ] **Step 4: Verify GREEN**

Run the focused impact test and the complete `tests.test_company_engine`
module. Expected: both pass.

### Task 3: Correct the durable repository state

**Files:**
- Create: `.divan/evidence/teftis-20260725-v016-publication-handoff.md`
- Modify: `.divan/progress.md`
- Modify: `BLUEPRINT.md`

**Interfaces:**
- Consumes: reproduced PR, commit, tag, Release, Pages, and Wiki observations.
- Produces: a bound publication-state section and a non-stale next step.

- [ ] **Step 1: Write the bounded evidence record**

Record only PR #31, commit/tag identity, HTTP reachability, and v0.16.0 live
surface markers. List every unverified state explicitly.

- [ ] **Step 2: Update progress and blueprint**

Bind progress to the evidence record and make issue #34, independent non-owner
adoption evidence, the exact next step. Preserve v1 at 7/8.

- [ ] **Step 3: Re-run focused checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/handoff.py --check
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_devral \
  tests.test_company_engine -v
```

Expected: both commands pass.

### Task 4: Full verification and GitHub handoff

**Files:**
- Modify only files already listed in Tasks 1–3.

**Interfaces:**
- Consumes: the complete branch diff.
- Produces: local test evidence and a GitHub-ready commit.

- [ ] **Step 1: Run required gates**

Run the AGENTS.md commands with `PYTHONDONTWRITEBYTECODE=1`, plus Ruff, mypy,
Clean Code, Wiki, Company OS impact, and `git diff --check`.

- [ ] **Step 2: Recalculate actual impact**

Run `company/cli.py impact` over every changed path. Expected:
`unclassified_paths` is empty.

- [ ] **Step 3: Review and commit**

Inspect `git diff --check`, the exact changed-file list, and full test output.
Commit only the scoped files on branch `agent/v016-publication-handoff`.
