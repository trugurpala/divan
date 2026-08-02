# Divan Risk Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the actionable code-scanning, public-command, dependency-observation,
and duplicate-test risks proven by the 2026-08-02 audit.

**Architecture:** Keep the stdlib-only Divan runtime unchanged. Add one Python
regression harness that executes distributed JavaScript with Node, extend the
existing verification runner with an optional coverage command sequence, and
repair canonical documentation and impact metadata in place.

**Tech Stack:** Python 3.11+, `unittest`, Node.js 24, GitHub Actions, JSON,
Markdown.

## Global Constraints

- Preserve the immutable v1.3.3 tag and release assets.
- Add no runtime dependency and fork no external repository.
- Treat claim patterns as literal text; do not execute user-provided regex.
- Keep default `python scripts/verify.py` behavior backward compatible.
- Do not change GitHub rulesets, repository account settings, or alert state.

---

### Task 1: Security regression contract

**Files:**
- Create: `tests/test_distributed_skill_security.py`

**Interfaces:**
- Consumes: Node.js and the existing exported Vercel Optimize functions.
- Produces: `DistributedSkillSecurityTests`, the regression gate for skill code.

- [ ] **Step 1: Write failing behavioral and source-boundary tests**

Add tests that invoke Node to prove literal-pattern handling, backslash-safe
Markdown rendering, all-star package export replacement, bootstrap token
non-reflection, and p5.js Subresource Integrity.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m unittest tests.test_distributed_skill_security -v
```

Expected: failures identify regex execution, incomplete escaping, first-only
star replacement, token interpolation, and the missing integrity attribute.

- [ ] **Step 3: Keep the failing output as the regression evidence**

Do not weaken assertions to match current behavior. Each assertion must describe
the safer public contract in the design document.

### Task 2: Minimal distributed-skill security fixes

**Files:**
- Modify: `plugins/core-pack/skills/brainstorming/scripts/server.cjs`
- Modify: `plugins/core-pack/skills/brainstorming/scripts/helper.js`
- Modify: `plugins/react-pack/skills/vercel-optimize/lib/verify-claim.mjs`
- Modify: `plugins/react-pack/skills/vercel-optimize/lib/cost-coverage.mjs`
- Modify: `plugins/react-pack/skills/vercel-optimize/lib/render-report.mjs`
- Modify: `plugins/react-pack/skills/vercel-optimize/lib/workspace-resolver.mjs`
- Modify: `plugins/zanaat-pack/skills/algorithmic-art/templates/viewer.html`

**Interfaces:**
- Consumes: the tests from Task 1.
- Produces: literal-only claim matching and complete output/resource escaping.

- [ ] **Step 1: Remove token reflection from the bootstrap page**

Make `bootstrapPage()` parameterless, rely on the existing HttpOnly same-origin
cookie for subsequent HTTP/WebSocket authentication, and remove session-storage
token propagation from `helper.js`.

- [ ] **Step 2: Make claim matching literal-only**

Replace the regex-literal branch in `compilePattern` with a single escaped-string
construction. Preserve caller flags such as `g`.

- [ ] **Step 3: Complete Markdown and package-export replacement**

Escape backslashes before pipes/newlines in both Markdown helpers and use
`replaceAll('*', star)` for package export targets.

- [ ] **Step 4: Pin the p5.js resource**

Add
`integrity="sha384-Mhzoc5EVkjFUVtIW2M3h8BgXtFlUsUpu9lTCThPrV7+k6MN6vTi079rew0LkvgFb"`
and `crossorigin="anonymous"` to the existing p5.js script element.

- [ ] **Step 5: Run focused security tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_distributed_skill_security -v
```

Expected: all security regression tests pass.

### Task 3: Public command and durable-state truth

**Files:**
- Modify: `tests/test_community.py`
- Modify: `tests/test_devral.py`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `README.tr.md`
- Modify: `docs/Project-Contract.md`
- Modify: `docs/Project-Contract.tr.md`
- Modify: `docs/Host-Uyumlulugu.md`
- Modify: `BLUEPRINT.md`
- Modify: `.divan/progress.md`

**Interfaces:**
- Consumes: current CLI parser behavior and release v1.3.3 truth.
- Produces: copy-paste-safe public commands and a current next-action record.

- [ ] **Step 1: Add failing documentation contract assertions**

Assert that active public pages contain `audit --project . --json`, never
`audit --project . --format json`, and that active host/progress guidance names
v1.3.3.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -m unittest tests.test_community tests.test_devral -v
```

Expected: assertions fail on the current invalid command and stale state.

- [ ] **Step 3: Repair canonical English and Turkish surfaces**

Replace only active instructions, preserve historical release records, keep
`README.md` byte-identical to `README.en.md`, and state that the next work is
security-alert triage rather than republishing an old release.

- [ ] **Step 4: Run documentation gates**

Run:

```powershell
python -m unittest tests.test_community tests.test_devral -v
python scripts/prose.py --check
python scripts/handoff.py --check
python scripts/wiki.py --check
```

Expected: all commands exit zero.

### Task 4: Single-pass coverage and dependency observation

**Files:**
- Modify: `tests/test_verify.py`
- Modify: `tests/test_workflows.py`
- Modify: `tests/test_company_engine.py`
- Modify: `scripts/verify.py`
- Modify: `.github/workflows/quality-gate.yml`
- Modify: `.github/dependabot.yml`
- Modify: `plugins/sadrazam/divan_runtime/impact-graph.json`
- Modify: `plugins/sadrazam/company/impact-graph.json`

**Interfaces:**
- Consumes: `verify.run(root, commands, cache_root)` and the existing timeout policy.
- Produces: `coverage_commands(commands)` and CLI flag `--coverage`.

- [ ] **Step 1: Add failing verification/workflow/impact tests**

Assert that coverage mode substitutes, rather than duplicates, unittest; the
quality workflow invokes `python scripts/verify.py --coverage` and has no direct
coverage test command; pip Dependabot is present; and nested skill implementation
plus Dependabot paths are classified.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -m unittest tests.test_verify tests.test_workflows tests.test_company_engine -v
```

Expected: the new assertions fail against the current duplicate-test workflow
and incomplete impact graph.

- [ ] **Step 3: Implement coverage command substitution**

Add argparse parsing for `--coverage`. Replace the unittest command with:

```text
-m coverage run -m unittest discover -s tests -v
-m coverage report --fail-under=64
```

Teach `command_class` to classify the coverage-run child as `test` and leave the
default sequence unchanged.

- [ ] **Step 4: Update CI, Dependabot, and impact graphs**

Use one `python scripts/verify.py --coverage` call, add weekly pip observation,
and add rules for nested skill implementation and repository-security metadata.
Keep canonical and legacy impact JSON byte-identical.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run the Step 2 command again. Expected: all focused tests pass.

### Task 5: Integrated verification and GitHub handoff

**Files:**
- Modify: `release-manifest.json` only if the release checker requires new public
  surfaces to be registered.
- Create: `.divan/evidence/teftis-20260802-risk-hardening.md`

**Interfaces:**
- Consumes: all changes and test evidence from Tasks 1-4.
- Produces: one reviewable branch and pull request; no release.

- [ ] **Step 1: Recalculate actual impact**

Run the Divan impact command for every changed path and require an empty
`unclassified_paths` array.

- [ ] **Step 2: Run focused static and repository gates**

Run:

```powershell
ruff check .
mypy scripts evals plugins/sadrazam/divan_runtime plugins/sadrazam/company
python scripts/prose.py --check
python scripts/release.py --check
python scripts/verify.py
python scripts/verify.py --coverage
git diff --check
```

Expected: every command exits zero; the two full test modes each execute one
unittest suite.

- [ ] **Step 3: Record bounded evidence**

Write only command summaries, counts, known remaining Scorecard/governance
items, and the exact next action. Do not claim CodeQL alerts are closed until a
new GitHub scan confirms that state.

- [ ] **Step 4: Commit, push, and open a ready pull request**

Use branch `codex/v134-risk-hardening`. The pull request must separate proven
fixes from deferred repository-setting and large-refactor work.

- [ ] **Step 5: Observe required CI**

Do not report completion while required GitHub checks are pending or failing.
