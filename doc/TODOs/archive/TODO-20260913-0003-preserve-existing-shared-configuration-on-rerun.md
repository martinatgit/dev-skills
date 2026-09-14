---
id: TODO-20260913-0003
title: Preserve existing shared configuration on rerun
status: resolved
created: 2026-09-13
updated: 2026-09-13
resolved-at: 2026-09-13
resolved-in: scripts/setup-conventions.py, tests/test_setup_conventions.py
next-step: implementation
references:
  - path: scripts/setup-conventions.py
    lines: 185-217
    note: Existing data is not merged into the rendered per-skill overrides.
  - path: tests/test_setup_conventions.py
    note: Seven existing tests pass but do not check preservation on rerun.
  - path: docs/install.md
    lines: 136-163
    note: User-facing shared-conventions setup instructions.
discovered-in-task: Review fresh installation, configuration, and upgrades for Claude Code and Codex.
discovered-by: codex
---

# Preserve existing shared configuration on rerun

## Discovery context

Examined repeat setup as part of the requested upgrade journey. Reproduced using the existing test helper in a temporary project, then removed that temporary project. No real project configuration was changed.

## Raw observation

Running setup-conventions.py with `--non-interactive --docs-root agent-docs --terminology-filename terms.md` creates the custom filename. Running it again with only `--non-interactive --docs-root agent-docs` exits successfully but removes the entire skills block. The code constructs skill_overrides solely from current CLI arguments and rewrites the whole file. Interactive setup also does not carry existing per-skill overrides forward. A noninteractive rerun without --docs-root additionally falls back to doc. This can change where skills look for existing project artifacts during a routine reconfiguration. The script needs explicit preservation/update semantics and regression coverage before it can be recommended as a safe repeatable setup step.

## Resolution notes

Setup now merges existing parsed shared configuration, retaining `docs_root`, per-skill blocks, and future scalar keys; explicit flags replace only named values. Regression tests cover noninteractive and selective reruns.
