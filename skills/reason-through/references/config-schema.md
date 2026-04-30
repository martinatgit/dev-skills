# reason-through configuration schema

The skill reads its configuration from two scopes:

- **User scope** at `~/.config/reason-through/config.yaml`
  (or `$XDG_CONFIG_HOME/reason-through/config.yaml`).
- **Project scope** at `<project_root>/.reason-through/config.yaml`,
  where `<project_root>` is detected by `scripts/find_project_root.py`.

Both files are mode `0600` on POSIX.

## Resolution order

First match wins:

1. Environment variable `REASON_THROUGH_<UPPERCASE_KEY>`.
2. Project-local config (`<project_root>/.reason-through/config.yaml`).
3. User-level config (`~/.config/reason-through/config.yaml`) — applies to all keys here, since `reason-through` has no path-typed project-bound keys (caches and logs are inherently user-scoped).
4. Built-in default.

## Keys

| Key | Type | Default | Purpose |
|---|---|---|---|
| `cache_dir` | path | `~/.cache/reason-through` | Where the orchestrator writes per-task cache files (`{sha256}.json`). |
| `log_dir` | path | `~/.local/state/reason-through` | Where `cost-log.jsonl` is appended. |
| `cache_ttl_seconds` | int | `86400` | Cache entries older than this are treated as a miss. |
| `max_refinement_passes` | int (1–3) | `3` | Hard ceiling on refinement loops. |
| `specialist_model_tier` | enum | `fast` | Tier hint for specialist agents. One of `fast`, `default`, `strong`. The host translates this to its own model names. |
| `orchestrator_model_tier` | enum | `strong` | Tier hint for the orchestrator. |

Path values may use `~` and `$VAR`; the resolver expands both.

## Example file

```yaml
# Configuration for the reason-through skill.
# Override any value with env var REASON_THROUGH_<UPPERCASE_KEY>.

cache_dir: ~/.cache/reason-through
log_dir: ~/.local/state/reason-through
cache_ttl_seconds: 86400
max_refinement_passes: 3
specialist_model_tier: fast
orchestrator_model_tier: strong
```

## How the skill uses it

At runtime the orchestrator runs `python3 scripts/resolve_config.py --all` to
get every key as `key=value` lines, then uses the resolved `cache_dir` and
`log_dir` for all reads/writes. The skill never writes outside those two
directories or its own `~/.config/reason-through/` config directory.

Model-tier values are advisory hints. Hosts that don't expose tiers ignore them.

## Manage the file

```sh
# First-time setup (interactive prompts, accepts Enter for defaults)
python3 scripts/configure.py

# Fill missing keys without overwriting existing ones
python3 scripts/configure.py --repair

# Print resolved values (env + file + defaults merged)
python3 scripts/configure.py --print

# Print just the file path the skill will read
python3 scripts/configure.py --path

# Write defaults non-interactively (CI / first run)
python3 scripts/configure.py --non-interactive
```
