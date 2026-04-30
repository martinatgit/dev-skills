# update-todos configuration schema

The skill reads configuration from two scopes:

- **User scope** at `~/.config/update-todos/config.yaml`
  (or `$XDG_CONFIG_HOME/update-todos/config.yaml`).
- **Project scope** at `<project_root>/.update-todos/config.yaml`,
  where `<project_root>` is detected by `scripts/find_project_root.py`.

Both files are mode `0600` on POSIX.

## Resolution order

First match wins:

1. Environment variable `UPDATE_TODOS_<UPPERCASE_KEY>`.
2. Project-local config (`<project_root>/.update-todos/config.yaml`).
3. User-level config (`~/.config/update-todos/config.yaml`) — **non-path keys only**. The `root_dir` is project-bound by design and is never read from this layer.
4. Built-in default (for non-path keys only).

If `root_dir` cannot be resolved, the agent runs the first-use flow described in [`SKILL.md`](../SKILL.md#configuration): detect project root → suggest `<project_root>/doc/TODOs` → ask the user → persist via `configure.py --scope project`.

## Keys

| Key | Type | Scope | Default | Purpose |
|---|---|---|---|---|
| `root_dir` | path | **project-only** | `doc/TODOs` (relative to project root) | Where the TODO tree lives. May be relative or absolute. |
| `inbox_wip_limit` | int | user-default-able | `20` | Refuse to capture if `inbox/` exceeds this count. |
| `active_wip_limit` | int | user-default-able | `15` | Refuse to capture if `active/` exceeds this count. |
| `default_expiry_days` | int | user-default-able | `90` | Default expiry horizon for human-discovered TODOs. |

Path values may use `~` and `$VAR`; the resolver expands both.

## Why `root_dir` is project-only

If a user installs `update-todos` in their home directory (e.g. `~/.claude/skills/update-todos/`) and invokes it across many repositories, the TODOs must still belong to the *current* project. Storing `root_dir` in user config would mix one project's TODOs into another. Storing it project-local-only ensures every project keeps its own TODO tree, even when the skill code is shared.

## Example file (project scope)

```yaml
# <project_root>/.update-todos/config.yaml
root_dir: doc/TODOs
inbox_wip_limit: 20
active_wip_limit: 15
default_expiry_days: 90
```

## Example file (user scope)

```yaml
# ~/.config/update-todos/config.yaml
# root_dir is intentionally absent — it is project-bound.
inbox_wip_limit: 25
active_wip_limit: 20
default_expiry_days: 60
```

## CLI

```sh
# First-time project setup (interactive)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --root-dir doc/TODOs --inbox-wip-limit 25

# User-level defaults (non-path keys only)
python3 scripts/configure.py --scope user --inbox-wip-limit 25

# Print resolved values
python3 scripts/configure.py --print

# Print the config-file path for the chosen scope
python3 scripts/configure.py --path
python3 scripts/configure.py --scope project --path

# Repair a partial config without overwriting good values
python3 scripts/configure.py --repair
```

## Environment-variable overrides

| Variable | Effect |
|---|---|
| `UPDATE_TODOS_ROOT_DIR` | Overrides `root_dir`. |
| `UPDATE_TODOS_INBOX_WIP_LIMIT` | Overrides `inbox_wip_limit`. |
| `UPDATE_TODOS_ACTIVE_WIP_LIMIT` | Overrides `active_wip_limit`. |
| `UPDATE_TODOS_DEFAULT_EXPIRY_DAYS` | Overrides `default_expiry_days`. |

These take precedence over both project and user config.
