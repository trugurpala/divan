# Divan Company OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `core-pack:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an English-canonical, bilingual Divan Company OS that discovers
a project, selects qualified Core/UI/React/Zanaat capabilities, calculates
change impact, and remains compatible with existing installations.

**Architecture:** A standard-library engine and machine-readable registries
ship inside `plugins/sadrazam/company`. The repository-level English CLI loads
that engine and delegates host lifecycle operations to an English module while
legacy Turkish entry points remain narrow wrappers.

**Tech Stack:** Python 3 standard library, JSON contracts, Agent Skills,
GitHub Actions, unittest.

## Global Constraints

- No default daemon, model API, hosted runtime, or third-party harness.
- English is canonical for technical contracts; Turkish is a complete locale.
- Existing v0.13 host transactions and unrelated plugins remain compatible.
- Project inspection is read-only, bounded, deterministic, and path-safe.
- React/UI/Zanaat capabilities are selected by task and project evidence, not
  installed as application runtime dependencies.
- Every production behavior starts with a failing test.

---

### Task 1: Portable company contracts

**Files:**
- Create: `plugins/sadrazam/company/roles.json`
- Create: `plugins/sadrazam/company/workflows.json`
- Create: `plugins/sadrazam/company/frameworks.json`
- Create: `plugins/sadrazam/company/impact-graph.json`
- Create: `tests/test_company_engine.py`

**Interfaces:**
- Produces: schema-versioned role, workflow, framework, and impact dictionaries.
- Produces: package-qualified skill references shaped as
  `{"package": "core-pack", "skill": "test-driven-development"}`.

- [ ] Write tests asserting unique identifiers, valid role/workflow references,
  known package/skill pairs, English schema keys, bilingual labels, and safe
  relative detector paths.
- [ ] Run `python -m unittest tests.test_company_engine -v` and confirm the
  missing registries fail.
- [ ] Add the four JSON registries with 12 roles, 8 workflows, bounded framework
  detectors, and conditional impact rules.
- [ ] Re-run the focused tests and keep the contracts deterministic.

### Task 2: Project intelligence and impact engine

**Files:**
- Create: `plugins/sadrazam/company/engine.py`
- Create: `plugins/sadrazam/company/__init__.py`
- Modify: `tests/test_company_engine.py`

**Interfaces:**
- Produces: `load_contracts(root: Path) -> Contracts`.
- Produces: `inspect_project(project: Path, contracts: Contracts) -> dict`.
- Produces: `plan_intent(intent: str, project: Path, contracts: Contracts) -> dict`.
- Produces: `calculate_impact(paths: list[str], contracts: Contracts) -> dict`.

- [ ] Add failing tests for Next.js, React, Python, static web, documentation,
  and generic detection without executing project code.
- [ ] Add failing tests for feature/UI/bug/release/integration/creative routing,
  minimal role selection, and Core/UI/React/Zanaat pack inclusion.
- [ ] Add failing tests for transitive impact closure, stable ordering, malformed
  registries, absolute paths, traversal paths, and symlink escape rejection.
- [ ] Implement immutable contract dataclasses, validation, bounded marker
  reading, keyword scoring, role/skill expansion, and impact traversal.
- [ ] Run the focused suite after every red-green increment.

### Task 3: English CLI and host compatibility

**Files:**
- Move: `scripts/kur-hostlar.py` to `scripts/host_lifecycle.py`
- Create: `scripts/divan.py`
- Create: `scripts/kur-hostlar.py`
- Create: `plugins/sadrazam/company/cli.py`
- Create: `tests/test_divan_cli.py`
- Modify: host recovery command producers and their tests.

**Interfaces:**
- Produces: `python scripts/divan.py inspect|plan|impact|company-validate`.
- Produces: `python scripts/divan.py install|update|doctor|recover`.
- Preserves: legacy `python scripts/kur-hostlar.py` v0.13 arguments.

- [ ] Write failing CLI tests for stable UTF-8 JSON, English/Turkish human
  output, dry-run defaults, host argument translation, and legacy parity.
- [ ] Move the implementation to `host_lifecycle.py` and make the old file a
  deprecation wrapper without duplicating lifecycle logic.
- [ ] Implement portable and repository CLIs; ensure generated recovery commands
  use `scripts/divan.py recover`.
- [ ] Run host install/doctor/upgrade and CLI focused suites.

### Task 4: Sadrazam automatic company routing

**Files:**
- Modify: `plugins/sadrazam/skills/sadrazam/SKILL.md`
- Create: `plugins/sadrazam/commands/company.md`
- Modify: `plugins/sadrazam/.claude-plugin/plugin.json`
- Modify: both marketplace descriptions.
- Modify: `tests/test_validate.py`

**Interfaces:**
- Consumes: company CLI plan result.
- Produces: a natural-language-first workflow where users need not name skills.

- [ ] Write a failing repository contract test requiring Sadrazam to discover
  the project, calculate impact, select the smallest team, and treat commands
  as optional expert interfaces.
- [ ] Add the Company OS protocol to Sadrazam and the optional `/company`
  inspection command.
- [ ] Update English marketplace copy without changing the five-package
  inventory.
- [ ] Run repository, marketplace, and official Agent Skills validators.

### Task 5: English canonical naming and bilingual community surface

**Files:**
- Create: `registry/naming-policy.json`
- Create: `docs/Company-OS.md`
- Create: `docs/Company-OS.tr.md`
- Modify: `README.md`, `README.en.md`, `README.tr.md`, `AGENTS.md`,
  `CONTRIBUTING.md`, `CONTRIBUTING.en.md`, Wiki sources, site sources,
  `release-manifest.json`, and community standards.
- Modify: tests for community, Wiki, publication, workflows, and naming.

**Interfaces:**
- Produces: English canonical documentation and Turkish first-class links.
- Produces: a machine-enforced ASCII-English naming policy for new technical
  files while explicitly allowlisting compatibility and brand surfaces.

- [ ] Add failing naming-policy and documentation tests.
- [ ] Make `README.md` English canonical, preserve Turkish as `README.tr.md`,
  and retain `README.en.md` as a compatibility surface.
- [ ] Document Company OS, framework routing, impact semantics, privacy,
  limitations, and locale behavior in both languages.
- [ ] Synchronize Wiki/site/catalog/install/community/publication surfaces.
- [ ] Run UI accessibility markup tests and the UI Pack pre-delivery checklist;
  do not add React to Divan’s static site.

### Task 6: Repository integration and delivery evidence

**Files:**
- Modify: `scripts/validate.py`, English canonical controllers and compatibility
  wrappers, `.github/workflows/*`, `registry/clean-code-baseline.json`,
  `BLUEPRINT.md`, `.divan/progress.md`.
- Create: `.divan/decisions/0005-company-os.md`
- Create: `.divan/evidence/teftis-20260723-company-os.md`

**Interfaces:**
- Produces: one primary validation chain covering company contracts and naming.
- Produces: truthful implementation evidence without behavioral improvement
  claims.

- [ ] Integrate `company-validate` and naming checks into local validation and
  the primary quality workflow.
- [ ] Run focused tests, then the entire AGENTS.md gate, Ruff, mypy, Clean Code,
  coverage, actionlint, Agent Skills validation, and Claude plugin validation.
- [ ] Request independent code review; resolve all critical and important
  findings with regression tests.
- [ ] Record exact evidence and update Blueprint/progress with the next concrete
  step. Do not claim release/global installation until PR, main, release, and
  both hosts are separately verified.

