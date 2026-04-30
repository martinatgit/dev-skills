# Host adaptation notes

This skill describes its work in **intent language** ("dispatch N parallel
sub-agents") rather than calling a host-specific dispatch API. Each host
agent translates the intent into its own primitives. This file lists the
known mappings.

## The dispatch contract

Whatever the host, every dispatched specialist must receive:

1. The full text of `agents/specialist-base.md` (the base contract).
2. The full text of `agents/families/{family_id}.md` (the family-specific prompt).
3. A `## USER TASK` section containing the user's task (with skill flags stripped).

All dispatches in one phase MUST happen in parallel. Sequential dispatch
defeats the architecture and inflates wall-clock time.

The orchestrator collects each specialist's response, parses the JSON inside,
and proceeds with Phases 4 onwards.

## Model tier hints

The skill exposes two tier hints (`specialist_model_tier`,
`orchestrator_model_tier`) with values `fast`, `default`, `strong`. Hosts map
these to concrete model names if they expose model selection; otherwise they
ignore them.

| Host | `fast` | `default` | `strong` |
|---|---|---|---|
| Claude Code | `haiku` | (host default) | `sonnet` or `opus` |
| Codex CLI | smallest available | (host default) | largest available |
| Cursor / Windsurf / Goose | (host default) | (host default) | (host default) |

A host that does not expose model selection runs every agent on its
configured default model. This is acceptable; the skill works either way.

## Per-host translation

### Claude Code

Sub-agent dispatch uses the `Agent` tool with `subagent_type` set to a
matching agent type. Example shape:

```
Agent({
  description: "{family_name} analysis",
  subagent_type: "general-purpose",
  model: "<resolved tier>",
  prompt: "<specialist-base>\n\n<family-prompt>\n\n## USER TASK\n\n{task}"
})
```

All Agent calls for one phase go in a single message to run in parallel.

### Codex CLI

Sub-agent dispatch uses parallel `task` invocations. The host translates the
intent into multiple concurrent task launches; the orchestrator awaits all
results and continues. Codex does not require `subagent_type`.

### Cursor / Windsurf / Goose

Hosts that lack a native sub-agent primitive simulate parallelism by
preparing each specialist prompt as a separate request and awaiting them
together. The orchestrator's downstream phases are unchanged.

## Filesystem and shell

The skill avoids host-specific shell idioms. State writes go through the
provided Python helpers:

- `scripts/append_log.py` — append a JSON line to `cost-log.jsonl`.
- `scripts/resolve_config.py` — read configured paths and tunables.

These work identically on POSIX shells, PowerShell, and Windows `cmd`,
because all heavy lifting is inside Python 3 stdlib.
