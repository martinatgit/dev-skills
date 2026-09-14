# Install

Start with the [README installation and update walkthrough](../README.md#install). It covers a local checkout, both hosts, personal/project scope, optional subagents, configuration, and upgrades. This page is the detailed reference.

Claude Code and Codex references were checked on 2026-09-13. Other hosts below retain the previously documented paths; consult their official documentation for current support. Python helpers use the standard library and run with Python 3.10+; tests require 3.11+.

## Quick start — multi-agent install

From the dev-skills checkout, install selected personal skills into both hosts:

```sh
npx skills add . -g -a claude-code -a codex --skill developer-diary update-todos --copy
```

Use `--skill '*'` for all skills, or `--list` to browse without installing. For project scope, run from the consuming project, pass the checkout's absolute path, and omit `-g`. The external skills CLI defaults to project scope; do not rely on this repository's project-root algorithm to determine its destination.

For remote-source installation, replace `.` with `martinatgit/dev-skills`. Keep track of the original source and scope for [updates](../README.md#update-an-existing-installation).

## Install matrix (per agent × per scope)

| Agent | User scope | Project scope |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | `<project>/.claude/skills/<name>/` |
| Codex | `~/.agents/skills/<name>/` | `<project>/.agents/skills/<name>/` |
| Cursor | `~/.agents/skills/<name>/` or `~/.cursor/skills/<name>/` | `<project>/.agents/skills/<name>/` or `<project>/.cursor/skills/<name>/` |
| Windsurf | `~/.codeium/windsurf/skills/<name>/` | `<project>/.windsurf/skills/<name>/` |
| Goose | `~/.config/agents/skills/<name>/` | `<project>/.agents/skills/<name>/` |

## Manual install (any agent)

Create the appropriate destination from the matrix and copy the complete `skills/<name>` directory into it, including scripts and references. For example, from the checkout in a POSIX shell:

```sh
mkdir -p "$HOME/.claude/skills"
cp -R skills/improve-prompt "$HOME/.claude/skills/"
```

In PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE/.claude/skills"
Copy-Item -Recurse -LiteralPath "skills/improve-prompt" -Destination "$env:USERPROFILE/.claude/skills/"
```

These examples are for a **first install**. For a manual update, back up the old skill folder outside every host discovery directory, then replace the folder as a whole. Overlaying files can leave files deleted upstream behind. Never remove unrelated skills. Configuration belongs outside the installed skill, so replacing its code need not overwrite project preferences.

## Claude Code plugin install

In Claude Code running in the checkout:

```text
/plugin marketplace add .
/plugin install dev-skills@dev-skills
```

Alternatively add `martinatgit/dev-skills` for a GitHub-backed marketplace. The plugin includes skills and Claude agents. The default scope is user; select project/local scope through `/plugin`. Skills use the plugin namespace, for example `/dev-skills:improve-prompt`.

The manifest is [marketplace.json](../.claude-plugin/marketplace.json). `dev-skills` is both the plugin name and marketplace name; `martinatgit` is its owner. Avoid installing the same Claude skills both standalone and through the plugin.

For updates, refresh the marketplace then run `claude plugin update dev-skills@dev-skills`; add `--scope project` for a project installation. Update a local marketplace's checkout first. Refreshing a marketplace listing alone is not a substitute for updating the installed plugin.

## Installing agents

The installer handles Claude Markdown and Codex TOML files; it does not install their paired skills. From the checkout:

```sh
python scripts/install-agents.py -g -a claude-code -a codex --dry-run
python scripts/install-agents.py -g -a claude-code -a codex
```

Choose one host if needed. Explicit hosts do not require pre-existing destination directories. Without `-a`, detection considers host config roots in the consuming project and user home. Personal scope is `-g`; otherwise cwd determines the consuming project root. Invoke by absolute path from another project:

```sh
cd "/path/to/your-project"
python "/path/to/dev-skills/scripts/install-agents.py" -a codex --agents improve-prompt-agent
```

Destinations: Claude `<scope>/.claude/agents/<name>.md`; Codex `<scope>/.codex/agents/<name>.toml`. Unknown hosts/names fail before copying. This repository supplies subagent formats only for these two hosts.

Codex agents inherit parent skill discovery and ask to load their paired skill in their instructions. They do not encode Claude's preload list as Codex configuration. Install paired skills at a scope visible to the consuming session. See the [agents guide](agents-guide.md#codex-cli-generated).

## Agent updates and recovery

Use the same host/scope and optionally the same `--agents` selection:

```sh
python scripts/install-agents.py -g -a codex --update --dry-run
python scripts/install-agents.py -g -a codex --update
```

- First installs create missing destinations.
- Identical files are skipped and can be adopted into installer tracking.
- `--update` replaces an older tracked file only when it still matches its recorded installed hash.
- Different untracked files and locally edited tracked files are conflicts; inspect before opting into `--force`.
- `--force` backs up changed existing files before replacing them and prints the backup paths.
- All destinations are checked before planned copies begin. Filesystem errors can still interrupt a batch; this is not a multi-file transaction.
- Dry runs write neither agents, backups, nor tracking data.
- Obsolete tracked names are reported, not deleted. Untracked legacy names require the inventory below.
- `-y/--yes` is retained for command compatibility; the installer has no interactive prompts and it never implies `--force`.

The installer keeps `.dev-skills-install.json` alongside installed agents. Preserve it to retain source/hash tracking. Backups live outside normal agent file names; use the exact path printed by the installer. To restore, preserve the new version if needed and copy the saved bytes back to the original agent file. A restored older version may differ from the manifest and will correctly be treated as a conflict on the next update.

For installations made before tracking existed, identical files are adopted on reinstallation. Different existing files require reviewed `--force` replacement and are backed up. Never overwrite a plugin cache with this installer; update that plugin through its host.

### Legacy names

| Old skill folder | Current skill folder |
|---|---|
| formal-methods-expert | formal-methods |
| debugger-expert | debugger |
| srs-expert | srs |
| type-theory-expert | type-theory |

| Old agent stem | Current agent stem |
|---|---|
| prompt-engineer | improve-prompt-agent |
| formal-methods-expert | formal-methods-agent |
| petri-net-expert | petri-net-theory-agent |
| srs-expert | srs-agent |
| type-theory-expert | type-theory-agent |
| debugger-expert | debugger-agent |

Inspect personal and project skill/agent directories, including `~/.codex/skills` if an earlier manual setup used it. Install and verify the replacement, then unregister the old skill through its original installer, or move a manual copy outside host discovery. Back up local modifications first. The repository does not automatically rename project references or delete old registrations.

## Verifying the install

Start a fresh host session in the consuming project, check skill discovery, and invoke a selected skill. For a plugin installation also check its enabled scope through `/plugin`. If subagents were selected, explicitly dispatch one. Merely seeing a file on disk does not validate host loading.

Inspect configuration from that same project:

```sh
python "/path/to/dev-skills/skills/update-todos/scripts/configure.py" --print
python "/path/to/dev-skills/skills/update-todos/scripts/resolve_config.py" --project-root
```

## Shared conventions

A project-scope `<project>/.agents/dev-skills.yaml` supplies output conventions for developer-diary, update-todos, terminology, and create-tutorial:

```yaml
schema: dev-skills/v1
docs_root: agent-docs
skills:
  terminology:
    filename: terms.md
```

From the consuming project:

```sh
python "/path/to/dev-skills/scripts/setup-conventions.py" --non-interactive --docs-root agent-docs --terminology-filename terms.md
python "/path/to/dev-skills/scripts/setup-conventions.py" --print
```

Omit `--non-interactive` for interactive setup. Reruns preserve existing parsed `docs_root` and per-skill blocks; only supplied settings change. Omitted `docs_root` defaults to `doc` on first use only. The writer normalizes formatting and comments; unsupported top-level keys are outside the schema. Edit the file to remove an override intentionally.

A missing/wrong schema or malformed file is ignored by runtime with a diagnostic, while the setup writer refuses to overwrite it. `DEV_SKILLS_CONFIG_FILE` can point to an alternate shared file. Shared conventions are intended to be committed with the project.

## Per-skill runtime configuration

Per-key precedence:

1. Per-key environment variable.
2. `<project>/.<skill-name>/config.yaml`.
3. Shared conventions.
4. User config at `~/.config/<skill-name>/config.yaml` (or `XDG_CONFIG_HOME`), non-path keys only.
5. Built-in default.

Skills without shared output conventions, such as reason-through and example-skill, skip layer 3. Unresolved output paths trigger the skill's first-use configuration flow. Keep cwd in the consuming project; an installed skill folder is not the consuming project.

```sh
python "/path/to/dev-skills/skills/update-todos/scripts/configure.py" --scope project --non-interactive --root-dir doc/TODOs
python "/path/to/dev-skills/skills/update-todos/scripts/configure.py" --scope user --non-interactive --default-expiry-days 60
python "/path/to/dev-skills/skills/update-todos/scripts/configure.py" --print
```

For all four shared-config skills, `configure.py --print` delegates to the runtime resolver and prints effective values. It does not write files. `--scope` selects the file to write, not a filter on runtime precedence. Each skill's `references/config-schema.md` describes its private settings.

Existing project config overrides a new shared convention. Neither setting `docs_root` nor repairing config moves existing project artifacts. The [README migration instructions](../README.md#upgrade-from-older-names-or-configuration) explain deprecated update-todos keys, explicit repair, and legacy-name cleanup.

### Per-skill env-var overrides

| Skill | Variable | Purpose |
|---|---|---|
| `developer-diary` | `DEVELOPER_DIARY_ROOT_DIR` | Override where the diary tree is read/written. |
| `developer-diary` | `DEVELOPER_DIARY_FEATURE_ROUTING_FILE` | Override the routing-index file path. |
| `developer-diary` | `DEVELOPER_DIARY_NODE_TOKEN_LIMIT` | Override the soft node-size limit. |
| `update-todos` | `UPDATE_TODOS_ROOT_DIR` | Override where the TODO tree is read/written. |
| `update-todos` | `UPDATE_TODOS_HEALTH_TIER_HEALTHY_MAX` | Upper count for the healthy tier. |
| `update-todos` | `UPDATE_TODOS_HEALTH_TIER_GUIDANCE_MAX` | Upper count for advisory guidance. |
| `update-todos` | `UPDATE_TODOS_HEALTH_TIER_STRONG_THRESHOLD` | Count above which guidance is strong (not blocking). |
| `update-todos` | `UPDATE_TODOS_AUTO_MAINTENANCE_ON_RESOLVE` | Enable maintenance on resolve. |
| `update-todos` | `UPDATE_TODOS_DEFAULT_EXPIRY_DAYS` | Override the default expiry horizon. |
| `reason-through` | `REASON_THROUGH_CACHE_DIR` | Override the cache directory. |
| `reason-through` | `REASON_THROUGH_LOG_DIR` | Override the log directory. |
| `reason-through` | `REASON_THROUGH_CACHE_TTL_SECONDS` | Override the cache TTL. |
| `reason-through` | `REASON_THROUGH_MAX_REFINEMENT_PASSES` | Override the refinement-pass ceiling. |
| `reason-through` | `REASON_THROUGH_SPECIALIST_MODEL_TIER` | Override the specialist-model tier hint. |
| `reason-through` | `REASON_THROUGH_ORCHESTRATOR_MODEL_TIER` | Override the orchestrator-model tier hint. |
| `example-skill` | `EXAMPLE_SKILL_API_ENDPOINT` | (Reference only.) |
| `example-skill` | `EXAMPLE_SKILL_PROJECT_ID` | (Reference only.) |
| (shared) | `DEV_SKILLS_CONFIG_FILE` | Path to the shared conventions file (default `<proj>/.agents/dev-skills.yaml`). |
| `create-tutorial` | `CREATE_TUTORIAL_TUTORIALS_DIR` | Override where generated tutorials are written. |

### Project root detection

Skills detect a project root by walking up from the current directory looking for any of:

- VCS markers: `.git`, `.hg`, `.svn`
- Language manifests: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `deno.json`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `Gemfile`, `mix.exs`
- Agent config dirs: `.agents`, `.claude`, `.codex`, `.cursor`, `.windsurf`
- Agent manifests: `AGENTS.md`, `CLAUDE.md`, `CODEX.md`

The walk stops at the filesystem root or the user's home directory, whichever first. To debug:

```sh
python "/path/to/dev-skills/template/scripts/find_project_root.py"
python "/path/to/dev-skills/template/scripts/find_project_root.py" --from /some/path
python "/path/to/dev-skills/template/scripts/find_project_root.py" --mark .my-marker  # custom marker
```

## Sources

- [Claude Code Skills documentation](https://code.claude.com/docs/en/skills)
- [agentskills.io](https://agentskills.io/home)
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills/)
- [Cursor Skills documentation](https://cursor.com/docs/skills)
- [Windsurf Cascade Skills](https://docs.windsurf.com/windsurf/cascade/skills)
- [Goose Skills extension](https://block.github.io/goose/docs/mcp/skills-mcp/)
- [`skills` npm package](https://www.npmjs.com/package/skills) ([vercel-labs/skills](https://github.com/vercel-labs/skills))
