# Portability checklist

Every skill in this repo passes every item. Walk this list before opening a PR.

## Frontmatter

- [ ] `SKILL.md` starts with `---`, has exactly `name` and `description` keys, and nothing else.
- [ ] `name` is kebab-case, unique within the repo.
- [ ] `description` states what the skill does AND when to trigger it.
- [ ] `description` uses pushy language ("use whenever...", "even if phrased casually...").

## Structure

- [ ] The skill is a single folder under `skills/`.
- [ ] `SKILL.md` body is under 500 lines.
- [ ] Detail longer than 30 lines is in `references/`, not in SKILL.md.
- [ ] Scripts live under `scripts/`, assets under `assets/`, reference docs under `references/`.
- [ ] No `README.md` inside the skill folder (SKILL.md is the readme).

## Portability

- [ ] Scripts are POSIX bash or Python 3 stdlib or Node.js stdlib only.
- [ ] No Bun, no uv, no `#!/usr/bin/env -S` shebangs, no Node version pins.
- [ ] No external package installs at any point.
- [ ] No tool-specific files inside the skill (no `allowed-tools` in frontmatter, no `agents/openai.yaml` unless documented).
- [ ] No symlinks.

## Configuration (if applicable)

- [ ] Config path is `~/.config/<skill-name>/config.yaml` with permissions `0600`.
- [ ] Resolution order is env var → user config → project-local → interactive prompt.
- [ ] `scripts/configure.sh` prompts for missing values, is idempotent, accepts `--repair`.
- [ ] Configuration never writes outside `~/.config/<skill-name>/`.
- [ ] Schema is documented in `references/config-schema.md` with an example file.

## State and side effects

- [ ] The skill does not modify files outside its own folder, its config directory, or paths the user explicitly asks about.
- [ ] The skill does not modify CLAUDE.md, AGENTS.md, or any agent's settings.json.
- [ ] No telemetry. No network calls during configure. No background daemons.

## Failure behavior

- [ ] Missing config → clear message, one-line fix command.
- [ ] Missing dependency → clear message, install hint.
- [ ] Bad input → message identifies exactly which input and why.
- [ ] Never silently falls back to defaults for required inputs.

## Triggering

- [ ] Tested on Claude Code: skill triggers on all canonical prompts in `evals/fixtures/<skill-name>/`.
- [ ] Tested on one other agent (Codex CLI, Cursor, or Windsurf).
- [ ] Trigger rate at or above 80% on canonical prompts — if not, rewrite the description.

## Documentation

- [ ] README table updated with the new skill.
- [ ] `.claude-plugin/marketplace.json` plugins list updated.
- [ ] At least two worked examples in SKILL.md's Examples section.
- [ ] Troubleshooting section covers the top three failure modes.

## Final

- [ ] `grep -rn '{{' skills/<your-skill>/` returns nothing (no unfilled placeholders).
- [ ] `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null` exits 0.
- [ ] `bash -n skills/<your-skill>/scripts/*.sh` exits 0 for every script.
