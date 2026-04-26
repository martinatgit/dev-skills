# Resolve — archive a TODO with closure notes

Marks a TODO as resolved, wont-fix, or discarded, and migrates it to `archive/`.

## Inputs

- TODO id (required).
- Resolution type: `resolved | wont-fix | discarded`.
  - `resolved` — the work is done.
  - `wont-fix` — explicit decision not to do it (record reason).
  - `discarded` — no longer relevant, rotted, or duplicate of another TODO (record which one).
- Resolution notes: at minimum a one-paragraph closure. For `resolved`, include the commit SHA, PR number, spec revision, or diary node that carries the work.

## Step 1 — locate the file

Search `inbox/`, `active/`, `blocked/`, `deferred/` for `TODO-<id>-*.md`. Refuse if found in `archive/` already (ambiguous intent).

## Step 2 — update frontmatter

- `status: resolved | wont-fix | discarded` (match the resolution type).
- `updated: <today>`.
- Add `resolved-at: <today>` and `resolved-in: <commit/PR/spec-section/diary-node reference>`.
- Leave `expires` as-is (historical record).

## Step 3 — fill Resolution notes section

Append to the body (do not overwrite earlier sections):
```markdown
## Resolution notes

- **Resolved on:** 2026-04-16
- **Resolution type:** resolved
- **Resolved in:** commit a1b2c3d / PR #142 / doc/requirements/aiqeung-core/v7.3-spec.md §4.2.1
- **Closure:** <one paragraph — what was actually done, any surprises, any follow-ups>
- **Follow-ups (if any):** TODO-20260418-0002 (captured during this resolution)
```

## Step 4 — update cross-links

For each TODO id in `blocks[]`:
- Open the blocked TODO, remove this id from its `blocked-by[]`.
- If the blocked TODO's `blocked-by[]` is now empty and status is `blocked`, move it from `blocked/` to `active/` and update its status to `open`. Notify the user.

For each TODO id in `related[]`:
- Open the related TODO and add a reference in its body (Summary section or Open questions) if the resolution changes the picture: "Related TODO-X resolved on <date> via <ref>."

## Step 5 — migrate to archive/

Move the file from its current folder to `doc/TODOs/archive/`. Keep filename and id.

## Step 6 — update the index

Rewrite the row in `doc/TODOs/index.md` with the new status. Do not remove the row — archive TODOs remain visible in the index for retrospectives.

## Step 7 — link to diary (optional but recommended)

If the resolution involved meaningful engineering decisions, prompt the user: "This resolution may merit a developer-diary update. Run `developer-diary update`?" Do not auto-invoke.

## Step 8 — report

```
Resolved TODO-20260410-0003 (spec-update) → doc/TODOs/archive/
  resolved-in: commit a1b2c3d — "docs(aiqeung-core): document snake_case convention for place names"
  unblocked: 1 TODO (TODO-20260411-0005 moved to active/)
  cross-links updated: 2
```

## Red flags

- Resolving without a `resolved-in` reference (commit/PR/spec/diary). Closure must be verifiable.
- `wont-fix` with no rationale. Future engineers must understand the decision.
- `discarded` without identifying which TODO superseded it (if any).
- Silently dropping `blocks[]` cross-links. Cascading unblocks are a feature — surface them.
