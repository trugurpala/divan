# Divan engineering contract

## Product

Divan is a Codex-first engineering plugin with a portable Agent Skills source. Keep the product simple for the user and sophisticated internally. Maintain one shared set of seven skills; do not duplicate their behavior for each editor.

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

## Continuity and capability choices

Read [docs/project.md](docs/project.md) for product intent and current scope,
[docs/decisions.md](docs/decisions.md) before changing architecture, and
[docs/development.md](docs/development.md) for setup and verification.
Read [docs/compatibility.md](docs/compatibility.md) before changing host support or portable installation instructions. Distinguish file installation, host discovery, and real task behavior.
The [50-point reference library](docs/reference-library.md) is an on-demand guide,
not a requirement to load or install 50 skills.

- Keep the user's natural-language outcome and existing authorization across turns.
- Distinguish an installed skill, configured MCP, loaded tool, live service, and candidate.
- Choose existing capabilities first. For a genuinely missing installation, present
  its purpose, source/version, scope, permissions/cost, and verification before asking.
- Record durable decisions in the existing docs; keep machine-specific evidence and
  credentials out of the public repository. `.local/` is ignored, not a secret vault.
- Recheck evidence after changes. A previous session's test result is not current proof.

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
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/package_divan_v2.py
```

On Windows, `./scripts/check.ps1` resolves an existing compatible Python and runs
all three gates. CI runs the full suite on Linux and Windows. Divan itself does not
need a web server, database, Docker, or an MCP runtime.

Do not say the branch is ready unless these checks pass in the current tree.
