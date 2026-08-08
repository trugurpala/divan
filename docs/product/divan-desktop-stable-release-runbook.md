# Divan Desktop Stable Windows Release Runbook

This runbook is the operator sequence for the first stable Divan Desktop Windows release. It does not weaken or replace `docs/product/divan-desktop-release-checklist.md`; the checklist remains authoritative for DONE/OPEN gate state.

Divan Core remains authoritative for task state, mandate, evidence, review, approval, merge and release. Orca remains a replaceable execution engine.

## Safety rules

- Run the stable chain only from `main`.
- Resolve the exact current `main` commit immediately before DSK-06 and use that 40-character SHA as the acceptance `source_sha`.
- Freeze `main` while the DSK-06 -> DSK-07 -> DSK-08 chain is in progress. Any new `main` commit invalidates the chain; rerun acceptance/readiness/candidate on the new source instead of reusing stale evidence.
- Never upload, paste into issue/PR text, or commit Authenticode credentials, Tauri private keys, private-key passwords, or signing command secret values.
- Do not treat a PR contract run, unsigned installer, synthetic acceptance file, or unattested artifact as stable-release evidence.
- Keep the `desktop-acceptance` and `production-release` GitHub environments protected.

## 1. Resolve and freeze the source identity

From an authenticated maintainer shell:

```powershell
$SourceSha = (gh api repos/$env:GITHUB_REPOSITORY/git/ref/heads/main --jq '.object.sha').Trim()
if ($SourceSha -notmatch '^[0-9a-f]{40}$') { throw 'Could not resolve exact main SHA' }
$SourceSha
```

When running outside GitHub Actions, set `GITHUB_REPOSITORY` first or replace it with `trugurpala/divan`.

Do not merge another commit to `main` until the release chain completes. If `main` moves, stop and restart this runbook from step 1.

## 2. DSK-06 — Real-user Windows acceptance

Prerequisites:

- protected Windows x64 self-hosted runner online with labels `self-hosted`, `windows`, `x64`, `divan-desktop-acceptance`
- genuine authenticated Codex and Claude Code sessions available to that runner account
- `desktop-acceptance` environment approval/policy satisfied

Dispatch `Desktop Real-User Acceptance` with the exact source SHA:

```powershell
gh workflow run desktop-acceptance.yml --ref main -f source_sha=$SourceSha
```

The workflow must pass the authenticated agent preflight, build/install the exact source, execute the real worker -> diff -> independent cross-agent reviewer -> approval -> `ff-only` merge flow, verify installed Core provenance, attest the privacy-minimal JSON evidence and upload exactly the expected acceptance artifact.

Record the successful workflow run ID as `AcceptanceRunId`. Do not continue with a failed, cancelled, stale or source-mismatched run.

## 3. DSK-07 — Production signing readiness

The protected `production-release` environment must provide these secret names without exposing their values:

- `DIVAN_UPDATER_PUBKEY`
- `DIVAN_UPDATER_ENDPOINT`
- `DIVAN_UPDATER_ARTIFACT_BASE_URL`
- `DIVAN_WINDOWS_SIGN_COMMAND`
- `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` when the key requires it

The artifact base must target the exact immutable Desktop release namespace `desktop-v<version>`, and the updater endpoint must be production-controlled HTTPS.

Before dispatch, confirm `main` still equals `$SourceSha`:

```powershell
$LiveMain = (gh api repos/$env:GITHUB_REPOSITORY/git/ref/heads/main --jq '.object.sha').Trim()
if ($LiveMain -ne $SourceSha) { throw 'main moved; restart from DSK-06 on the new source' }
```

Dispatch `Desktop Production Readiness`:

```powershell
gh workflow run desktop-production-readiness.yml --ref main
```

The workflow must prove that the configured Authenticode command can create a Windows signature reported as valid, that the Tauri private key can sign through the official Tauri signer CLI, that updater/public configuration is valid, and that attested evidence contains no private signing material.

Record the successful workflow run ID as `ProductionReadinessRunId`.

## 4. DSK-08a — Build and verify the signed stable candidate

Confirm `main` still equals `$SourceSha`, then dispatch `Desktop Stable Candidate` with both exact-source run IDs:

```powershell
gh workflow run desktop-release.yml --ref main `
  -f production_readiness_run_id=$ProductionReadinessRunId `
  -f acceptance_run_id=$AcceptanceRunId
```

The candidate workflow must independently verify that readiness and acceptance are successful manual runs from the expected workflows on the same exact `main` SHA. It must verify attestations, source commit/tree, updater E2E evidence, Authenticode, installed-app smoke, the production Tauri updater public/private key pair on the exact installer/signature pair, and build provenance.

Record the successful manual workflow run ID as `CandidateRunId`.

## 5. Pre-stage the production updater feed

Before irreversible promotion, the production updater endpoint must serve the exact source-bound `latest.json` produced by the successful candidate run. Do not hand-edit the feed into a different installer URL, signature or version.

The repository immutable-release policy must be enabled before promotion. The protected `production-release` environment must also provide `DIVAN_RELEASE_ADMIN_TOKEN` with only the repository administration capability required by the promotion workflow's immutable-release policy check.

Do not publish the GitHub Release manually; the promotion workflow owns the verified publication step.

## 6. DSK-08b — Verify and promote the stable release

Confirm `main` still equals `$SourceSha`, then dispatch `Desktop Stable Promotion`:

```powershell
gh workflow run desktop-promote.yml --ref main `
  -f production_readiness_run_id=$ProductionReadinessRunId `
  -f acceptance_run_id=$AcceptanceRunId `
  -f candidate_run_id=$CandidateRunId
```

Promotion must fail closed unless all three run IDs belong to successful manual workflows on the same exact source SHA. It re-downloads and verifies evidence/artifacts, re-runs the stable release guard, verifies the immutable-release policy, checks the pre-staged production updater feed, publishes or idempotently verifies the namespaced `desktop-v<version>` GitHub Release, re-downloads promoted assets, verifies byte identity/attestations/Authenticode and confirms the live updater artifact URL serves the exact promoted installer.

## 7. Completion criteria

Do not mark the stable Windows release complete until the canonical checklist records DSK-06, DSK-07 and DSK-08 as DONE from the real successful run IDs and exact accepted source identity.

At minimum record:

- accepted source commit and source tree
- `AcceptanceRunId`
- `ProductionReadinessRunId`
- `CandidateRunId`
- promotion run ID
- immutable `desktop-v<version>` release tag
- final installer/checksum/update-feed verification result

If any stage fails after `main` moved, restart from DSK-06 rather than attempting to reuse evidence from the old SHA.
