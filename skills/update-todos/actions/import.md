# Import — migrate a flat markdown bullet list of TODOs into atomic files

One-shot migration. Runs once per source file. After a clean import, the source file is renamed to `<source>.archived.md` so it is not re-imported.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all` and use the resolved `<root_dir>` for every read and write below. If `root_dir` is empty, follow the first-use flow in SKILL.md before continuing.

## Inputs

- `--from <path>` (required) — source file to import. No default; the invocation must specify it.
- `--discovered-by <name>` (optional, default `imported`) — populates the `discovered-by` field of each generated TODO.
- `--dry-run` (optional) — shows what would be created without writing.

## Step 1 — parse

The source file is a flat bullet list with inconsistent structure. Split on top-level bullets (`^- ` or `^* ` at column 0). Each bullet is one candidate TODO. Sub-bullets are context for that TODO.

Ignore empty bullets, headings, and horizontal rules.

## Step 2 — for each candidate

Construct a capture with these rules:

- `title` — first line of the bullet (truncate to 12 words, preserve meaning).
- `discovery-context` — the full bullet text and all its sub-bullets, verbatim. Prefix with "Imported from `<source-path>` on <today>; original capture context not preserved."
- `references[]` — scan the bullet text for file paths, spec section references, and commit hashes; populate. If none found, leave empty and add a note: "No explicit references in source entry — rehydration may require archaeology."
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
- `discovered-by` — value supplied via `--discovered-by`, default `imported`.
- `discovered-in-task: "Legacy TODO list migration from <source-path>"`.

## Step 3 — dedup against each other

As you generate TODOs, run dedup (per `capture.md`) between new TODOs as well as against any existing `<root_dir>/**/*.md`. Near-duplicates within the source list (common, since flat lists grow organically) should be merged, not replicated.

When merging source-to-source, concatenate discovery-context sections with a horizontal rule and a note: "Merged from two source bullets."

## Step 4 — write

Create one `<root_dir>/inbox/TODO-YYYYMMDD-NNNN-<slug>.md` per deduplicated candidate. Use sequential IDs for the import batch — consumers can tell they came from the same run by date.

## Step 5 — handle unparseable content

Some bullets are verbose code fragments, design discussions, or reasoning snippets — for example: long technical analyses or design discussions embedded in the source file. These are NOT TODOs, they are notes. Do NOT create TODO files for them.

Instead, extract them into a single inbox TODO using the standard filename convention — `TODO-YYYYMMDD-NNNN-legacy-notes-unparsed.md` (counter follows the same rule as every other capture). Set `next-step: diary-update` and discovery-context = "Source notes not structured as action items; kept for archival. Consider migrating to developer-diary."

## Step 6 — report dry-run diff

```
Import summary (dry-run):
  Source bullets parsed: 24
  TODOs to create: 18 (6 deduped against each other)
  Unparsed notes bundle: 1
  Candidates surfacing to dedup review: 3 (matched existing TODOs)
Proceed with write? (y/n)
```

After write, invoke `review` automatically to run the first forced-triage pass and generate the index.

## Step 7 — preserve the source file

Do NOT delete the source file. Rename to `<source>.archived.md` and add a top-of-file note: "Imported to `<root_dir>` on <date>. Do not edit. See `<root_dir>` for the live TODO system." This preserves the original record for provenance.

## Red flags

- Auto-classifying `next-step` on ambiguous bullets without surfacing to user. Wrong classification propagates and is painful to undo. When unsure: `decide`.
- Losing sub-bullet context. Every sub-bullet is verbatim discovery-context.
- Creating one TODO per sub-bullet. Sub-bullets are children of the parent idea — one parent TODO with rich context is correct.
- Forgetting to run dedup. Long-running source lists typically have several near-duplicates.
