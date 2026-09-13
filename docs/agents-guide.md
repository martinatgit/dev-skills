# Agents authoring guide

This guide covers the `agents/` layer — Claude Code subagents and Codex CLI subagents shipped from this repo. Skills are documented separately in [`docs/authoring-guide.md`](authoring-guide.md). Read both if you are adding a new agent that also needs a paired skill.

## When to write an agent vs. a skill

Prefer skills. A SKILL.md with strong description-as-trigger language reaches every host that implements the [agentskills.io](https://agentskills.io/specification) standard (Claude Code, Codex CLI, Cursor, Windsurf, Goose, and others). An agent reaches only the host whose subagent format it targets (Claude Code or Codex CLI; not portable to the others).

Write an agent when you genuinely need:

- An **isolated context window** (long parallel exploration, heavy tool use, sandbox isolation).
- A specific **model tier** or **reasoning effort** different from the parent session.
- A **named dispatchable role** the user invokes by name (e.g. "have `improve-prompt-agent` rewrite this prompt").
- **Banned-construct enforcement** that requires a separate prompt (rare).

If none of those apply, the skill alone is enough.

## Naming rule

Agent name = `<paired-skill-name>` + `-agent`.

Skill names carry no `-expert` suffix; agents inherit the clean skill name plus `-agent`. Examples:

| Skill | Agent |
|---|---|
| `improve-prompt` | `improve-prompt-agent` |
| `formal-methods` | `formal-methods-agent` |
| `srs` | `srs-agent` |
| `petri-net-theory` | `petri-net-theory-agent` |

This makes the agent-to-skill mapping unambiguous and machine-checkable (`evals/run.py` enforces it).

## Format conventions

### Claude Code (canonical)

`agents/<name>.md` is the canonical source. YAML frontmatter:

- **Required:** `name`, `description`.
- **Optional:** `tools` (Claude Code tool allow-list), `model`, `skills` (array of paired skills to auto-load).

The Markdown body is the agent's system prompt.

### Codex CLI (generated)

`agents/<name>.toml` is generated from the `.md` by `scripts/generate-codex-agents.py`. Schema (per [Codex 2026 subagent docs](https://developers.openai.com/codex/subagents)):

- **Required:** `name`, `description`, `developer_instructions`.
- **Optional:** `model`, `model_reasoning_effort`, `nickname_candidates`, `sandbox_mode`, `mcp_servers`, `[skills.config]`.

The Markdown body becomes `developer_instructions` as a multi-line TOML string.

### Cross-format invariants

`evals/run.py` enforces:

- Every `agents/<name>.md` has a `agents/<name>.toml` sibling.
- The `.toml` is byte-identical (newline-normalised) to what
  `scripts/generate-codex-agents.py` would produce from the `.md` right now.
  This is checked by importing the generator and regenerating in memory —
  not by comparing individual fields — so it catches any divergence, not
  just a changed `name`.

Fields the generator drops (`tools`, `model`) never reach the `.toml` at all;
that is expected, not a divergence the check flags.

## Generation workflow

After editing any `<name>.md`:

```sh
python3 scripts/generate-codex-agents.py
```

Then commit both the `.md` and the regenerated `.toml`.

Editing the `.toml` by hand is unsupported — the eval check regenerates the `.toml` from the `.md` in memory and fails on any difference from what is on disk, not just a changed `name` or `description`. Always regenerate; never hand-edit the output.

## Banned constructs in agent bodies

Agents should not:

- Read or write user project files outside what their paired skill mandates.
- Embed credentials, API keys, or hardcoded paths.
- Reference peer agents that do not exist in this repo. (Nothing in `evals/run.py` checks this — the pairing check only maps `<name>-agent.md` to `skills/<name>/` and never reads agent bodies. This is a manual review item.)

## Distribution

Agents are not portable across all hosts. Each format ships to its specific host:

- **Claude Code:** via plugin marketplace (`/plugin install dev-skills@martinatgit`) or manual copy of `agents/*.md` to `~/.claude/agents/` or `<project>/.claude/agents/`.
- **Codex CLI:** via `python3 scripts/install-agents.py` or manual copy of `agents/*.toml` to `~/.codex/agents/` or `<project>/.codex/agents/`.
- **Cursor, Windsurf, Goose:** no file-based agent slot exists today. Skills are the portable alternative.

See [`docs/install.md`](install.md) for the full install matrix.

## Authoring checklist

Before opening a PR with a new or modified agent, walk [`docs/agents-portability-checklist.md`](agents-portability-checklist.md).
