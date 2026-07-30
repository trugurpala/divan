# v0.18.1 local release-candidate evidence

Verified on 2026-07-30 for
[issue #57](https://github.com/trugurpala/divan/issues/57).

## Candidate identity

- Version: v0.18.1
- Base commit: `162d8eb8363f03d6a050faa416cf761c5d6f29a6`
- Verified implementation head:
  `4f46e25e0c0e16baceed8f3d87a8c31f6c2ea4e8`
- Branch: `feat/codex-auto-install`
- Product shape: one Divan repository and one modular stdlib-only engine
- v1 readiness: 7/8; independent adoption issue #34 remains open

## Implemented capability

Codex Desktop installation has an explicit `auto` profile. It distinguishes a
healthy native CLI from missing, non-executable, access-denied, and invalid-JSON
states. A healthy CLI keeps the native plugin route. Only eligible launch
barriers may select the checksum-backed skill fallback; invalid JSON blocks.

The fallback verifies its immutable ref, source commit, release archive
SHA-256, exactly 41 skill names, and each installed skill-tree SHA-256. Human
output states that skills and instructions are available while native
commands, agents, hooks, MCP configuration, and lifecycle are unavailable. It
also prints a rollback command pinned to the interpreter that performed the
install.

Host option parsing, human output, process diagnosis, profile policy, and
native lifecycle execution are separate modules. The refactor removed the
existing `install` function's registered complexity and function-length debt
while preserving the CLI contract.

## Local gates

- 580 tests passed; 13 expected platform-specific tests skipped.
- Branch coverage: 77%, above the 64% fail-under gate.
- Ruff passed.
- The Clean Code ratchet passed; no new debt was accepted.
- Mypy passed across 90 first-party source files.
- Release consistency passed for v0.18.1 and 180 controlled surfaces.
- Repository validation reported 5 packages and 41 unique skills.
- Handoff, catalog, v1 scorecard, eval contracts, and final hygiene passed.

## Windows canary

The canonical PowerShell installer and uninstaller ran in isolated temporary
skill and state directories. Installation produced 41 Divan skills and left an
unrelated skill untouched. A pre-existing colliding Divan skill was quarantined
and restored after removal. No real user skill directory was used.

The immutable remote `--profile auto --ref v0.18.1 --execute` canary remains a
post-publication gate because the checksum-backed release asset does not exist
before the tag and GitHub Release are published.

## Publication boundary

This record establishes a local release candidate. It does not claim an
immutable tag, GitHub Release, published assets, attestations, GitHub CI,
checksum-backed remote fallback success, live Pages/Wiki convergence,
independent adoption, or measured productivity improvement. Those claims
require remote readback and are recorded separately.
