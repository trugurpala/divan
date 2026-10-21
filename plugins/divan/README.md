# Divan 2.0 alpha

**Vibe coding, engineered.**

This folder is the native Codex plugin package and the single source of Divan's portable Agent Skills.

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

After installation, open a new Codex conversation in your project and use natural language:

`Divan, bu projeyi incele. En önemli riskleri bul ve bana sade anlat.`

`Divan, bu özelliği en küçük doğru değişiklikle yap ve gerçekten bittiğini kanıtla.`

You do not need to know the internal skill names.

Write in your preferred language, including ordinary spelling mistakes and mixed
technical terms. Divan inspects your project, handles routine choices, and asks
only when a missing decision affects the result or authorization. It reports
meaningful progress and explains what was actually checked at the end.

`Divan, este formulario duplica pedidos. Encuentra la causa, corrígela y verifica el resultado.`

`Divan, kaldığımız yerden devam et; ne çalışıyor ve ne eksik sade anlat.`

For a status update, ask without restarting the task. An explicit language switch
changes the explanation, not your code identifiers or previous requirements.
Divan runs within the active host session; it is not a background monitoring service.

## Install and update

```sh
codex plugin marketplace add trugurpala/divan --ref main
codex plugin add divan@divan
codex plugin list --marketplace divan --json
```

For a GitHub marketplace update, run `codex plugin marketplace upgrade divan`,
then `codex plugin add divan@divan`, and open a new conversation. No separate API
key, server, or npm package is required for Divan itself.

For Claude Code, Cursor, GitHub Copilot, or another Agent Skills host, see the
[portable installation guide](https://github.com/trugurpala/divan/blob/main/docs/compatibility.md).
Install all seven folders under `skills/`, including their references and LICENSE
files. The Codex manifest is not a universal plugin manifest. The host supplies
tools, permissions, authentication, and any subagents.

## Validation

From the repository root:

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/package_divan_v2.py
```

Mechanical validation proves package consistency, not model-quality improvement.
