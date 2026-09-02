# Divan 2.0 alpha

**Vibe coding, engineered.**

This folder is the Codex-native Divan plugin package.

Divan keeps a software task bounded, uses repository evidence before generic preferences, reviews material engineering quality, and refuses to call unverified work complete.

## Alpha scope

- skills-only;
- seven core skills;
- progressive-disclosure engineering references;
- no MCP server;
- no UI;
- no published lifecycle hooks;
- no custom agent runtime.

## Daily use

After installation, use natural language:

`Divan, bu projeyi incele. En önemli riskleri bul ve bana sade anlat.`

`Divan, bu özelliği en küçük doğru değişiklikle yap ve gerçekten bittiğini kanıtla.`

You do not need to know the internal skill names.

## Validation

From the repository root:

```bash
python scripts/divan_v2_validate.py
python -m unittest tests/test_divan_v2.py tests/test_divan_v2_evals.py -v
```

Mechanical validation proves package consistency, not model-quality improvement.
