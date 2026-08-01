# Divan v1.1 Vibe UX Council Implementation Plan

> Execute this plan test-first. Preserve v1.0.2 and work only on the isolated release-candidate branch.

**Goal:** Create one premium product-design audit path, reduce redundant approval friction safely, curate current UI/UX sources, and make the public entry points human-readable.

**Architecture:** Existing packs and the stdlib-only engine remain unchanged. A new UI-pack skill composes existing design/testing skills. Candidate research stays metadata-only in `registry/candidates.json`. Behavioral authority is documented and mechanically tested in the brainstorming skill. Generated catalogs remain derived artifacts.

## Task 1: Lock the behavior contract with failing tests

- Add a characterization test for explicit, bounded pre-authorization.
- Add exclusions for publishing, release, destructive actions, secrets, payments, messaging, and account/security work.
- Run the focused test and observe RED before editing the skill.
- Update `brainstorming/SKILL.md` minimally and rerun to GREEN.

## Task 2: Add the product-design-audit skill test-first

- Add catalog/schema tests that require the skill and its five-stage contract.
- Add contract eval cases for a desktop/mobile audit, missing visual evidence, and prioritized findings.
- Run focused tests and observe RED.
- Add the original `product-design-audit/SKILL.md` and rerun to GREEN.

## Task 3: Expand the Candidate Council

- Add tests for at least ten exact source IDs, immutable commits, decisions, and licenses.
- Run the council tests and observe RED.
- Add reviewed records to `registry/candidates.json`; do not copy candidate code.
- Regenerate `docs/Aday-Meclisi.md` and rerun council checks.

## Task 4: Synchronize product and release surfaces

- Update UI pack metadata and product catalog surfaces for the new skill.
- Prepare consistent v1.1 candidate metadata using the repository release workflow.
- Rewrite the README opening and quick path in English and Turkish canonical surfaces.
- Update Blueprint/progress/changelog/site/wiki surfaces required by the release manifest.

## Task 5: Update the public profile independently

- Create a separate profile-repository branch.
- Replace the stale pre-v1 statement with accurate v1.0.2 language and a direct start link.
- Keep the personal voice concise and avoid product slogans.

## Task 6: Inspect and deliver evidence

- Run focused unit, catalog, candidate, skill, release, and docs tests.
- Inspect the rendered public surfaces at desktop and mobile sizes.
- Run `python scripts/verify.py` and `git diff --check`.
- Request an independent code review, resolve findings, push branches, and open pull requests.
- Do not merge or publish a release without a separate explicit instruction.

