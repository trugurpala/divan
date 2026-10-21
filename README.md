# Divan

**Vibe coding, engineered.**

[Website](https://trugurpala.github.io/divan/) · [Türkçe](README.tr.md) · [Start here](docs/getting-started.md) · [Editors and agents](docs/compatibility.md) · [Latest prerelease](https://github.com/trugurpala/divan/releases/tag/v2.0.0-alpha.4) · [Development](docs/development.md)

Divan turns a software request into project-aware implementation, debugging, review, and verified delivery. Use it as a Codex plugin or install the same seven Agent Skills in another compatible coding agent.

> Divan, people can submit this order twice. Find the cause, fix it, and show how you checked it.

Describe the outcome in your own language. Expect working changes, meaningful progress, the checks that actually ran, and any remaining blocker. You do not need to select an internal skill or agent team.

**Where is Divan?** It runs inside a project chat in Codex after the plugin is
installed. Open a new chat in your project and ask, "Divan, inspect this project
and tell me the next useful change." The same skills can run in compatible coding
agents after project installation. The source repository is not a separate app or
a live service.

## Install

### Codex plugin

Add the repository marketplace, then open a new conversation in your project:

```bash
codex plugin marketplace add trugurpala/divan --ref main
codex plugin add divan@divan
```

Alternatively, install **Divan** through the plugin marketplace in a supported Codex surface. Daily use is natural language; there is no Divan-specific command language to learn. For a local development checkout, see [setup and verification](docs/development.md).

### Other coding agents

With Node.js 22.20+ available, run this inside the project where you want Divan:

```sh
npx --yes skills@1.7.4 add https://github.com/trugurpala/divan/tree/main/plugins/divan/skills --skill '*'
```

Choose your agent and project installation in the installer. Keep all seven skills;
they share one workflow. This uses the open-source [Vercel Skills CLI](https://github.com/vercel-labs/skills),
not a Divan service. The installer may download code and writes skill files to the
selected scope. It does not install the editor or grant tool access.

| Where | Installation route |
| --- | --- |
| Codex | Native plugin above, or portable skills; choose one per project |
| Claude Code | Portable skills with `--agent claude-code` |
| Cursor | Portable skills with `--agent cursor` |
| GitHub Copilot | Portable skills with `--agent github-copilot` in a skills-capable surface |
| Other Agent Skills hosts | Check the host's discovery paths and the installer's supported agent list |

See [compatibility, installation evidence, updates, and removal](docs/compatibility.md).
File installation, host discovery, and successful task execution are separate checks.
This repository does not claim that every editor, chat surface, or model has been tested.

## Use

```text
Divan, bu projeyi incele.
Divan, bu özelliği en küçük doğru değişiklikle yap.
Divan, bu bug'ın kök nedenini bul ve düzelt.
Divan, gerçekten bitti mi kontrol et.
```

Describe the result you want in your own language. You can use everyday words,
mixed technical terms, or imperfect spelling. Divan works with your current project,
chooses relevant tools, explains meaningful progress, and checks the result.

```text
Divan, this checkout sometimes loses the address. Fix it and show how you tested it.
Divan, mejora este formulario sin cambiar el diseño; comprueba que funciona.
Divan, kaldığımız yerden devam et. Ne çalışıyor, ne eksik, sade anlat.
```

You do not need to choose a skill or an agent team. Divan asks when an answer changes
the product or the scope of an external action; it handles routine engineering choices.
See the [first task, updates, and troubleshooting guide](docs/getting-started.md).

When a task needs another capability, Divan distinguishes installed skills, configured MCP connections, loaded tools, and live services before proposing an installation. Project rules and decisions stay in concise, linked Markdown documents; existing equivalents take precedence. See the [documentation map](docs/README.md) and the [50-point reference library](docs/reference-library.md).

## Architecture

- one shared skill source and a native Codex plugin;
- seven focused core skills;
- progressive-disclosure engineering references loaded only when relevant;
- deterministic validation and packaging;
- no MCP server, hosted backend, custom agent runtime, or bundled UI;
- no published lifecycle hooks in the current line.

The publishable package lives at `plugins/divan/`.

| Skill | Role |
| --- | --- |
| `divan` | Coordinate the user's request and choose the next relevant step |
| `repo-audit` | Understand the repository and available capabilities |
| `implementation-plan` | Plan and carry out verifiable changes |
| `root-cause-debug` | Reproduce a failure, find its cause, and fix it |
| `quality-review` | Review material engineering and user experience risks |
| `completion-proof` | Verify the result before claiming completion |
| `project-contract` | Preserve useful project rules and continuation notes |

Tools, authentication, execution permissions, and subagents come from the host.
Installing Divan does not add an API integration or bypass a host restriction.

## Quality model

Divan treats product quality as more than code style. When relevant it checks correctness, security, reliability, type and API boundaries, database integrity, i18n, responsive behavior, accessibility, loading/empty/error states, network resilience, performance, observability, dependency discipline, tests, and evidence-based definition of done.

## Validate

```bash
python scripts/divan_v2_validate.py
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/package_divan_v2.py
```

On Windows, run `./scripts/check.ps1`. It uses an existing Python 3.12+ interpreter (including Codex's bundled runtime when available); it does not install packages. CI exercises Python 3.13 on Linux and Windows.

Mechanical checks prove repository and package consistency. They do not by themselves prove that a model becomes more accurate or faster.

## Maintenance

The [launch kit](docs/launch-kit.md) includes editable Figma assets, a Turkish share card, and accurate copy for sharing Divan.

For a real task result or bug, use the [task report form](https://github.com/trugurpala/divan/issues/new/choose)
with your host and version, installation route, observed result, and a small
reproduction without credentials. Completed and failed tasks are both useful. For a contribution,
read [AGENTS.md](AGENTS.md) and [the development guide](docs/development.md), make a
focused change, and run the checks above.

Install the current Codex plugin from the repository marketplace above.

## License

[MIT](LICENSE). Each portable skill includes the same license notice. External
discovery catalogs are references, not bundled dependencies or endorsements.
