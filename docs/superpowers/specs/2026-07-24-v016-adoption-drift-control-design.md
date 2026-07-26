# Divan v0.16.0 Adoption and Drift Control Specification

## Purpose

Divan v0.16.0 makes an initialized Project OS installation maintainable after
its first successful `init`. It records which immutable Divan release owns each
managed surface, detects local and upstream drift, updates only content that
Divan can prove it still owns, repairs damaged generated content
transactionally, archives completed goals, and exports a privacy-safe adoption
receipt.

This release does not add more roles, skills, providers, a dashboard, or a
background daemon. The existing five packages and 41 discoverable skills remain
the product surface. The priority is safe lifecycle maintenance and
reproducible use in a project outside the Divan repository.

## Research decision

The design adopts four bounded ideas without adding a runtime dependency:

- Agent Skills remains the skill-format authority. Project lifecycle metadata
  stays outside skill directories and does not extend the Agent Skills schema.
- Spec Kit's separation between idempotent installation and explicit component
  update informs the `project update` command.
- OpenSpec's completed-change archive informs goal archival, but Divan does not
  copy OpenSpec's directory format or delta merger.
- Auto-Company's visible state and circuit-breaker ideas inform actionable
  status output. Divan does not adopt its unattended daemon, persona imitation,
  chain-of-thought logging, or continuous model loop.

No upstream code is copied, vendored, or executed by this feature.

## Product boundary

v0.16.0 has four related lifecycle units:

1. **Ownership state** records the installed Project OS release and managed
   payload fingerprints.
2. **Status, update, and repair** compare desired, recorded, and observed state
   without treating user edits as Divan-owned content.
3. **Goal archive** moves completed goals out of the active set while preserving
   their verified evidence.
4. **Adoption export and canary** prove that the public runner works in a
   separate repository without falsely satisfying the independent-user gate.

These units share one transaction engine and one redaction contract. Host
installation and host upgrade remain separate commands and state stores.

## Canonical command surface

The English machine interface is canonical:

```powershell
python scripts/divan.py project status --project . --json
python scripts/divan.py project update --project .
python scripts/divan.py project update --project . --execute
python scripts/divan.py project repair --project .
python scripts/divan.py project repair --project . --execute
python scripts/divan.py goal archive --project . --goal <goal-id>
python scripts/divan.py goal archive --project . --goal <goal-id> --execute
python scripts/divan.py adoption export --project . --goal <goal-id>
python scripts/divan.py adoption verify <receipt-path>
```

The release runner uses the same routes:

```powershell
python divan-project.pyz project status --project . --json
python divan-project.pyz project update --project . --execute
```

`project update` updates the target project to the immutable version and source
commit embedded in the running Divan checkout or release runner. It does not
accept an arbitrary `--ref`, download code, invoke a package manager, or execute
target-project code. A user obtains a newer verified runner through the existing
release/checksum/provenance path and then runs its dry-run update.

All mutation commands are dry-run-first. Human output must state:

- the observed state;
- why an item is safe, changed, blocked, or inapplicable;
- the exact project-relative paths affected; and
- one safe continuation command when user action is required.

JSON output is stable UTF-8 with a trailing newline. Status values are
`CURRENT`, `UPDATE_AVAILABLE`, `DRIFTED`, `BLOCKED`, `PLANNED`, `APPLIED`,
`REPAIRED`, and `ARCHIVED`.

## Installed ownership state

An initialized or migrated project contains `.divan/install-state.json`:

```json
{
  "schema_version": 1,
  "product": "divan-project-os",
  "contract_schema": 2,
  "installed": {
    "version": "0.16.0",
    "source_repository": "https://github.com/trugurpala/divan",
    "source_ref": "v0.16.0",
    "source_commit": "40-lowercase-hex"
  },
  "project_identity": "sha256:64-lowercase-hex",
  "managed_files": [
    {
      "path": ".divan/PROJECT_RULES.md",
      "mode": "whole-file",
      "payload_sha256": "sha256:64-lowercase-hex"
    },
    {
      "path": "AGENTS.md",
      "mode": "marked-block",
      "payload_sha256": "sha256:64-lowercase-hex"
    }
  ]
}
```

Rules:

- Keys, ordering, path normalization, and enum values are schema-locked.
- `project_identity` uses the existing project identity function and never
  contains an absolute path.
- `source_commit` comes from verified release metadata or a clean repository
  HEAD. Ambient environment variables cannot establish it.
- `source_ref` must be an immutable release tag for release runners. Clean
  development checkouts record `development@<commit>` only in local fixtures
  and cannot establish public adoption evidence.
- `managed_files` is sorted by normalized path and contains no duplicate,
  absolute, parent, symlink, reparse-point, directory, or unknown paths.
- `payload_sha256` identifies the last Divan-generated whole-file payload or
  marked block, not the entire mixed host file.
- The file contains no baseline file bodies, credentials, usernames, hostnames,
  personal paths, plugin inventory, or hidden reasoning.

`.divan/config.json` advances to schema 2 but retains its existing user-facing
fields. `managed_files` remains a sorted path list for compatibility and human
inspection; ownership fingerprints live only in `install-state.json`.

## Status and drift classification

`project status` is read-only and does not create a lock, journal, backup, cache,
or network request. It validates config, install state, waivers, managed files,
current project inspection, receipts, and the running Divan source identity.

Each managed surface receives exactly one classification:

| Classification | Meaning |
|---|---|
| `current` | Observed owned payload equals both recorded and desired payload |
| `update-available` | Observed payload equals recorded payload; desired payload changed |
| `user-modified` | Observed payload differs from recorded payload |
| `missing` | Recorded managed path or required marked block is absent |
| `unsafe` | Path, file type, marker structure, encoding, or containment is unsafe |
| `unmanaged` | Desired v0.16 surface is not present in prior ownership state |
| `stale-record` | Ownership state names a surface the current contract no longer manages |

Overall status is deterministic:

- any `unsafe`, malformed schema, unknown future schema, unverifiable source, or
  concurrent transaction produces `BLOCKED`;
- any `user-modified` whole file produces `DRIFTED`;
- only safe desired changes produce `UPDATE_AVAILABLE`;
- exact equality produces `CURRENT`.

The existing `audit` and `verify` commands keep their DPS responsibilities.
`project status` is the lifecycle and ownership view; it does not duplicate
standards evaluation.

## Update algorithm

`project update` builds a deterministic plan from three facts:

1. the recorded payload hash from `install-state.json`;
2. the observed whole-file payload or marked Divan block; and
3. the desired payload rendered by the running immutable Divan version.

No target code or generated workflow is executed during planning.

Rules by ownership mode:

- **Whole file, unchanged by user:** if observed hash equals recorded hash,
  Divan may replace it with the desired payload.
- **Whole file, user modified:** if observed hash differs from recorded hash,
  update is `BLOCKED`. Divan reports the path and does not overwrite, merge,
  rename, delete, or create a conflict file.
- **Marked block, unchanged by user:** if the block hash equals the recorded
  hash and exactly one well-formed marker pair exists, Divan may replace only
  that block. Surrounding bytes and original LF/CRLF convention remain intact.
- **Marked block, user modified:** a changed, missing, duplicated, reordered, or
  nested marker region is `BLOCKED`; content outside markers is never a reason
  to block.
- **New managed surface:** Divan may create it only when the path is absent. An
  existing unowned file at the path is `BLOCKED`.
- **Retired managed surface:** v0.16.0 does not delete it automatically. It is
  reported as `stale-record` with a later explicit removal path; automatic
  managed-file deletion is a non-goal for this release.

After every planned write, the plan binds the preimage hash, desired hash,
ownership mode, source commit, project identity, and full plan digest.
`--execute` rejects any changed preimage before mutation.

## Repair algorithm

`project repair` restores the currently installed release; it is not an update
to a newer release.

- A missing whole-file surface may be recreated only when ownership state proves
  that Divan owned the path and the path is still absent.
- A corrupted or user-modified whole-file surface is `BLOCKED`. v0.16.0 has no
  force-overwrite option; the user must restore a trusted copy or reconcile the
  file manually before rerunning repair.
- A missing or modified marked block is never force-repaired because its
  boundary ownership cannot be proven. The command returns `BLOCKED` with
  instructions to restore the markers or reinitialize in a clean copy.
- Unsafe paths, unknown schemas, and source identity failures cannot be forced.

Repair therefore fixes only provably missing generated whole files and
incomplete trusted transactions. It cannot be used as a general overwrite
switch.

## Schema 1 to schema 2 migration

The only automatic migration in v0.16.0 is Project OS config schema 1 to schema
2.

Migration is allowed when all of the following are true:

- the project passes the v0.15 config, waiver, containment, marker, and managed
  surface validators;
- no Project OS transaction is active or ambiguous;
- every existing managed payload can be reproduced and hashed from the schema 1
  configuration;
- the running Divan source identity is verified; and
- a complete dry-run migration plan is accepted with `--execute`.

Migration first records a trusted schema 1 ownership snapshot, then applies the
schema 2 update in the same transaction. If any payload is modified or cannot
be reproduced, migration returns `BLOCKED` without creating
`install-state.json`.

Unknown, malformed, or schema versions greater than 2 are never coerced or
downgraded.

## Transaction and recovery model

Project update and repair reuse the proven initialization transaction
primitives but move their orchestration into focused lifecycle modules. A
transaction has:

- a private host state directory with the existing ACL/mode checks;
- one project lock bound to project identity, process identity, hostname, nonce,
  and creation time;
- an authority document containing exact preimages and desired payloads;
- a durable journal persisted before every filesystem mutation;
- a trusted external marker binding authority hash, project identity, source
  commit, and plan digest; and
- verified rollback of only the paths owned by that transaction.

Recovery is progressive and repeatable. A second interruption can resume
recovery. A changed postimage, replaced lock, forged journal, missing authority,
or ambiguous staging directory fails closed and preserves evidence for manual
inspection.

Successful update or repair atomically writes the new ownership state last.
Failure restores the previous config, ownership state, and managed payloads.

## Goal archive

`goal archive` keeps active work legible without deleting evidence.

- Only goals in `VERIFIED`, `RELEASED`, or `OBSERVED` may be archived.
- `BLOCKED`, `FAILED`, and unfinished goals cannot be archived.
- Dry-run reports the source goal, terminal phase, artifact hashes, receipt
  verification, and destination.
- Execution re-verifies the receipt and every referenced spec, plan, task, and
  result immediately before mutation.
- The goal moves from `.divan/specs/<goal-id>/` to
  `.divan/archive/YYYY-MM-DD-<goal-id>/`.
- Its evidence moves from `.divan/evidence/<goal-id>/` into the same archive
  directory under `evidence/`.
- `archive.json` binds the prior receipt hash, artifact hashes, terminal phase,
  archive date, and source-relative paths.
- Archive dates use the verified receipt's terminal event date, not the local
  clock, so repeated planning is deterministic.
- A legacy schema-1 receipt has no signed event date. Its archive plan is
  `BLOCKED` until the owner supplies `--recorded-on YYYY-MM-DD`; the explicit
  declaration becomes the deterministic `declared-legacy-terminal-event`
  authority in `archive.json`. Divan never infers this date from file metadata.
- Existing destinations, symlinks, invalid receipts, hash drift, or
  cross-filesystem partial moves are `BLOCKED`.

The archive is append-only. v0.16.0 does not merge feature specifications into a
new global product spec because Divan cannot infer a project's authoritative
spec structure safely.

## Adoption receipt

`adoption export` produces a portable JSON document and a Markdown summary from
an already verified project receipt. It is read-only and writes to stdout unless
the user explicitly redirects it.

The JSON contains:

- schema version and Divan release identity;
- coarse OS family and architecture;
- declared Agent Skills host name and version supplied by the user;
- project type and workspace count, without repository name or path;
- goal intent hash, terminal phase, check IDs, outcomes, and evidence hashes;
- init/update/repair/rollback outcomes when present;
- a boolean stating whether the submitter declares independence from the Divan
  maintainer; and
- the source receipt hash.

It excludes command output bodies, environment variables, emails, usernames,
repository remotes, tokens, secrets, absolute paths, unrelated plugins, and
hidden reasoning. `adoption verify` validates schema, redaction, hashes, release
identity, and required evidence but cannot prove a human's independence.

Only evidence submitted by a person who is not the Divan owner/developer can
change the `independent-adoption` v1 gate. The validator reports
`valid-owner-canary` for maintainer-operated evidence and never upgrades that
status to independent adoption.

## Public canary repository

The release process creates or updates `trugurpala/divan-project-canary` only
after the core lifecycle implementation passes Divan's protected PR.

The canary is a minimal public static application with no credentials,
analytics, database, billing, or production dependency. Its workflow uses the
released `divan-project.pyz` checksum and attestation, never an unpinned branch.
The canary proves:

1. clean v0.15.0 initialization;
2. preservation of user text outside managed markers;
3. a small goal through verification and receipt validation;
4. v0.15.0 to v0.16.0 schema migration and update;
5. deterministic detection of a user-modified whole file;
6. safe repair of a missing owned generated file;
7. transaction rollback after injected interruption;
8. goal archival;
9. public release and live URL readback; and
10. owner-canary adoption export that remains ineligible for the v1 gate.

The canary repository is product evidence, not a fork and not an independent
user. It does not add a runtime dependency to Divan.

## Module boundaries

The current `project_os.py` is already large. v0.16.0 must not add lifecycle
ownership, migration, and archive orchestration directly to it.

- `project_state.py`: schemas, safe loading, normalization, source identity, and
  managed payload classifications.
- `project_lifecycle.py`: status, update, repair plans, execution, and recovery.
- `goal_archive.py`: archive planning, validation, execution, and archive
  verification.
- `adoption.py`: export, redaction, and receipt verification.
- `project_os.py`: existing init/audit/verify compatibility façade and shared
  rendering helpers.
- `cli.py`: argument parsing and dispatch only.

Public functions use JSON-compatible dictionaries at the CLI boundary and
focused frozen dataclasses internally. Filesystem mutation is injected behind
small functions so interruption and tamper tests do not require subprocesses.

## Testing and acceptance

Tests are written first. The minimum behavior matrix covers:

- exact schema validation and stable serialization;
- v0.15 schema 1 migration on library, public-web, and monorepo fixtures;
- unchanged, user-modified, missing, unsafe, new, and stale managed surfaces;
- whole-file and marked-block ownership differences;
- LF/CRLF preservation and Turkish UTF-8 content;
- dry-run purity and idempotent second execution;
- stale preimage rejection and transaction rollback at every write boundary;
- repeated interruption recovery;
- symlink, junction/reparse point, traversal, hard-link where detectable, and
  forged-journal rejection;
- secret, home path, email, repository remote, and unrelated-plugin redaction;
- goal phase eligibility, archive collision, deterministic date, and receipt
  tampering;
- owner canary versus independent adoption classification;
- byte-identical runner builds on two clean checkouts; and
- Windows, Linux, and macOS clean-host compatibility.

The release cannot close until:

- all existing repository gates pass;
- lifecycle tests pass on all three operating systems;
- the standalone runner performs the canary migration and rollback;
- canary CI and live readback pass from immutable release assets;
- Claude and Codex remain healthy with five packages and 41 skills;
- unrelated plugin and marketplace inventories remain unchanged; and
- v1 stays 7/8 unless valid evidence is actually submitted by an independent
  user.

## Documentation and impact

The same change must update the English canonical and Turkish localized Project
OS guides, quick start, README, CLI reference, Community Standards explanation,
Wiki sources, Pages, changelog, blueprint, release manifest, and progress
ledger. The impact graph must classify lifecycle modules, install state,
adoption evidence, archive state, canary contract, and their tests.

Public documentation explains that:

- host `update` upgrades installed Divan packages;
- project `update` upgrades the Project OS contract inside one repository;
- `audit` evaluates DPS contracts;
- `project status` evaluates lifecycle ownership and drift; and
- owner-operated canary evidence does not satisfy independent adoption.

## Non-goals

v0.16.0 does not provide:

- a 24/7 daemon, scheduler, dashboard, telemetry collector, or remote state
  service;
- automatic deletion of retired managed files;
- automatic merging of user-modified whole files or malformed marked blocks;
- arbitrary remote ref download or execution;
- target dependency installation or target code execution during inspection;
- conversion of existing project specs into OpenSpec or Spec Kit formats;
- new roles, skills, packs, providers, or framework breadth;
- automatic proof that an adoption submitter is independent; or
- a v1 release without genuine external acceptance evidence.
