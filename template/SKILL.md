---
name: your-skill-name
description: One sentence on what this skill does and specific contexts when the agent should trigger it. Be a little pushy — agents under-trigger. Example — "Generate release notes from a git range. Use whenever the user mentions changelogs, release notes, version bumps, or wants to summarize commits for a new tag."
---

# Your Skill Name

One-paragraph overview. What does this skill help the agent do? Keep it to 3-5 sentences.

## When to use

Concrete trigger phrases and contexts. Even though the frontmatter description carries the main triggering load, restating the shape here helps the agent during a session.

## When not to use

Adjacent tasks that superficially look similar but should be handled differently. This is often more useful than "when to use" — it prevents false triggers.

## Configuration

This skill reads user configuration from `~/.config/your-skill-name/config.yaml`.

**Resolution order** (first match wins):

1. Environment variables prefixed `YOUR_SKILL_NAME_*` (e.g. `YOUR_SKILL_NAME_API_ENDPOINT`).
2. `~/.config/your-skill-name/config.yaml`.
3. Project-local `./.your-skill-name/config.yaml` (only if the skill is project-scoped).
4. Interactive prompt on first use.

**Required keys:** (list them — e.g. `api_endpoint`, `project_id`). See `references/config-schema.md` for the full schema with examples.

**On first use, if the config file does not exist:**

1. Run the bundled helper: `bash scripts/configure.sh` — it will prompt for required values and write the file with correct permissions (0600).
2. If the user declines to configure interactively, fail fast with a clear message pointing them at `references/config-schema.md`.

Do not proceed with the task until configuration is resolved. Do not invent values. Do not write config anywhere other than the paths above.

## Inputs

What the agent needs from the user to do the task. Be specific about shape — file paths, URLs, date ranges, whatever.

## Workflow

1. Resolve configuration (see above).
2. [Step one of the actual task.]
3. [Step two.]
4. [Step three.]
5. Present the result to the user in the Output format below.

Use imperative verbs. Keep steps short. If a step is conditional, say so explicitly.

## Output format

Exact shape of what the skill returns. Markdown section? JSON block? A file written to disk? Be precise — ambiguity here is where skills drift.

## Examples

### Example 1 — <typical case>

**User:** "<representative prompt>"

**Skill output:** <what the agent produces>

### Example 2 — <edge case>

**User:** "<prompt that tests a boundary>"

**Skill output:** <expected handling>

## Troubleshooting

- **Config file exists but is missing a key.** Run `bash scripts/configure.sh --repair`.
- **Permission denied reading config.** Expected permissions are 0600; `chmod 600 ~/.config/your-skill-name/config.yaml`.
- **[Other common failure modes.]**

## References

- `references/config-schema.md` — configuration schema with example values.
- [Add other reference files as the skill grows. Keep SKILL.md lean; detail belongs in references/.]
