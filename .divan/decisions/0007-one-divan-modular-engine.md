# ADR 0007: One Divan, modular engine, owner-first governance

## Status

Accepted for v0.17.0 implementation on 2026-07-29.

This decision supersedes ADR 0005 and ADR 0006 only for current public naming
and canonical source paths. Their historical context, stable CLI contracts,
DCS/DPS identifiers, `.divan/` formats, receipts, hashes, and published release
evidence remain authoritative.

## Context

Divan grew from a skill distribution into repository routing, installed-project
state, provider evidence, release control, and adoption proof. `Company OS`,
`Project OS`, `Brain`, `Forge`, and `Nizâm-ı Sefer` began to look like separate
products even though they share one authority, one runtime, and one release
contract. The first-party core also lived under a historically named
`company/` package with flat imports.

The Hükümdar has decided that Divan remains one product and one repository. The
system must be modular without depending on another repository or a third-party
agent runtime.

## Decision

1. The product name is **Divan**. `Divan Governance Model / Divan Nizamı` names
   the governance model, not a second product.
2. The machine authority chain is:
   `owner → mandate → orchestrator → council → specialist → provider`.
   Turkish presentation labels are
   `Hükümdar → Ferman → Sadrazam → Divan → Uzman → Sağlayıcı`.
3. Only `owner` may expand scope. Every delegated layer is narrower than its
   source. Tool or provider availability never creates authority.
4. The canonical stdlib-only package is
   `plugins/sadrazam/divan_runtime/`. Its machine-readable module graph and
   governance contract are `modules.json` and `governance.json`.
5. Runtime modules are `kernel`, `governance`, `council`, `evidence`, `project`,
   `records`, `providers`, `release`, and `api`. Compatibility belongs to the
   API boundary instead of creating a second dependency branch.
6. `plugins/sadrazam/company/`, `company-validate`, `Company OS`, and
   `Project OS` remain bounded compatibility surfaces through v1 and are not
   removed before v2.
7. Existing generic commands, `.divan/`, DCS/DPS ids, install-state product
   identifiers, receipt schemas, hashes, and release provenance do not change.
8. External repositories may be research sources or bounded providers, never
   Divan's core runtime dependency. No external project is copied, installed,
   or promoted by this decision.
9. v0.17 performs a behavior-preserving package move, establishes a
   machine-validated module contract and a local public-CLI authority boundary,
   and preserves aliases. Divan Nizamı is workflow governance, not identity or
   access-control software: the host operating-system account and repository
   permissions remain the security boundary. Further internal decomposition of
   large modules happens in later reviewed slices.

## Consequences

- `python scripts/divan.py architecture --json` makes the system's order,
  modules, labels, and authority visible.
- Public runtime mutations bind the exact command scope to a deterministic
  mandate id. `--execute` is explicit local owner authority; a delegated
  `--actor` is rejected for mutation. Direct internal Python calls are not an
  independent authentication boundary.
- Canonical package imports use explicit relative imports; legacy flat imports
  are isolated in a compatibility bridge.
- The deterministic project runner carries the canonical package tree and
  validates the same contracts.
- Characterization tests must prove canonical and legacy CLIs return the same
  JSON and legacy contract JSON remains byte-identical.
- v0.17 publication does not satisfy independent adoption issue #34. v1 remains
  7/8 until a non-owner supplies reproducible, privacy-bounded evidence.
