---
name: completion-proof
description: Verify a software task before claiming it is complete. Use after implementation or repair to connect the requested outcome to executed checks, observed results, changed files, and remaining risks.
---

# Completion Proof

Before saying done:

- restate the requested outcome;
- inspect the final diff;
- run the narrowest behavior check that proves the change;
- run applicable repository gates such as tests, typecheck, lint, build, migration validation, or security checks;
- separate pre-existing failures from introduced failures;
- report skipped or unavailable checks explicitly;
- identify remaining material risk.

Use observed language: `passed`, `failed`, `blocked`, or `not run`.
Never convert a timeout, missing tool, skipped test, or unobserved deployment into success.
Do not claim production publication unless the published artifact or live result was actually verified.
