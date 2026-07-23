# Divan Company OS

Divan turns a natural-language request into a small, evidence-led software
company around the coding agent. It does not simulate dozens of personas or
add a second agent runtime. It selects only the roles, packs, framework rules,
and verification gates justified by the project and requested outcome.

## How it works

1. **Inspect** reads bounded project manifests without executing project code.
2. **Plan** classifies the work, detects frameworks, selects a workflow, and
   names the smallest qualified team.
3. **Deliver** uses Core Pack for engineering discipline, UI Pack for product
   interfaces, React Pack only for detected React/Next.js work, and Zanaat Pack
   only for creative or integration work.
4. **Impact** expands changed paths through the dependency graph so catalog,
   documentation, Wiki, site, evaluation, and release checks cannot be missed.
5. **Verify** requires fresh tests and independent review before completion.

Ordinary users write their intent naturally. Maintainers and integrations can
use the same portable contracts directly:

```powershell
python scripts/divan.py inspect --project .
python scripts/divan.py plan --project . --intent "Improve the onboarding UI"
python scripts/divan.py impact README.md plugins/sadrazam/skills/sadrazam/SKILL.md
python scripts/divan.py company-validate
```

The installed plugin carries the stdlib-only implementation under
`plugins/sadrazam/company/`; it does not send project data anywhere.

| Pack | Selected for | Excluded from |
|---|---|---|
| Core Pack | planning, tests, debugging, review, verification | never skipped for product changes |
| UI Pack | interface, UX, accessibility, browser validation | backend-only work |
| React Pack | detected React, Next.js, or React Native projects | unrelated frameworks |
| Zanaat Pack | MCP/API integrations and original creative assets | ordinary feature development |

The contracts are `roles.json`, `workflows.json`, `frameworks.json`, and
`impact-graph.json`. English is canonical for technical identifiers; Turkish
remains a supported user locale. See [Türkçe](Company-OS.tr.md).
