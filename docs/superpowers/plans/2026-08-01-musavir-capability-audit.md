# Musavir Capability Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Divan a deterministic, evidence-based way to assess current task capability gaps, research technology choices, and apply only bounded local improvements.

**Architecture:** Extend the existing `musavir` skill instead of creating a new runtime. A stdlib-only Python command validates and scores an explicit requirement list; focused references own the audit and toolkit guidance, while contract evals and repository tests protect behavior.

**Tech Stack:** Markdown skill contracts, Python 3 standard library, `unittest`, Divan eval contracts and catalog generator.

## Global Constraints

- Percentages describe task-specific capability coverage, never model intelligence or universal software quality.
- Unstable technology claims require current official primary-source verification.
- Add no package, MCP server, daemon, hosted service, or runtime dependency.
- Apply automatically only to bounded, reversible local files after explicit authorization.
- Paid services, accounts, secrets, broad permissions, security changes, external messages, destructive actions, commit, push, and release require separate authorization.
- Do not claim a win rate without a real baseline-versus-skill provider evaluation.

---

### Task 1: Deterministic capability scorer

**Files:**
- Create: `tests/test_musavir_capability_score.py`
- Create: `plugins/sadrazam/skills/musavir/scripts/score_capabilities.py`

**Interfaces:**
- Consumes: UTF-8 JSON from a file path or standard input with `requirements: list[object]`.
- Produces: JSON containing `requirement_count`, status counts, `coverage_percent`, `gap_percent`, and `confidence_percent`; exits `2` with a concise stderr message for invalid input.

- [ ] **Step 1: Write the failing happy-path test**

```python
payload = {"requirements": [
    {"id": "repo", "status": "verified", "evidence": ["AGENTS.md read"]},
    {"id": "browser", "status": "partial"},
    {"id": "release", "status": "unknown"},
    {"id": "mobile", "status": "missing"},
]}
assert result["coverage_percent"] == 37.5
assert result["gap_percent"] == 62.5
assert result["confidence_percent"] == 75.0
```

- [ ] **Step 2: Add rejection tests**

Cover an empty list, duplicate IDs, an unsupported status, malformed JSON,
missing string ID, and non-string evidence. Each case must return exit code `2`
without a traceback.

- [ ] **Step 3: Run tests and observe RED**

Run: `python tests/test_musavir_capability_score.py -v`

Expected: FAIL because `score_capabilities.py` does not exist.

- [ ] **Step 4: Implement validation and scoring**

Use only `argparse`, `json`, `sys`, and `pathlib`. Keep status weights in one
constant, reject unknown top-level shapes, preserve deterministic key order, and
round percentages to one decimal place.

- [ ] **Step 5: Run tests and reach GREEN**

Run: `python tests/test_musavir_capability_score.py -v`

Expected: all capability scorer tests pass.

- [ ] **Step 6: Record the local checkpoint**

Run: `git diff -- tests/test_musavir_capability_score.py plugins/sadrazam/skills/musavir/scripts/score_capabilities.py`

Expected: only the test and scorer are present. Do not commit without an
explicit user instruction.

### Task 2: Musavir workflow, toolkit, and eval contract

**Files:**
- Modify: `plugins/sadrazam/skills/musavir/SKILL.md`
- Create: `plugins/sadrazam/skills/musavir/references/capability-audit.md`
- Create: `plugins/sadrazam/skills/musavir/references/toolkit-2026.md`
- Create: `plugins/sadrazam/skills/musavir/evals/evals.json`

**Interfaces:**
- Consumes: repository context, current host evidence, user task, and official primary-source research.
- Produces: requirement ledger, scorer result, `KEEP | ADD | LATER | REPLACE | REJECT` decisions, bounded changes, and state-separated reporting.

- [ ] **Step 1: Add three contract eval cases**

Create cases for a percentage self-audit, modernization of a conflicting legacy
stack, and an over-broad "decide and apply" request. Require an explicit
denominator and evidence, rejection of fake AI-IQ percentages, conflict-aware
technology decisions, and approval boundaries.

- [ ] **Step 2: Write the audit reference**

Document requirement discovery, evidence levels, scorer invocation, research
rules, autonomy boundaries, and the distinction between local, committed,
pushed, published, and live states.

- [ ] **Step 3: Write the current toolkit matrix**

Group web UI, contracts/data, testing, observability/security, governance, and
mobile tools. For every recommendation specify delivery model, trigger,
conflict, and decision. Mark Moment, NativeBase, and React Native Camera as
replacement paths only after verifying their official maintenance notices.

- [ ] **Step 4: Update the skill router**

Extend the frontmatter triggers and make `SKILL.md` read the audit reference for
self-assessment requests and the toolkit reference for stack modernization.
Require primary-source revalidation for version, deprecation, pricing,
security, and compatibility claims.

- [ ] **Step 5: Validate the eval contract**

Run: `python evals/run.py --check --skill musavir`

Expected: the `musavir` eval file is discovered and valid. If the runner uses a
different local flag, inspect `python evals/run.py --help` and use its documented
validation command.

- [ ] **Step 6: Record the local checkpoint**

Run: `git diff -- plugins/sadrazam/skills/musavir`

Expected: only the focused skill, references, script, and eval contract changed.
Do not commit without an explicit user instruction.

### Task 3: Catalog, product record, and canonical verification

**Files:**
- Modify: `docs/skill-catalog.md` using the generator
- Modify: `BLUEPRINT.md`
- Verify: all files in the working tree

**Interfaces:**
- Consumes: final `musavir` frontmatter and the repository verification suite.
- Produces: synchronized public catalog, dated implementation record, and fresh verification evidence.

- [ ] **Step 1: Regenerate the catalog**

Run: `python scripts/catalog.py --render`

Expected: `docs/skill-catalog.md` reflects the expanded `musavir` description.

- [ ] **Step 2: Add the Blueprint record**

Record the capability-audit feature, deterministic formula, bounded autonomy
rules, and explicit non-claims: no provider win rate, release, push, or live
deployment.

- [ ] **Step 3: Run focused checks**

Run:

```powershell
python tests/test_musavir_capability_score.py -v
python scripts/catalog.py --check
python scripts/validate.py
```

Expected: every command exits `0`.

- [ ] **Step 4: Run canonical verification**

Run:

```powershell
python scripts/verify.py
git diff --check
```

Expected: both commands exit `0`; no required session remains running.

- [ ] **Step 5: Inspect the final working tree**

Run: `git status --short` and `git diff --stat`.

Expected: only planned local changes are listed. Report tested and untested
states separately, and do not commit, push, or release.
