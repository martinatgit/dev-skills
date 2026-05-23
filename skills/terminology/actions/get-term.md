# `get` — retrieve terms in a paste-ready format

Triggered by `terminology get <term1> [term2 …] [--format row|definition-only|blockquote]`.

Read-only. Never edits the glossary.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all`. If `terminology_file` is empty, run the first-use flow in `SKILL.md` before continuing.

## 1. Parse the request

- **Terms.** One or more, space- or comma-separated. The user may pass them with or without quotes. Strip trailing punctuation.
- **Format.** One of:
    - `row` (default) — the full markdown table row, header included if more than one term is returned.
    - `definition-only` — `**<Term>** — <Definition>` on one line.
    - `blockquote` — a markdown blockquote per term, suitable for pasting into a spec or review comment, containing Term, Abbreviations (if any), Definition, and Comments on use (if any), in that order.

If the user did not specify a format, use `row`. If the user clearly wants a single inline insertion (asked for "the definition of X" in running prose), prefer `definition-only`.

## 2. Look up each term

Use `python3 scripts/parse_glossary.py --read <terminology_file>` to get all rows. For each requested term, match in this order, taking the first hit:

1. Case-insensitive exact match on `Term`.
2. Case-insensitive exact match on any entry in `Abbreviations`.
3. Fuzzy match: case-insensitive, ignoring whitespace and punctuation, with at most one character edit distance per ten characters of the term length (round down, minimum one). Do not fuzzy-match below this threshold — it produces false positives that look authoritative.

For ambiguous matches (two or more rows tie at the same match tier), present all candidates and ask the user which they meant. Do not pick silently.

## 3. Emit the requested format

### `row`

```
| Term | Abbreviations | Definition | Comments on use | Disambiguate from |
|---|---|---|---|---|
| Run | R | The persisted artefact … | Always capitalise … | |
```

Include the header once if multiple terms are returned. Omit the header when exactly one term is returned (the row alone is usually what the caller wants).

### `definition-only`

```
**Run** — The persisted artefact produced by one engine execution.
```

One line per term, in the order the user asked.

### `blockquote`

```
> **Run** *(R)* — The persisted artefact produced by one engine execution.
>
> Always capitalise *Run* when referring to the artefact. Lowercase *run* is
> acceptable only for the everyday English verb.
```

Omit the `*(abbrev)*` parenthetical if the row has no abbreviations. Omit the second paragraph if `Comments on use` is empty. Include a `Disambiguate from: <terms>` trailing line only if that column has content.

## 4. Handle unknown terms

For each requested term with no match, emit one line:

```
**<term>** — not in glossary. Suggest `/note-term <term> …` if it has a project-specific meaning.
```

Do not invent a definition. Do not draw on general knowledge. The whole point of the glossary is that it carries the project's *narrow* meaning; emitting a generic dictionary definition would teach the caller that the glossary is unreliable.

## 5. Output

Emit only the requested entries in the requested format, followed by any "not in glossary" lines. No preface, no postscript, no commentary unless an ambiguous match required a clarifying question.
