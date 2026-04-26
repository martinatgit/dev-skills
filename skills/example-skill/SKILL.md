---
name: example-skill
description: Starter skill demonstrating the repo's authoring conventions — spec-strict frontmatter, Pattern 2 lazy runtime configuration, and portable scripts. Use this as a reference when creating new skills in this repository. Do not use for real work; this is a template-in-use, not a production skill.
---

# Example Skill

A minimal reference skill that shows the shape every skill in this repository follows. It demonstrates how to declare configuration lazily, how to structure the workflow section, and where helper scripts and reference docs live. Copy `template/SKILL.md` (not this file) when you start a new skill.

## When to use

Never triggered for real work. This skill exists so contributors can read it side-by-side with `template/SKILL.md` to see a filled-in version.

## When not to use

Any real task. Use one of the other skills in this repo, or write a new one using `template/SKILL.md`.

## Configuration

This skill reads user configuration from `~/.config/example-skill/config.yaml`.

**Resolution order** (first match wins):

1. Environment variables prefixed `EXAMPLE_SKILL_*` (e.g. `EXAMPLE_SKILL_API_ENDPOINT`).
2. `~/.config/example-skill/config.yaml`.
3. Project-local `./.example-skill/config.yaml` (only if the skill is project-scoped).
4. Interactive prompt on first use.

**Required keys:** `api_endpoint`, `project_id`. See `references/config-schema.md` for the full schema with examples.

**On first use, if the config file does not exist:**

1. Run the bundled helper: `bash scripts/configure.sh` — it will prompt for required values and write the file with correct permissions (0600).
2. If the user declines to configure interactively, fail fast with a clear message pointing them at `references/config-schema.md`.

Do not proceed with the task until configuration is resolved. Do not invent values. Do not write config anywhere other than the paths above.

## Inputs

No inputs — this skill is a reference example and has no real task to perform.

## Workflow

1. Resolve configuration (see above).
2. Read the configured `api_endpoint` and `project_id`.
3. Print them back to the user as a sanity check that configuration resolution works.
4. Exit. Do not make any network calls.

## Output format

A single markdown block confirming which values were loaded and from which source (env var vs. config file vs. interactive prompt).

## Examples

### Example 1 — first run, no config

**User:** "Run the example skill."

**Skill output:** Detects no config, runs `bash scripts/configure.sh`, prompts the user for `api_endpoint` and `project_id`, writes `~/.config/example-skill/config.yaml` with permissions 0600, then echoes the resolved values.

### Example 2 — config already present

**User:** "Run the example skill."

**Skill output:** Loads `~/.config/example-skill/config.yaml`, echoes the resolved values, and notes the source path.

## Troubleshooting

- **Config file exists but is missing a key.** Run `bash scripts/configure.sh --repair`.
- **Permission denied reading config.** Expected permissions are 0600; `chmod 600 ~/.config/example-skill/config.yaml`.
- **Want to reset.** Delete `~/.config/example-skill/config.yaml` and rerun.

## References

- `references/config-schema.md` — configuration schema with example values.
