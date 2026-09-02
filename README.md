# Divan

**Vibe coding, engineered.**

Divan is a Codex-first engineering plugin for builders who want simple natural-language control without giving up planning, code quality, debugging discipline, and evidence-based delivery.

## Status

`2.0.0-alpha.1` is the Codex-native rewrite line.

The active package lives at:

```text
plugins/divan/
```

The previous Divan implementation remains available in Git history and published legacy releases. It is not carried forward into the active rewrite tree.

## Install

After this rewrite is merged to `main`, add the repository marketplace:

```bash
codex plugin marketplace add trugurpala/divan
```

Restart the ChatGPT desktop app, open the Plugins Directory, choose the Divan marketplace, and install **Divan**. Daily use is natural language; no Divan-specific CLI is required.

For the alpha branch, append `--ref rewrite/codex-native` while testing.

## What Divan does

You can speak normally:

```text
Divan, bu projeyi incele.
Divan, bu özelliği en küçük doğru değişiklikle yap.
Divan, bu bug'ın kök nedenini bul ve düzelt.
Divan, gerçekten bitti mi kontrol et.
```

Internally Divan uses a small set of focused skills to inspect the repository, plan bounded work, debug root causes, review engineering quality, and verify completion. You do not need to learn the internal skill names.

## V2 alpha architecture

- one plugin;
- seven core skills;
- engineering-taste references loaded only when relevant;
- standard-library validation and packaging;
- no MCP server;
- no custom agent runtime;
- no hosted backend;
- no UI;
- no published lifecycle hooks.

## Validate

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_divan_v2*.py" -v
python scripts/package_divan_v2.py
```

Mechanical checks prove package consistency. They do not by themselves prove that a model becomes more accurate or faster.

## Repository policy

Read `AGENTS.md` before changing the project.

The V2 design and implementation plan are in:

- `docs/superpowers/specs/2026-09-02-codex-native-divan-design.md`
- `docs/superpowers/plans/2026-09-02-codex-native-divan.md`

## License

MIT
