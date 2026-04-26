# Import — migrate legacy `doc/martin-TODOs.md` into atomic files

One-shot migration. Runs once per legacy list. After a clean import, the legacy file should be deleted or renamed to `doc/martin-TODOs.archived.md` so it is not re-imported.

## Inputs

- Source file (default `doc/martin-TODOs.md`).
- Optional `--dry-run` flag that shows what would be created without writing.

## Step 1 — parse

The legacy file is a flat bullet list with inconsistent structure. Split on top-level bullets (`^- ` or `^* ` at column 0). Each bullet is one candidate TODO. Sub-bullets are context for that TODO.

Ignore empty bullets, headings, and horizontal rules.

## Step 2 — for each candidate

Construct a capture with these rules:

- `title` — first line of the bullet (truncate to 12 words, preserve meaning).
- `discovery-context` — the full bullet text and all its sub-bullets, verbatim. Prefix with "Imported from legacy doc/martin-TODOs.md on <today>; original capture context not preserved."
- `references[]` — scan the bullet text for file paths, spec section references, and commit hashes; populate. If none found, leave empty and add a note: "No explicit references in legacy entry — rehydration may require archaeology."
- `next-step` — infer from bullet text keywords:
  - "specify", "spec", "document" → `spec-update`
  - "implement", "add", "build" → `implementation`
  - "test" → `test`
  - "investigate", "research", "explore", "ideate" → `investigate`
  - "refactor", "rename", "clean up" → `refactor`
  - "decide", "review" (with human in loop) → `decide`
  - "reproduce", "bug" → `reproduce`
  - Ambiguous → `decide` (let the user sort it out at clarify time).
- `status: inbox` — every imported TODO starts in inbox, never active. User must run `clarify` to promote.
- `discovered-by: martin` (conservative — the legacy file is Martin's notes).
- `discovered-in-task: "Legacy TODO list migration"`.

## Step 3 — dedup against each other

As you generate TODOs, run dedup (per `capture.md`) between new TODOs as well as against any existing `doc/TODOs/**/*.md`. Near-duplicates within the legacy list (common, since the list grew organically) should be merged, not replicated.

When merging legacy-to-legacy, concatenate discovery-context sections with a horizontal rule and a note: "Merged from two legacy bullets."

## Step 4 — write

Create one `doc/TODOs/inbox/TODO-YYYYMMDD-NNNN-<slug>.md` per deduplicated candidate. Use sequential IDs for the import batch — consumer can tell they came from the same run by date.

## Step 5 — handle unparseable content

Some bullets are verbose code fragments or reasoning snippets (see existing `doc/martin-TODOs.md` for examples — the Prolog/Petri nets discussion). These are NOT TODOs, they are notes. Do NOT create TODO files for them.

Instead, extract them into a single inbox TODO using the standard filename convention — `TODO-YYYYMMDD-NNNN-legacy-notes-unparsed.md` (counter follows the same rule as every other capture). Set `next-step: diary-update` and discovery-context = "Legacy notes not structured as action items; kept for archival. Consider migrating to developer-diary."

## Step 6 — report dry-run diff

```
Import summary (dry-run):
  Legacy bullets parsed: 24
  TODOs to create: 18 (6 deduped against each other)
  Unparsed notes bundle: 1
  Candidates surfacing to dedup review: 3 (matched existing TODOs)
Proceed with write? (y/n)
```

After write, invoke `review` automatically to run the first forced-triage pass and generate the index.

## Step 7 — preserve the legacy file

Do NOT delete `doc/martin-TODOs.md`. Rename to `doc/martin-TODOs.archived.md` and add a top-of-file note: "Imported to doc/TODOs/ on <date>. Do not edit. See doc/TODOs/ for live TODO system." This preserves Martin's original record for provenance.

## Red flags

- Auto-classifying `next-step` on ambiguous bullets without surfacing to user. Wrong classification propagates and is painful to undo. When unsure: `decide`.
- Losing sub-bullet context. Every sub-bullet is verbatim discovery-context.
- Creating one TODO per sub-bullet. Sub-bullets are children of the parent idea — one parent TODO with rich context is correct.
- Forgetting to run dedup. The legacy list has at least 3 near-duplicates in the current state.
