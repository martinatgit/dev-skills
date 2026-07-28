# Host adaptation

A skill in this repo must run unmodified on every skills-compatible agent. That
rules out naming a host's tools in skill prose: `AskUserQuestion` is Claude Code
only, `Agent`/`subagent_type` is Claude Code only, Codex CLI names the same
capabilities differently, and Cursor/Windsurf/Goose differ again.

## The rule

Write **intent**, not a tool call.

| Don't write | Write |
|---|---|
| "Ask via `AskUserQuestion`." | "Ask the user a single consolidated question covering every uncertain field." |
| "Dispatch with the `Agent` tool." | "Dispatch N sub-agents in parallel, one per family." |
| "See `.claude/agents/foo.md`." | "See [`agents/foo.md`](../agents/foo.md)." |

Shipped agents are named `<paired-skill-name>-agent.md` (e.g.
`agents/improve-prompt-agent.md`, `agents/petri-net-theory-agent.md`) — a
consistent suffix, no `-expert` on either side. Link to the file by that name.

If the intent genuinely needs a per-host translation table, put it in the
skill's `references/host-notes.md` and link it from the workflow step. The
canonical example is
[`skills/reason-through/references/host-notes.md`](../skills/reason-through/references/host-notes.md).

## Structured questioning without a host tool

Hosts that expose a structured question tool will use it; hosts that don't fall
back to plain prose. Both satisfy the same contract, so state the contract:

> Ask **exactly one** consolidated question covering every uncertain field.
> Offer 2–4 concrete options per field where the choice space is closed. Do not
> ask sequential follow-ups.

## Referring to agents

Agents ship from `agents/` in this repo and are installed per host by
`scripts/install-agents.py`. When pointing readers at where
an agent's definition lives, link the repo-relative source path, never a host's
installed location (`~/.claude/agents/`, `~/.codex/agents/`) — that path is
per-user and doesn't exist until install. Citing a host's install path as an
illustrative example inside explanatory prose (e.g. why a config key must
stay project-scoped) is fine; the rule is about where a skill sends readers
to find its own files, not about mentioning that a host path exists.
