# Divan v0.16.0 Adoption and Drift Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `executing-plans` task-by-task. Every behavior change follows
> `test-driven-development`; completion requires `requesting-code-review`,
> `verification-before-completion`, and `finishing-a-development-branch`.

**Goal:** Make an initialized Divan Project OS safely maintainable through
ownership-aware status, schema migration, update, repair, goal archive, and
privacy-safe adoption evidence.

**Architecture:** Keep the stdlib-only portable core. Add focused state,
lifecycle, transaction, archive, and adoption modules behind the existing
Company CLI. Managed payload hashes establish ownership; user-modified content
always fails closed.

**Tech Stack:** Python standard library, `unittest`, deterministic JSON,
GitHub Actions, reproducible Python zipapp.

## Global constraints

- Work only in `codex/v016-adoption-drift`; preserve the dirty local `main`.
- Keep five packages and 41 discoverable skills.
- English machine interfaces are canonical; Turkish remains first-class UTF-8.
- All mutations are dry-run-first and require `--execute`.
- Do not execute target-project code, fetch an arbitrary ref, persist secrets,
  overwrite user-modified content, or add a daemon/dashboard/provider.
- v1 remains 7/8 until a real independent user supplies valid evidence.

---

### Task 1: Baseline and ownership state

**Files:**
- Create: `plugins/sadrazam/company/project_state.py`
- Modify: `plugins/sadrazam/company/project_os.py`
- Modify: `scripts/build_project_runner.py`
- Test: `tests/test_project_lifecycle.py`
- Test: `tests/test_project_runner.py`

- [ ] Add failing schema tests for exact source identity, managed payload
  records, deterministic serialization, unsafe paths, duplicates, unknown
  schemas, and secret/path rejection.
- [ ] Run the focused tests and confirm failures are caused by missing
  `project_state`.
- [ ] Implement frozen state models and strict loaders/renderers.
- [ ] Add failing init tests requiring config schema 2 plus
  `.divan/install-state.json`, with an idempotent second init.
- [ ] Implement schema 2 init and immutable runner metadata.
- [ ] Run focused and existing init/runner tests; refactor only while green.
- [ ] Commit `feat: add project ownership state`.

### Task 2: Read-only status and drift classification

**Files:**
- Modify: `plugins/sadrazam/company/project_state.py`
- Create: `plugins/sadrazam/company/project_lifecycle.py`
- Modify: `plugins/sadrazam/company/cli.py`
- Modify: `scripts/divan.py`
- Test: `tests/test_project_lifecycle.py`
- Test: `tests/test_divan_cli.py`

- [ ] Add failing tests for every managed-surface classification and overall
  status precedence.
- [ ] Prove status leaves the complete project and trusted-state roots
  byte-identical.
- [ ] Implement `project status`, exact actionable errors, stable JSON, and
  English/Turkish human output.
- [ ] Add CLI forwarding and exit-code tests, then implement the nested
  `project` command group.
- [ ] Run focused tests and commit `feat: report project lifecycle drift`.

### Task 3: Shared transaction engine and schema migration

**Files:**
- Create: `plugins/sadrazam/company/project_transactions.py`
- Modify: `plugins/sadrazam/company/project_os.py`
- Modify: `plugins/sadrazam/company/project_lifecycle.py`
- Test: `tests/test_project_lifecycle.py`
- Test: `tests/test_project_os.py`

- [ ] Add characterization tests around init locks, ACL/mode checks, authority,
  journal transitions, recovery, stale preimages, and second interruption.
- [ ] Extract common transaction primitives without changing init behavior.
- [ ] Add failing update-plan tests for unchanged whole files, marked blocks,
  new surfaces, stale records, user edits, unsafe paths, and ownership-state
  ordering.
- [ ] Implement deterministic update planning and execution.
- [ ] Add failing v0.15 schema 1 migration tests for library, public-web, and
  monorepo fixtures.
- [ ] Implement schema 1 reproduction, trusted ownership snapshot, schema 2
  migration, rollback, and future-schema rejection.
- [ ] Run lifecycle/init suites and commit
  `feat: add transactional project updates`.

### Task 4: Safe repair

**Files:**
- Modify: `plugins/sadrazam/company/project_lifecycle.py`
- Test: `tests/test_project_lifecycle.py`

- [ ] Add failing tests for missing owned whole files and interrupted trusted
  transactions.
- [ ] Add failing tests proving modified whole files, damaged blocks, unowned
  paths, unsafe paths, and source drift remain `BLOCKED`.
- [ ] Implement dry-run repair and transaction execution without a force flag.
- [ ] Inject failure at every write boundary and verify repeatable recovery.
- [ ] Run focused suites and commit `feat: repair only proven project files`.

### Task 5: Goal archive

**Files:**
- Create: `plugins/sadrazam/company/goal_archive.py`
- Modify: `plugins/sadrazam/company/cli.py`
- Test: `tests/test_goal_archive.py`
- Test: `tests/test_divan_cli.py`

- [ ] Add failing phase, receipt, hash, collision, symlink, deterministic-date,
  dry-run, and rollback tests.
- [ ] Implement archive planning from verified receipt data.
- [ ] Implement transactional archive copy, verification, controlled source
  removal, `archive.json`, and repeatable recovery.
- [ ] Add `goal archive` CLI routing and stable results.
- [ ] Run focused suites and commit `feat: archive verified project goals`.

### Task 6: Adoption receipt

**Files:**
- Create: `plugins/sadrazam/company/adoption.py`
- Modify: `plugins/sadrazam/company/cli.py`
- Test: `tests/test_adoption.py`
- Test: `tests/test_divan_cli.py`

- [ ] Add failing exact-schema and deterministic JSON/Markdown export tests.
- [ ] Add failing redaction tests for secrets, emails, usernames, absolute
  paths, remotes, command bodies, and unrelated plugins.
- [ ] Implement export with required host/version and safe maintainer default.
- [ ] Implement verification outcomes `valid-owner-canary`,
  `valid-independent-declaration`, and `invalid`, without changing v1 gates.
- [ ] Run focused suites and commit `feat: export adoption evidence safely`.

### Task 7: Portable runner, documentation, and release preparation

**Files:**
- Modify: `scripts/build_project_runner.py`
- Modify: `plugins/sadrazam/company/impact-graph.json`
- Modify: public English/Turkish docs, Wiki/Page sources, manifests, blueprint,
  changelog, and progress ledger required by the impact graph.

- [ ] Add failing runner membership/reproducibility and impact coverage tests.
- [ ] Package every new module and prove two clean builds are byte-identical.
- [ ] Add project lifecycle paths to the fail-closed impact graph.
- [ ] Synchronize canonical English and Turkish user surfaces, explaining host
  update versus project update, audit versus lifecycle status, and honest
  owner-canary evidence.
- [ ] Run documentation, Wiki, naming, catalog, and publication checks.
- [ ] Prepare v0.16.0 only through
  `python scripts/release.py --prepare 0.16.0`.
- [ ] Commit `release: prepare Divan v0.16.0`.

### Task 8: Review and public delivery

- [ ] Run the complete local validation suite, Ruff, mypy, Clean Code,
  coverage, official skill validators, and `git diff --check`.
- [ ] Perform a fresh whole-branch code review and fix every material finding
  test-first.
- [ ] Push a ready PR, wait for all required checks, and merge without bypass.
- [ ] Verify immutable main/tag/Release, ZIP, checksums, SBOM, runner,
  attestations, Pages, and Wiki.
- [ ] Create the public secrets-free `trugurpala/divan-project-canary`, run
  v0.15→v0.16 migration, drift, repair, rollback, archive, release, and live
  readback from released assets.
- [ ] Record the canary only as `valid-owner-canary`; leave v1 at 7/8.
- [ ] Capture four pre-upgrade host inventories, transactionally upgrade Claude
  and Codex, verify both healthy with five packages/41 skills, and prove all
  unrelated inventory unchanged.
- [ ] Remove only the merged agent worktree/branch/scratch artifacts and retain
  user changes plus transaction journals.
