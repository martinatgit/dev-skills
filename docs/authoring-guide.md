# Authoring guide

These rules are the reason this library stays universal. Break them in a fork, not in this repo.

## The single job rule

One skill, one job. If your skill has two natural ways it could trigger or two distinct workflows inside it, split it into two skills. Large, general-purpose skills trigger less reliably than focused ones.

## Frontmatter discipline

SKILL.md frontmatter contains exactly two fields:

```yaml
---
name: kebab-case-name
description: What the skill does, and specific contexts for when to trigger it.
---
```

Do not add `version`, `owner`, `tags`, `allowed-tools`, `metadata`, or any other field. The open standard's `metadata` namespace is experimental and support varies across agents. Things you add here silently get ignored on half the platforms.

If a platform-specific field genuinely matters (Claude Code `allowed-tools`, a Codex `agents/openai.yaml`), ship it as a sidecar file inside the skill folder and mention it in the skill's README section. Do not bake it into SKILL.md.

## Writing the description

The description is the entire triggering mechanism. The agent sees it in its system prompt and decides whether your skill is relevant based on those words alone. Write accordingly.

- State **what** the skill does.
- List **trigger contexts and phrases** the agent should watch for.
- Use **pushy language**. "Use this whenever..." "Use this even if the user phrases it casually..." "Prefer this over ad-hoc <thing>."
- Include **counter-examples** when there's a near-neighbor the skill should not steal. "Do not use for X — use `other-skill` instead."

Agents systematically under-trigger. Over-trigger is usually better; you can always tighten later.

## SKILL.md structure

Keep the body under 500 lines. If you're over, push detail into `references/`.

Suggested sections, in order:

1. One-paragraph overview.
2. When to use / when not to use.
3. Configuration (if the skill has any — see below).
4. Inputs expected from the user.
5. Workflow as numbered imperative steps.
6. Output format.
7. Examples (at least two — typical case and edge case).
8. Troubleshooting.
9. References (pointers into the `references/` folder).

Use imperative verbs ("Read the file", not "The file is read"). Keep steps short. If a step is conditional, say so explicitly.

## Scripts

**Prefer Python 3 stdlib for everything.** It is the most portable, runs identically on Windows / macOS / Linux PowerShell / bash / zsh, and has no shell-quoting traps. Reach for shell only when shelling out is genuinely simpler.

Allowed:

- Python 3 stdlib, no external packages. **Default choice.**
- POSIX bash (must work on macOS's default 3.x). Use only when Python is overkill.
- Node.js with no external packages beyond what ships with Node.

If your skill genuinely needs a dependency, document it in the skill's `references/dependencies.md` and fail loudly with an install hint when it's missing. Do not install silently.

Scripts are executable helpers, not install steps. They run when the agent invokes them during skill execution. They never run at install time.

## Configuration

Skills that need configuration use **Pattern 2 (lazy, two-scope, Python helpers)**. The canonical reference is `skills/example-skill/`. The pattern is:

1. Two scopes:
   - User scope at `~/.config/<skill-name>/config.yaml` (or `$XDG_CONFIG_HOME/<skill-name>/config.yaml`).
   - Project scope at `<project_root>/.<skill-name>/config.yaml`. `<project_root>` is detected by walking upward from the cwd looking for VCS / language-manifest / agent-config markers.
2. Resolution order (first match wins): env var → project-local → user-level (non-path keys only) → built-in default.
3. **Path-typed keys are project-only.** A user-installed skill must not bleed one project's writes into another. The resolver refuses to read path-typed keys from the user-level layer.
4. Three Python helpers ship per skill: `scripts/configure.py`, `scripts/resolve_config.py`, `scripts/find_project_root.py`. Stdlib only. Mode `0600` on POSIX.
5. On first use with a missing path key, the agent prompts the user once, persists the answer to project-local config, and never asks again in that project.
6. Never modify files outside the two configured paths during configuration.
7. Never commit a config file to the repo.

### Write-directory configuration

If your skill writes user-visible files (e.g. a diary, a TODO tree, generated reports), expose a `root_dir` config key. It must be:

- **Project-only** (never read from user-level config).
- Resolved via `python3 scripts/resolve_config.py root_dir` at the start of each invocation.
- Defaulted to a project-relative suggestion (e.g. `doc/<skill-name>`) presented at the first-use prompt.
- Overridable via env var `<SKILL_NAME_UPPER>_ROOT_DIR` for ad-hoc use.

This is what makes a skill installable user-scope (so the code is shared) while writes stay project-scope (so corpora never bleed across projects).

## Failure modes

Fail loudly and early. Silent wrong output is the worst outcome. For each expected failure:

- State exactly what's missing.
- State the single command to fix it.
- Do not guess values or proceed with defaults for missing required inputs.

## Don't do

- No AGENTS.md, CLAUDE.md, or REVIEW.md inside a skill folder.
- No install scripts at the repo root.
- No symlinks across agent directories (`~/.claude/skills`, `~/.codex/skills`).
- No modifications to CLAUDE.md, settings.json, or any file outside the skill's own folder and config directory.
- No network calls during configuration without explicit user consent in the same turn.
- No telemetry by default.

## Testing before submitting

1. Install your skill into at least two different agents (Claude Code + Codex CLI is the easy baseline).
2. Run each test prompt in `evals/fixtures/<your-skill>/` on both.
3. Confirm the skill triggers on each prompt. If it doesn't, rewrite the description before blaming the agent.
4. Walk the [portability checklist](portability-checklist.md). Every item must pass.
