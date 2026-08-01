# Divan v1.1 Vibe UX Council Design

**Date:** 2026-08-01  
**Status:** Approved for implementation by the user's explicit “plan, then apply without asking” instruction

## Goal

Make Divan easier to understand and more useful to a vibe coder without turning it into an unreviewed skill dump. The release candidate will add one clear premium-design entry point, document at least ten current UI/UX skill sources in the existing Candidate Council, and replace product-first public copy with a human-first path.

## Findings

- Divan v1.0.2 is a stable product: all v1 gates are closed, the canonical verification run passes 707 tests, and current GitHub workflows are green.
- The public profile still says Divan is not v1, which is now false.
- Divan already has 41 skills. Installing every popular UI repository would increase overlap, context load, license risk, and maintenance work without proving better output.
- The strict design gate prevents accidental implementation, but it also asks again when a user has already given explicit, bounded, reversible pre-authorization. That is avoidable friction; external publication, destructive work, secrets, spending, and account actions must remain gated.
- Existing UI skills are capable but fragmented. A vibe coder needs one entry point that turns a request into findings, priorities, fixes, and visual evidence.

## Chosen approach

Use a curated-council model:

1. Keep `never-auto-install` as the candidate registry authority.
2. Record at least ten immutable, license-reviewed UI/UX sources and reject or reference unsuitable ones.
3. Add one original orchestration skill, `product-design-audit`, rather than copying ten overlapping skills.
4. Relax the brainstorming gate only for explicit pre-authorization of bounded and reversible work. The agent must still state its assumptions and design before acting.
5. Rewrite the README opening around three user questions: what Divan does, what to run, and what proof appears.
6. Update the GitHub profile README separately so it describes the published v1 accurately.

## Product-design audit contract

The skill routes an existing product or interface through five stages:

1. **Brief:** identify the user, the page or flow's single job, platform, and constraints from available context.
2. **Inspect:** inspect the real interface at desktop and mobile sizes when browser tooling is available; otherwise state the evidence limitation.
3. **Audit:** cover hierarchy, interaction, accessibility, responsive behavior, content, states, and visual distinctiveness.
4. **Prioritize:** return at most ten findings, each with severity, evidence, impact, and an actionable fix. Separate blocking defects from polish.
5. **Verify:** after authorized implementation, capture focused tests and before/after visual evidence. Never claim improvement without a comparison or a named limitation.

The skill composes existing Divan capabilities; it does not copy third-party prompts or require a new runtime dependency.

## Authority and behavior

Explicit phrases such as “do not ask, apply,” “you decide and implement,” or an equivalent unambiguous instruction count as advance approval only when all work is:

- within the named repository or artifact;
- reversible;
- free of external publication, merging, release, payment, messaging, account/security, secret, or destructive actions;
- consistent with repository instructions.

The agent still presents a compact design and records assumptions. Any boundary above requires a fresh explicit approval. Ambiguity remains fail-closed.

## Public copy

The first screen of the README will use plain language and a short “start here” path. Ottoman terminology remains part of Divan's identity and governance vocabulary, but it will not be the first thing a new user must decode. Claims will stay tied to commands and current release evidence.

## Candidate decisions

The council will record at least ten sources with immutable commit pins, license evidence, overlap notes, and one of `ADAPT`, `REFERENCE`, or `REJECT`. An `ADAPT` decision is permission for a future clean-room implementation, not permission to copy or auto-install code. Provider-specific or specially licensed material remains a reference.

## Release boundary

The implementation is a v1.1 release candidate on a separate branch. It does not mutate the v1.0.2 tag or publish a release automatically. Repository checks, generated catalogs, documentation surfaces, and release metadata must agree before a pull request is opened.

## Success criteria

- A focused test proves the pre-authorization exception and its safety exclusions.
- The new skill has schema/catalog tests and contract eval cases.
- Candidate Council contains at least ten newly reviewed UI/UX sources with valid evidence.
- README and profile copy no longer contradict the published v1 state.
- `python scripts/verify.py` and `git diff --check` pass.
- No third-party skill content is copied without an explicit provenance and license path.

