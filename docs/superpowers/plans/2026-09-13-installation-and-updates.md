# Installation and Updates Implementation Plan

**Goal:** Close TODO-20260913-0001 through 0005 and provide usable first-install, configuration, and upgrade instructions for Claude Code and Codex.

**Authorization:** The user requested implementation of the five reviewed TODOs on 2026-09-13. This plan records implementation choices within that scope; it does not approve unrelated proposed requirements.

**Architecture:** Keep the existing Python stdlib installers and per-skill configuration interface. Delegate independent configuration and installer fixes; integrate and review centrally. Skill distribution remains the external skills CLI or Claude marketplace. Codex agents inherit host skill discovery and explicitly request their paired skills in their instructions instead of emitting an unsupported configuration mapping.

**Tech stack:** Python stdlib, unittest, Markdown, generated TOML, existing eval runner.

## Task 1: Preserve configuration and make inspection accurate

- [x] Add failing tests to tests/test_setup_conventions.py for interactive/noninteractive reruns retaining docs_root and all existing skill overrides, with explicit CLI values replacing only named keys.
- [x] Merge existing parsed values in scripts/setup-conventions.py; retain foreign-file refusal. Preserve all supported parsed fields, document serialization limits.
- [x] Test configure.py --print against runtime resolution for each shared-config skill (developer-diary, update-todos, terminology, create-tutorial); fix their print paths to use the runtime resolver.
- [x] Run configuration regression suites. Document the preservation and diagnostic contract in docs/install.md and README.md (main agent).

## Task 2: Make agent installation repeatable and updates recoverable

- [x] Add failing tests to tests/test_install_agents.py for fresh project detection from host config directories under home, explicit targets, unknown selected names, unchanged repeat installs, safe managed updates, local conflicts, backups, and dry-run purity.
- [x] Extend scripts/install-agents.py: detect host config roots rather than requiring agents destinations; use canonical project detection; fail unknown selections before writes; skip identical files; record installed hashes/source in a private manifest; --update replaces only unmodified tracked files, while --force preserves a backup before replacing any changed existing file.
- [x] Report stale managed files without deleting them. Document manual legacy rename reconciliation and exact backup/restore paths. No automatic deletion of untracked host files.
- [x] Run installer regression tests; communicate CLI contract to main agent for README and install guide.

## Task 3: Fix generated Codex agents

- [x] Add a failing TOML structure test that verifies no unsupported skills.config mapping and preserves paired-skill names in developer_instructions.
- [x] Update scripts/generate-codex-agents.py to append an explicit paired-skill loading instruction; omit skills.config so parent discovery/configuration is inherited. Regenerate agents/*.toml.
- [x] Validate generator tests, structural evals, and host configuration parsing without changing real host installations. Record that prompt-level loading is not host-level automatic preloading.

## Task 4: Document the full user journey

- [x] Correct marketplace identifiers in README.md, docs/install.md, docs/agents-guide.md, and current design guidance. Keep the manifest's marketplace name dev-skills.
- [x] Rewrite README setup to distinguish checkout source from consuming project; cover prerequisites, user/project scopes, both hosts, optional agents, shared/per-skill configuration, inspection, verification, local/remote/plugin updates, backups, renames, and deprecated configuration migration.
- [x] Align docs/install.md and agent/schema documentation with tested behavior; test marketplace command identifiers against the manifest.
- [x] Add a current implementation contract at doc/requirements/installation-v1.md with user-authorized behavior and explicit migration boundaries.

## Task 5: Verify and close

- [x] Run python -m unittest discover -s tests, python evals/run.py, generator drift checks, and claude plugin validate .; inspect all failures before claiming completion.
- [x] Review combined changes and documentation commands. Exercise isolated install/update/configuration scenarios; do not alter the user's actual host installations.
- [x] Use developer-diary update to create the missing diary root and an installation node with decisions, evidence, limitations, and routing.
- [x] Resolve the five TODOs only after their fixes pass verification; retain discovery history, add closure evidence, move to archive, and regenerate the index.

## Scope boundaries

This work does not build a new universal CLI or automatically migrate user project artifacts. Existing per-skill configuration takes precedence over shared conventions. Legacy skill folders installed manually or through third-party tools are reconciled through the documented original installation method; renamed/deleted agents are reported and removed only by an explicit user action. No commits or publication are needed for this task.

