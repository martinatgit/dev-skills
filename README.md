# dev-skills

A collection of useful skills to incorporate LLMs and agentic AI into the development workflow.

Skills in this repository follow the [Agent Skills open standard](https://agentskills.io/specification) and are designed to be portable across Claude Code, Codex, Cursor, GitHub Copilot, Windsurf, Goose, and other skills-compatible agents.

## Install

**Any agent (recommended):**

```sh
npx skills add martinatgit/dev-skills
```

The [`skills` CLI](https://www.npmjs.com/package/skills) detects your installed agents and copies the skills into each one's skills directory.

**Claude Code (native):**

```
/plugin marketplace add martinatgit/dev-skills
/plugin install <plugin-name>@martinatgit
```

**Manual:**

```sh
git clone https://github.com/martinatgit/dev-skills.git
# Copy the skills you want into your agent's skills directory, e.g.:
cp -r dev-skills/skills/<skill-name> ~/.claude/skills/
```

## Skills in this repository

<!-- Update this table when you add a skill. -->

| Skill | Description |
|---|---|
| `example-skill` | Starter skill demonstrating the repo's authoring conventions. |

## Authoring a new skill

1. Copy `template/SKILL.md` into `skills/<your-skill-name>/SKILL.md`.
2. Read [`docs/authoring-guide.md`](docs/authoring-guide.md) for the conventions this repo enforces.
3. Before opening a PR, walk through [`docs/portability-checklist.md`](docs/portability-checklist.md).
4. Add your skill to the table above and to `.claude-plugin/marketplace.json`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Not yet licensed for distribution. This repository is currently private / in development — no LICENSE file has been added. Do not redistribute without the owner's permission. A license will be chosen before any public release.
