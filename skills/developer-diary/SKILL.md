---
name: developer-diary
description: Persistent engineering knowledge across sessions. Maintains a hierarchical project diary that captures decisions, reasoning, alternatives considered, debugging stories, and lessons learned — the colleague-handoff context that is otherwise lost between sessions and engineers. Invoke with `read` (before design or implementation work, to load relevant context), `update` (after meaningful work, while context is fresh), or `review` (occasionally, to repair structural drift). Use whenever the user mentions "developer diary", "engineering notebook", "session notes", "what did we do last time", "carry over context", or asks you to load or write project history. Use this even if phrased casually like "remind me where we left off" or "write down what we just did". Do not use for ephemeral chat memory or for action-item tracking — use `update-todos` for the latter.
---

# Developer Diary

The developer diary is a hierarchical, project-local notebook of durable engineering knowledge. Each node is a markdown file that captures not only what was done, but how it was thought about, what alternatives were considered, what surprised the engineer, and what the next reader needs to watch out for.

You maintain it as your personal engineering notebook — the place where you write down everything a trusted colleague needs to know to continue your work. You write like a conscientious engineer clocking off for the day: reasoning traces, doubts, "aha" moments, things that feel fragile, gut feelings about risk.

You are keenly aware that your context window is limited and the next engineer reading your notes starts with zero context. You write with enough richness that reading a diary node feels like getting a thorough handoff, not like reading a change log.

**The quality bar.** If a new LLM reads your diary entry and still needs to read every source file and spec section you referenced to understand the decisions and trade-offs, your entry is too sparse. The diary should transfer understanding, not just facts.

## Inputs

The skill is invoked as:

```
/developer-diary [read | update | review]
```

- `read` — invoke before design/implementation work, to selectively load relevant context.
- `update` — invoke after completing meaningful work, while context is still fresh.
- `review` — invoke occasionally, to repair the diary's structure (orphan refs, parent/child duplication, stale cross-links).

If no mode is supplied or the value is unrecognised, ask the user which mode to use.

## Configuration

Resolution order (first match wins):

1. Environment variable `DEVELOPER_DIARY_<UPPERCASE_KEY>` (e.g. `DEVELOPER_DIARY_ROOT_DIR`).
2. **Project-local** config at `<project_root>/.developer-diary/config.yaml`.
3. **User-level** config at `~/.config/developer-diary/config.yaml` — applies to non-path keys only (e.g. `node_token_limit`). The `root_dir` is project-bound and is never read from this layer.
4. Built-in default (for non-path keys only).

Path-typed keys (`root_dir`, `feature_routing_file`) are project-only by design: the diary is a per-project artefact, and a user-installed skill must not bleed one project's diary into another.

**Configure**

```sh
# Project-scope (writes <project_root>/.developer-diary/config.yaml)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --root-dir doc/developer-diary

# User defaults (e.g. for node_token_limit, applies across projects)
python3 scripts/configure.py --scope user

# Inspect resolution
python3 scripts/configure.py --print
```

**First-use flow.** If `root_dir` cannot be resolved (no env var, no project-local config), the agent must:

1. Detect the project root via `python3 scripts/find_project_root.py`. If it returns a path, suggest `<project_root>/doc/developer-diary` as the default.
2. Ask the user "Where should the developer diary live in this project? [default: <suggestion>]".
3. Persist the answer with `python3 scripts/configure.py --scope project --root-dir <answer>`.
4. Re-resolve and proceed. The prompt will not recur in this project.

If no project root is detected, refuse with the configure command and a one-line hint. Never fall back to a user-home location for `root_dir` — that would mix diaries across projects.

See [`references/config-schema.md`](references/config-schema.md) for the full schema.

## Workflow

Every invocation begins with:

**Step 0 — Resolve configuration.** Run `python3 scripts/resolve_config.py --all` and parse the `key=value` lines. Use the resolved `root_dir` for every read and write below. If `root_dir` is empty, run the first-use flow above before continuing.

After Step 0, follow the action file matching the requested mode (paths relative to this SKILL.md):

- `read`   → [`actions/read-diary.md`](actions/read-diary.md)
- `update` → [`actions/update-diary.md`](actions/update-diary.md)
- `review` → [`actions/review-diary.md`](actions/review-diary.md)

## Diary tree layout

The root node is always:

```
<root_dir>/developer-diary.md
```

Each child node is stored in a numbered child directory:

```
<root_dir>/child_1/diary-entry.md
<root_dir>/child_3/child_6/diary-entry.md
```

The hierarchy mirrors the software architecture. Higher nodes (closer to root) contain routing and abstraction. Lower nodes contain narrower implementation detail. Each node abstracts and summarises over its children, so the root contains an overarching summary of the entire project.

## Node-writing principles

### Content richness (highest priority)

- **"Notes and commentary" is the most important section.** It captures the internal monologue — decision reasoning, session context, uncertainties, observations. Never leave it empty. Structure it with subsections: Decision journal, Session context, Uncertainties and risks.
- **Design decisions must include alternatives.** Never write "We chose X" without naming at least one alternative and explaining why X won.
- **Problems must include the diagnosis story.** Never write "No problems encountered" unless the work was truly trivial. Describe what you debugged, even if the fix was quick.
- **Progress entries must include WHY, not just WHAT.** "Implemented X because Y; the key insight was Z" — not just "Implemented X."
- Include what was referenced during the session: spec sections, source files, test results, error messages, other diary nodes read.
- Include confidence assessments: what feels solid, what feels fragile, what assumptions might be wrong.
- Write durable engineering knowledge, not chat transcripts — but durable knowledge includes reasoning, not just conclusions.

### Structure and scope

- Keep each node focused on a single architectural concern.
- Assume the reader already understands the nodes on the direct path from root to the current node.
- Do not duplicate large amounts of information from parent or sibling nodes.
- Prefer a single source of truth. Use `Relevant related diary nodes` for cross-references instead of duplicating content.
- Reference relevant knowledge that is in the context window when writing, so future readers can locate the source.
- Put immediate handoff instructions in `Special instructions for next reader`. Remove or migrate them once consumed.
- Keep markdown easy to scan and navigate.

## Size limit and splitting

A single `diary-entry.md` should remain below the configured `node_token_limit` (default `4000`).

If a node would exceed that size:

1. Split it into independent child concerns.
2. Keep the parent as an abstraction and routing layer.
3. Move detailed content into new child nodes.
4. Add the children to the parent `Child nodes` table.
5. Update peer scoping where needed.

Prefer low coupling between peers. Avoid unnecessary cross-links between unrelated branches.

## Quick deep-access reference

At top level, maintain a routing index at the path resolved from `feature_routing_file` (default `<root_dir>/feature-routing.md`).

The file contains a tabular index of identifiable units of the architecture (packages, modules, components, functions, features, etc.):

```md
| Feature name | Index | Description |
| --- | --- | --- |
| HM Type System | R.1.2.1 | `MonoType`, `PolyType`, `Linearity`; Algorithm W (Milner 1978) inference; advisory, non-blocking |
```

When invoked in `update` mode, the skill also updates this table accordingly.

## Final behaviour

Treat the diary as shared engineering memory:

- read it before meaningful implementation or design work,
- update it after meaningful implementation or design work,
- review and repair it when explicitly asked or when a concrete inconsistency is discovered.

## References

- [`references/config-schema.md`](references/config-schema.md) — full configuration schema and CLI usage.
- [`actions/read-diary.md`](actions/read-diary.md) — read-mode procedure.
- [`actions/update-diary.md`](actions/update-diary.md) — update-mode procedure.
- [`actions/review-diary.md`](actions/review-diary.md) — review-mode procedure.
