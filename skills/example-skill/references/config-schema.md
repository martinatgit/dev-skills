# Configuration schema

The skill reads configuration from two scopes:

- **User scope** at `~/.config/example-skill/config.yaml`
  (or `$XDG_CONFIG_HOME/example-skill/config.yaml`).
- **Project scope** at `<project_root>/.example-skill/config.yaml`,
  where `<project_root>` is detected by `scripts/find_project_root.py`.

Both files are mode `0600` on POSIX.

## Resolution order

First match wins:

1. Environment variable `EXAMPLE_SKILL_<UPPERCASE_KEY>`.
2. Project-local config (`<project_root>/.example-skill/config.yaml`).
3. User-level config (`~/.config/example-skill/config.yaml`) — **non-path keys only**. Path-typed keys are project-bound and never resolved from the user layer.
4. Built-in default.

## Required keys

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `api_endpoint` | `EXAMPLE_SKILL_API_ENDPOINT` | string (URL) | `https://api.example.com` | Base URL for the upstream API. |
| `project_id`   | `EXAMPLE_SKILL_PROJECT_ID`   | string        | `demo`                    | Project identifier. |

example-skill has no path-typed keys. Skills that write user files (e.g.
`developer-diary`, `update-todos`) include a project-only `root_dir` key.

## Example file

```yaml
# ~/.config/example-skill/config.yaml  (or <project_root>/.example-skill/config.yaml)
api_endpoint: https://api.example.com
project_id: proj_abc123
```

## CLI

```sh
# User-scope (defaults reused across projects)
python3 scripts/configure.py

# Project-scope (writes <project_root>/.example-skill/config.yaml)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --api-endpoint https://api.example.com --project-id demo

# Print resolved configuration (env + project + user + defaults merged)
python3 scripts/configure.py --print

# Print just the file path that will be written for the chosen scope
python3 scripts/configure.py --path
python3 scripts/configure.py --scope project --path
```
