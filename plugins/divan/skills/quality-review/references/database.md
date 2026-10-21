# Database and Data Integrity

- Enforce invariants in the database when correctness depends on them: foreign keys, unique constraints, checks, and appropriate transactions.
- Treat read-then-write flows as possible race conditions.
- Consider idempotency for retries, jobs, webhooks, payments, and other repeatable operations.
- Avoid unbounded list queries; paginate intentionally.
- Check N+1 behavior on collection paths.
- Use decimal-safe storage for money and UTC/ISO-8601 conventions for timestamps unless the project defines otherwise.
- Make destructive migrations deploy-safe and reversible where practical.
