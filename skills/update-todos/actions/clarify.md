# Clarify — promote an inbox TODO to `active/`

The GTD "clarify" step. Converts a raw capture into a fully-articulated atomic note suitable for another engineer to action. This is the phase where the LLM is allowed to do synthesis work; `capture` is intentionally restricted.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all` and use the resolved `<root_dir>` and `<default_expiry_days>` for every read and write below. If `root_dir` is empty, follow the first-use flow in SKILL.md before continuing.

## When to run

- Explicitly requested: `update-todos clarify TODO-20260416-0003` (or similar identifier).
- Proactively in `review` mode when the inbox has ≥5 items.
- Before invoking `writing-plans` or `brainstorming` on a TODO.

## Inputs

- TODO id (from filename or frontmatter).
- Optional user-supplied additional context.

## Iron rule

**No promotion without ≥1 related link.** A TODO with zero inbound and zero outbound links is an orphan — the Zettelkasten anti-pattern. If no link candidate exists, ask the user or cancel promotion.

## Step 1 — read the inbox file

Load the full file. Parse frontmatter and body. Verify it is under `<root_dir>/inbox/` (reject if already elsewhere).

## Step 2 — enrich frontmatter

Add or verify:
- `updated: <today>`
- `priority: low | medium | high` — if unclear, ask user; do not invent.
- `effort: small | medium | large | unknown`
- `scope: project | area | resource` (PARA):
  - `project` — defined outcome with deadline (e.g. "Ship release X by Y date").
  - `area` — ongoing responsibility without end (e.g. "Test coverage", "Code quality").
  - `resource` — reference material of enduring interest (e.g. "Encoding patterns").
- `tags: [...]` — ≥2 tags recommended. Use kebab-case. Include subsystem names, layer or component names, and concern types (`naming-convention`, `soundness`, `performance`).
- `expires: <today + N days>` — forced-triage date. Default N by discovered-by:
  - `discovered-by: claude` (or any LLM agent) → **N = 30 days**. LLM captures tend to over-trigger; shorter horizon forces earlier triage. (Failure mode documented in multiple Claude Code / Cursor memory systems: inbox bloats within weeks.)
  - `discovered-by: <a human name>` → **N = `<default_expiry_days>` days** (default `90`). Humans filter more; longer horizon is fine.
  - User may override.
- `very-next-action: <one imperative sentence>` — what is the literal next physical action? Allen's core test: it must be **physical and visible** — a concrete verb that produces an artefact. Examples that PASS: "Read §4.2.1 of requirements.md", "Write failing test for empty-firing case", "Ask <owner> whether the rule applies here", "Draft the snake_case subsection of §4.2.1". Examples that FAIL and must be rewritten: "Think about X", "Consider whether Y", "Figure out Z", "Look into W", "Investigate the tradeoffs of V". These verbs signal undefined work and are the #1 cause of GTD inbox rot (widely documented in GTD forums and Allen 2015). If you cannot articulate a physical next action, the TODO is not ready to leave `inbox/` — the concern is underspecified. Either ask the user to clarify, or set `next-step: decide` and list the open decision. This field is load-bearing — the whole GTD system hinges on it.
- `related: [...]` — at least one entry. Candidates to propose:
  - Other TODOs citing overlapping files or the same component.
  - Developer-diary nodes for the subsystem (run `Grep` over the project's diary root for the subsystem name).
  - Spec sections in the project's requirements/spec docs.
  - Project FAQ or knowledge-base entries.
  Refuse to proceed if none found — ask the user to name one.
- `blocks: [...]` and `blocked-by: [...]` — optional; fill if evident.

## Step 3 — write body sections

Use `resources/active-entry.md.tpl` as skeleton. Fill each section with substance (not filler):

- **Summary** (≤3 sentences) — the TODO stated crisply. If the discovery-context rambles, distil it here.
- **Problem / opportunity** — what goes wrong if we do nothing? Where is the asymmetry, gap, or violation? Cite evidence. Include code snippets or spec excerpts where they clarify. Ground claims.
- **Rationale for deferral** — why not fix this now? ("Out of scope of current task", "blocks larger refactor not yet planned", "needs product-owner decision", "spec must be updated first"). If you cannot articulate a deferral rationale, the TODO should probably be actioned now — tell the user.
- **Proposed approach(es)** — sketch one or more directions. Name alternatives where they exist. This is NOT a plan — a plan belongs to a planning skill (e.g. `superpowers:writing-plans`) at action time. This is a trailhead.
- **Acceptance criteria** — how will we know this TODO is done? A passing test, a spec section added, a naming convention documented in a style guide, a product-owner decision recorded in the diary. Concrete and verifiable.
- **Open questions** — what genuinely remains undecided? Each question SHOULD have a hypothesised answer or a decision owner.

Keep Discovery context and Required references from the inbox file verbatim. Do not rewrite them — they are the timestamped record.

## Step 4 — move the file

Move from `<root_dir>/inbox/` to `<root_dir>/active/`. Keep the same filename. Do NOT change the id.

## Step 5 — update cross-references

For each entry in `related`, `blocks`, `blocked-by`:
- If it points to another TODO, open that TODO's file and ensure the reverse link is present (`blocks` ↔ `blocked-by`, `related` is symmetric). Add if missing.
- If it points to a diary node, remind the user (textual output): "consider adding `related-todos: [this id]` to the diary node's frontmatter."
- If it points to a spec section, the link is one-way (specs do not link back).

## Step 6 — update the index

Update the row in `<root_dir>/index.md` — status column changes from `inbox` to `open`, new columns get populated (priority, expires, very-next-action summary).

## Step 7 — report

```
Clarified TODO-20260416-0003 → <root_dir>/active/
  next-step: spec-update | priority: medium | scope: area | expires: 2026-07-15
  related: [TODO-20260410-0003, R.6.3.2 in developer-diary]
  very-next-action: Add §4.2.1 to requirements.md documenting the snake_case naming convention.
```

## Red flags

- Promoting a TODO with no `related` links. Reject.
- Fabricating a Rationale for deferral when the TODO is actually in-scope right now. The user should be told to just do the work.
- Inventing Acceptance criteria you cannot verify. Ask the user what "done" looks like.
- Overwriting Discovery context. It is historical record; preserve it verbatim.
- Assigning `priority: high` to everything. High = must be resolved before next release.
- Accepting a `very-next-action` that starts with "think", "consider", "figure out", "look into", "investigate the tradeoffs". These are not actions. Rewrite or reject.
