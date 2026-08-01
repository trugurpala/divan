---
name: product-design-audit
description: Use when a vibe coder wants a premium, evidence-based audit of an existing product, page, or flow before or after implementation. Produces prioritized UI/UX findings and verifies authorized fixes without inventing visual evidence.
---

# Product Design Audit

Turn “make it better” into a small, inspectable design decision set. Audit the
real product, not an imagined replacement. Prefer a few high-impact fixes over
a decorative redesign.

## Brief

State the user, platform, page or flow, its single job, and known constraints in
five lines or fewer. Derive these from the request and repository when possible.
If one missing fact would materially change the result, name the assumption.

## Inspect

Inspect the running interface and its code when available. Cover at least one
desktop and one mobile viewport. Check the primary path, empty/loading/error
states, keyboard navigation, visible focus, content overflow, and reduced motion.
Use screenshots or DOM evidence for visual claims. If browser access or a
running build is unavailable, say so and limit findings to the evidence you have.

## Audit

Review these lenses without turning them into a generic checklist:

- information hierarchy and the page's single job;
- interaction clarity, feedback, recovery, and state continuity;
- accessibility: semantics, keyboard, focus, contrast, labels, and motion;
- responsive behavior at content-driven breakpoints;
- content that sounds human and names actions consistently;
- visual distinctiveness grounded in the product's subject;
- implementation quality that can change user-visible behavior.

Use existing `ui-ux-pro-max` guidance for the broad UX quality floor,
`frontend-design` when a new visual direction is truly needed, and
`webapp-testing` for browser evidence. Do not invoke all three by habit.

## Prioritize

Return at most ten findings. Put blockers first, then high-leverage improvements,
then polish. Every finding must include:

- **severity:** blocker, high, medium, or polish;
- **evidence:** screenshot/DOM/file reference or a clearly named limitation;
- **impact:** what becomes difficult, unclear, inaccessible, or untrustworthy;
- **actionable fix:** the smallest concrete change that resolves the finding.

Separate defects from taste. Do not present a preference as an accessibility or
usability failure.

## Verify

Implement fixes only when authorized. Re-run focused tests and the affected
user path, then compare before and after at desktop and mobile sizes. Report
what changed, what was tested, and what remains uncertain. Never claim a quality,
accessibility, or performance improvement without direct evidence or a named
limitation.

## Output

Lead with the outcome in plain language. Follow with the prioritized findings,
the recommended first slice, and verification evidence. Avoid agency-style
sales language, invented user research, arbitrary scores, and “premium” as an
unsupported claim.
