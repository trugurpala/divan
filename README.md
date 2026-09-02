# Divan

**Vibe coding, engineered.**

Divan is a Codex-first engineering plugin for builders who want simple natural-language control without giving up planning, debugging discipline, product quality, and evidence-based delivery.

## Install

Add the repository marketplace:

```bash
codex plugin marketplace add trugurpala/divan --ref main
```

Then install **Divan** from the plugin marketplace in a supported Codex surface. Daily use is natural language; there is no Divan-specific command language to learn.

## Use

```text
Divan, bu projeyi incele.
Divan, bu özelliği en küçük doğru değişiklikle yap.
Divan, bu bug'ın kök nedenini bul ve düzelt.
Divan, gerçekten bitti mi kontrol et.
```

Divan keeps the workflow behind the scenes: repository inspection, bounded planning, root-cause debugging, engineering review, and completion evidence.

## Architecture

- one Codex plugin;
- seven focused core skills;
- progressive-disclosure engineering references loaded only when relevant;
- deterministic validation and packaging;
- no MCP server, hosted backend, custom agent runtime, or bundled UI;
- no published lifecycle hooks in the current line.

The publishable package lives at `plugins/divan/`.

## Quality model

Divan treats product quality as more than code style. When relevant it checks correctness, security, reliability, type and API boundaries, database integrity, i18n, responsive behavior, accessibility, loading/empty/error states, network resilience, performance, observability, dependency discipline, tests, and evidence-based definition of done.

## Validate

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_divan_v2*.py" -v
python scripts/package_divan_v2.py
```

Mechanical checks prove repository and package consistency. They do not by themselves prove that a model becomes more accurate or faster.

## Maintenance

Read `AGENTS.md` before changing Divan. Keep the public repository focused on product source, tests, validation, and user documentation. Internal implementation-session artifacts are not part of the shipped product.

Previous Divan implementations remain recoverable from Git history and published legacy releases, but they are not part of the active package.

## License

MIT
