# Divan engineering contract

## Product

Divan is a Codex-first engineering plugin. Keep the product simple for the user and sophisticated internally.

## Working rules

1. Read the requested outcome, current Git state, and relevant project files before editing.
2. Preserve user-authored changes. Do not overwrite unrelated work.
3. Prefer the smallest correct change and existing repository primitives.
4. Do not add MCP, hooks, services, frameworks, databases, or dependencies without a demonstrated product need.
5. Keep top-level skills few and high-signal. Put specialized detail in progressive-disclosure references.
6. Treat external input as untrusted at system boundaries.
7. Keep naming and domain vocabulary consistent with the repository.
8. For bugs, reproduce before claiming a cause.
9. A review is not verification. Run the real applicable checks before saying work is complete.
10. Report only observed results. Missing tools, skipped tests, timeouts, and unverified deployments are not success.
11. Do not claim model-quality, speed, or accuracy improvements without real comparative eval evidence.
12. Do not commit, merge, tag, release, or publish beyond the scope explicitly requested by the user.

## V2 alpha boundary

The publishable plugin is `plugins/divan/`.

V2 alpha is skills-only:
- no MCP;
- no app/UI;
- no published hooks;
- no custom agent runtime.

## Canonical checks

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_divan_v2*.py" -v
python scripts/package_divan_v2.py
```

Do not say the branch is ready unless these checks pass in the current tree.
