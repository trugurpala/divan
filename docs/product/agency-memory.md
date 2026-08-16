# Agency Memory — Product Contract

## Promise

A vibe coder should be able to open a project and ask Divan to understand it without paying the discovery cost from zero every time.

Agency Memory turns previous project work into reusable, explainable local knowledge while keeping external facts attributable and refreshable.

## Primary experience

The Desktop destination is `Hafıza`, not `Kitap`.

The first view answers:

- What has this agency learned?
- Which lessons are relevant to the current project?
- Which patterns have worked in more than one project?
- Which knowledge is stale or only a candidate?
- Where did an external fact come from?

## Information architecture

### Overview

Show compact metrics:

- knowledge items;
- validated items;
- learned failures;
- patterns reused across projects;
- observed success rate;
- stale external sources.

Metrics are descriptive, not a magic agency score.

### Relevant now

When a project is selected, rank knowledge by:

1. exact framework/library matches;
2. project-type/tag matches;
3. repeated success in similar projects;
4. freshness and validation status;
5. direct task/problem text match.

A candidate lesson may be shown, but must be visibly different from validated knowledge.

### Lessons

Each lesson shows:

- practical problem;
- verified resolution;
- stack and tags;
- source project identity;
- evidence identity when available;
- how many distinct projects reused it;
- observed success/failure history;
- candidate / validated / deprecated status.

Do not show raw worker transcripts by default.

### Patterns and recipes

A pattern describes reusable structure. A recipe describes a repeatable operation or project baseline.

Future recipe execution must remain behind Divan mandate/evidence gates. A successful past recipe is not permission to mutate a new project automatically.

### Sources

External knowledge shows:

- source name and URL;
- license/terms class;
- fetched/verified timestamp;
- cache policy;
- what normalized fields Divan retained.

Source popularity must never be presented as correctness.

## Project-open workflow

When the operator says `Projeyi tanı ve planla`:

1. fingerprint the current repository locally;
2. query Agency Memory first;
3. show relevant prior lessons/patterns;
4. check cached upstream metadata freshness;
5. perform targeted provider lookups only for missing/material facts;
6. build the plan with citations to local knowledge and fresh provider evidence;
7. do not mutate until the normal execution approval gate.

This reduces repeated searches while preventing stale memory from silently becoming truth.

## End-of-task workflow

After review/evidence is complete, Divan may create a **learning proposal** containing:

- what was attempted;
- what failed;
- what fixed it;
- reusable pattern, if any;
- stack/framework versions;
- evidence hashes;
- suggested tags.

The proposal enters memory as `candidate`. Reuse observations accumulate later. Validation remains explicit and auditable.

## Noise controls

Do not save every chat message, terminal line, source file or transient exception.

Prefer records only when at least one condition holds:

- a non-obvious failure was solved;
- a decision had meaningful trade-offs;
- an implementation pattern is likely reusable;
- a recipe establishes a repeatable quality baseline;
- external metadata materially affected planning;
- a previous lesson was proven wrong and needs deprecation.

## Vibe-coder example

Operator:

`Bu klasörü aç, projeyi tanı ve planla.`

Divan:

- detects a React/Vite wellness tracker;
- finds a prior hydration-dashboard pattern;
- recalls a date/timezone lesson that previously caused a bug;
- sees the earlier Playwright baseline succeeded in two projects;
- checks framework docs only if the stored version/fact is stale;
- proposes a plan that reuses proven patterns and flags what still needs fresh research.

The user benefits from agency memory without needing to understand how the knowledge database works.

## Design rules

- Search-first, not document-first.
- Plain-language consequence before metadata.
- Status uses text, not color alone.
- Provenance is visible but secondary until needed.
- No opaque AI confidence badge.
- No automatic mutation because a recipe exists.
- No arbitrary public-code corpus.
- Generated Book/Markdown is export, never authority.
