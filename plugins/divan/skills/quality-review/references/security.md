# Security

- Treat external input as untrusted at HTTP, form, URL, webhook, file, queue, environment, and third-party API boundaries.
- Client-side visibility is not authorization; enforce permissions at trusted server/database boundaries.
- Prefer deny-by-default behavior for sensitive capability checks.
- Keep secrets out of source control, diagnostics, snapshots, and fixtures.
- Do not weaken sandbox, permission, CI, or repository security gates to make a task easier.
