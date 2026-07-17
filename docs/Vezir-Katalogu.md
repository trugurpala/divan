# Vezir Kataloğu

> Tek doğru kaynak: `plugins/*/skills/*/SKILL.md`. Bu sayfa
> `python scripts/katalog.py --render` ile deterministik üretilir.

Toplam **41 skill**, **5 paket**.

## core-pack (18 vezir)

| Vezir | Ne yapar / ne zaman |
|---|---|
| **arama-ustasi** | Evidence-first codebase search using ripgrep for bounded text discovery and optional ast-grep for syntax-aware structural search. Use when exploring an unfamiliar repository, locating definitions or call sites, estimating refactor impact,… |
| **baglam-muhafizi** | Context-budget guardian for long-running agent work. Use when a session becomes long or repetitive, tool outputs dominate the conversation, retrieved documents overwhelm the task, compaction or handoff is approaching, multiple agents need… |
| **brainstorming** | You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. |
| **dispatching-parallel-agents** | Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies |
| **executing-plans** | Use when you have a written implementation plan to execute in a separate session with review checkpoints |
| **finishing-a-development-branch** | Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup |
| **kaynak-kuratori** | Evidence-first curator for repository lists, agent skills, plugins and templates. Use when the user shares GitHub or shortened links, asks to install or learn from many repositories, says kendini geliştir, bu repoları incele, hangisini… |
| **kural-hazinesi** | Curated framework and craft rule library (CC0, from the awesome-cursorrules treasury). Provides battle-tested coding rules for clean code, anti-overengineering, code quality, databases, Docker, Next.js plus Tailwind plus SEO, Python or… |
| **receiving-code-review** | Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation |
| **requesting-code-review** | Use when completing tasks, implementing major features, or before merging to verify work meets requirements |
| **subagent-driven-development** | Use when executing implementation plans with independent tasks in the current session |
| **systematic-debugging** | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes |
| **temkin** | Engineering prudence for coding agents - four enforced principles that prevent the classic agent failure modes. Apply proactively on every coding task, and especially when the user says temkinli ol, sade tut, abartma, over-engineer etme,… |
| **test-driven-development** | Use when implementing any feature or bugfix, before writing implementation code |
| **using-git-worktrees** | Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback |
| **verification-before-completion** | Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always |
| **writing-plans** | Use when you have a spec or requirements for a multi-step task, before touching code |
| **writing-skills** | Use when creating new skills, editing existing skills, or verifying skills work before deployment |

## react-pack (8 vezir)

| Vezir | Ne yapar / ne zaman |
|---|---|
| **deploy-to-vercel** | Deploy applications and websites to Vercel. Use when the user requests deployment actions like "deploy my app", "deploy and give me the link", "push this live", or "create a preview deployment". |
| **vercel-composition-patterns** | React composition patterns that scale. Use when refactoring components with boolean prop proliferation, building flexible component libraries, or designing reusable APIs. Triggers on tasks involving compound components, render props,… |
| **vercel-optimize** | Use for Vercel cost and performance optimization on deployed projects, especially Next.js, SvelteKit, Nuxt, and limited Astro apps. Collect Vercel metrics, usage, project config, and code scan results first; investigate only metric-backed… |
| **vercel-react-best-practices** | React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance patterns. Triggers on tasks involving React… |
| **vercel-react-native-skills** | React Native and Expo best practices for building performant mobile apps. Use when building React Native components, optimizing list performance, implementing animations, or working with native modules. Triggers on tasks involving React… |
| **vercel-react-view-transitions** | Guide for implementing smooth, native-feeling animations using React's View Transition API (`<ViewTransition>` component, `addTransitionType`, and CSS view transition pseudo-elements). Use this skill whenever the user wants to add page… |
| **web-design-guidelines** | Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices". |
| **writing-guidelines** | Review docs/prose for Writing Guidelines compliance. Use when asked to "review my docs", "check writing style", "audit prose", "review docs voice and tone", or "check this page against the writing handbook". |

## sadrazam (5 vezir)

| Vezir | Ne yapar / ne zaman |
|---|---|
| **defterdar** | Persistent project memory keeper for the USER's project (Ottoman treasurer-scribe). Creates and maintains AGENTS.md, BLUEPRINT.md (vision, ADR decision records, roadmap, status log), a .divan/ progress journal, decision records and a… |
| **musavir** | Technology stack advisor (counselor vizier). Recommends the current world-standard stack by project type - landing page, SaaS, e-commerce, mobile, AI app, fintech/borsa - covering framework, database, ORM, auth, payments and hosting, each… |
| **ordu-nizami** | Native-first agent orchestration for Claude Code and Codex. Use when a task may benefit from subagents, parallel research, isolated worktrees, dynamic agent workflows, or experimental Agent Teams, and when the user asks for orchestration,… |
| **sadrazam** | End-to-end delivery orchestrator (the "Grand Vizier"). Use whenever the user asks to build, create, produce, or ship anything substantial — a feature, an app, a document, a campaign — especially with phrases like "baştan sona", "hepsini… |
| **vezir-yetistirme** | Skill-creation and evaluation coach for the Divan marketplace ("training a new vizier"). Use when the user wants to add, improve, benchmark or test a skill, write a SKILL.md, contribute to the marketplace, compare skill-enabled behavior… |

## ui-pack (3 vezir)

| Vezir | Ne yapar / ne zaman |
|---|---|
| **frontend-design** | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. |
| **ui-ux-pro-max** | UI/UX design intelligence for web and mobile. Searchable local database with 84 styles, 192 color palettes, 74 font pairings, 192 product types, 98 UX guidelines, 104 icon entries, 16 GSAP motion presets, and 25 chart types across 22… |
| **webapp-testing** | Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs. |

## zanaat-pack (7 vezir)

| Vezir | Ne yapar / ne zaman |
|---|---|
| **algorithmic-art** | Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems. Create original… |
| **canvas-design** | Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying… |
| **claude-api** | Claude API and Anthropic SDK reference for model selection, pricing, parameters, streaming, tool use, MCP, agents, caching, token counting and migrations. Use whenever the request names Claude, Anthropic, Opus, Sonnet, Haiku, the… |
| **mcp-builder** | Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python… |
| **slack-gif-creator** | Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like "make me a GIF of X doing Y for Slack. |
| **theme-factory** | Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate… |
| **web-artifacts-builder** | Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui… |
