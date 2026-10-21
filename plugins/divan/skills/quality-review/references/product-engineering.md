# Product Engineering Quality

Use this reference for user-facing product work. Apply it proportionally to the feature instead of forcing irrelevant ceremony.

## Product states and interaction

- Design every async flow for loading, success, empty, and error states; add retry, timeout, offline, or partial-data behavior when the workflow can encounter them.
- Prevent duplicate submits and duplicate destructive actions. Give meaningful feedback without creating toast noise.
- Do not ship fake UI or fake data as production behavior. A visible control must work, and demo fixtures must be explicitly separated from real data.
- Destructive actions need risk-appropriate confirmation, undo, or typed confirmation when the action cannot be recovered safely.
- Forms need labels, validation, server errors, disabled/loading states, keyboard submit, correct input types, autofill behavior, and accessible error feedback.

## UI system

- Prefer an existing design system and reusable primitives before creating new components. Keep color, spacing, typography, radius, shadow, breakpoint, z-index, and motion decisions token-driven.
- Premium quality means controlled hierarchy, spacing, typography, states, alignment, and consistency—not decorative gradients, glow, glass effects, or cards everywhere.
- Responsive behavior is a component-level requirement. Check mobile, tablet, laptop, desktop, wide screens, long text, table overflow, dialogs, dropdowns, sidebars, and touch targets.
- Accessibility is part of correctness: semantic HTML, keyboard navigation, visible focus, heading order, label relationships, accessible dialogs/menus/tooltips, sufficient contrast, and screen-reader status messages.
- Respect `prefers-reduced-motion`; use motion only when it explains state or improves orientation.
- If dark mode is supported, express it through tokens rather than one-off overrides.

## i18n and content

- User-facing strings should be i18n-ready when the product is localized. Use meaningful namespaces and locale-aware date, time, number, percentage, currency, timezone, and plural formatting.
- Avoid string concatenation that breaks translation and layouts that assume English-length copy or left-to-right text.
- UI copy should explain the result of an action. Prefer specific labels such as “Save changes” or “Create project” over ambiguous “OK”, “Submit”, or “Click here”.
- Keep terminology consistent across UI, API, types, and documentation.

## Data, API, and network

- Treat API requests, API responses, forms, URL parameters, webhooks, environment variables, database JSON, and third-party responses as untrusted at their boundaries.
- Use type safety and runtime validation where compile-time types cannot protect the boundary. Avoid `any`, unsafe casts, and suppression comments without an explicit reason.
- Keep API contracts and error shapes consistent; use correct status semantics and predictable route naming.
- Network flows should consider timeout, cancellation, stale responses, race conditions, retries only for transient failure, and debounce where user input can create request storms.
- Put shareable navigation state such as search, filters, sorting, pagination, and selected tabs in the URL when it is genuinely part of navigation.

## Security and data integrity

- Security is deny-by-default at trust boundaries. Client-side visibility is not authorization; enforce authorization on the server or database boundary.
- Never expose secrets, tokens, credentials, private URLs, stack traces, SQL, or sensitive user data to the client or logs.
- Check relevant risks including XSS, CSRF, injection, SSRF, path traversal, unsafe uploads, rate limits, secret leakage, and privilege escalation.
- Database changes should use migrations and deliberate primary keys, foreign keys, unique/not-null constraints, indexes, timestamps, transaction boundaries, and concurrency behavior.
- Avoid N+1 access patterns and unlimited list queries; paginate or bound work based on expected data size.

## Performance and dependencies

- Performance is a product feature. Look for unnecessary renders, client components, requests, duplicate requests, oversized bundles/images, blocking work, leaks, and expensive calculations.
- Use lazy loading, code splitting, pagination, virtualization, caching, prefetch, or memoization only when the measured or obvious workload justifies them.
- Before adding a dependency, prefer the platform, framework, current dependency set, or a small internal implementation. Check maintenance, license, security, bundle/runtime cost, and API stability.

## Observability and verification

- Production failures should be diagnosable through structured logging, request/correlation IDs, timing, error context, audit logs, and health signals when the system needs them. Never log secrets or unnecessary personal data.
- Test behavior rather than implementation details. Cover critical happy paths and meaningful failures: authentication, authorization, validation, create/update/delete flows, loading/empty/error states, permissions, and critical responsive behavior where relevant.
- A completed implementation should pass the repository’s applicable format, lint, typecheck, tests, and build commands. Browser work should have no known console errors, hydration warnings, failed requests, key warnings, or accessibility warnings in the verified flow.

## Definition of done

Definition of done means the requested workflow works end-to-end and the applicable quality gates are observed, not assumed. Confirm correctness, security, reliability, usability, accessibility, performance, consistency, validation, tests, build/type/lint gates, dead-code absence, and that no fake UI or fake data remains in the shipped path. If a relevant gate cannot be run, report it as unverified instead of calling the work complete.
