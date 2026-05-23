# `terminology_file` — format specification

The skill targets a single markdown file (default `doc/terminology.md`). This document specifies the exact format and what each mode is allowed to touch.

## Top-level structure

The file has four parts, in this order:

1. The page heading: `# Project Terminology`.
2. A `Status` blockquote.
3. A `## Motivation` prose section.
4. A `## Glossary` section containing exactly one markdown table.

Anything outside these four parts is unexpected. `review` flags it; no mode rewrites it.

## Status blockquote

```md
> **Status.** Living document. No fixed version. The glossary records the project's
> *current* shared vocabulary; where it disagrees with current code or specs, that is
> a discrepancy to flag (via `terminology review` or a TODO), not authority to follow.
```

The blockquote sits immediately after the page heading. Its purpose is to make explicit that the glossary is descriptive, not authoritative — when reality and the glossary disagree, the disagreement is a review finding, not a binding rule.

`review` may flag this block as stale (e.g. if it has been edited to say something contradictory), but no mode rewrites it.

## Motivation prose

Two to four short paragraphs, in the project's voice. The skill ships a seed paragraph set in `SKILL.md` § *Glossary file structure*. On first creation that seed is written verbatim; the user is expected to tighten and re-voice it during ordinary work.

The prose must, in some order, communicate:

- That ordinary English words carry narrow technical meanings here, and the glossary records those meanings.
- That consistent terminology is a precondition for reliable spec-vs-implementation review.
- That contributors should propose new entries rather than coin synonyms in passing.
- That the `Disambiguate from` column is intentionally sparse and populated only for genuinely confusable neighbours.

`review` checks for these points only loosely — if the prose has been replaced with something that visibly contradicts them, that is a finding; otherwise leave it alone.

`note`, `get`, and `validate` never touch the prose.

## Glossary table

Exact header, in this order:

```md
| Term | Abbreviations | Definition | Comments on use | Disambiguate from |
|---|---|---|---|---|
```

The header line and the alignment line are written once on file creation. Subsequent `note` invocations leave them untouched.

### Column semantics

| Column | Required | Content |
|---|---|---|
| `Term` | yes | The canonical name as it should appear in code, prose, and review comments. Capitalisation is significant — match how the project actually writes it. |
| `Abbreviations` | no | Comma-separated. Only abbreviations actually used in this project. Do not invent. |
| `Definition` | yes | One sentence stating what the thing *is*. Declarative, in the project's voice. |
| `Comments on use` | no | Short, prescriptive, opinionated guidance on correct usage — capitalisation rules, scope of applicability, when to abbreviate, when not to use the term, etc. May reference other glossary terms by name. |
| `Disambiguate from` | no | Comma-separated `Term` values from this glossary. Populate only for genuinely confusable neighbours. |

### Sort order

Rows are sorted alphabetically by `Term`, case-insensitive, with stable tie-breaking by the row's original casing as it appears in the file. `note` re-sorts on every write; the parse helper is the single writer that performs the sort.

### Cell escaping

`note` and the parse helper handle escaping for the user. Authors editing the file by hand should follow GFM table rules:

- Replace `|` inside a cell with `\|`.
- Replace embedded newlines with `<br>` (the renderer will display them as line breaks; the parser preserves them).

### What the skill does NOT enforce

- Cell length. A short, precise definition is usually right; an entry that genuinely needs two sentences is fine. The skill does not truncate.
- Cross-references. `Disambiguate from` is the only structurally-tracked cross-reference. Free-prose mentions of other terms inside `Comments on use` are allowed and intentional, and `review` validates them lightly under the Drift check.
- Linking to source. Definitions may but need not reference code symbols, file paths, or spec sections. The Drift check verifies any such references still resolve.

## What each mode is allowed to touch

| Mode | Reads | Writes |
|---|---|---|
| `note` | Whole file (preserves non-table content verbatim) | Glossary table rows only |
| `get` | Glossary table | Nothing |
| `review` | Whole file | Nothing |
| `validate` | Glossary table, external sources | Nothing |

`note` is the only mode that writes. Prose is the user's responsibility.

## Parse-helper invariants

`scripts/parse_glossary.py` is the single writer. Invariants it guarantees:

- The motivation prose, status blockquote, and any unexpected non-table content are preserved verbatim across reads and writes.
- The table header and alignment row are not rewritten unless they are absent.
- After every write, rows are alphabetically sorted by `Term` (case-insensitive); duplicates are detected by `Term` (case-insensitive) and by abbreviation overlap and are merged rather than duplicated.
- Pipe characters and embedded newlines in user input are escaped on write and unescaped on read.

If any invariant is violated by a third-party edit (someone hand-edited the file in a way the helper cannot parse), the helper exits non-zero with the diagnostic on stderr and never writes a partial file.
