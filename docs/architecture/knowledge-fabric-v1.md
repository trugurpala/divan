# Divan Knowledge Fabric v1

## Product goal

Divan should remember what the agency has learned without turning a growing Markdown book into a database.

The authoritative layer is structured local knowledge. Human-readable books, briefs and project reports are projections generated from that structured data.

## What is remembered

Knowledge is intentionally split into reusable record types:

- `project-profile` — what a project is, its stack and important constraints;
- `pattern` — a reusable implementation or architecture pattern proven in a project;
- `lesson` — a problem signature plus a resolution that should not be rediscovered blindly;
- `decision` — why an architectural or product decision was made and what trade-offs were accepted;
- `recipe` — a bounded repeatable way to create or change a project;
- `source` — an external source with provenance and license information;
- `tool` — a tool/library/framework record and why Divan may select it.

A record is not automatically true forever. Status remains explicit: `candidate`, `validated`, or `deprecated`.

## Storage model

v1 uses Python's stdlib `sqlite3` and stores data below the per-user Divan state root. No server is required.

Two tables are authoritative:

1. `knowledge_items` — normalized reusable knowledge and provenance;
2. `knowledge_observations` — where a knowledge item was reused and whether the observed outcome was success, failure or neutral.

This makes it possible to answer questions such as:

- Which patterns were reused across several projects?
- Which failure lessons keep recurring?
- Which stacks and tools appear most often?
- Did a previously successful recipe later fail?
- Which external facts are stale or missing provenance?

v1 intentionally does not auto-promote a record to `validated` because a high reuse count is evidence, not authority.

## Capture rule

A failure lesson is captured as:

`problem signature -> bounded problem summary -> resolution -> stack/tags -> evidence hash`

The deterministic problem/solution hashes reduce duplicates without requiring an embedding model or remote AI service.

A project pattern is captured as:

`pattern identity -> summary -> stack/tags -> source project -> evidence hash`

Raw project source trees are not copied into Knowledge Fabric by default. User-owned code can later be referenced by repository/commit/file identity, while external open-source code must keep source and license provenance.

## The Book is a projection

`knowledge_projection.render_book()` creates a readable Markdown view from the SQLite store.

The generated file explicitly says it is a projection. Editing it must never silently mutate the authoritative store.

This prevents the previous failure mode where the same knowledge is repeatedly copied into documentation and gradually becomes inconsistent.

## External knowledge strategy

`registry/knowledge-sources.json` is the machine-readable source policy.

The intended source model is:

- Backstage — adapt software-catalog, TechDocs and template concepts; do not pull the whole developer portal into Core.
- deps.dev — package/dependency/license/security metadata provider.
- ecosyste.ms — research/reference source with AGPL service code and CC BY-SA API-data obligations kept visible.
- OpenSSF Scorecard — timestamped open-source security-health signals, never one magic trust score.
- OSV — vulnerability/advisory provider with original advisory provenance retained.
- Copier — optional future blueprint/recipe engine with pinned template source and revision.
- MADR — decision-record shape adapted into structured decision knowledge.
- DuckDB — later analytics option only if SQLite is measured to be insufficient.
- sqlite-vec — later semantic-search option only after its pre-v1 compatibility risk is acceptable.

## World-knowledge refresh model

Divan should not perform a broad internet search for every task.

The target lookup order is:

1. project-local facts from the current repository;
2. validated Divan local knowledge;
3. candidate lessons/patterns with observation history;
4. cached attributed upstream metadata that is still fresh;
5. targeted provider lookup when material information is missing or stale;
6. explicit owner review before a new external source becomes reusable agency knowledge.

Every external record should carry source URL, license/terms class where known, fetch/verification timestamp and source-specific identity. Cached data is evidence, not permanent truth.

## Analytics v1

The first analytics surface is deliberately simple and explainable:

- total knowledge items;
- validated-item count;
- learned failure count;
- observation count;
- observed success rate;
- number of items reused across more than one project;
- top tags;
- top stack identifiers.

Future analytics may add time decay, project-type cohorts and confidence calibration, but should not create opaque AI-generated scores without measurable definitions.

## Example: hydration tracker website

A project asks for a water-intake tracking website.

Divan may remember:

- project profile: `web`, `hydration`, chosen framework and deployment constraints;
- pattern: local form state + persistence pattern that worked;
- lesson: a timezone/date bug encountered and its verified resolution;
- decision: why a particular chart or notification approach was selected;
- recipe: reusable accessibility/test/release baseline;
- observations: whether the same pattern succeeded in later wellness-dashboard projects.

The next similar project starts from these records before spending tokens and time rediscovering the same facts.

## Not implemented in v1

This slice intentionally does not yet:

- crawl arbitrary GitHub repositories for source code;
- copy public source trees into a private corpus;
- call package/security APIs automatically;
- generate embeddings;
- add a remote vector database;
- auto-promote candidate knowledge;
- let generated Markdown become authoritative;
- expose knowledge mutation to third-party plugins.

Those are separate reviewed slices.

## Next slices

1. Project fingerprint capture from lockfiles/manifests and Divan task evidence.
2. Read-only knowledge query through Desktop/Core protocol.
3. End-of-task lesson proposal: `what changed / what failed / what fixed it` with explicit acceptance.
4. deps.dev + OSV + Scorecard read-only providers with cache freshness and attribution.
5. Copier-backed blueprint registry for explicitly licensed/pinned reusable project templates.
6. Knowledge UI: `Agency Memory` with search, stale-source warnings, reuse history and success/failure observations.
7. Only after measured need: DuckDB analytics and optional semantic search.
