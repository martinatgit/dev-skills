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
| `health_tier_healthy_max` | int | user-default-able | `20` | Per-bucket count at or below = healthy tier (silent). |
| `health_tier_guidance_max` | int | user-default-able | `60` | Per-bucket count at or below (but above healthy) = guidance tier (advisory commentary). |
| `health_tier_strong_threshold` | int | user-default-able | `60` | Per-bucket count above = strong tier (loud commentary; still does not block capture). |
| `default_expiry_days` | int | user-default-able | `90` | Default expiry horizon for human-discovered TODOs. |
| `auto_maintenance_on_resolve` | bool | user-default-able | `false` | Run a Phase-1 drift scan on related TODOs at `resolve` time. Off by default; opt-in. |

Path values may use `~` and `$VAR`; the resolver expands both.

## Why `root_dir` is project-only

If a user installs `update-todos` in their home directory (e.g. `~/.claude/skills/update-todos/`) and invokes it across many repositories, the TODOs must still belong to the *current* project. Storing `root_dir` in user config would mix one project's TODOs into another. Storing it project-local-only ensures every project keeps its own TODO tree, even when the skill code is shared.

## Example file (project scope)

```yaml
# <project_root>/.update-todos/config.yaml
root_dir: doc/TODOs
health_tier_healthy_max: 20
health_tier_guidance_max: 60
health_tier_strong_threshold: 60
default_expiry_days: 90
auto_maintenance_on_resolve: false
```

## Example file (user scope)

```yaml
# ~/.config/update-todos/config.yaml
# root_dir is intentionally absent — it is project-bound.
health_tier_healthy_max: 20
health_tier_guidance_max: 60
health_tier_strong_threshold: 60
default_expiry_days: 60
auto_maintenance_on_resolve: false
```

## CLI

```sh
# First-time project setup (interactive)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --root-dir doc/TODOs --health-tier-guidance-max 50

# User-level defaults (non-path keys only)
python3 scripts/configure.py --scope user --health-tier-healthy-max 25

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
| `UPDATE_TODOS_HEALTH_TIER_HEALTHY_MAX` | Overrides `health_tier_healthy_max`. |
| `UPDATE_TODOS_HEALTH_TIER_GUIDANCE_MAX` | Overrides `health_tier_guidance_max`. |
| `UPDATE_TODOS_HEALTH_TIER_STRONG_THRESHOLD` | Overrides `health_tier_strong_threshold`. |
| `UPDATE_TODOS_DEFAULT_EXPIRY_DAYS` | Overrides `default_expiry_days`. |
| `UPDATE_TODOS_AUTO_MAINTENANCE_ON_RESOLVE` | Overrides `auto_maintenance_on_resolve`. |

These take precedence over both project and user config.

## Deprecated keys

The following keys are accepted for one release for backward compatibility.
`configure.py` migrates them to their successors and emits a warning. They
will be removed in the next major bump.

| Old key | Successor |
|---|---|
| `inbox_wip_limit` | `health_tier_guidance_max` |
| `active_wip_limit` | `health_tier_guidance_max` |
