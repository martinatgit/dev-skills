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

## Skills in this repository

<!-- Update this table when you add a skill. -->

| Skill | Description |
|---|---|
| [`example-skill`](skills/example-skill/SKILL.md) | Starter skill demonstrating the repo's authoring conventions. |
| [`developer-diary`](skills/developer-diary/SKILL.md) | Persistent engineering knowledge across sessions. Reads the diary before design or implementation work, updates it after, and reviews it for structural repair. Invoke with `read`, `update`, or `review`. |
| [`reason-through`](skills/reason-through/SKILL.md) | Multi-perspective reasoning framework. Dispatches up to 23 specialist reasoning agents in parallel and synthesises their outputs into one integrated answer with a falsifiable terminal claim. |
| [`update-todos`](skills/update-todos/SKILL.md) | Captures deferred decisions, design inconsistencies, convention violations, missing tests, and open questions as atomic markdown notes in `doc/TODOs/` with full context. Invoke with `capture`, `clarify`, `list`, `resolve`, `review`, or `import`. |

## Authoring a new skill

1. Copy `template/SKILL.md` into `skills/<your-skill-name>/SKILL.md`.
2. Read [`docs/authoring-guide.md`](docs/authoring-guide.md) for the conventions this repo enforces.
3. Before opening a PR, walk through [`docs/portability-checklist.md`](docs/portability-checklist.md).
4. Add your skill to the table above and to `.claude-plugin/marketplace.json`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Not yet licensed for distribution. This repository is currently private / in development — no LICENSE file has been added. Do not redistribute without the owner's permission. A license will be chosen before any public release.
