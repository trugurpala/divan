# Codex Desktop Auto-Install Design

**Issue:** [#57](https://github.com/trugurpala/divan/issues/57)  
**Target:** v0.18.1  
**Status:** Approved for implementation

## Purpose

Divan should choose the strongest installation route that the current Codex
environment can actually execute, without pretending that a skill-only
installation is a native plugin installation.

The user opts into this behavior with one command:

```powershell
python scripts/divan.py install --host codex --profile auto --ref v0.18.1 --execute
```

The same command without `--execute` remains a read-only preview.

## Product Contract

### Native route

When the Codex CLI is healthy, Divan keeps the existing native installation
path. This route may provide:

- skills and instructions,
- native commands,
- agents,
- hooks,
- MCP configuration,
- native lifecycle management.

### Verified skill fallback

When the Codex CLI is missing, not executable, or denied by the operating
system, the explicit `auto` profile selects the existing checksum- and
provenance-verified Codex skill installer.

This route provides:

- all 41 Divan skills and their instructions,
- a manifest containing version, immutable ref, source commit, archive
  checksum, and installed file checksums,
- transactional rollback and recovery.

It does **not** claim to provide native commands, hooks, MCP configuration,
agents, or native host lifecycle integration.

### Blocking route

When the Codex CLI runs but returns invalid JSON, Divan stops. This is a host
protocol or version compatibility problem, not evidence that native execution
is unavailable. Silently falling back would conceal a real incompatibility.

## Diagnosis Model

Each host doctor result exposes a stable `cli_status`:

| Status | Meaning | Auto-install decision |
|---|---|---|
| `healthy` | CLI launched and returned valid marketplace JSON | Native route |
| `missing` | Executable was not found | Verified skill fallback |
| `not-executable` | Executable format or launch contract is invalid | Verified skill fallback |
| `access-denied` | OS or package ACL denied execution | Verified skill fallback |
| `invalid-json` | CLI launched but returned an incompatible response | Block |

The subprocess boundary converts launch failures into structured results
instead of allowing `PermissionError` or `OSError` to crash the installer.

## Command-Line Experience

Existing commands keep their current behavior:

```powershell
python scripts/divan.py install --host codex
python scripts/divan.py doctor --host codex
```

The new opt-in profile is:

```powershell
python scripts/divan.py install --host codex --profile auto
python scripts/divan.py install --host codex --profile auto --execute
```

The preview states:

1. detected CLI status,
2. selected installation mode,
3. capabilities that will and will not be installed,
4. exact command that execution will run.

The execution result states:

1. selected installation mode,
2. installed version and immutable ref,
3. verification result,
4. exact rollback command,
5. one exact next command.

The first release supports `--profile auto` only with `--host codex`.
`--host both` remains available through the existing native lifecycle, while
mixed native/fallback transactions are deferred until they can share a single
atomic rollback boundary.

## Architecture

### `scripts/host_probe.py`

Owns executable discovery, launch, and error classification. It returns normal
`CompletedProcess` objects with stable Divan markers for:

- executable missing,
- access denied,
- not executable.

### `scripts/host_adapters.py`

Maps probe results and JSON parsing into the public `cli_status` contract.
Doctor output remains backward compatible at the top level and adds capability
details inside each host result.

### `scripts/host_lifecycle.py`

Adds `--profile native|auto` with `native` as the default. In `auto` mode it:

1. diagnoses Codex,
2. selects native, fallback, or blocked,
3. previews the decision unless `--execute` is present,
4. delegates fallback execution to the canonical platform installer,
5. reads the resulting manifest and verifies the declared capability mode.

### Existing fallback installers

`scripts/install_codex.ps1` and `scripts/install_codex.sh` remain the canonical
skill fallback. Divan does not duplicate their release download, checksum,
provenance, transaction, or rollback logic.

## Safety and Recovery

- No fallback is applied unless the user explicitly selects `--profile auto`.
- Dry-run remains the default.
- Immutable release refs remain mandatory.
- Existing unrelated skills are preserved.
- Interrupted fallback installation uses the existing transaction journal.
- The execution response includes the matching Codex fallback uninstall
  command.
- Secrets and raw token material are never written to manifests or logs.

## Verification

The implementation must prove:

1. missing CLI is classified as `missing`,
2. Windows access denial is classified as `access-denied`,
3. executable format failure is classified as `not-executable`,
4. valid JSON is classified as `healthy`,
5. invalid JSON is classified as `invalid-json` and blocks fallback,
6. plain install behavior is unchanged,
7. auto preview does not write,
8. auto execute uses the canonical installer,
9. fallback output declares the capability boundary,
10. rollback remains deterministic,
11. Windows canary installation and removal preserve unrelated skills,
12. full repository quality, security, compatibility, and release checks pass.

## Deliberate Non-Goals

- No automatic MCP installation.
- No hidden elevation or ACL modification.
- No replacement for the Codex CLI.
- No mixed Claude-native/Codex-fallback transaction in this patch.
- No claim that skill fallback is equivalent to native plugin support.

