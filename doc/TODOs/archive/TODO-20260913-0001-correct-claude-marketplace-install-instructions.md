---
id: TODO-20260913-0001
title: Correct Claude marketplace install instructions
status: resolved
created: 2026-09-13
updated: 2026-09-13
resolved-at: 2026-09-13
resolved-in: README.md, docs/install.md, docs/agents-guide.md, tests/test_installation_docs.py
next-step: implementation
references:
  - path: .claude-plugin/marketplace.json
    lines: 1-12
    note: Marketplace name is dev-skills; owner name is martinatgit.
  - path: README.md
    lines: 21-26
    note: Quick start uses the owner as the marketplace identifier.
  - path: docs/install.md
    lines: 62-67
    note: The same command is repeated in the agents section and agents-guide.md.
discovered-in-task: Review fresh installation, configuration, and upgrades for Claude Code and Codex.
discovered-by: codex
---

# Correct Claude marketplace install instructions

## Discovery context

The user asked: "Assume somebody has checked out the repository. Talk me through the installation process for claude and codex. Include the case that some skills need update from a prvious version."

Read README.md, docs/install.md, docs/agents-guide.md, and the marketplace manifest. Checked Anthropic's current marketplace documentation at https://code.claude.com/docs/en/plugin-marketplaces. This is a review; installation instructions were not edited.

## Raw observation

The documented `/plugin install dev-skills@martinatgit` uses the owner rather than the declared marketplace name. The identifier should be `dev-skills@dev-skills` with the current manifest. Claude Code 2.1.270 accepts `claude plugin validate .`, so JSON/manifest validation alone does not catch this documentation error. No plugin was installed during this review. Check every occurrence, including the design document, and verify the complete documented install journey against an isolated host configuration.

## Resolution notes

README and installation references now use `dev-skills@dev-skills`; a regression test compares documented identifiers with the marketplace manifest.
