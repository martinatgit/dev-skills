---
id: TODO-20260913-0005
title: Improve agent installer fresh and repeat behavior
status: resolved
created: 2026-09-13
updated: 2026-09-13
resolved-at: 2026-09-13
resolved-in: scripts/install-agents.py, tests/test_install_agents.py
next-step: implementation
references:
  - path: scripts/install-agents.py
    lines: 30-32
    note: Host detection requires the destination agents directory to exist.
  - path: scripts/install-agents.py
    lines: 109-156
    note: Scope-dependent detection, unmatched names, collisions, and copying.
  - path: tests/test_install_agents.py
    note: Existing tests precreate destination directories and test forced overwrite.
  - path: docs/install.md
    lines: 105-121
    note: Primary Codex instruction relies on autodetection.
discovered-in-task: Review fresh installation, configuration, and upgrades for Claude Code and Codex.
discovered-by: codex
---

# Improve agent installer fresh and repeat behavior

## Discovery context

Ran the six existing installer tests successfully and exercised dry-run behavior in a new temporary project. Also checked unknown-name selection without installing anything. The user's request explicitly includes upgrading previously installed skills and agents.

## Raw observation

Autodetection in a fresh project exits 2 because neither .claude/agents nor .codex/agents exists; it probes the project in project scope even if hosts are installed globally. Its diagnostic misleadingly names the home directory. Explicit `-a codex` or `-a claude-code` avoids this issue. Selecting only a nonexistent agent exits 0 with `no agent files matched`. Repeat installation treats even identical files as collisions; --force overwrites without checking local modifications or keeping a backup. Renamed/removed old agents are never reconciled. The parser accepts -y but there is no confirmation code. Establish clear first-install and update semantics, detect no-op versus changed versus locally modified files, and expose exact source and target paths. Capture migration policy separately when planning the user-facing upgrade workflow.

## Resolution notes

The installer now supports explicit fresh-host selection, canonical project detection, idempotent installs, tracked `--update`, conflict-safe `--force` backups outside discovery directories, stale-file reporting, manifest validation, symlink safety, and write-free dry runs. It intentionally does not delete stale files or provide multi-file transaction locking.
