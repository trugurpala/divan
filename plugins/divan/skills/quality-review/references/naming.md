# Naming and Vocabulary

- Follow existing repository conventions first.
- Prefer `kebab-case` for web-facing paths and file names when the project has no stronger convention.
- Prefer `camelCase` for JavaScript/TypeScript values and functions; `PascalCase` for components and types.
- Boolean names should read as questions: `is`, `has`, `can`, `should`.
- Functions should use explicit verbs and stable semantics: `find` may return absence; `get` should not secretly create.
- Do not mix synonyms such as customer/client/account for one domain concept.
- Avoid vague names such as `data`, `temp`, `misc`, `helper`, or `manager` when a domain term exists.
