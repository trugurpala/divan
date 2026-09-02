---
name: quality-review
description: Review an implementation or diff for material engineering quality issues after code is written or before it is declared ready. Focus on correctness, maintainability, type design, architecture, data integrity, reliability, security, product UX, testing, accessibility, and unnecessary complexity.
---

# Quality Review

Review the smallest relevant diff and load only the reference documents needed for that surface.

For user-facing product work, load `references/product-engineering.md` in addition to narrower references that match the changed surface.

Prioritize:
1. incorrect behavior, regressions, and incomplete user workflows;
2. invalid or ambiguous states;
3. hidden side effects and unclear contracts;
4. inconsistent domain vocabulary and weak type or API boundaries;
5. data integrity, transaction, concurrency, retry, idempotency, or N+1 risks when relevant;
6. authentication, authorization, validation, and other security-boundary mistakes;
7. missing loading, empty, error, responsive, i18n, or accessibility behavior for product UI;
8. unnecessary abstractions, requests, dependencies, or performance cost;
9. missing meaningful tests, observability, or completion evidence.

Do not report formatter-owned preferences as engineering defects.
Order findings by impact and provide the smallest reasonable correction.
A review is not proof that the implementation works; hand behavioral verification to `completion-proof`.
