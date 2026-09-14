## Index

R.1

## Last updated

2026-09-13

## Title

Installation, configuration, and upgrade workflow

## Relevant context

The review found five gaps: the Claude marketplace suffix was wrong in documentation; generated Codex TOML used an invalid skills configuration shape; shared setup discarded existing values on rerun; configuration inspection omitted runtime shared conventions; and the agent installer lacked safe fresh-install and update semantics.

## Design decisions made

- The marketplace command uses `dev-skills@dev-skills`, because `dev-skills` is the declared marketplace name and `martinatgit` is only the owner.
- Generated Codex agents omit `skills.config`. Claude's frontmatter skill list is converted into an instruction to load the paired skill through normal host discovery, because a name-keyed map is rejected by the installed Codex CLI and Codex's array controls different settings.
- Agent updates track SHA-256 hashes in `.dev-skills-install.json`; conflicting replacements require `--force` and are backed up in `.dev-skills-agent-backups` outside the discovery directory.
- Shared setup merges parsed values and explicit flags, preserving future per-skill scalar keys while intentionally normalizing comments and unsupported top-level fields.

## Peers

This node owns user-facing installation and upgrade behavior. Skill authoring and host portability remain in sibling documentation.

## Progress made

- README and `docs/install.md` now describe local/remote skill installation, personal/project scope, shared configuration, verification, plugin updates, skill updates, agent updates, conflict recovery, and legacy-name migration.
- Configuration writers retain existing shared values and `configure.py --print` delegates to runtime resolution.
- Agent lifecycle tests cover fresh host detection, selection validation, idempotent installs, tracked updates, conflicts, backups, stale files, malformed manifests, symlink safety, and dry-run purity.
- Codex agents were regenerated without `skills.config` mappings.

## Outstanding items

- Verify the complete suite and resolve the five captured TODOs into the archive.

## Problems encountered

- Full-suite verification initially found that the installer imported the shared project-root module and created `__pycache__` during dry-run. Setting `sys.dont_write_bytecode` before that import restored the documented no-write guarantee.
- The initial Codex generator tests only checked source/output agreement, so they did not catch host schema rejection. A TOML parser test now asserts that generated output contains no `skills` table and includes paired-skill instructions.

## What works well

- The existing test fixtures made it possible to reproduce all five issues without touching real host directories or user configuration.

## Next steps

- Run `python -B -m unittest discover -s tests`, `python -B evals/run.py`, `python -B scripts/generate-codex-agents.py --dry-run`, and `claude plugin validate .` before release.

## Child nodes
| Index | File name | Description |
| --- | --- | --- |

## Relevant related diary nodes
| Index | File name | Description |
| --- | --- | --- |

## Notes and commentary

### Decision journal

The work stayed within the existing architecture. The main tradeoff is that `--force` is recoverable through backups but still cannot make a multi-file update atomic; exposing that limitation is safer than implying transactional behavior. Runtime inspection uses a subprocess rather than importing the sibling resolver to preserve the exact consuming-project cwd and avoid duplicate module state.

### Session context

The relevant implementation plan is `docs/superpowers/plans/2026-09-13-installation-and-updates.md`. Verification ran on Windows with Python 3 and the installed Claude/Codex binaries available. Official Claude marketplace and OpenAI Codex subagent documentation informed the command and schema corrections.

### Uncertainties and risks

The plugin route and standalone skill route can create duplicate Claude registrations if users combine them; the README explicitly tells users to choose one. Remote `npx skills update` behavior depends on the original source recorded by that CLI, so local checkout updates are documented as explicit reinstallation.

## Special instructions for next reader

If the Codex custom-agent schema changes, update the generator, generated TOML, requirement, docs, and parser regression together.
