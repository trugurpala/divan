---
name: quality-review
description: Review an implementation or diff for material engineering quality issues after code is written or before it is declared ready. Focus on correctness, maintainability, type design, architecture, data integrity, reliability, security, testing, accessibility, and unnecessary complexity.
---

# Quality Review

Review the smallest relevant diff and load only the reference documents needed for that surface.

Prioritize:
1. incorrect behavior and regressions;
2. invalid or ambiguous states;
3. hidden side effects and unclear contracts;
4. inconsistent domain vocabulary and weak type boundaries;
5. data integrity, transaction, concurrency, retry, idempotency, or N+1 risks when relevant;
6. security boundary mistakes;
7. unnecessary abstractions or dependencies;
8. missing meaningful tests;
9. accessibility and user-state failures for UI work.

Do not report formatter-owned preferences as engineering defects.
Order findings by impact and provide the smallest reasonable correction.
A review is not proof that the implementation works; hand behavioral verification to `completion-proof`.
