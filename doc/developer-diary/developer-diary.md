## Index

R

## Last updated

2026-09-13

## Title

Developer diary

## Relevant context

This repository distributes portable agent skills and optional Claude Code/Codex subagents. Installation behavior, project configuration, and upgrade safety are recorded under child node R.1.

## Design decisions made

- Keep skill distribution with the external skills CLI and Claude marketplace; improve the repository's Python helpers rather than introduce a second universal installer.

## Peers

The root routes repository-wide concerns. Installation and update behavior is owned by child R.1.

## Progress made

- Created the installation and upgrade requirements in `doc/requirements/installation-v1.md`.

## Outstanding items

- Run the full verification suite and close the installation TODOs after evidence is recorded.

## Problems encountered

- The original repository had no developer-diary tree, so this root and its installation child were created during the implementation.

## What works well

- The repository already had isolated Python helpers, generated-agent checks, and host-specific installation documentation that could be repaired incrementally.

## Next steps

- Maintain R.1 when installation contracts or migration behavior change.

## Child nodes
| Index | File name | Description |
| --- | --- | --- |
| R.1 | `child_1/diary-entry.md` | Installation, configuration, and upgrade behavior. |

## Relevant related diary nodes
| Index | File name | Description |
| --- | --- | --- |

## Notes and commentary

### Decision journal

The implementation uses a focused set of host-specific helpers and preserves the distinction between skills, subagents, and project configuration. A new universal installer was considered but rejected because the external skills CLI already owns skill distribution and duplicating its scope/source behavior would create a second contract. Confidence is high for the documented file workflows; host loading still depends on the installed Claude/Codex versions.

### Session context

Relevant sources were `README.md`, `docs/install.md`, `docs/agents-guide.md`, `.claude-plugin/marketplace.json`, `scripts/setup-conventions.py`, `scripts/install-agents.py`, `scripts/generate-codex-agents.py`, and the four shared-config skill resolvers. The installation requirements are `doc/requirements/installation-v1.md`. Regression tests cover configuration, installer lifecycle, generated TOML, and documentation identifiers.

### Uncertainties and risks

The installer is not a multi-file transaction and does not lock against concurrent edits. Legacy manual installations cannot be safely identified without their original source metadata, so the documentation requires explicit user review. Marketplace behavior can vary by Claude Code version and authentication setup.

## Special instructions for next reader

Run the installation lifecycle tests before changing the manifest or installer. Preserve the requirement that backups stay outside `.claude/agents` and `.codex/agents` discovery trees.
