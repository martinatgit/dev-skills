# dev-skills

A collection of useful skills to incorporate LLMs and agentic AI into the development workflow.

Skills in this repository follow the [Agent Skills open standard](https://agentskills.io/specification) and are designed to be portable across Claude Code, Codex, Cursor, GitHub Copilot, Windsurf, Goose, and other skills-compatible agents.

## Install

See [`docs/install.md`](docs/install.md) for the full {scope × agent} matrix, per-skill env-var overrides, and project-root detection. Quick starts below.

**Any agent (recommended):**

```sh
npx skills add martinatgit/dev-skills              # all detected agents
npx skills add martinatgit/dev-skills --project    # force project scope
npx skills add martinatgit/dev-skills -a claude-code -a codex   # specific agents
```

The [`skills` CLI](https://www.npmjs.com/package/skills) detects your installed agents and copies the skills into each one's skills directory.

**Claude Code (native plugin marketplace):**

```
/plugin marketplace add martinatgit/dev-skills
/plugin install dev-skills@martinatgit
```

**Manual:**

```sh
git clone https://github.com/martinatgit/dev-skills.git
# Pick the right destination for your agent and scope (see docs/install.md):
cp -r dev-skills/skills/<skill-name> ~/.claude/skills/        # Claude Code, user scope
cp -r dev-skills/skills/<skill-name> ~/.agents/skills/        # Codex / Cursor / Goose, user scope
cp -r dev-skills/skills/<skill-name> .claude/skills/          # project scope (Claude Code)
cp -r dev-skills/skills/<skill-name> .agents/skills/          # project scope (Codex / Cursor / Goose)
```

### Per-skill runtime configuration

Skills follow a two-scope configuration pattern:

- **User scope** at `~/.config/<skill-name>/config.yaml` — for non-path tunables (limits, expiry, model tiers).
- **Project scope** at `<project_root>/.<skill-name>/config.yaml` — for path-typed keys like `root_dir`. Path keys are project-only by design, so a user-installed skill never bleeds one project's writes into another.

```sh
# Configure a skill for the current project
python3 scripts/configure.py --scope project

# Set a one-off override
DEVELOPER_DIARY_ROOT_DIR=/tmp/test-diary  # env var wins over both files
```

Full env-var table and the project-root detection rules are in [`docs/install.md`](docs/install.md).

### Project conventions (one-line setup)

Set one docs-folder convention for every skill in the project:

```sh
# Create <project_root>/.agents/dev-skills.yaml with docs_root: agent-docs
python3 scripts/setup-conventions.py --non-interactive --docs-root agent-docs
```

See [`docs/install.md`](docs/install.md#shared-conventions) for the full schema and resolution rules.

## Skills in this repository

<!-- Update this table when you add a skill. -->

| Skill | Description |
|---|---|
| [`example-skill`](skills/example-skill/SKILL.md) | Starter skill demonstrating the repo's authoring conventions. |
| [`developer-diary`](skills/developer-diary/SKILL.md) | Persistent engineering knowledge across sessions. Reads the diary before design or implementation work, updates it after, and reviews it for structural repair. Invoke with `read`, `update`, or `review`. |
| [`reason-through`](skills/reason-through/SKILL.md) | Multi-perspective reasoning framework. Dispatches up to 23 specialist reasoning agents in parallel and synthesises their outputs into one integrated answer with a falsifiable terminal claim. |
| [`update-todos`](skills/update-todos/SKILL.md) | Captures deferred decisions, design inconsistencies, convention violations, missing tests, and open questions as atomic markdown notes in `doc/TODOs/` with full context. Invoke with `capture`, `clarify`, `list`, `resolve`, `review`, `maintenance`, `health`, or `import`. |
| [`terminology`](skills/terminology/SKILL.md) | Curates the project's shared technical vocabulary in a single glossary file (default `doc/terminology.md`). Invoke with `define` (or `/define-term <…>`), `get`, `review`, or `validate`. |
| [`create-tutorial`](skills/create-tutorial/SKILL.md) | Generate a textbook-style technical tutorial for a software component. Invoke with `/create-tutorial <topic>`. Writes to `tutorials_dir` (project-only Pattern 2 key; falls through to `.agents/dev-skills.yaml`). |
| [`chargebee`](skills/chargebee/SKILL.md) | Chargebee billing and subscription development guidance: Product Catalog 1.0/2.0, hosted checkout and Chargebee.js, payment intents (3DS/SCA), webhooks and event ordering, dunning, entitlements. Loads detailed references on demand. |
| [`debugger`](skills/debugger/SKILL.md) | Authoritative reference for debugger and tracer design: trace semantics, event-model design, breakpoint/spy-point semantics, cross-formalism coherence, time-travel replay, remote debug protocols. |
| [`formal-methods`](skills/formal-methods/SKILL.md) | Authoritative reference for SAT/SMT, CLP/CP, theorem proving, temporal logic, TLA+, and model checking. Use for algorithm selection, decidability analysis, propagator engine review, formal-system audits. |
| [`improve-prompt`](skills/improve-prompt/SKILL.md) | Transform rough user-intent text into one polished, paste-ready LLM prompt. Evidence-guarded against the well-replicated failure modes of prompt engineering (CoT misuse, persona-on-factual, lost-in-middle, unwrapped untrusted input). |
| [`petri-net-theory`](skills/petri-net-theory/SKILL.md) | Authoritative reference for Petri net theory: formal foundations, decidability, compliance modelling, P/T/CPN/WF-net patterns. |
| [`sanity-design-analysis`](skills/sanity-design-analysis/SKILL.md) | Analyse a software design for simplicity and maintainability. Produces a structured report covering mental model, assumptions, narrative, rules, happy/error paths, conflicts, diagrams, and a build-from-scratch tutorial. |
| [`srs`](skills/srs/SKILL.md) | Authoritative reference for synchronous reactive systems: tick architecture, signal semantics, clock calculus, constructive causality. |
| [`type-theory`](skills/type-theory/SKILL.md) | Authoritative reference for formal type systems: lambda cube, type inference (HM, bidirectional), advanced systems (GADTs, refinement, gradual, session, graded), category-theoretic foundations. |

## Agents in this repository

Agents are dispatchable subagent definitions paired with skills. They ship in two formats — Markdown for Claude Code and TOML for Codex CLI — and are installed via `scripts/install-agents.py` (or `/plugin install` for Claude Code).

| Agent | Paired skill |
|---|---|
| [`improve-prompt-agent`](agents/improve-prompt-agent.md) | `improve-prompt` |
| [`create-tutorial-agent`](agents/create-tutorial-agent.md) | `create-tutorial` |
| [`formal-methods-agent`](agents/formal-methods-agent.md) | `formal-methods` |
| [`petri-net-theory-agent`](agents/petri-net-theory-agent.md) | `petri-net-theory` |
| [`srs-agent`](agents/srs-agent.md) | `srs` |
| [`type-theory-agent`](agents/type-theory-agent.md) | `type-theory` |
| [`debugger-agent`](agents/debugger-agent.md) | `debugger` |
| [`terminology-agent`](agents/terminology-agent.md) | `terminology` |

See [`docs/agents-guide.md`](docs/agents-guide.md) and [`docs/install.md`](docs/install.md#installing-agents).

## Authoring a new skill

1. Copy `template/SKILL.md` into `skills/<your-skill-name>/SKILL.md`.
2. Read [`docs/authoring-guide.md`](docs/authoring-guide.md) for the conventions this repo enforces.
3. Before opening a PR, walk through [`docs/portability-checklist.md`](docs/portability-checklist.md).
4. Add your skill to the table above and to `.claude-plugin/marketplace.json`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Not yet licensed for distribution. This repository is currently private / in development — no LICENSE file has been added. Do not redistribute without the owner's permission. A license will be chosen before any public release.
