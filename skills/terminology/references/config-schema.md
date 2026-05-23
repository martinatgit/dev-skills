# terminology configuration schema

The skill reads configuration from two scopes:

- **User scope** at `~/.config/terminology/config.yaml`
  (or `$XDG_CONFIG_HOME/terminology/config.yaml`).
- **Project scope** at `<project_root>/.terminology/config.yaml`,
  where `<project_root>` is detected by `scripts/find_project_root.py`.

Both files are mode `0600` on POSIX.

## Resolution order

First match wins:

1. Environment variable `TERMINOLOGY_<UPPERCASE_KEY>`.
2. Project-local config (`<project_root>/.terminology/config.yaml`).
3. User-level config (`~/.config/terminology/config.yaml`) — **non-path keys only**. Path-typed keys are project-bound by design and are never read from this layer.
4. Built-in default (for non-path keys only).

If a path-typed key cannot be resolved when a mode actually needs the file, the agent runs the first-use flow described in [`SKILL.md`](../SKILL.md#configuration): detect project root → suggest a default → ask the user → persist via `configure.py --scope project`.

## Keys

| Key | Type | Scope | Default | Purpose |
|---|---|---|---|---|
| `terminology_file` | path | **project-only** | `doc/terminology.md` (relative to project root) | Where the glossary lives. May be relative to project root or absolute. |
| `validation_timeout` | int (seconds) | user-default-able | `10` | Per-source fetch timeout used by `validate`. Set to `0` to disable network validation entirely. |

Path values may use `~` and `$VAR`; the resolver expands both.

## Why `terminology_file` is project-only

If the skill is installed user-scope (e.g. `~/.claude/skills/terminology/`) and invoked across multiple repositories, the glossary must still belong to the *current* project. Storing `terminology_file` in user config would mix one project's glossary into another. Project-local-only ensures every project keeps its own glossary, even when the skill code is shared.

## Example file (project scope)

```yaml
# <project_root>/.terminology/config.yaml
terminology_file: doc/terminology.md
validation_timeout: 10
```

## Environment-variable overrides

| Variable | Effect |
|---|---|
| `TERMINOLOGY_FILE` | Overrides `terminology_file` for this invocation. |
| `TERMINOLOGY_VALIDATION_TIMEOUT` | Overrides `validation_timeout`. |

These take precedence over both project and user config.

## CLI

```sh
# First-time project setup (interactive)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --terminology-file doc/terminology.md

# User-level defaults (non-path keys only)
python3 scripts/configure.py --scope user --validation-timeout 15

# Print resolved values
python3 scripts/configure.py --print

# Print the file path for the chosen scope
python3 scripts/configure.py --path
python3 scripts/configure.py --scope project --path

# Repair a partial config without overwriting good values
python3 scripts/configure.py --repair
```
