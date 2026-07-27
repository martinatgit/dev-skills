# developer-diary configuration schema

The skill reads configuration from two scopes:

- **User scope** at `~/.config/developer-diary/config.yaml`
  (or `$XDG_CONFIG_HOME/developer-diary/config.yaml`).
- **Project scope** at `<project_root>/.developer-diary/config.yaml`,
  where `<project_root>` is detected by `scripts/find_project_root.py`.

Both files are mode `0600` on POSIX.

## Resolution order

First match wins:

1. Environment variable `DEVELOPER_DIARY_<UPPERCASE_KEY>`.
2. Project-local config (`<project_root>/.developer-diary/config.yaml`).
3. User-level config (`~/.config/developer-diary/config.yaml`) — **non-path keys only**. Path-typed keys are project-bound by design and are never read from this layer.
4. Built-in default (for non-path keys only).

If a path-typed key cannot be resolved, the agent runs the first-use flow described in [`SKILL.md`](../SKILL.md#configuration): detect project root → suggest a default → ask the user → persist via `configure.py --scope project`.

## Keys

| Key | Type | Scope | Default | Purpose |
|---|---|---|---|---|
| `root_dir` | path | **project-only** | `doc/developer-diary` (relative to project root) | Where the diary tree lives. May be relative to project root or absolute. |
| `feature_routing_file` | path | **project-only** | `<root_dir>/feature-routing.md` | Routing index regenerated during `update`/`review`. |
| `node_token_limit` | int | user-default-able | `4000` | Soft node-size limit; trigger to split into children. Also used as the `maintain` action's Phase 7 split threshold. |
| `requirements_dir` | path | **project-only** | _(unset)_ | Optional. Used by `maintain` to verify internal requirement-ID references (regex `[A-Z]{3,}-\d{3,}`). When unset, requirement-ID drift checks are silently skipped. |
| `todos_inbox_dir` | path | **project-only** | _(unset)_ | Optional. Used by `maintain` to detect open-TODO references (regex `TODO-\d{8}-\d{4}`). When unset, TODO drift checks are silently skipped. Must be set together with `todos_archive_dir`. |
| `todos_archive_dir` | path | **project-only** | _(unset)_ | Optional. Companion to `todos_inbox_dir`; the `maintain` action classifies discharged TODOs by looking here. Must be set together with `todos_inbox_dir`. |

Path values may use `~` and `$VAR`; the resolver expands both.

## Why `root_dir` is project-only

If a user installs `developer-diary` in their home directory (e.g. `~/.claude/skills/developer-diary/`) and invokes it across many repositories, the diary must still belong to the *current* project. Storing `root_dir` in user config would mix one project's diary into another. Storing it project-local-only ensures every project keeps its own diary, even when the skill code is shared.

## Example file (project scope)

```yaml
# <project_root>/.developer-diary/config.yaml
root_dir: doc/developer-diary
feature_routing_file:                # blank -> <root_dir>/feature-routing.md
node_token_limit: 4000
requirements_dir: doc/requirements   # blank = skip requirement-ID drift checks
todos_inbox_dir: doc/TODOs/inbox     # blank = skip TODO-ID drift checks
todos_archive_dir: doc/TODOs/archive # required iff todos_inbox_dir is set
```

## CLI

```sh
# First-time project setup (interactive)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --root-dir doc/notes --node-token-limit 5000

# User-level defaults (non-path keys only)
python3 scripts/configure.py --scope user --node-token-limit 5000

# Print resolved values
python3 scripts/configure.py --print

# Print the file path for the chosen scope
python3 scripts/configure.py --path
python3 scripts/configure.py --scope project --path

# Repair a partial config without overwriting good values
python3 scripts/configure.py --repair

# Opt into requirement-ID drift checks
python3 scripts/configure.py --scope project --requirements-dir doc/requirements

# Opt into TODO-ID drift checks (both flags required together)
python3 scripts/configure.py --scope project \
    --todos-inbox-dir doc/TODOs/inbox --todos-archive-dir doc/TODOs/archive
```

## Environment-variable overrides

| Variable | Effect |
|---|---|
| `DEVELOPER_DIARY_ROOT_DIR` | Overrides `root_dir` for this invocation. |
| `DEVELOPER_DIARY_FEATURE_ROUTING_FILE` | Overrides `feature_routing_file`. |
| `DEVELOPER_DIARY_NODE_TOKEN_LIMIT` | Overrides `node_token_limit`. |
| `DEVELOPER_DIARY_REQUIREMENTS_DIR` | Overrides `requirements_dir` (opt-in). |
| `DEVELOPER_DIARY_TODOS_INBOX_DIR` | Overrides `todos_inbox_dir` (opt-in). |
| `DEVELOPER_DIARY_TODOS_ARCHIVE_DIR` | Overrides `todos_archive_dir` (opt-in). |

These take precedence over both project and user config.
