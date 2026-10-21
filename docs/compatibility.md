# Divan across editors and agents

[Türkçe özet](#türkçe-kısa-yol) · [First task](getting-started.md) · [Development](development.md)

Divan has one source: seven Agent Skills in `plugins/divan/skills/`. Codex also
has a native plugin wrapper. Install one route for a given host and project;
duplicate plugin and skill installations can create ambiguous routing.

Because the workflow must inspect and change local project files, the Codex
skills-only manifest declares `requires_local_executor: true`. This labels a
public-directory submission as Desktop only; it does not grant local execution
permissions. Portable skills remain available for other compatible coding agents
in their own project workspaces. See the [official OpenAI desktop-only plugin
guidance](https://developers.openai.com/plugins/deploy/desktop-only).

## Choose an installation

| Host | Project route | What the host documentation establishes |
| --- | --- | --- |
| Codex | Native plugin, or portable `.agents/skills/` | Plugin and skill discovery are separate installation routes |
| Claude Code | `.claude/skills/`, installer agent `claude-code` | Skill discovery and explicit `/divan` invocation |
| Cursor | `.agents/skills/`, installer agent `cursor` | Agent Skills discovery; `.cursor/skills/` is another native location |
| GitHub Copilot | `.agents/skills/`, installer agent `github-copilot` | Skills support in documented Copilot surfaces; availability varies by surface |
| Other Agent Skills hosts | Consult the host and installer agent list | File-format compatibility alone does not prove discovery or task success |

The installer currently shares `.agents/skills/` between Codex, Cursor, and
Copilot. These are shared files, not three separate copies. User-wide local skills
do not automatically appear in remote or cloud sessions. This guide does not
claim installation into every ChatGPT surface, an API endpoint, or a generic chat box.

For the native Codex plugin, use the [README installation](../README.md#codex-plugin).
It requires no Node.js installation for Divan.

## Portable installation

Prerequisite: Node.js 22.20 or later. The optional installer is the MIT-licensed
[Vercel Skills CLI 1.7.4](https://github.com/vercel-labs/skills/releases/tag/v1.7.4).
`npx` can download and execute that package; the skills themselves are Markdown
and license files. No Divan server, API key, account, or subscription is introduced.
Host usage charges and permissions still belong to the host.

In the project where you want Divan, first inspect the source:

```sh
npx --yes skills@1.7.4 add https://github.com/trugurpala/divan/tree/main/plugins/divan/skills --list
```

Then install all seven skills. This example targets Claude Code:

```sh
npx --yes skills@1.7.4 add https://github.com/trugurpala/divan/tree/main/plugins/divan/skills --skill '*' --agent claude-code --copy
```

Replace `claude-code` with `cursor`, `github-copilot`, or `codex` as appropriate.
Omit `--agent` to use the interactive host selector. Project scope is the default;
`-g` deliberately changes it to user-wide scope. `--copy` keeps independent
installed files. Do not use `--all` to mean all Divan skills: it also targets every
supported agent. `--skill '*'` is the intended skill selector.

All seven skills are required because `divan` links to companion instructions.
Preserve their `references/` and `LICENSE` files. Existing skills with the same
names must be reviewed before replacement; the names are not namespaced.

For a checked-out source, replace the GitHub URL with the absolute
`plugins/divan/skills` directory. This is the path used for local installation
verification. A reviewed commit URL can replace `main` when reproducibility is
more important than tracking the latest source.

## Verify and use

1. Check that the selected project skill directory contains all seven folders,
   each with `SKILL.md`, its license notice, and any references.
2. Start a new host session or follow its reload instructions. Check its skill
   list if exposed; ask it to identify the loaded Divan file before a first task.
3. Try a small real task in a disposable project. Observe changed files and the
   actual test output; installation success is not task success.

> Divan, inspect this repository, explain the most useful next fix, and implement it with evidence.

If automatic discovery fails, use the host's documented skill invocation. In
Claude Code, `/divan` explicitly invokes this standalone skill. A prompt containing
the word “Divan” alone does not prove that any host loaded the skill.

Tools, subagents, authentication, and execution access are supplied by the host.
An unavailable action stays unavailable after installing a skill. Keep the host's
existing project instructions, including `CLAUDE.md`, `AGENTS.md`, and editor rules.

## Update or remove

For the Codex plugin, follow [the update steps](getting-started.md).
For portable skills, review the new source, then repeat the same `add` command in
the same project and host scope. Recheck the files and start a new session. Keep
intentional local edits before replacing a copied installation.

For removal, use the Skills CLI's `remove` command and select only the seven Divan
skills in the intended scope. The skill names are `divan`, `repo-audit`,
`implementation-plan`, `root-cause-debug`, `quality-review`, `completion-proof`,
and `project-contract`. Review shared `.agents/skills` use before removing them:
another host in the same project may use those files. Do not remove unrelated skills.

## Evidence and limits

Keep three distinct checks: files were installed correctly; a particular host
discovered them; a real task succeeded in that host. Versioned validation and
packaging check source consistency, linked resources, and retained notices.
They do not establish comparative model quality or equal results across languages.

On 2026-10-21, Windows with Node.js 24.19.0 and `skills@1.7.4` installed a snapshot
of the current local skill source into a temporary project and user profile using
`--agent codex claude-code cursor github-copilot --copy -y`. Both generated trees
(`.agents/skills` and `.claude/skills`) contained all seven skills and 28 files;
their SHA-256 hashes matched the source, including notices and references. The
entrypoint's companion links resolved inside the installed tree. Global profile
changes were not needed. This verifies file installation, not runtime discovery
in Cursor or Copilot; the CLI's inventory labeled Codex and Claude Code only.

The local Codex plugin was detected and enabled. A separate real Codex CLI task
trial reached a host execution-policy block before reading its requested files;
that trial is not a passing behavior test. No Claude Code, Cursor, or Copilot
end-to-end task result is claimed here. Machine-specific paths and raw trial
evidence stay outside the public repository.

On 2026-10-22, the published GitHub `main` skills-folder URL was installed into
a fresh temporary Codex project with `skills@1.7.4`, `--skill '*'`, `--agent codex`,
`--copy`, and `-y`. The command found and installed seven skills. All 28 installed
files matched the current source tree by SHA-256, with no missing or extra files.
This verifies the remote-source installation path, not host discovery or task
behavior.

## Sources checked on 2026-10-21

- [Agent Skills specification](https://agentskills.io/specification): portable format and relative resources.
- [Vercel CLI commands at v1.7.4](https://github.com/vercel-labs/skills/blob/v1.7.4/docs/commands.md) and [agent locations](https://github.com/vercel-labs/skills/blob/v1.7.4/docs/agents.md).
- [Claude Code skills](https://code.claude.com/docs/en/skills), [Cursor skills](https://cursor.com/docs/context/skills), and [GitHub Copilot skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).
- [GitHub README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes): purpose, getting started, help, and maintenance.

[AgenticSkills.io](https://agenticskills.io/) is a discovery directory, distinct
from the Agent Skills specification above. Directory listings and prompts.chat
candidates are not installed tools or proof of compatibility. Commands are based
on the official versioned installer documentation rather than directory articles.

## Türkçe kısa yol

Codex eklentisini koruyoruz; aynı yedi beceri başka editörlere de kurulabiliyor.
Yukarıdaki komutta ajanını seç, proje kapsamında kur ve yeni sohbet aç. `/divan`
Claude Code'un açık çağırma yoludur; diğer uygulamalarda kendi beceri listesini
kontrol et. Kurulu dosya, algılanan beceri ve başarılı gerçek iş ayrı kanıtlardır.
Bir beceri kurulumu GitHub yetkisi, MCP bağlantısı veya alt ajan erişimi oluşturmaz.
