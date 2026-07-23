# ADR 0005: English-canonical Divan Company OS

## Status

Accepted for implementation on 2026-07-23.

## Context

Divan already validates packages, releases, Wiki, site, host lifecycle, and
community standards, but those relationships are distributed across scripts
and documents. Installed users still need to understand internal skill and
script names. Turkish technical filenames also increase the contribution
barrier for a global public repository.

## Decision

Ship a standard-library Company OS inside the Sadrazam plugin. It discovers
project evidence, routes intent to functional roles and package-qualified
skills, calculates transitive change impact, and returns deterministic plans.
English becomes canonical for technical contracts and entry points; Turkish
remains a complete locale and brand language. Existing Turkish entry points
remain compatibility wrappers during migration.

## Consequences

- Claude and Codex receive the same portable contracts.
- Users can state intent without memorizing package, skill, or script names.
- Repository and target-project impact can be explained from one graph.
- No daemon, hosted service, or new runtime dependency is introduced.
- Compatibility surfaces increase short-term maintenance but prevent a
  breaking migration.
- Behavioral quality claims still require the existing real-agent eval
  protocol; contract validation alone proves only mechanism and structure.

