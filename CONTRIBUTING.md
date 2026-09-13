# Contributing

Thanks for contributing. A few conventions this repo enforces.

## Prerequisites

- **Python 3.12 or newer.** Verify with `python3 --version`. `evals/run.py` and three test files (`tests/test_check_reference_drift.py`, `tests/test_smoke_end_to_end.py`, `tests/test_evals_agent_checks.py`) use un-deferred `list[str]` / `Path | None` annotations and fail at import under older interpreters. Skill scripts under `skills/*/scripts/` defer annotation evaluation via `from __future__ import annotations` and would still import on older Pythons, but 3.12 is the floor for the whole repo regardless.

## Universal first

Every skill in this repo must work on at least Claude Code and Codex CLI without modification. Skills with tool-specific quirks go in a fork, not here.

Concretely:

- Frontmatter contains only `name` and `description`. Nothing else.
- Scripts use POSIX bash or Python 3.12 stdlib. No Bun, no Node version pins, no `uv`.
- The skill does not modify files outside its own directory or `~/.config/<skill-name>/` during any operation.
- No install scripts for a skill. Configuration is lazy — read from `~/.config/<skill-name>/config.yaml` on first use, and prompt via `scripts/configure.py` if missing. (`scripts/install-agents.py` at the repo root installs the separate `agents/` layer, not a skill, and is not an exception to this rule for skills.)

The [portability checklist](docs/portability-checklist.md) is the authoritative list.

## Workflow

1. Fork and branch.
2. Copy `template/SKILL.md` to `skills/<your-skill-name>/SKILL.md`.
3. Write the skill. Keep SKILL.md under 500 lines; push detail into `references/`.
4. Test on at least two agents. Record results in `evals/fixtures/<your-skill-name>/prompts.json`, following the [fixture schema](docs/portability-checklist.md#fixture-schema).
5. Walk the [portability checklist](docs/portability-checklist.md). Every item must pass.
6. Update the skills table in `README.md` and the plugins list in `.claude-plugin/marketplace.json`.
7. Open a PR.

## Triggering reliability

The `description` field in SKILL.md frontmatter is the primary trigger mechanism. It must:

- State what the skill does.
- List concrete phrases and contexts that should trigger it.
- Err toward "pushy" language. Agents under-trigger by default.
- Include "use this even if the user phrases it casually" or similar for common informal prompts.

If your skill's trigger rate is below ~80% on the canonical test prompts in `evals/fixtures/`, rewrite the description before submitting.

## Review criteria

PRs are reviewed against:

1. Does it follow the portability checklist?
2. Does the skill trigger reliably on its test prompts?
3. Is SKILL.md focused (one job, under 500 lines)?
4. Does it fail loudly and with actionable errors when config or inputs are missing?
5. Does it avoid modifying state outside the skill's config directory?

Partial coverage is fine for a first submission — reviewers will flag what's missing.
