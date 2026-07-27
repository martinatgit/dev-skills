# create-tutorial configuration schema

The skill reads configuration from two scopes:

- **User scope** at `~/.config/create-tutorial/config.yaml`.
- **Project scope** at `<project_root>/.create-tutorial/config.yaml`.

Both files are mode `0600` on POSIX.

## Resolution order

First match wins:

1. Environment variable `CREATE_TUTORIAL_<UPPERCASE_KEY>`.
2. Project-local config (`<project_root>/.create-tutorial/config.yaml`).
3. Shared conventions file (`<project_root>/.agents/dev-skills.yaml`).
4. User-level config -- **non-path keys only**.
5. Built-in default.

## Keys

| Key | Type | Scope | Default | Purpose |
|---|---|---|---|---|
| `tutorials_dir` | path | **project-only** | `doc/tutorials` | Directory where generated tutorials are written. |

## Environment-variable overrides

| Variable | Effect |
|---|---|
| `CREATE_TUTORIAL_TUTORIALS_DIR` | Overrides `tutorials_dir`. |
| `DEV_SKILLS_CONFIG_FILE` | Overrides the path to `.agents/dev-skills.yaml`. |

## CLI

```sh
# First-time project setup
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --tutorials-dir doc/tutorials

# Print resolved values
python3 scripts/configure.py --print
```
