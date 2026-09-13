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
- [ ] Every file sits in a sanctioned sub-directory:

  | Directory | Contents | Placeholder-checked |
  |---|---|---|
  | `references/` | Reference docs the skill loads on demand. | yes |
  | `scripts/` | Executable helpers (Python 3.12 stdlib preferred). | no |
  | `actions/` | One file per invocable sub-command (`capture`, `review`, …). | no |
  | `resources/` | Output templates, `*.md.tpl`. | no |
  | `schemas/` | JSON Schema for the skill's structured output. | no |
  | `agents/` | Sub-agent prompt files the skill dispatches. | no |
  | `assets/` | Static binary assets. | no |

  `SKILL.md` is the only file permitted at the skill root. "Placeholder-checked" marks the surfaces `evals/run.py` scans for unfilled `{{...}}`; the rest legitimately carry placeholder markers filled at runtime.
- [ ] No `README.md` inside the skill folder (SKILL.md is the readme).

## Portability

- [ ] Scripts are POSIX bash or Python 3.12 stdlib or Node.js stdlib only.
- [ ] Python scripts run under 3.12 with no deprecation warnings. Scripts with their own CLI entry point: `python3 -W error::DeprecationWarning skills/<name>/scripts/<script>.py --help`. `read_shared_conventions.py` has no CLI of its own — it is only ever imported, never invoked directly — so check it by importing under the same flag: `python3 -W error::DeprecationWarning -c "import sys; sys.path.insert(0, 'skills/<name>/scripts'); import read_shared_conventions"`.
- [ ] No Bun, no uv, no `#!/usr/bin/env -S` shebangs, no Node version pins.
- [ ] No external package installs at any point.
- [ ] No tool-specific files inside the skill (no `allowed-tools` in frontmatter, no `agents/openai.yaml` unless documented).
- [ ] No host-specific tool name appears in skill prose (`AskUserQuestion`, `Agent`, `subagent_type`, `TodoWrite`, …). Write intent; put any per-host translation in `references/host-notes.md`. See [`docs/host-adaptation.md`](host-adaptation.md).
- [ ] No path under `.claude/`, `~/.claude/`, `.codex/`, or `~/.codex/` is cited as where one of *this repo's* files lives — link the repo-relative `agents/<name>-agent.md` source instead. Citing such a path as an illustrative example of a host's install location (e.g. explaining why a config key must be project-scoped) is fine.
- [ ] No symlinks.

## Configuration (if applicable)

- [ ] Non-path config is at `~/.config/<skill-name>/config.yaml` with permissions `0600`; path-typed keys are at `<project_root>/.<skill-name>/config.yaml`.
- [ ] Resolution order is env var → project-skill config → user-skill config (non-path keys only) → built-in default; skills with path-typed keys insert a `.agents/dev-skills.yaml` layer between project-skill and user-skill config (five layers total — see the bullet below). Path-typed keys always skip the user-skill layer.
- [ ] `scripts/configure.py` prompts for missing values, is idempotent, accepts `--repair`.
- [ ] Configuration writes only to `~/.config/<skill-name>/config.yaml`, `<project_root>/.<skill-name>/config.yaml`, or — when the user opts in via a skill's first-use prompt — the shared `<project_root>/.agents/dev-skills.yaml` file. Nothing else.
- [ ] Schema is documented in `references/config-schema.md` with an example file.
- [ ] If the skill has path-typed keys, the resolver consults `<project_root>/.agents/dev-skills.yaml` between project-skill and user-skill layers (see `docs/authoring-guide.md` -> Consulting the shared conventions file).
- [ ] Both canonical stamped scripts — `template/scripts/read_shared_conventions.py` and `template/scripts/find_project_root.py` — have been stamped into the skill via `python3 scripts/refresh-shared-reader.py`. `python3 evals/run.py` reports no drift for either.

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
- [ ] `evals/fixtures/<skill-name>/prompts.json` uses the fixture schema below — every fixture file in the repo must match it exactly.

### Fixture schema

`evals/fixtures/<skill-name>/prompts.json` is a single JSON object:

```json
{
  "skill": "<skill-name>",
  "prompts": [
    { "id": "short-kebab-slug", "text": "the literal prompt text", "expect_trigger": true }
  ]
}
```

- Top level: exactly `skill` (the skill's folder name) and `prompts` (an array). No other top-level keys — no `purpose` blurb; the schema and its intent are documented here, once, for every fixture file.
- Each entry in `prompts`: exactly `id` (kebab-case, unique within the file), `text` (the prompt string), and `expect_trigger` (`true` for a prompt that should trigger the skill, `false` for a negative/counter-example). No other per-prompt keys — no `category` field; encode any useful classification into the `id` itself (e.g. `negative-unrelated-skill-chargebee`).
- Include at least one negative (`expect_trigger: false`) prompt per skill to catch over-triggering.

Verify every fixture file shares this shape:

```sh
python3 -c "
import json, pathlib
shapes = set()
for p in sorted(pathlib.Path('evals/fixtures').glob('*/prompts.json')):
    d = json.loads(p.read_text(encoding='utf-8'))
    shapes.add((tuple(sorted(d)), tuple(sorted({k for e in d['prompts'] for k in e}))))
assert len(shapes) == 1, f'{len(shapes)} schemas: {shapes}'
"
```

## Documentation

- [ ] README table updated with the new skill.
- [ ] `.claude-plugin/marketplace.json` plugins list updated.
- [ ] At least two worked examples in SKILL.md's Examples section.
- [ ] Troubleshooting section covers the top three failure modes.

## Final

- [ ] `python3 evals/run.py` (unscoped — this is the gate; there is no CI in this repo) returns OK. It covers, repo-wide: frontmatter for every skill, marketplace JSON validity, README + marketplace registration, unfilled `{{...}}` placeholders in user-facing surfaces, Python script compilation, stamped-script drift, agent-skill pairing (every `agents/<name>-agent.md` has a `skills/<name>/`), and agent format parity (every `agents/<name>.toml` matches what `scripts/generate-codex-agents.py` would produce from its `.md`). `python3 evals/run.py --skill <your-skill>` only checks that one skill's frontmatter — it is a fast iteration shortcut, not a substitute for the unscoped run before opening a PR.
- [ ] `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null` exits 0.
- [ ] `python3 -m py_compile skills/<your-skill>/scripts/*.py` exits 0 for every script.
- [ ] If the skill writes user files, it exposes a `root_dir` (or equivalent path-typed) config key marked project-only.
