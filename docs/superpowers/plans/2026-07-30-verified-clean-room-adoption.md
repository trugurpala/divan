# Verified Clean-Room Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unverifiable independent-user v1 gate with a dry-run-first, machine-verifiable clean-room adoption proof that binds a pinned Divan release, a distinct real project, a verified goal, bounded passing checks, and privacy-safe offline evidence.

**Architecture:** Keep the feature inside Divan's existing nine-module stdlib runtime. `adoption.py` owns schema compatibility, serialization, and offline verification; a focused `adoption_proof.py` file inside the existing `records` module owns proof planning, safe check selection, bounded execution, journaling, and atomic promotion. Existing `engine`, `execution`, `timeouts`, `project_state`, `goals`, and `receipts` modules remain the sole authorities for discovery, subprocesses, timeout policy, installed source, goal state, and goal evidence.

**Tech Stack:** Python 3.11+ standard library, `unittest`, JSON/Markdown receipts, deterministic `.pyz` runners, Git/GitHub Actions, existing Divan release/Wiki/Pages tooling.

## Global Constraints

- Target mechanism release is `v0.18.3`; the v1 score remains 7/8 until a receipt produced by the released mechanism is committed and verified.
- Do not add a tenth top-level runtime module, database, daemon, telemetry, arbitrary shell execution, third-party runtime dependency, or external harness.
- Schema 2 initially qualifies only `claude-code` and `codex`; Cursor and other hosts remain schema-1 compatibility paths.
- `operator.role` is exactly `maintainer` or `external` and never changes eligibility.
- Preview executes no project checks and writes no project files. It reports a fixed host probe that execution will run; only `--execute` observes and binds the host version.
- Execute at most eight deduplicated checks, requires at least one test-class check, runs each check once, never retries, stops after the first failure, and uses the packaged timeout policy.
- Never persist project/home paths, remotes, URLs, raw argv, raw output, usernames, emails, secrets, environment values, or unrelated package inventory.
- Preserve schema-1 offline verification with explicit non-v1 statuses `valid-schema-1-owner-canary` and `valid-schema-1-independent-declaration`.
- A complete or partial Divan source signature blocks clean-room qualification; the caller cannot set `distinct_from_divan`.
- All project paths and workspaces must be real, contained, non-symlink/non-reparse paths.
- Keep English/Turkish README, Project Contract, installation, status, Wiki source, Pages, issue form, release manifest, and `.divan/progress.md` synchronized.
- Before public delivery run `python scripts/verify.py` and `git diff --check`; do not claim release until tag, assets, checksums, Pages, and Wiki have been read back.

---

## File and Interface Map

### Runtime

- `plugins/sadrazam/divan_runtime/adoption.py`
  - Preserve schema-1 export.
  - Add schema dispatch, schema-2 assembly, JSON/Markdown serialization, strict offline verification, privacy validation, and explicit compatibility statuses.
- `plugins/sadrazam/divan_runtime/adoption_proof.py`
  - Add immutable preflight, distinct-project classification, fixed host probe planning/execution, safe argv construction, check selection, execution journal, drift checks, receipt staging, and atomic promotion.
- `plugins/sadrazam/divan_runtime/modules.json`
  - Register `adoption_proof` under the existing `records` module and add `clean_room_adoption` capability without increasing the module count.
- `plugins/sadrazam/divan_runtime/cli_parser.py`
  - Add `adoption prove --project --goal --host --operator-role [--execute] [--json] [--lang]`.
- `plugins/sadrazam/divan_runtime/cli.py`
  - Route preview/execute and render short bilingual proof progress/results.
- `plugins/sadrazam/divan_runtime/impact-graph.json`
- `plugins/sadrazam/company/impact-graph.json`
  - Classify schema, proof, v1 evidence, documentation, and release drift with the focused test command.

### Tests

- `tests/test_adoption.py`
  - Update schema-1 compatibility expectations and preserve privacy/tamper coverage.
- `tests/test_adoption_v2.py`
  - Add schema-2 assembly, verifier, role-equivalence, canonical-order, privacy, hash, and Markdown parity coverage.
- `tests/test_adoption_proof.py`
  - Add project classification, safe argv, selection, preview, execution, timeout/failure, drift, staging, and atomic-promotion coverage.
- `tests/test_cli.py`
  - Add parser/routing/human/JSON contract coverage for `adoption prove`.
- `tests/test_modules.py`
  - Assert nine top-level modules and the new records capability/module membership.
- `tests/test_v1.py`
  - Replace identity-declaration expectations with machine-backed schema-2 evidence enforcement.
- `tests/test_impact_graph.py`
  - Assert proof/evidence/public-surface classification and canonical check selection.

### v1 and public surfaces

- `registry/v1-gates.json`
- `scripts/v1.py`
- `docs/V1-Hazirlik.md`
  - Rename the gate to `verified-clean-room-adoption`; validate real schema-2 evidence before `passed`.
- `.github/ISSUE_TEMPLATE/kabul-kaniti.yml`
  - Request technical evidence without a forced independent-user declaration.
- `README.md`, `README.tr.md`, `BLUEPRINT.md`
- `docs/Project-Contract.md`, `docs/Project-Contract.tr.md`
- `docs/Kurulum.md`, `docs/Durum-ve-Yol-Haritasi.md`
- `docs/Home.md`, `docs/SSS.md`, `docs/index.html`
  - Lead with `adoption prove`, explain operator role and the bounded public claim, and keep 7/8 until real schema-2 evidence exists.
- `release-manifest.json`
  - Register all new source, test, and public evidence surfaces.
- `.divan/progress.md`
  - Record the exact next action and release/evidence dependency.

### Release and evidence

- `CHANGELOG.md`, `VERSION`, `.claude-plugin/marketplace.json`
- plugin manifests and versioned public references selected by `scripts/release.py`
  - Prepare v0.18.3 through the canonical release command only.
- `.divan/evidence/verified-clean-room-adoption-v0183.json`
- `.divan/evidence/verified-clean-room-adoption-v0183.md`
  - Add only after the released v0.18.3 runner produces and verifies the real RSK proof.

---

### Task 1: Schema-1 Compatibility and Schema-2 Offline Verifier

**Files:**
- Modify: `plugins/sadrazam/divan_runtime/adoption.py`
- Modify: `tests/test_adoption.py`
- Create: `tests/test_adoption_v2.py`

**Interfaces:**
- Produces: `build_clean_room_receipt(*, divan: dict[str, object], host: dict[str, object], environment: dict[str, object], operator: dict[str, object], project: dict[str, object], goal: dict[str, object], checks: list[dict[str, object]], proof: dict[str, object]) -> dict[str, object]`
- Produces: `serialize_adoption_json(value: dict[str, object]) -> bytes`
- Produces: `serialize_adoption_markdown(value: dict[str, object]) -> bytes`
- Produces: `verify_adoption_value(value: dict[str, object], *, document_text: str | None = None) -> dict[str, object]`
- Preserves: `export_adoption(...) -> dict[str, Any]`
- Preserves and dispatches: `verify_adoption(path: pathlib.Path | str) -> dict[str, Any]`

- [ ] **Step 1: Change schema-1 status tests before production code**

Update assertions in `tests/test_adoption.py`:

```python
assert exported["status"] == "valid-schema-1-owner-canary"
assert adoption.verify_adoption(json_path) == {
    "schema_version": 1,
    "status": "valid-schema-1-owner-canary",
    "eligible_for_v1": False,
    "errors": [],
}
```

Add the equivalent assertion for `valid-schema-1-independent-declaration` and `eligible_for_v1 is False`.

- [ ] **Step 2: Add a complete canonical schema-2 fixture and rejection matrix**

In `tests/test_adoption_v2.py`, define `clean_room_parts()` with fixed valid values and tests that assert:

```python
value = adoption.build_clean_room_receipt(**clean_room_parts())
verification = adoption.verify_adoption_value(value)
assert verification["status"] == "valid-clean-room-adoption"
assert verification["schema_version"] == 2
assert verification["eligible_for_v1"] is True
assert verification["errors"] == []
```

Add separate tests for maintainer/external equivalence, empty checks, build-only checks, duplicate IDs, noncanonical order, nonzero exit, timeout, unknown keys, boolean-as-integer values, invalid release identity, unsupported host, caller-supplied host-version source, empty artifacts, false distinctness, bad hashes, digest tampering, paths/remotes/emails/secrets in JSON and Markdown, and semantic JSON/Markdown parity.

- [ ] **Step 3: Run the focused tests and record the expected red state**

Run:

```powershell
python -m unittest tests.test_adoption tests.test_adoption_v2 -v
```

Expected: schema-1 status assertions fail and `tests.test_adoption_v2` fails because the new functions do not exist.

- [ ] **Step 4: Implement strict schema dispatch and canonical receipt creation**

Add schema-specific key sets and validation helpers. The builder must:

```python
def build_clean_room_receipt(*, divan, host, environment, operator,
                             project, goal, checks, proof):
    value = {
        "schema_version": 2,
        "product": "divan-clean-room-adoption",
        "divan": divan,
        "host": host,
        "environment": environment,
        "operator": operator,
        "project": project,
        "goal": goal,
        "checks": checks,
        "proof": {**proof, "receipt_digest": ""},
    }
    value["proof"]["receipt_digest"] = _digest_schema_2(value)
    result = verify_adoption_value(value)
    if not result["eligible_for_v1"]:
        raise ValueError("; ".join(result["errors"]))
    return value
```

The digest helper must exclude only `proof.receipt_digest`, use sorted compact UTF-8 JSON, and prefix SHA-256 values with `sha256:`. Validate exact key sets, lowercase canonical hashes, RFC3339 UTC timestamps, sorted unique artifact hashes, sorted unique check IDs, `duration_ms <= timeout_ms`, a passed test-class check, and every eligibility rule from the approved specification.

- [ ] **Step 5: Implement explicit schema-1 compatibility results**

Change schema-1 emission and verification to return:

```python
{
    "schema_version": 1,
    "status": "valid-schema-1-owner-canary",
    "eligible_for_v1": False,
    "errors": [],
}
```

or the independent-declaration compatibility status. Accept historical `valid-owner-canary` only as input data inside a schema-1 envelope; never emit it as the verifier result.

- [ ] **Step 6: Run focused tests and commit**

Run:

```powershell
python -m unittest tests.test_adoption tests.test_adoption_v2 -v
python scripts/hygiene.py --check
```

Expected: all adoption tests pass and hygiene reports clean.

Commit:

```powershell
git add plugins/sadrazam/divan_runtime/adoption.py tests/test_adoption.py tests/test_adoption_v2.py
git commit -m "feat: verify clean-room adoption receipts"
```

---

### Task 2: Immutable Preflight, Distinct Project, and Safe Check Planning

**Files:**
- Create: `plugins/sadrazam/divan_runtime/adoption_proof.py`
- Create: `tests/test_adoption_proof.py`
- Modify: `plugins/sadrazam/divan_runtime/modules.json`
- Modify: `tests/test_modules.py`

**Interfaces:**
- Consumes: `engine.inspect_project(project: pathlib.Path | str) -> dict[str, Any]`
- Consumes: `project_state.load_install_state(project) -> tuple[dict[str, Any] | None, list[str]]`
- Consumes: `receipts.verify_receipt(path) -> dict[str, Any]`
- Produces: `build_proof_plan(project: pathlib.Path | str, goal_id: str, host: str, operator_role: str = "maintainer", *, runner_path: pathlib.Path | None = None) -> dict[str, Any]`
- Produces: `classify_distinct_project(root: pathlib.Path) -> dict[str, Any]`
- Produces: `select_checks(inspection: dict[str, Any], goal_receipt: dict[str, Any], root: pathlib.Path) -> list[dict[str, Any]]`
- Produces: `safe_argv(command: dict[str, Any], *, python_executable: str = sys.executable) -> tuple[str, ...]`

- [ ] **Step 1: Add preflight and check-selection tests**

Create table-driven tests that prove:

```python
plan = adoption_proof.build_proof_plan(
    project_root,
    "goal-123456789abc",
    "claude-code",
    "maintainer",
    runner_path=runner_path,
)
assert plan["status"] == "ready"
assert plan["execution"]["mutating"] is True
assert 1 <= len(plan["checks"]) <= 8
assert any(row["class"] == "test" for row in plan["checks"])
assert not (project_root / ".divan" / "adoption").exists()
```

Add rejection tests for development/mutable source, invalid install state, nonterminal/tampered goal, empty artifacts, `cursor`, unsafe operator role, full Divan signature, partial Divan signature, symlink/reparse project/workspace, package-manager conflict, unsafe script name, build-only project, more than eight discovered checks, and workspace escape.

- [ ] **Step 2: Add exact argv constructor tests**

Assert these tuples and no shell strings:

```python
("npm", "run", "test")
("pnpm", "run", "typecheck")
("bun", "run", "lint")
(sys.executable, "-m", "unittest", "discover")
("go", "test", "./...")
("cargo", "test")
```

Assert rejection of `test && curl example.invalid`, `../workspace`, absolute executable fields, environment assignments, redirection, command substitution, and unrecognized manager values.

- [ ] **Step 3: Run tests and confirm missing-module failure**

Run:

```powershell
python -m unittest tests.test_adoption_proof tests.test_modules -v
```

Expected: import failure for `divan_runtime.adoption_proof`.

- [ ] **Step 4: Implement pure planning and policy hashes**

Use immutable constants:

```python
QUALIFYING_HOSTS = {"claude-code": ("claude", "--version"),
                    "codex": ("codex", "--version")}
OPERATOR_ROLES = frozenset({"maintainer", "external"})
MAX_CHECKS = 8
DISTINCTNESS_POLICY = {
    "version": 1,
    "complete_signature": [
        "VERSION",
        ".claude-plugin/marketplace.json:name=divan",
        "plugins/sadrazam/divan_runtime/modules.json",
    ],
    "partial_signature": "blocked",
}
```

Build the policy digest from canonical JSON. Treat zero markers as distinct, all markers as Divan, and any nonzero incomplete marker set as ambiguous/blocked. Resolve every path and reject symlink/reparse points before reading.

- [ ] **Step 5: Implement deterministic selection**

Select and deduplicate in this order:

1. goal check names that exactly map to discovered commands;
2. root `test`;
3. root `typecheck`, otherwise root `check`;
4. root `lint`;
5. root `build`;
6. directly affected workspace test/regression checks.

Normalize each row to:

```python
{
    "id": "root:test",
    "class": "test",
    "workspace": ".",
    "workspace_sha256": "sha256:...",
    "runner": "bun",
    "name": "test",
    "argv": ("bun", "run", "test"),
    "argv_sha256": "sha256:...",
    "timeout_class": "test",
    "timeout_ms": 120000,
    "timeout_policy_sha256": "sha256:...",
}
```

Keep raw workspace and argv only in the private in-memory plan. Public serialization in Task 3 removes them.

- [ ] **Step 6: Register inside the existing records module**

Add `"adoption_proof"` to `records.python_modules`, add `"clean_room_adoption"` to its capabilities, and retain exactly nine `modules` entries.

- [ ] **Step 7: Run focused tests and commit**

Run:

```powershell
python -m unittest tests.test_adoption_proof tests.test_modules -v
python scripts/catalog.py --check
```

Expected: all focused tests pass and module/catalog contracts remain valid.

Commit:

```powershell
git add plugins/sadrazam/divan_runtime/adoption_proof.py plugins/sadrazam/divan_runtime/modules.json tests/test_adoption_proof.py tests/test_modules.py
git commit -m "feat: plan bounded clean-room proofs"
```

---

### Task 3: Bounded Host Probe, Check Execution, Journal, and Atomic Promotion

**Files:**
- Modify: `plugins/sadrazam/divan_runtime/adoption_proof.py`
- Modify: `tests/test_adoption_proof.py`
- Modify: `plugins/sadrazam/divan_runtime/adoption.py`
- Modify: `tests/test_adoption_v2.py`

**Interfaces:**
- Consumes: `execution.run(command: Sequence[str], decision: TimeoutDecision, *, mutating: bool = False, cwd: pathlib.Path | None = None, env: Mapping[str, str] | None = None, input_text: str | None = None, runner: Callable[..., CompletedProcess[str]] = subprocess.run) -> ExecutionResult`
- Consumes: `timeouts.resolve_default(command_class: str, *, override_seconds: int | None = None, data_directory: pathlib.Path | str = DATA_DIRECTORY) -> TimeoutDecision`
- Produces: `execute_proof(plan: dict[str, Any], *, command_runner: Callable[..., execution.ExecutionResult] = execution.run, clock: Callable[[], datetime] = _utc_now) -> dict[str, Any]`
- Produces: `.divan/adoption/<proof-id>/adoption-receipt.json`, `adoption-receipt.md`, and `journal.json`

- [ ] **Step 1: Add execution-state tests**

Add fake-runner tests for:

- fixed host probe returns `Claude Code 2.1.220` and is normalized to `2.1.220`;
- unsupported or unsafe host output blocks before checks;
- all checks pass and final directory is atomically promoted;
- first nonzero check stops later scheduling and leaves only staging journal;
- timeout is recorded as `timed-out`, distinct from `failed`;
- interruption remains staged and never yields a valid receipt;
- pending journal row exists before the fake subprocess is invoked;
- tracked Git source change fails the proof;
- unchanged tracked source plus ignored cache creation passes;
- project identity drift without Git fails;
- existing final proof directory is never overwritten;
- public files contain no raw argv, raw output, path, remote, username, or email.

- [ ] **Step 2: Run execution tests and confirm red state**

Run:

```powershell
python -m unittest tests.test_adoption_proof.CleanRoomExecutionTests -v
```

Expected: failure because `execute_proof` is not implemented.

- [ ] **Step 3: Implement fixed host observation and bounded execution**

Resolve host timeout with `timeouts.resolve_default("discovery")`; resolve check timeout with each planned class. Invoke only tuple argv through `execution.run`, with `mutating=False` for the host probe and `mutating=True` for project checks. Never retry.

Normalize private results to public check entries:

```python
{
    "id": row["id"],
    "class": row["class"],
    "workspace_sha256": row["workspace_sha256"],
    "runner": row["runner"],
    "name": row["name"],
    "argv_sha256": row["argv_sha256"],
    "status": "passed",
    "exit_code": 0,
    "duration_ms": min(round(result.elapsed_seconds * 1000), timeout_ms),
    "timeout_ms": timeout_ms,
    "timeout_policy_sha256": row["timeout_policy_sha256"],
    "output_sha256": domain_hash(result.stdout + "\n" + result.stderr),
}
```

The host version parser accepts only a single `SAFE_TOKEN` version extracted from the fixed executable's output.

- [ ] **Step 4: Implement durable staging and fail-closed promotion**

Before each subprocess, atomically write a journal entry with `status: pending`. After each result, replace it with `passed`, `failed`, or `timed-out`. On success:

1. recheck tracked-source or project-identity fingerprint;
2. assemble the schema-2 receipt;
3. write JSON and Markdown inside `.staging/<proof-id>`;
4. call `adoption.verify_adoption` on both files;
5. require both to return `valid-clean-room-adoption`;
6. atomically rename the staging directory to `<proof-id>`.

On failure return a bounded result with the staging location represented as a project-relative path in CLI output; never promote.

- [ ] **Step 5: Run focused tests and commit**

Run:

```powershell
python -m unittest tests.test_adoption_v2 tests.test_adoption_proof -v
```

Expected: all schema and execution tests pass.

Commit:

```powershell
git add plugins/sadrazam/divan_runtime/adoption.py plugins/sadrazam/divan_runtime/adoption_proof.py tests/test_adoption_v2.py tests/test_adoption_proof.py
git commit -m "feat: execute and seal clean-room proofs"
```

---

### Task 4: Dry-Run-First CLI and Vibe-Coder Progress Copy

**Files:**
- Modify: `plugins/sadrazam/divan_runtime/cli_parser.py`
- Modify: `plugins/sadrazam/divan_runtime/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `plugins/sadrazam/divan_runtime/locales.py`
- Modify: `tests/test_locales.py`

**Interfaces:**
- Consumes: `adoption_proof.build_proof_plan(...)`
- Consumes: `adoption_proof.execute_proof(plan, ...)`
- Produces command:
  - `adoption prove --project PATH --goal GOAL-ID --host {claude-code,codex} --operator-role {maintainer,external} [--execute] [--json] [--lang {en,tr}]`

- [ ] **Step 1: Add parser and no-side-effect preview tests**

Assert:

```python
options = cli_parser.build_parser().parse_args([
    "adoption", "prove", "--project", str(root),
    "--goal", "goal-123456789abc", "--host", "claude-code",
])
assert options.execute is False
assert options.operator_role == "maintainer"
```

Patch `execute_proof` to raise if called and assert preview returns the check plan, file plan, fixed host probe, blockers, and exact execute command without calling it.

- [ ] **Step 2: Add execute and bilingual rendering tests**

Assert JSON output preserves stable machine fields. Assert human Turkish includes:

```text
Divan neyi kanıtlayacak?
Çalışacak kontroller
Henüz hiçbir dosya yazılmadı.
Başlatmak için:
Temiz-proje kanıtı geçti.
```

Assert English includes the equivalent bounded wording and neither language claims an independent user.

- [ ] **Step 3: Run CLI tests and confirm parser failure**

Run:

```powershell
python -m unittest tests.test_cli tests.test_locales -v
```

Expected: parser rejects `adoption prove`.

- [ ] **Step 4: Implement parser, route, and concise progress model**

Add prove parser with `_mutation_control(prove)` and `_common_output(prove)`. In `cli._execute`, call `build_proof_plan`; call `execute_proof` only when `options.execute` is true. Return structured fields:

```python
{
    "status": "ready",
    "summary": "Divan can prove this goal with 5 bounded checks.",
    "project": {"classification": "external", "workspace_count": 11},
    "goal": {"id": "...", "state": "VERIFIED"},
    "checks": [...],
    "host_probe": {"command": ["claude", "--version"], "status": "planned"},
    "writes": [".divan/adoption/<proof-id>/"],
    "next_command": "python divan-project.pyz adoption prove ... --execute",
}
```

Human output must explain outcomes in vibe-coder language while JSON remains stable and complete.

- [ ] **Step 5: Run CLI tests and commit**

Run:

```powershell
python -m unittest tests.test_cli tests.test_locales tests.test_adoption_proof -v
```

Expected: all tests pass.

Commit:

```powershell
git add plugins/sadrazam/divan_runtime/cli_parser.py plugins/sadrazam/divan_runtime/cli.py plugins/sadrazam/divan_runtime/locales.py tests/test_cli.py tests/test_locales.py
git commit -m "feat: expose clean-room proof workflow"
```

---

### Task 5: Machine-Backed v1 Gate

**Files:**
- Modify: `registry/v1-gates.json`
- Modify: `scripts/v1.py`
- Modify: `tests/test_v1.py`
- Regenerate: `docs/V1-Hazirlik.md`

**Interfaces:**
- Consumes: `divan_runtime.adoption.verify_adoption(path)`
- Produces: `_validate_clean_room_evidence(root: pathlib.Path, gate: dict[str, object]) -> None`
- Gate ID: `verified-clean-room-adoption`

- [ ] **Step 1: Replace identity-based test expectations**

Add tests that copy a valid schema-2 receipt into a temporary repo and assert:

```python
gate["id"] = "verified-clean-room-adoption"
gate["status"] = "passed"
gate["evidence"] = [".divan/evidence/verified-clean-room-adoption-v0183.json"]
assert v1.oku(root)["gates"][-1]["status"] == "passed"
```

Add rejection cases for missing evidence, schema 1, invalid/tampered schema 2, `eligible_for_v1: false`, release/source mismatch, no test-class check, failed check, and a generated readiness document that does not reference the evidence.

- [ ] **Step 2: Run v1 tests and confirm old gate failure**

Run:

```powershell
python -m unittest tests.test_v1 -v
```

Expected: failures reference `independent-adoption` and missing schema-2 validation.

- [ ] **Step 3: Implement verifier-backed gate loading**

Load the canonical adoption module from the runtime path without duplicating its schema logic. When gate status is `passed`, require exactly one repository-contained JSON receipt under `.divan/evidence/`, verify it, require `status == "valid-clean-room-adoption"` and `eligible_for_v1 is True`, and cross-check the gate evidence metadata with receipt release/ref/commit.

When evidence is absent, retain:

```json
{
  "id": "verified-clean-room-adoption",
  "status": "ready",
  "title": "Doğrulanmış temiz-proje kullanımı"
}
```

so v0.18.3 mechanism release remains honestly 7/8.

- [ ] **Step 4: Regenerate and verify readiness copy**

Run:

```powershell
python scripts/v1.py --render
python scripts/v1.py --check
python -m unittest tests.test_v1 -v
```

Expected: the generated page says the automation is ready, the real schema-2 proof is pending, operator identity is not the gate, and the score is 7/8.

- [ ] **Step 5: Commit**

```powershell
git add registry/v1-gates.json scripts/v1.py tests/test_v1.py docs/V1-Hazirlik.md
git commit -m "feat: verify clean-room evidence for v1"
```

---

### Task 6: Public Contract, Intake Form, Impact Graph, and Surface Parity

**Files:**
- Modify: `.github/ISSUE_TEMPLATE/kabul-kaniti.yml`
- Modify: `README.md`
- Modify: `README.tr.md`
- Modify: `BLUEPRINT.md`
- Modify: `docs/Project-Contract.md`
- Modify: `docs/Project-Contract.tr.md`
- Modify: `docs/Kurulum.md`
- Modify: `docs/Durum-ve-Yol-Haritasi.md`
- Modify: `docs/Home.md`
- Modify: `docs/SSS.md`
- Modify: `docs/index.html`
- Modify: `plugins/sadrazam/divan_runtime/impact-graph.json`
- Modify: `plugins/sadrazam/company/impact-graph.json`
- Modify: `tests/test_impact_graph.py`
- Modify: public-copy tests selected by `rg -l "independent-adoption|bağımsız kullanıcı|independent user" tests`
- Modify: `release-manifest.json`
- Modify: `.divan/progress.md`

**Interfaces:**
- Public claim: “one machine-verifiable clean-room adoption,” not independent-user adoption, market adoption, endorsement, speed gain, or quality win.
- Primary command: `python divan-project.pyz adoption prove --project . --goal GOAL-ID --host claude-code`

- [ ] **Step 1: Add public-copy and impact failures**

Update tests to require the new gate/command/status words and reject the old forced identity language. Add impact tests that map changes in `adoption.py`, `adoption_proof.py`, committed evidence, issue form, and v1 registry to:

```text
python -m unittest tests.test_adoption tests.test_adoption_v2 tests.test_adoption_proof tests.test_v1
```

- [ ] **Step 2: Run affected tests and capture drift**

Run:

```powershell
python -m unittest tests.test_impact_graph tests.test_v1 -v
python scripts/catalog.py --check
python scripts/release.py --check
python scripts/wiki.py --check
```

Expected: failures identify stale public copy, impact graph, Wiki, and release surfaces.

- [ ] **Step 3: Rewrite the contract and issue intake**

The issue form must ask for release, host, coarse environment, real-task summary, generated proof status, redacted schema-2 JSON, and rollback result/reason. Remove any required checkbox claiming the operator is not the owner.

English and Turkish surfaces must explain:

```text
Preview: Divan shows the checks and writes nothing.
Execute: Divan observes the host, runs bounded checks once, and seals evidence.
Eligibility: technical proof; maintainer and external roles are equivalent.
Current v1 status: 7/8 until released schema-2 evidence is committed.
```

- [ ] **Step 4: Synchronize generated and registered surfaces**

Run the repository's existing render/update commands for catalog, v1 page, Wiki source, site data, and release manifest where those scripts expose a render mode. Update `release-manifest.json` through the canonical release tooling rather than hand-adjusting counts.

Record this exact next action in `.divan/progress.md`:

```text
Release v0.18.3 mechanism, rebuild both portable runners, then rerun adoption prove
against the existing verified RSK goal and commit only the privacy-reviewed schema-2
receipt before changing the v1 score from 7/8 to 8/8.
```

- [ ] **Step 5: Run parity checks and commit**

Run:

```powershell
python scripts/catalog.py --check
python scripts/v1.py --check
python scripts/wiki.py --check
python scripts/release.py --check
python -m unittest tests.test_impact_graph -v
```

Expected: every source/generated/public surface is synchronized.

Commit:

```powershell
git add .github README.md README.tr.md BLUEPRINT.md docs plugins/sadrazam/divan_runtime/impact-graph.json plugins/sadrazam/company/impact-graph.json tests release-manifest.json .divan/progress.md
git commit -m "docs: explain verified clean-room adoption"
```

---

### Task 7: Full Verification, Review, PR, and v0.18.3 Mechanism Release

**Files:**
- Modify through canonical release tooling: `VERSION`, `CHANGELOG.md`, `.claude-plugin/marketplace.json`, plugin manifests, README/Wiki/site/version references, `release-manifest.json`
- No manual tag or asset construction.

**Interfaces:**
- Consumes: `python scripts/release.py` workflow.
- Produces: immutable tag `v0.18.3`, two portable runners, two checksum files, release notes, attestations, synchronized Pages/Wiki.

- [ ] **Step 1: Run focused security and compatibility matrix**

Run:

```powershell
python -m unittest tests.test_adoption tests.test_adoption_v2 tests.test_adoption_proof tests.test_cli tests.test_modules tests.test_v1 tests.test_impact_graph -v
python scripts/handoff.py --check
python scripts/catalog.py --check
python scripts/release.py --check
```

Expected: all tests and checks pass.

- [ ] **Step 2: Run canonical repository verification**

Run:

```powershell
python scripts/verify.py
git diff --check
git status --short
```

Expected: the complete suite passes, diff check is silent, and status contains only intended tracked changes.

- [ ] **Step 3: Review the branch against the approved specification**

Inspect:

```powershell
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
```

Confirm every eligibility rule has a failing test, schema 1 cannot pass v1, preview has no write/check side effects, no raw command/output/path leaks, nine runtime modules remain, and public copy makes no independent-user claim.

- [ ] **Step 4: Push and open a ready PR**

Run:

```powershell
git push -u origin feat/verified-clean-room-adoption
gh pr create --base main --head feat/verified-clean-room-adoption --title "feat: verify clean-room adoption" --body-file .divan/pr/verified-clean-room-adoption.md
```

The PR body must list focused/full test evidence, security boundaries, schema migration, current 7/8 status, and the post-release real-proof step.

- [ ] **Step 5: Wait for and repair CI before merge**

Use:

```powershell
gh pr checks --watch
```

If a check fails, inspect the failing log, reproduce locally, add a regression test, apply the smallest fix, rerun focused/full verification, push, and wait again. Merge only when required checks are green and the PR is mergeable.

- [ ] **Step 6: Merge and prepare v0.18.3 with the canonical release path**

After merge, update local `main`, run the release preparation path documented by:

```powershell
python scripts/release.py --help
python scripts/divan.py yayin --help
```

Use the supported v0.18.3 preparation/execution commands those help texts expose. Do not construct tags or assets manually.

- [ ] **Step 7: Verify the published mechanism**

Read back from GitHub:

```powershell
gh release view v0.18.3
gh release download v0.18.3 --dir .divan/release-readback/v0.18.3
```

Verify both `.pyz` files against their downloaded `.sha256` files, confirm tag commit matches release provenance, inspect Actions, Pages, and Wiki, and rerun each runner's `--help`/`doctor` smoke command.

---

### Task 8: Real RSK Proof and Final v1 Decision

**Files:**
- Create only after real execution: `.divan/evidence/verified-clean-room-adoption-v0183.json`
- Create only after real execution: `.divan/evidence/verified-clean-room-adoption-v0183.md`
- Modify after valid proof: `registry/v1-gates.json`
- Regenerate after valid proof: `docs/V1-Hazirlik.md`
- Modify: `.divan/progress.md`
- Modify through canonical release/publication tooling if v1.0 is authorized: version and release surfaces.

**Interfaces:**
- Uses existing RSK goal: `goal-5e033a4d324a`
- Requires verifier result: `valid-clean-room-adoption`
- Does not redo the original RSK task and does not require a different human.

- [ ] **Step 1: Verify the released runner before use**

On the clean Windows 11 / Claude Code environment, download the four v0.18.3 runner/checksum assets and verify SHA-256 before executing either runner.

- [ ] **Step 2: Preview the real proof**

Run inside the existing RSK project:

```powershell
python divan-project.pyz adoption prove --project . --goal goal-5e033a4d324a --host claude-code --operator-role maintainer
```

Confirm the project is classified external, the goal is `VERIFIED`, a test-class check exists, the selected checks match the project, timeouts are finite, and no proof files were written.

- [ ] **Step 3: Execute and verify**

Run:

```powershell
python divan-project.pyz adoption prove --project . --goal goal-5e033a4d324a --host claude-code --operator-role maintainer --execute
python divan-project.pyz adoption verify .divan/adoption/proof-*/adoption-receipt.json
python divan-project.pyz adoption verify .divan/adoption/proof-*/adoption-receipt.md
```

Require both verification results to be `valid-clean-room-adoption`; otherwise retain 7/8 and record the exact bounded failure.

- [ ] **Step 4: Privacy-review and transfer only public evidence**

Inspect JSON and Markdown for paths, remotes, URLs, usernames, emails, tokens, secrets, raw argv/output, and customer data. Copy only the reviewed receipt pair into Divan's `.divan/evidence/` directory. Verify byte hashes after transfer.

- [ ] **Step 5: Change the gate only when the committed evidence passes**

Set `verified-clean-room-adoption` to `passed`, name the exact JSON/Markdown evidence paths, then run:

```powershell
python scripts/v1.py --render
python scripts/v1.py --check
python scripts/verify.py
git diff --check
```

Expected: 8/8 only when the committed schema-2 receipt remains valid.

- [ ] **Step 6: Publish the bounded result**

The public statement must be:

```text
Divan completed one machine-verifiable clean-room adoption on Windows 11,
Claude Code, and a real external project using a pinned release and bound
project checks.
```

Do not convert it into an independent-user count, third-party endorsement, market-adoption claim, speed improvement, or quality win.

