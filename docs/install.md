# Install

This page covers every supported way to install skills from this repository, across every host agent that supports the [agentskills.io](https://agentskills.io/specification) open standard.

> Verified state: **April 2026**. Each agent's official docs are authoritative; cross-check those if a path looks off.

## Quick start — multi-agent install

The fastest way: the [`skills`](https://www.npmjs.com/package/skills) npm CLI auto-detects every installed agent and copies skills into the right place for each.

```sh
# All detected agents, current scope (project if cwd is a project root, else user)
npx skills add martinatgit/dev-skills

# Specific agents only
npx skills add martinatgit/dev-skills -a claude-code -a codex

# Specific skill only
npx skills add martinatgit/dev-skills --skill reason-through

# Force user scope ("global")
npx skills add martinatgit/dev-skills -g

# Non-interactive (CI)
npx skills add martinatgit/dev-skills -y
```

`npx skills` walks upward from your cwd looking for project markers (`.git`, `package.json`, etc.) to decide between project and user scope. Pass `-g` to force user scope.

Source: [npm — `skills` package](https://www.npmjs.com/package/skills) and the [vercel-labs/skills](https://github.com/vercel-labs/skills) repo.

## Install matrix (per agent × per scope)

| Agent | User scope | Project scope | Notes |
|---|---|---|---|
| **Claude Code** | `~/.claude/skills/<name>/` | `<repo>/.claude/skills/<name>/` | Also supports plugin marketplaces (`/plugin marketplace add`, `/plugin install`). Live change detection; nested `.claude/skills/` in subdirectories auto-discovered. |
| **Codex CLI** | `~/.agents/skills/<name>/` | `<repo>/.agents/skills/<name>/` | Walks parent directories to project root. Skills support shipped December 2025. |
| **Cursor** | `~/.agents/skills/<name>/` or `~/.cursor/skills/<name>/` | `<repo>/.agents/skills/<name>/` or `<repo>/.cursor/skills/<name>/` | Reads both the cross-vendor `.agents/` convention and Cursor-specific `.cursor/`. Falls back to Claude / Codex skills directories for compatibility. |
| **Windsurf** | `~/.codeium/windsurf/skills/<name>/` | `<repo>/.windsurf/skills/<name>/` | Ships as "Cascade Skills". |
| **Goose** | `~/.config/agents/skills/<name>/` | `<repo>/.agents/skills/<name>/` | Desktop app + CLI; managed as a dedicated platform extension. |

**`.agents/skills/`** is the emerging cross-vendor convention used by Codex, Cursor (alternative path), and Goose. Claude Code and Windsurf still use vendor-specific paths but are converging.

## Manual install (any agent)

```sh
# Clone the repo
git clone https://github.com/martinatgit/dev-skills.git

# Copy a single skill into the agent of your choice
cp -r dev-skills/skills/reason-through ~/.claude/skills/        # Claude Code, user scope
cp -r dev-skills/skills/reason-through ~/.agents/skills/        # Codex CLI / Cursor / Goose, user scope
cp -r dev-skills/skills/reason-through .claude/skills/          # Claude Code, project scope
cp -r dev-skills/skills/reason-through .agents/skills/          # Codex CLI / Cursor / Goose, project scope

# Or copy all skills at once
cp -r dev-skills/skills/* ~/.claude/skills/
```

Manual install is the right fallback when `npx skills` is unavailable or you want full control over which skills land where.

## Claude Code plugin install

```
/plugin marketplace add martinatgit/dev-skills
/plugin install dev-skills@martinatgit
```

The marketplace manifest is at [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) and lists every shipped skill.

## Verifying the install

```sh
# Claude Code (user scope)
ls ~/.claude/skills/

# Codex CLI / Cursor / Goose (user scope)
ls ~/.agents/skills/

# Project scope (run from inside the project)
ls .claude/skills/   .agents/skills/
```

Each of these should show a directory per skill with a `SKILL.md` inside.

## Per-skill runtime configuration

Skills in this repo follow a uniform configuration pattern:

- Configuration files live at `~/.config/<skill-name>/config.yaml` (user scope) and/or `<project_root>/.<skill-name>/config.yaml` (project scope).
- Path-typed keys (`root_dir` and similar) are **project-only**. A user-installed skill never bleeds one project's writes into another.
- Resolution order: env var → project-local → user-level (non-path keys only) → built-in default.
- All helpers are Python 3 stdlib, identical on Windows / macOS / Linux.

### Configure a skill

```sh
# Inside a skill folder (or use absolute paths)
cd ~/.claude/skills/update-todos      # or wherever the skill is installed

# Project scope (where path-typed keys belong)
python3 scripts/configure.py --scope project

# User scope (defaults reused across projects)
python3 scripts/configure.py --scope user

# Non-interactive
python3 scripts/configure.py --scope project --root-dir doc/TODOs

# Inspect resolution
python3 scripts/configure.py --print
```

### Per-skill env-var overrides

| Skill | Variable | Purpose |
|---|---|---|
| `developer-diary` | `DEVELOPER_DIARY_ROOT_DIR` | Override where the diary tree is read/written. |
| `developer-diary` | `DEVELOPER_DIARY_FEATURE_ROUTING_FILE` | Override the routing-index file path. |
| `developer-diary` | `DEVELOPER_DIARY_NODE_TOKEN_LIMIT` | Override the soft node-size limit. |
| `update-todos` | `UPDATE_TODOS_ROOT_DIR` | Override where the TODO tree is read/written. |
| `update-todos` | `UPDATE_TODOS_INBOX_WIP_LIMIT` | Override the inbox WIP limit. |
| `update-todos` | `UPDATE_TODOS_ACTIVE_WIP_LIMIT` | Override the active WIP limit. |
| `update-todos` | `UPDATE_TODOS_DEFAULT_EXPIRY_DAYS` | Override the default expiry horizon. |
| `reason-through` | `REASON_THROUGH_CACHE_DIR` | Override the cache directory. |
| `reason-through` | `REASON_THROUGH_LOG_DIR` | Override the log directory. |
| `reason-through` | `REASON_THROUGH_CACHE_TTL_SECONDS` | Override the cache TTL. |
| `reason-through` | `REASON_THROUGH_MAX_REFINEMENT_PASSES` | Override the refinement-pass ceiling. |
| `reason-through` | `REASON_THROUGH_SPECIALIST_MODEL_TIER` | Override the specialist-model tier hint. |
| `reason-through` | `REASON_THROUGH_ORCHESTRATOR_MODEL_TIER` | Override the orchestrator-model tier hint. |
| `example-skill` | `EXAMPLE_SKILL_API_ENDPOINT` | (Reference only.) |
| `example-skill` | `EXAMPLE_SKILL_PROJECT_ID` | (Reference only.) |

### Project root detection

Skills detect a project root by walking up from the current directory looking for any of:

- VCS markers: `.git`, `.hg`, `.svn`
- Language manifests: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `deno.json`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `Gemfile`, `mix.exs`
- Agent config dirs: `.agents`, `.claude`, `.codex`, `.cursor`, `.windsurf`
- Agent manifests: `AGENTS.md`, `CLAUDE.md`, `CODEX.md`

The walk stops at the filesystem root or the user's home directory, whichever first. To debug:

```sh
python3 scripts/find_project_root.py
python3 scripts/find_project_root.py --from /some/path
python3 scripts/find_project_root.py --mark .my-marker  # custom marker
```

## Sources

- [Claude Code Skills documentation](https://code.claude.com/docs/en/skills)
- [agentskills.io](https://agentskills.io/home)
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills/)
- [Cursor Skills documentation](https://cursor.com/docs/skills)
- [Windsurf Cascade Skills](https://docs.windsurf.com/windsurf/cascade/skills)
- [Goose Skills extension](https://block.github.io/goose/docs/mcp/skills-mcp/)
- [`skills` npm package](https://www.npmjs.com/package/skills) ([vercel-labs/skills](https://github.com/vercel-labs/skills))
