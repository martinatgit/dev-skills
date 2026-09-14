# Installation and upgrade requirements v1

**Status:** approved by user request on 2026-09-13

## Scope

The repository must give a checked-out user a reliable path to install and update portable skills and optional subagents for Claude Code and Codex CLI.

## Skills

1. A user can install skills from a local checkout at personal scope or from a consuming project at project scope.
2. A user can select Claude Code, Codex, or both, and can select all or named skills.
3. Shared project conventions are configured from the consuming project's working directory.
4. Repeating shared-convention setup preserves existing parsed `docs_root` and per-skill scalar values; explicit flags replace only the named values.
5. Configuration inspection reports effective runtime resolution, including shared conventions, environment expansion, and derived paths, without writing configuration.
6. Existing per-skill project configuration takes precedence over shared conventions; path settings remain project-scoped.

## Claude Code

7. The documented marketplace install identifier matches `.claude-plugin/marketplace.json`.
8. Marketplace refresh and plugin update instructions identify the plugin and marketplace separately.

## Subagents

9. Claude agents are Markdown files and Codex agents are generated TOML files with `name`, `description`, and `developer_instructions`.
10. Generated Codex agents do not encode Claude's skill preload list as a `skills.config` mapping. Paired skills are requested through developer instructions and remain discoverable through the host's normal skill locations.
11. The agent installer supports first installs when explicit hosts are selected, detects configured hosts when selection is omitted, skips identical files, and rejects unknown selections before writing.
12. `--update` replaces only tracked files whose installed contents remain unmodified. `--force` backs up conflicting files outside the agent discovery directory before replacement. Dry runs do not write files, manifests, or backups.
13. Obsolete or stale files are reported and retained; automatic deletion and artifact migration are outside this version.

## Migration boundaries

14. Users updating from renamed skill or agent names receive explicit mappings and must remove old registrations through the original installation method after verifying replacements.
15. Deprecated `update-todos` keys are documented with their migration and behavior change. Changing configured output paths never moves existing project artifacts automatically.

## Documentation and verification

16. README.md contains first-install, configuration, verification, update, conflict recovery, and legacy migration instructions.
17. The implementation has regression tests for configuration preservation, runtime inspection, agent lifecycle behavior, generated Codex TOML, and marketplace command identifiers.
