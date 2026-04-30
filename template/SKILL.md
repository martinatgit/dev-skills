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

This skill reads configuration from two scopes:

- **User scope** at `~/.config/your-skill-name/config.yaml`.
- **Project scope** at `<project_root>/.your-skill-name/config.yaml`.

**Resolution order** (first match wins):

1. Environment variables prefixed `YOUR_SKILL_NAME_*` (e.g. `YOUR_SKILL_NAME_API_ENDPOINT`).
2. Project-local config (`<project_root>/.your-skill-name/config.yaml`).
3. User-level config (`~/.config/your-skill-name/config.yaml`) — non-path keys only. Path-typed keys are project-bound by design and are never read from this layer.
4. Built-in default.

**Required keys:** (list them — e.g. `api_endpoint`, `project_id`). See `references/config-schema.md` for the full schema with examples.

**Configure**

```sh
# Project scope (where path-typed keys belong)
python3 scripts/configure.py --scope project

# User scope (defaults for non-path keys reused across projects)
python3 scripts/configure.py --scope user

# Non-interactive
python3 scripts/configure.py --scope project --your-key value

# Inspect resolution
python3 scripts/configure.py --print
```

**First-use flow.** If a required path-typed key cannot be resolved, the agent must:

1. Detect the project root via `python3 scripts/find_project_root.py`.
2. Suggest a default and ask the user.
3. Persist via `python3 scripts/configure.py --scope project --<key> <answer>`.
4. Re-resolve and proceed.

If no project root is detected, refuse with the exact configure command. Never fall back to a user-home location for path-typed keys.

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

- **Config file exists but is missing a key.** Run `python3 scripts/configure.py --repair`.
- **Permission denied reading config.** Expected permissions are 0600; `chmod 600 ~/.config/your-skill-name/config.yaml`.
- **[Other common failure modes.]**

## References

- `references/config-schema.md` — configuration schema with example values.
- [Add other reference files as the skill grows. Keep SKILL.md lean; detail belongs in references/.]
