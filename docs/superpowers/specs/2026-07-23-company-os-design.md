# Divan Company OS Design

## Product decision

Divan becomes an English-canonical, bilingual company operating system for
vibe coders. A user states intent in natural language; Divan discovers the
project, selects the smallest qualified team, maps affected surfaces, applies
the relevant Core/UI/React/Zanaat skills, and reports verified delivery.

The brand names Divan and Sadrazam remain. Technical filenames, commands,
schemas, identifiers, diagnostics, and default contributor documentation use
English. Turkish remains a complete, first-class locale.

## Boundaries

- No always-on daemon, hidden network service, model API, or third-party agent
  harness is added.
- The engine is Python standard-library only and ships inside the `sadrazam`
  plugin so Claude and Codex receive the same contracts.
- Project inspection is read-only. It reads bounded marker files and never
  installs dependencies or executes project code.
- Role definitions describe responsibilities, inputs, outputs, skills, and
  gates. They do not impersonate named people or claim unmeasured expertise.
- Existing Turkish script entry points remain temporary compatibility wrappers.
  New documentation and generated recovery commands use the English CLI.

## Installed architecture

`plugins/sadrazam/company/` is the portable control plane:

- `roles.json`: functional company roles and skill contracts.
- `workflows.json`: feature, bug, UI, React, release, integration, creative,
  and documentation delivery chains.
- `frameworks.json`: bounded project detectors and framework-specific skills
  and checks.
- `impact-graph.json`: conditional source-to-surface relationships.
- `engine.py`: registry validation, project detection, workflow selection,
  team selection, and transitive impact calculation.
- `cli.py`: stable `inspect`, `plan`, `impact`, and `validate` commands.

The repository-level `scripts/divan.py` is the canonical developer entry
point. It exposes company commands and the host lifecycle commands `install`,
`update`, `doctor`, and `recover`. `scripts/kur-hostlar.py` remains a deprecated
compatibility wrapper for the v0.13 argument shape.

## Company roles

The first contract contains Product Strategist, UX Designer, Frontend
Engineer, Backend Engineer, QA Engineer, Platform Engineer, Security Reviewer,
Release Manager, Technical Writer, Creative Producer, Integration Engineer,
and Independent Reviewer.

Every role has:

- stable English identifier and English/Turkish display labels;
- mission, required inputs, and concrete outputs;
- package-qualified skill references;
- required verification gates.

Core Pack supplies planning, TDD, debugging, review, worktree, and verification
discipline. UI Pack supplies design-system, accessibility, frontend design, and
browser testing. React Pack is selected only when React or Next.js is detected.
Zanaat Pack supplies MCP/API integration and creative artifact capabilities
only when the workflow requires them.

## Impact semantics

An impact rule has path globs, one or more effects, required checks, and an
optional change class. Effects can reference other effects; the engine computes
the transitive closure and returns a stable sorted result.

Examples:

- a skill contract change affects catalog, package validation, documentation,
  and evaluation;
- a package inventory change additionally affects marketplace metadata,
  README counts, Wiki, site, and release checks;
- a public version change affects every release-manifest surface;
- a UI source change requires accessibility and browser verification;
- a workflow or registry change requires company-contract validation.

The first release reports impact and fails closed on malformed contracts. A
later change may compare Git diffs automatically after this contract is proven.

## Localization and naming

- Python modules: ASCII English `snake_case`.
- Workflows and documents: ASCII English `kebab-case`.
- Schema keys and error codes: English.
- Human messages: English by default; Turkish through `--lang tr`.
- Root README: English canonical; Turkish content moves to `README.tr.md`.
- Compatibility wrappers are tested, documented as deprecated, and removed
  only in a later breaking release.

## Verification

The company registries and engine receive unit tests for malformed contracts,
framework detection, team routing, pack selection, impact closure, stable JSON,
locale output, path safety, and compatibility wrappers. Repository validation,
Clean Code, Ruff, mypy, coverage, official skill/plugin validators, Wiki,
publication, and all existing tests remain mandatory.

