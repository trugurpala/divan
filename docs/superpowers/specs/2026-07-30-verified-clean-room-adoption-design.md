# Verified Clean-Room Adoption Design

**Target:** v0.18.3
**Status:** Approved product direction; written specification awaiting review

## Purpose

Divan's eighth v1 gate currently asks whether a person is outside the
repository's owner/developer group. The code cannot verify that identity. It
only records a caller-selected `maintainer` or `independent` string and returns
`valid-independent-declaration` when the latter is selected.

This makes the gate hard for a real user to complete while measuring something
Divan cannot prove. It also gives the word `valid` more authority than the
receipt actually has.

The replacement gate measures what the product can verify:

> A pinned Divan release was used on a supported host in a project distinct
> from Divan, a real goal reached `VERIFIED`, bounded project checks passed,
> and the privacy-safe evidence remains tamper-evident offline.

The operator may be the maintainer or an external user. Operator role remains
provenance, not eligibility.

## Evidence That Motivated the Change

The Windows 11 / Claude Code / React Starter Kit rehearsal established a strong
candidate:

- Divan `v0.18.2` at immutable commit
  `d3a2a41f9b88c3639f9832c24dd898fd8b88cbe4`;
- both portable runner checksums matched their published values before use;
- Claude Code `2.1.220` was healthy;
- the project identity was distinct from Divan;
- goal `goal-5e033a4d324a` reached `VERIFIED`;
- regression, full tests, typecheck, lint, and build exited successfully;
- the schema-1 owner receipt passed privacy and integrity verification.

The rehearsal also exposed the exact schema defect: `goal.checks` was empty.
The checks were reported beside the receipt rather than bound into it. This
candidate demonstrates the workflow but does not silently become schema-2
evidence.

After implementation, the same project and verified goal may be qualified by
rerunning only the bounded checks through the new proof command. The original
task does not need to be recreated and no different human is required.

## Product Decision

### Old gate

`independent-adoption`:

- depends on a human identity declaration;
- cannot be verified by Divan;
- treats maintainer evidence as categorically ineligible;
- produces an overly strong `valid-independent-declaration` label.

### New gate

`verified-clean-room-adoption`:

- depends on immutable release, real-project, goal, check, and privacy proof;
- is evaluated offline from a schema-2 receipt;
- treats operator role as informational;
- returns `valid-clean-room-adoption` only when every technical condition
  passes.

This changes what Divan v1 claims. v1 will claim one verified clean-room
adoption, not independent market adoption or third-party endorsement.

## Scope

### Included

- Schema-2 adoption receipt and offline verifier.
- Dry-run-first `adoption prove` workflow.
- Bounded execution of discovered project checks.
- Adjacent release-checksum and embedded runner-source verification.
- Fresh-plan execution, goal-bound check priority, and Git-tracked source-drift
  rejection.
- Canonical Markdown rendering bound exactly to the JSON envelope.
- Operator provenance without an eligibility effect.
- Existing schema-1 receipt verification for compatibility.
- Machine-backed v1 registry evaluation from committed schema-2 evidence.
- Turkish and English CLI, README, Project Contract, Wiki, Pages, status, and
  GitHub intake wording.
- Migration of issue #34 from identity-based intake to technical evidence.
- A v0.18.3 evidence record produced from the existing RSK verified goal after
  the new proof workflow reruns its checks.

### Not included

- Claiming independent users, market adoption, productivity gains, or a
  third-party endorsement.
- Accepting prose, screenshots, an issue checkbox, or a caller-selected status
  as gate authority.
- Requiring a new person, computer, GitHub account, email address, or public
  project.
- Requiring uninstall/rollback in this gate. Rollback already has a separate
  passed v1 gate.
- Installing a host, changing a project, repairing a goal, or editing source
  code during proof.
- Running arbitrary shell strings supplied on the command line.
- Adding a tenth Divan runtime module, third-party harness, daemon, database,
  telemetry service, or external dependency.

## User Experience

The first command is read-only and shows exactly what Divan can prove:

```powershell
python divan-project.pyz adoption prove `
  --project . `
  --goal goal-5e033a4d324a `
  --host claude-code
```

The preview lists:

1. immutable Divan source,
2. coarse environment and host identity,
3. project classification and distinct-project result,
4. verified goal state,
5. selected check names, workspaces, exact argv, and timeouts,
6. files that execution will create,
7. one exact execute command.

The user then explicitly authorizes check execution and evidence writes:

```powershell
python divan-project.pyz adoption prove `
  --project . `
  --goal goal-5e033a4d324a `
  --host claude-code `
  --execute
```

Success ends with a short result:

```text
Clean-room proof passed.
Release: Divan v0.18.3
Project: external project, 11 workspaces
Goal: VERIFIED
Checks: 5 passed
Receipt: valid-clean-room-adoption
Files: .divan/adoption/<proof-id>/
Next: submit the generated technical evidence or keep it locally.
```

Failure states:

- `blocked`: proof could not start safely;
- `failed-checks`: one or more executed checks failed or timed out;
- `invalid`: receipt schema, privacy, hash, or authority is invalid;
- `valid-schema-1-owner-canary`: compatible historical receipt, not v1
  authority;
- `valid-schema-1-independent-declaration`: compatible historical
  declaration, not v1 authority;
- `valid-clean-room-adoption`: schema-2 technical gate passed.

No result says only `valid` without naming what was validated.

## Proof Architecture

The feature stays inside the existing nine-module Divan runtime:

- `records/adoption` owns schema-2 assembly, serialization, compatibility, and
  verification;
- `records/adoption_proof` owns bounded check planning, execution journaling,
  and atomic promotion while remaining inside the existing records module;
- `council/engine` remains the sole bounded project-command discovery source;
- `evidence/execution` remains the sole command execution and timeout policy;
- `project/project_state` proves immutable installed source and project
  identity;
- `records/goals` and `evidence/receipts` prove goal state and artifact chain;
- `api/cli_parser` and `api/cli` expose dry-run and execute behavior.

No tenth top-level runtime module or compatibility fork is added. The focused
`adoption_proof.py` implementation is declared under the existing `records`
entry in `modules.json`, avoiding further growth of the existing adoption
schema/verifier file. The existing
`plugins/sadrazam/company/adoption.py` remains a narrow alias to the canonical
module.

## Proof Lifecycle

### 1. Preflight

Both preview and execution:

1. resolve the real project root and reject files, symlinks, reparse points,
   and path escapes;
2. load schema-2 Divan project state;
3. require an immutable semantic release ref, release version, and 40-character
   source commit;
4. reject `development@...`, mutable branches, and unknown repositories;
5. load the goal through the existing contained goal-path contract;
6. require a cryptographically valid goal receipt in `VERIFIED`, `RELEASED`,
   or `OBSERVED`;
7. require at least one hashed goal artifact;
8. validate the selected supported host and plan its fixed shell-free version
   probe without accepting a caller-supplied version claim;
9. apply the packaged distinct-project rule and reject the Divan source tree
   itself;
10. discover project workspaces and commands without executing project code;
11. build a bounded check plan;
12. calculate a deterministic `proof_id` from stable inputs.

### 2. Dry-run

Without `--execute`, Divan:

- performs no project command;
- starts no subprocess, including the planned host probe;
- creates no proof directory, journal, receipt, log, or cache inside the
  project;
- reports every selected check and timeout;
- reports the exact fixed host-version probe that execution will run;
- reports blockers before any mutation;
- prints the exact execute command.

### 3. Execution

With `--execute`, Divan:

1. re-runs the complete preflight;
2. observes the supported host version through the planned fixed shell-free
   probe and rejects unsafe or ambiguous output;
3. compares the new proof plan with the preview inputs where a preview digest
   is supplied;
4. creates an atomic proof staging directory under
   `.divan/adoption/.staging/<proof-id>`;
5. records the pending check intent before each project-check subprocess;
6. runs each selected check once through the existing bounded executor;
7. redacts and summarizes output before persistence;
8. records exit status, duration class, timeout decision, normalized-output
   digest, and result;
9. stops scheduling new checks after the first failure;
10. requires Git and proves that HEAD, index, worktree, and bounded project
   identity inputs did not change during the checks;
11. assembles the schema-2 receipt only when all checks pass;
12. verifies the staged receipt with the public offline verifier;
13. atomically promotes the staging directory to
    `.divan/adoption/<proof-id>`.

An interrupted run remains resumable or removable through its journal. It is
never promoted as valid evidence.

Project checks may create their ordinary ignored test caches or build outputs.
Divan neither cleans those outputs nor calls them source changes. A tracked
source/configuration change, project-identity drift, or check that rewrites a
managed Divan contract fails the proof.

The adjacent checksum sidecar protects download integrity. Before preview,
Divan also reads the exact `divan-project.pyz` digest from the fixed public
GitHub Release API for the installed immutable tag. The local runner must match
that independent release authority. The v1 gate later pins the same reviewed
digest in `registry/v1-gates.json`.

## Check Selection

Divan does not execute a display string such as `npm test` through a shell.
It derives argv from the already validated discovery fields:

- workspace,
- package manager,
- validated script name,
- supported language marker.

Supported argv constructors are explicit:

- npm-compatible manager: `<manager> run <script>`;
- Python: current interpreter, `-m unittest discover`;
- Go: `go test ./...`;
- Rust: `cargo test`.

The working directory must be a real contained workspace. Script names must
already satisfy the existing package-script-name contract. Shell operators,
redirections, command substitutions, environment assignments, absolute
executables, and user-supplied command text are not accepted.

### Default policy

The bounded default selects verification-class scripts in this order:

1. goal-bound checks that map to discovered commands;
2. root-workspace `test`;
3. root-workspace `typecheck` or `check`;
4. root-workspace `lint`;
5. root-workspace `build`;
6. directly affected workspace regression checks.

The plan is deduplicated by workspace, manager, and script. It contains at most
eight checks. At least one test-class check is mandatory; build alone cannot
qualify adoption.

Unknown or ambiguous package-manager evidence blocks instead of guessing.

Schema-2 initially qualifies only the already verified `claude-code` and
`codex` hosts. Divan observes their version with fixed executable mappings and
the existing shell-free executor. Cursor and `other` remain available to the
schema-1 compatibility exporter but cannot qualify the v1 gate until they have
an equivalent observed-host contract.

### Distinct-project policy

The proof planner computes `distinct_from_divan`; the caller cannot supply it.
The first policy version rejects a project root when the bounded inspection
finds the complete Divan source signature:

- root `VERSION`;
- `.claude-plugin/marketplace.json` whose marketplace name is `divan`;
- `plugins/sadrazam/divan_runtime/modules.json`.

It also rejects a root equal to a locally executing Divan checkout when that
authority is available. Partial or malformed signature markers are treated as
ambiguous and block qualification instead of being accepted as external.

The receipt binds the policy version through
`distinctness_policy_sha256`. This proves which packaged rule produced the
boolean without publishing the project path or repository remote.

### Timing and retry

- Each check uses the existing evidence-backed timeout class.
- The total proof has a finite aggregate deadline.
- Mutation and project checks are never automatically retried.
- A timeout is distinct from a non-zero exit.
- Exact durations remain local; the public receipt stores bounded milliseconds
  and the timeout-policy identity.

## Schema-2 Receipt

The canonical JSON object contains only bounded, privacy-safe data:

```json
{
  "schema_version": 2,
  "product": "divan-clean-room-adoption",
  "divan": {
    "version": "0.18.3",
    "ref": "v0.18.3",
    "commit": "<40 lowercase hex>",
    "distribution": "immutable-release",
    "runner_sha256": "sha256:<64 lowercase hex>"
  },
  "host": {
    "name": "claude-code",
    "version": "2.1.220",
    "version_source": "observed-cli"
  },
  "environment": {
    "os": "windows",
    "architecture": "x86_64"
  },
  "operator": {
    "role": "maintainer"
  },
  "project": {
    "identity_sha256": "sha256:<64 lowercase hex>",
    "distinct_from_divan": true,
    "distinctness_policy_sha256": "sha256:<64 lowercase hex>",
    "types": ["application", "monorepo"],
    "workspace_count": 11
  },
  "goal": {
    "id": "goal-5e033a4d324a",
    "state": "VERIFIED",
    "target": "VERIFIED",
    "receipt_sha256": "sha256:<64 lowercase hex>",
    "artifact_sha256": ["sha256:<64 lowercase hex>"]
  },
  "checks": [
    {
      "id": "root:test",
      "class": "test",
      "workspace_sha256": "sha256:<64 lowercase hex>",
      "runner": "bun",
      "name": "test",
      "argv_sha256": "sha256:<64 lowercase hex>",
      "status": "passed",
      "exit_code": 0,
      "duration_ms": 18500,
      "timeout_ms": 120000,
      "timeout_policy_sha256": "sha256:<64 lowercase hex>",
      "output_sha256": "sha256:<64 lowercase hex>"
    }
  ],
  "proof": {
    "id": "proof-<12 lowercase hex>",
    "started_at": "<UTC RFC3339>",
    "completed_at": "<UTC RFC3339>",
    "source_stable": true,
    "receipt_digest": "sha256:<64 lowercase hex>"
  }
}
```

The exact final schema is locked by tests. Timestamps are execution metadata
and do not participate in `proof_id`; the final receipt digest covers them.

### Privacy rules

The receipt never contains:

- project or home-directory names;
- relative or absolute filesystem paths;
- repository remotes or URLs;
- raw argv or raw command output;
- usernames, email addresses, tokens, secrets, or environment values;
- package inventories unrelated to selected checks;
- customer data.

Workspace identity and argv are represented only by domain-separated SHA-256
digests. Runner and validated script name remain visible because they are
needed to understand the proof and are constrained safe tokens.

## Eligibility Rules

`valid-clean-room-adoption` requires all of the following:

1. schema version is exactly 2;
2. receipt identity and digest are valid;
3. Divan source is an immutable semantic release;
4. host name and version satisfy their bounded contracts;
5. the executing project runner hashes to the declared release asset;
6. host version was observed by the fixed CLI probe rather than supplied as a
   free-form claim;
7. environment contains only coarse supported values;
8. project identity is valid and `distinct_from_divan` is true;
9. goal receipt is valid and terminal at or beyond `VERIFIED`;
10. at least one goal artifact is hashed;
11. checks are non-empty and canonically ordered;
12. at least one test-class check exists;
13. every check passed with exit code zero;
14. every check has bounded timeout, duration, argv, output, and policy hashes;
15. tracked source or bounded project identity did not drift during proof;
16. privacy scanning returns no error;
17. no unknown keys, duplicate IDs, booleans-as-integers, unsafe tokens, or
    noncanonical hashes exist.

Operator role is restricted to `maintainer` or `external`, but neither value
changes eligibility.

## Backward Compatibility

Schema-1 JSON and Markdown receipts continue to verify offline. Their public
statuses become explicit compatibility results:

- `valid-schema-1-owner-canary`;
- `valid-schema-1-independent-declaration`.

The old status strings remain accepted only by the compatibility parser during
the v0.18 line where necessary. They are not emitted by new proofs and never
pass the schema-2 v1 gate.

`adoption export` remains available for schema-1 compatibility. New
documentation leads with `adoption prove`.

## Machine-Backed v1 Gate

`registry/v1-gates.json` renames the eighth gate to
`verified-clean-room-adoption`. Its status may become `passed` only when its
evidence list names a repository-contained schema-2 receipt that:

- passes `adoption verify`;
- matches the release/source identity claimed by the evidence record;
- has at least one test-class check and no failed check;
- is privacy-safe;
- is referenced by the generated v1 readiness document.

`scripts/v1.py --check` loads and validates the receipt rather than trusting
the gate's written status. Removing or tampering with evidence makes the gate
invalid.

The RSK rehearsal becomes qualifying evidence only after v0.18.3 is available
and the new proof command regenerates a schema-2 receipt from the existing
verified goal. Until that receipt exists and passes, the score remains 7/8.

## GitHub and Public Surfaces

Issue #34 is retained for history but retitled and rewritten around technical
proof. The issue form no longer requires a false identity checkbox. It asks
for:

- Divan release;
- host and coarse environment;
- real task summary;
- generated proof result;
- redacted schema-2 receipt;
- rollback result or bounded reason it was not attempted;
- confirmation that no private data is included.

README, README.tr, Project Contract, status/roadmap, v1 readiness, installation
guide, Wiki source, Pages, support routing, release notes, and
`release-manifest.json` must agree that:

- v1 measures verified clean-room adoption;
- maintainer and external operators are both eligible;
- this is not a claim of independent market adoption;
- schema-1 declarations do not close the gate.

## Security and Failure Cases

Automated tests must prove rejection of:

- mutable or development Divan source;
- Divan testing itself as the adopted project;
- missing, nonterminal, stale, or tampered goal receipt;
- empty artifact set;
- empty checks or build-only checks;
- arbitrary command text or shell metacharacters;
- path, workspace, package-manager, and script-name ambiguity;
- symlink/reparse workspace escape;
- timeout, non-zero exit, interruption, or skipped required check;
- duplicate or noncanonical checks;
- forged duration, timeout, policy, argv, output, or workspace hashes;
- schema-1 receipt presented as schema-2 authority;
- digest recomputation after an invalid schema or privacy change;
- email, home path, remote URL, token, secret, or raw output leakage;
- partial staging promoted as complete evidence.

## Verification Matrix

### Focused tests

- schema-1 compatibility and non-eligibility;
- schema-2 serialization and offline verification;
- maintainer/external role equivalence;
- immutable release and distinct-project checks;
- dry-run creates zero files and starts zero processes;
- safe argv construction for npm-compatible managers, Python, Go, and Rust;
- required test selection, ordering, deduplication, and eight-check cap;
- success, failure, timeout, and interruption journals;
- privacy redaction and hash binding;
- JSON/Markdown semantic parity;
- RSK-shaped monorepo fixture with regression, test, typecheck, lint, and build.

### Repository tests

- impact graph classification;
- English/Turkish public-surface parity;
- v1 registry evidence enforcement;
- release-manifest synchronization;
- deterministic project runner rebuild;
- official Agent Skills and Claude Code validation;
- full `python scripts/verify.py`;
- `git diff --check`.

### Real proof

After v0.18.3 release assets exist:

1. verify both portable runner checksums;
2. run clean host doctor;
3. use the existing external RSK project and verified goal;
4. preview `adoption prove`;
5. execute the bounded proof;
6. verify JSON and Markdown offline;
7. privacy-review the generated files;
8. commit only the bounded public evidence to Divan;
9. run `scripts/v1.py --check`;
10. change the public score to 8/8 only after every step passes.

## Delivery Slices

1. Schema-2 verifier and failing tests.
2. Dry-run proof planner and safe check selection.
3. Bounded execution journal and atomic evidence writer.
4. CLI and bilingual progress messages.
5. v1 registry and evidence-backed score calculation.
6. GitHub issue/intake and public documentation synchronization.
7. v0.18.3 portable runner and cross-platform verification.
8. RSK schema-2 proof, privacy review, and final v1 gate decision.

Each slice is independently reviewable. No slice may mark v1 8/8 before the
real schema-2 proof exists.

## Release Decision

v0.18.3 may ship the mechanism while v1 remains 7/8. Divan v1 becomes 8/8 only
when the released mechanism produces and verifies the real RSK schema-2 proof.

The resulting public statement is limited to:

> Divan completed one machine-verifiable clean-room adoption on Windows 11,
> Claude Code, and a real external project using a pinned release and bound
> project checks.

It must not be rewritten as an independent-user count, third-party validation,
market adoption, speed improvement, or quality win.
