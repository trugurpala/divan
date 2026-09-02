# Architecture

- Keep business rules independent from UI/framework/infrastructure details where practical.
- Make side effects visible and push I/O toward boundaries.
- Queries should not unexpectedly mutate state.
- Prefer existing modules and primitives over premature abstractions.
- Avoid generic `utils`, `helpers`, and `common` dumping grounds.
- Keep module public APIs intentionally small and avoid circular dependencies.
