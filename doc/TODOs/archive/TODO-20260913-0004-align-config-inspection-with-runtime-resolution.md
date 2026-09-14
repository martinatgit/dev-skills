---
id: TODO-20260913-0004
title: Align configuration inspection with runtime resolution
status: resolved
created: 2026-09-13
updated: 2026-09-13
resolved-at: 2026-09-13
resolved-in: skills/*/scripts/configure.py, tests/test_config_inspection.py
next-step: implementation
references:
  - path: skills/update-todos/scripts/configure.py
    lines: 243-250
    note: Print mode invokes the resolver that omits shared conventions.
  - path: skills/update-todos/scripts/resolve_config.py
    lines: 64-85
    note: Actual runtime resolution adds the shared-conventions layer.
  - path: docs/install.md
    lines: 186-203
    note: Inspection recommendation and changing into the installed skill directory.
  - path: README.md
    lines: 44-49
    note: Repository-root scripts/configure.py does not exist.
discovered-in-task: Review fresh installation, configuration, and upgrades for Claude Code and Codex.
discovered-by: codex
---

# Align configuration inspection with runtime resolution

## Discovery context

Followed the configuration documentation during an installation UX review. Tested configure.py and resolve_config.py from the same temporary project with a shared docs_root of agent-docs. The generic README command was checked against the repository file inventory.

## Raw observation

For update-todos, `configure.py --print` outputs an empty root_dir while `resolve_config.py root_dir` correctly outputs agent-docs/TODOs (Windows separators in the test). The documented inspection command therefore does not report runtime truth. Separately, docs/install.md tells users to cd into their user-installed skill before configuring project scope; project detection starts from cwd, so it can fail or target the installation environment rather than the consuming project. README.md shows a nonexistent root-level scripts/configure.py. Consolidate diagnostics on the actual resolver and provide commands that retain the consuming project's cwd. Investigate other configurable skills for the same divergence before claiming the repair covers all of them.

## Resolution notes

All four shared-config skill writers now delegate `--print` to their runtime resolver with the caller's working directory, so effective shared, project, user, and environment values agree. Read-only tests cover derived paths and precedence.
