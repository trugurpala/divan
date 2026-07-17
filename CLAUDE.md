# Divan repository guidance

Read `AGENTS.md`, `BLUEPRINT.md`, `UPSTREAM.md`, and
`THIRD_PARTY_LICENSES.md` before changing this repository.

Keep Divan native-first and dependency-light. Do not make an external agent
harness a default dependency. Never vendor content without a verified license,
and record every imported source and intentional patch. Use parallel agents
only for independent, bounded work; isolate concurrent writes with worktrees.

Before completion, run:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
git diff --check
```

If the product changes, update both READMEs, catalog, changelog, blueprint,
installation docs, version file, and site in the same change. A draft PR is an
intermediate state, not a public delivery. When publication is authorized,
verify the default branch and live surface after merge. Do not initialize,
commit, push, release, or overwrite user project files unless the user asks.
