# dev-skills

A collection of useful skills to incorporate LLMs and agentic AI into the development workflow.

Skills in this repository follow the [Agent Skills open standard](https://agentskills.io/specification) and are designed to be portable across Claude Code, Codex, Cursor, GitHub Copilot, Windsurf, Goose, and other skills-compatible agents.

## Install

Already checked out this repository? Start here. The **checkout** supplies the files; the **consuming project** is the project where you want to use them. They are usually different directories.

Prerequisites: Claude Code and/or Codex installed and signed in; Git for checkout updates; Node.js/npm for `npx skills`; Python 3.10+ for repository configuration and agent installers (Python 3.11+ to run the test suite). Commands below use `python`; use `python3` on systems where that is the Python 3 executable. Quoted forward-slash paths work with Python on Windows too. The helpers use only the Python standard library.

### 1. Install skills

From the **dev-skills checkout**, choose your host:

```sh
# Claude Code: personal skills available across projects
npx skills add . -g -a claude-code --skill '*' --copy

# Codex: personal skills available across projects
npx skills add . -g -a codex --skill '*' --copy
```

To install both, use `-a claude-code -a codex` in one command. To choose a subset, replace `--skill '*'` with, for example, `--skill developer-diary update-todos`. Run `npx skills add . --list` to browse first. These commands explicitly copy skills; they do not install the optional subagents below.

For **project-only** skills, change to the consuming project, give the checkout's absolute path, and omit `-g`:

```sh
cd "/path/to/your-project"
npx skills add "/path/to/dev-skills" -a claude-code -a codex --skill '*' --copy
```

| Content | Personal scope | Project scope |
|---|---|---|
| Claude skills | `~/.claude/skills/<name>/` | `<project>/.claude/skills/<name>/` |
| Codex skills | `~/.agents/skills/<name>/` | `<project>/.agents/skills/<name>/` |
| Claude subagents | `~/.claude/agents/<name>.md` | `<project>/.claude/agents/<name>.md` |
| Codex subagents | `~/.codex/agents/<name>.toml` | `<project>/.codex/agents/<name>.toml` |

Here `~` means your user home. Project installs belong in the consuming project, not the dev-skills checkout. The third-party [skills CLI](https://github.com/vercel-labs/skills) defaults to project scope; this repository's Python helpers detect a project root from the working directory.

**Claude alternative: install the whole plugin.** In Claude Code opened in the dev-skills checkout:

```text
/plugin marketplace add .
/plugin install dev-skills@dev-skills
```

This installs the bundled skills and Claude subagents at user scope by default. For project/local scope, use Claude's `/plugin` interface. The suffix is the marketplace name `dev-skills`, not the GitHub owner. For a remotely maintained marketplace, add `martinatgit/dev-skills` instead of `.`. Plugin skills are namespaced, for example `/dev-skills:improve-prompt`. Choose either the plugin route or standalone copies for Claude to avoid duplicate registrations.

### 2. Install optional subagents

Skip this step if you only need skills, or if the Claude plugin already supplies your agents. Install the paired skills first. From the checkout:

```sh
python scripts/install-agents.py -g -a claude-code -a codex --dry-run
python scripts/install-agents.py -g -a claude-code -a codex
```

Keep only the `-a` option for the host you use. Add `--agents improve-prompt-agent` to select one agent. Unknown agent names fail before installation. Identical existing files are skipped.

For project scope, run the script by absolute path **from the consuming project**, without `-g`:

```sh
cd "/path/to/your-project"
python "/path/to/dev-skills/scripts/install-agents.py" -a codex
```

Explicit `-a` options work on a first installation even before destination directories exist. Without `-a`, the installer detects host configuration directories in the project and user home. Codex agents inherit the parent's skill discovery and permissions, and their instructions request the paired skill. This is instruction-driven loading, not Claude's automatic skill preloading.

### 3. Configure each consuming project

Install once at user scope if convenient, but configure output locations separately for each project. Run from the consuming project:

```sh
cd "/path/to/your-project"
python "/path/to/dev-skills/scripts/setup-conventions.py" --non-interactive --docs-root docs
python "/path/to/dev-skills/scripts/setup-conventions.py" --print
```

This creates `<project>/.agents/dev-skills.yaml`:

```yaml
schema: dev-skills/v1
docs_root: docs
```

The shared convention covers `developer-diary`, `update-todos`, `terminology`, and `create-tutorial`. They derive paths under `docs/`, including `developer-diary/`, `TODOs/`, `terminology.md`, and `tutorials/`. Commit this file if the convention should be shared with the team.

Omit `--non-interactive` for a prompt. Repeating setup preserves existing `docs_root` and per-skill settings; supplied flags replace only their corresponding values. For example:

```sh
python "/path/to/dev-skills/scripts/setup-conventions.py" --non-interactive --terminology-filename terms.md
```

The writer normalizes YAML formatting/comments. It preserves parsed skill blocks, including keys it does not offer as CLI options; unsupported top-level keys are outside the shared schema.

For an individual exception, keep your working directory in the consuming project and invoke the relevant script:

```sh
python "/path/to/dev-skills/skills/update-todos/scripts/configure.py" --scope project --non-interactive --root-dir planning/TODOs
python "/path/to/dev-skills/skills/update-todos/scripts/configure.py" --print
```

Per-skill user defaults are at `~/.config/<skill>/config.yaml` (or `XDG_CONFIG_HOME`); project overrides are at `<project>/.<skill>/config.yaml`. Use `--scope user` for reusable non-path settings. Output-path settings are project-only. Do not put customization inside installed skill folders.

Resolution is **environment → per-skill project → shared project → per-skill user → default**, per key. Existing project overrides therefore take precedence over a new shared convention. See [the full configuration reference](docs/install.md#per-skill-runtime-configuration) for environment variables and root detection.

### 4. Verify

Open a fresh Claude Code or Codex session in the consuming project. Confirm the selected skills appear, then try `improve-prompt` on a short prompt. Claude plugin users invoke `/dev-skills:improve-prompt`; standalone Claude users invoke `/improve-prompt`; Codex users can explicitly request `$improve-prompt`. If you installed its subagent, explicitly ask the host to use `improve-prompt-agent` too.

Check the effective output path before invoking a skill that writes project artifacts:

```sh
python "/path/to/dev-skills/skills/update-todos/scripts/resolve_config.py" --project-root
python "/path/to/dev-skills/skills/update-todos/scripts/resolve_config.py" --all
```

A directory listing proves files were copied, not that the host loaded them. If discovery fails, check scope, restart the session, and confirm the paired skill is installed.

## Update an existing installation

Use the same installation route and scope as before. Preserve any local edits before replacing installed skill folders. Updating skill code, updating subagents, changing configuration, and moving existing project artifacts are separate operations.

### Skills copied from this checkout

From the checkout, fetch the desired upstream version, then reinstall the affected skills:

```sh
git pull --ff-only
npx skills add . -g -a claude-code -a codex --skill developer-diary update-todos --copy
```

Replace the names with your selection or `'*'`. For project scope, run `skills add` from the consuming project with the checkout's absolute path and no `-g`. A local-source update is an explicit reinstallation; pulling the checkout does not refresh installed copies.

### Skills installed directly from GitHub

If the original source was `martinatgit/dev-skills` through the skills CLI, use its updater:

```sh
npx skills update developer-diary update-todos -g
```

Use `-p` from the consuming project for project-scoped updates. Omit the names to update all skills in that scope, including skills from other repositories. See the [upstream CLI documentation](https://github.com/vercel-labs/skills) for the options supported by your installed CLI version.

### Claude plugin

For a local marketplace, update its checkout first. Then run in a terminal:

```sh
claude plugin marketplace update dev-skills
claude plugin update dev-skills@dev-skills
```

For a project-scoped plugin, add `--scope project` to the plugin update command from that project. Plugins update as a bundle. Start a fresh session after updating. Standalone copies are not updated by plugin commands.

### Separately installed subagents

From the updated checkout, preview and apply a managed update:

```sh
python scripts/install-agents.py -g -a claude-code -a codex --update --dry-run
python scripts/install-agents.py -g -a claude-code -a codex --update
```

Use `--agents <name> ...` to restrict the update. For project scope, keep the consuming project as cwd and omit `-g`.

The installer records hashes of files it installs. Unchanged files are skipped; `--update` replaces tracked files only when their installed contents have not been locally edited. Different untracked files and local modifications are conflicts. The entire planned batch is checked before copying. `--dry-run` creates no files.

For a conflict, inspect the file first. If replacement is intended, rerun the selected operation with `--force`: the previous bytes are backed up and the backup path is printed. See [agent update and recovery details](docs/install.md#agent-updates-and-recovery). Keep the installation manifest with the agents; without it the updater cannot distinguish older installed content from local customization.

### Upgrade from older names or configuration

Older releases used these skill names:

| Old skill | Current skill |
|---|---|
| `formal-methods-expert` | `formal-methods` |
| `debugger-expert` | `debugger` |
| `srs-expert` | `srs` |
| `type-theory-expert` | `type-theory` |

Install the new name, verify it, then remove only the confirmed old registration using the original installer or move the old manual copy outside the host's discovery directories. Check both user and project scopes, and legacy `~/.codex/skills` if you previously installed there. Copying new names does not remove old ones. [The migration reference](docs/install.md#legacy-names) also maps renamed subagents. The agent updater reports obsolete tracked files and never deletes them automatically.

For older `update-todos` configurations, `inbox_wip_limit` and `active_wip_limit` were replaced by `health_tier_guidance_max`. The configuration writer migrates old file keys; the runtime ignores deprecated keys and environment variables. Back up the config and choose the new threshold explicitly if the old limits differ:

```sh
cd "/path/to/your-project"
python "/path/to/dev-skills/skills/update-todos/scripts/configure.py" --scope project --repair --non-interactive --health-tier-guidance-max 60
```

Here `60` is an example, not a required value. Run separately with `--scope user` if that file also needs migration; update old environment variable names manually. A repair may materialize per-skill defaults that override shared settings, so inspect the resulting file and effective configuration. Migration from blocking WIP limits to advisory health thresholds changes behavior; it is not a one-to-one policy conversion.

Existing per-skill project configurations remain valid and override shared conventions. To consolidate them, remove only the redundant keys after comparing effective values. Changing `docs_root` does not move existing diary, TODO, glossary, or tutorial files: migrate those artifacts deliberately before changing their configured paths.

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
