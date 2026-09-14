---
id: TODO-20260913-0002
title: Fix Codex agent skills configuration format
status: resolved
created: 2026-09-13
updated: 2026-09-13
resolved-at: 2026-09-13
resolved-in: scripts/generate-codex-agents.py, agents/*.toml, tests/test_generate_codex_agents.py
next-step: implementation
references:
  - path: scripts/generate-codex-agents.py
    lines: 115-121
    note: Emits skills.config as a mapping keyed by skill name.
  - path: agents/formal-methods-agent.toml
    lines: 208-209
    note: Representative generated configuration; all eight TOML agents contain the same shape.
  - path: docs/agents-guide.md
    note: Documents the generated format and claims Codex compatibility.
  - path: tests/test_generate_codex_agents.py
    note: Generator checks need host-schema validation rather than only agreement with generated output.
discovered-in-task: Review fresh installation, configuration, and upgrades for Claude Code and Codex.
discovered-by: codex
---

# Fix Codex agent skills configuration format

## Discovery context

Inspected the generated agent files while checking whether copying them into .codex/agents is sufficient. Official documentation at https://learn.chatgpt.com/docs/agent-configuration/subagents describes custom agent files as Codex configuration layers and shows `[[skills.config]]` entries with path/enabled fields. Installation into the user's actual agent directory was not attempted.

## Raw observation

All eight generated TOML agents contain `[skills.config]` followed by `<skill-name> = {}`. A read-only parser probe against codex-cli 0.154.0, `codex -c 'skills.config={formal-methods={}}' features list`, fails with `invalid type: map, expected a sequence` in `skills.config`. This reproduces rejection of the emitted configuration shape, not a full agent-spawn test. Claude's skill-preloading semantics must be mapped deliberately; merely changing TOML brackets is insufficient because the supported entries have different fields and semantics. Correct the generator, generated files, and format documentation, then validate actual host loading.

## Resolution notes

The generator now omits the invalid `skills.config` mapping and prepends paired-skill loading instructions to `developer_instructions`. All generated TOML files were regenerated and parser tests pass.
