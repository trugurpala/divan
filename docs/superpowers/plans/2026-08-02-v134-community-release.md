# Divan v1.3.4 Community Release Plan

> **Status:** In progress  
> **Scope:** A bounded patch release; no new runtime, package, fork, or
> unverified product claim.

## Goal

Publish the already merged risk-hardening work as a safe, understandable
community patch. A new user must be able to install a pinned release on Windows,
macOS, or Linux, see a truthful result, and find the contribution and support
paths without reading internal implementation details.

## Evidence already available

- `main` contains the risk-hardening merge, the Ruff tool-contract repair, and
  the Windows PowerShell checksum portability repair.
- The Windows repair has focused regression coverage that runs with an empty
  `PSModulePath`, the environment that exposed the missing `Get-FileHash`
  command.
- The immutable `v1.3.3` tag and its assets remain untouched.

## Release steps

1. Wait for all workflows for merge commit `4d34971` to finish successfully.
   A running workflow is not treated as evidence.
2. Prepare `v1.3.4` only through `scripts/release.py`; update the changelog and
   public state records with precise, testable wording.
3. Run the canonical verifier with coverage, prose, catalog, release, v1,
   host doctor, and whitespace checks from a clean worktree.
4. Open a focused release PR, require its CI to pass, then merge it.
5. Read back the tag, non-draft GitHub Release, checksums, SBOM, attestations,
   Pages, Wiki, and canonical README from the default branch.
6. Record the evidence and leave one exact next maintenance action. If any
   required check fails, stop the release and fix only the proven failure.

## Acceptance criteria

- No open PR or issue is hidden behind the release claim.
- `v1.3.4` names the portable Windows checksum verification and the existing
  risk-hardening boundaries without claiming measured speed or quality gains.
- A fresh `python scripts/verify.py --coverage` and `git diff --check` pass.
- Current install examples pin `v1.3.4`; prior release tags remain immutable.
- The live community surfaces point to the same published source line.
