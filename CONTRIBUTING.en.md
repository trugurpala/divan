# Contributing to Divan

[Türkçe](CONTRIBUTING.md) · **English** · [Support routes](SUPPORT.md) ·
[Community standards](docs/Topluluk-Standartlari.md)

Divan is a local skill/plugin distribution, not a model or agent runtime. A
contribution must keep the 41-skill catalog portable, licensed, reversible,
and evidence-led.

## Choose the right route

- Ask usage questions through the Q&A route in [SUPPORT.md](SUPPORT.md).
- Report reproducible defects with the bug form.
- Report vulnerabilities only through a private security advisory.
- Propose an existing repository through the source-candidate form.
- Propose an original capability through the new-skill form.
- Submit independent v1 evidence through the acceptance-evidence form.

## Contribution path

1. Read `BLUEPRINT.md`, `UPSTREAM.md`, `THIRD_PARTY_LICENSES.md`, and the
   relevant package instructions before editing.
2. Add or change the smallest coherent unit. Do not turn source discovery into
   installation, and do not copy content without verified license/provenance.
3. Start behavior changes with a failing test. Keep host policy independent
   from Claude/Codex adapters and preserve unrelated user plugins.
4. Run the complete local gate:

```bash
python scripts/hijyen.py --check
python scripts/validate.py
python scripts/devral.py --check
python scripts/katalog.py --check
python scripts/v1.py --check
python scripts/yayin.py --check
python evals/run.py --check
python -m unittest discover -s tests -v
git diff --check
```

5. Open a focused pull request. Explain the user-visible result, risks,
   rollback path, and exact verification evidence. Do not claim behavioral
   improvement without the real-adapter and blinded-judge protocol.

## Add a new skill

Create an original skill at its real package path:

```text
plugins/<paket>/skills/<skill-adi>/SKILL.md
```

The `SKILL.md` YAML frontmatter requires a kebab-case `name` identical to its
directory (maximum 64 characters) and a `description` that says what it does
and when it triggers (maximum 1024 characters). Keep the body procedural and
single-purpose; move detail beyond 500 lines into `references/`. Then render
and verify the catalog and candidate registry:

```bash
python scripts/katalog.py --render
python scripts/katalog.py --check
python scripts/validate.py
python scripts/meclis.py --check
```

Entering the candidate registry is not adoption. An external source first
receives identity, license, provenance, hook/script/permission, and overlap
review. Even an `ADOPT` or `ADAPT` decision is not installation: immutable
pinning, attribution, evals, and inspection require a separate implementation
change.

Changes to the product must keep README, catalog, installation guide, Wiki
source, website, release manifest, and licensing/provenance records aligned.
The ten required rules in `DCS-001` through `DCS-010` are validated with:

```bash
python scripts/standartlar.py --check
```
