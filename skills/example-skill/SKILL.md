---
name: example-skill
description: Starter skill demonstrating the repo's authoring conventions — spec-strict frontmatter, Pattern 2 lazy runtime configuration, project-local-first writes, and portable Python scripts. Use this as a reference when creating new skills in this repository. Do not use for real work; this is a template-in-use, not a production skill.
---

# Example Skill

A minimal reference skill that shows the shape every skill in this repository follows. It demonstrates how to declare configuration lazily, how to layer user vs project scope, and where helper scripts and reference docs live. Copy `template/SKILL.md` (not this file) when you start a new skill.

## When to use

Never triggered for real work. This skill exists so contributors can read it side-by-side with `template/SKILL.md` to see a filled-in version.

## When not to use

Any real task. Use one of the other skills in this repo, or write a new one using `template/SKILL.md`.

## Configuration

Resolution order (first match wins):

1. Environment variable `EXAMPLE_SKILL_<UPPERCASE_KEY>` (e.g. `EXAMPLE_SKILL_API_ENDPOINT`).
2. **Project-local** config at `<project_root>/.example-skill/config.yaml`.
3. **User-level** config at `~/.config/example-skill/config.yaml` (or `$XDG_CONFIG_HOME/example-skill/config.yaml`). User-level config holds defaults for non-path keys only — path-typed keys are project-bound by definition and never read from this layer.
4. Built-in default.

The skill detects a project root by walking up from the current directory looking for `.git`, `package.json`, `.claude`, `AGENTS.md`, etc. (full marker list in `scripts/find_project_root.py`).

**Configure**

```sh
# User-scope config (defaults for tunables you reuse across projects)
python3 scripts/configure.py

# Project-scope config (writes <project_root>/.example-skill/config.yaml)
python3 scripts/configure.py --scope project

# Non-interactive (CI / scripted setup)
python3 scripts/configure.py --scope project --api-endpoint https://api.example.com --project-id demo

# Inspect resolution
python3 scripts/configure.py --print
python3 scripts/configure.py --path
```

**Required keys:** `api_endpoint`, `project_id`. See [`references/config-schema.md`](references/config-schema.md) for the full schema with examples.

The skill never writes outside `<project_root>/.example-skill/` (project scope) or `~/.config/example-skill/` (user scope).

## Inputs

No inputs — this skill is a reference example and has no real task to perform.

## Workflow

1. **Step 0 — Resolve configuration.** Run `python3 scripts/resolve_config.py --all` and parse the `key=value` lines.
2. Read the resolved `api_endpoint` and `project_id`.
3. Print them back to the user as a sanity check that configuration resolution works, naming the source layer.
4. Exit. Do not make any network calls.

## Output format

A single markdown block confirming which values were loaded and from which source (env var vs. project config vs. user config vs. default).

## Examples

### Example 1 — first run, no config

**User:** "Run the example skill."

**Skill output:** Detects no project-local config, no user config, no env var. Echoes the resolved values from built-in defaults and prints a one-liner suggesting `python3 scripts/configure.py --scope project` to persist a project-specific override.

### Example 2 — project-scoped config present

**User:** "Run the example skill."

**Skill output:** Loads `<project_root>/.example-skill/config.yaml`, echoes the resolved values, and notes the source path. The same skill in a different project sees a different (or no) project config.

## Troubleshooting

- **No project root found.** The skill is being run outside any project. Either `cd` into a project directory, or invoke `python3 scripts/configure.py --scope user` to fall back to a user-level default.
- **Config file exists but is missing a key.** Run `python3 scripts/configure.py --repair`.
- **Permission denied reading config.** Expected permissions are 0600; `chmod 600 ~/.config/example-skill/config.yaml`.
- **Want to reset.** Delete the relevant config file (project-local or user-level) and rerun.

## References

- [`references/config-schema.md`](references/config-schema.md) — configuration schema with example values.
