# `define` — capture or update one term

Triggered by `/define-term <free-form description>` or `terminology define <…>`.

Idempotent: re-noting an existing term updates the row rather than duplicating it.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all`. Use the resolved `terminology_file` for every read and write below. If `terminology_file` is empty, run the first-use flow in `SKILL.md` before continuing.

## 1. Parse the free-form input

Extract these five fields from the user's text. Use natural-language understanding; the user will not always present them in order or with labels.

- **Term** — the canonical name. Preserve the user's intended capitalisation. If the user clearly wrote the term in running prose ("the *run* is the persisted artefact"), normalise to the capitalisation they actually want it to have in the glossary, not the casing that happens to appear after a sentence-initial position. Ask if unclear.
- **Abbreviations** — comma-separated. Empty if the user did not mention any. Do not invent.
- **Definition** — one sentence stating what the thing *is*. Rephrase the user's text into a single, declarative sentence. Strip filler.
- **Comments on use** — short, prescriptive, opinionated. May be empty. Capture rules about capitalisation, scope, when to abbreviate, when not to use the term, etc.
- **Disambiguate from** — a comma-separated list of other glossary terms. Only fill if the user explicitly named a confusable neighbour, or if you can see one in the current glossary that is genuinely easy to mix up. **Do not invent disambiguations.**

If the user's input is so loose that one of `Term` or `Definition` cannot be filled with confidence, ask **exactly one** clarifying question via `AskUserQuestion` covering all uncertain load-bearing fields. Do not ask multiple sequential questions.

## 2. Load the existing glossary

Read `terminology_file`. If it does not exist, create it from the scaffold in `SKILL.md` § *Glossary file structure* and proceed. The scaffold's motivation prose is seed content; do not edit it during a `define` invocation — `review` will flag it if it grows stale.

Parse the table using `python3 scripts/parse_glossary.py --read <terminology_file>`. The helper returns one row per JSON object with the five columns plus the source line number.

## 3. Decide: insert or update

Match by case-insensitive `Term` equality, then by abbreviation match (an existing row whose `Abbreviations` list contains the new term, or vice versa). Two outcomes:

- **No match.** Insert a new row in alphabetical position. Done.
- **Match.** Diff the parsed fields against the existing row, field by field:
    - Identical fields are kept as-is.
    - Strictly-additive changes (the new input adds an abbreviation, adds a `Disambiguate from` reference, refines `Comments on use` with extra prose) are merged.
    - Conflicting changes (the new `Definition` says something incompatible with the existing one; the new `Comments on use` contradicts the existing rule) are surfaced to the user with the existing row and the proposed row shown side-by-side. The user decides whether to overwrite, keep, or hand-edit.

Never silently overwrite a `Definition` or `Comments on use` field that already has content.

## 4. Write the row

Use `python3 scripts/parse_glossary.py --upsert <terminology_file> --row <json>` to perform the insert or update. The helper:

- Preserves the existing motivation prose and any non-table content verbatim.
- Re-sorts the table alphabetically by `Term`, case-insensitive, with the row's original casing preserved.
- Escapes pipe characters and embedded newlines inside cells per GFM table rules.

Do not hand-edit the file with a text-editor tool in `define` mode. The parse-helper is the single writer.

## 5. Output

Emit exactly:

1. One block titled either `Inserted` or `Updated`, showing the final row in markdown table form.
2. For an `Updated` row, also show the diff of changed cells (old → new).
3. One line: the absolute path to `terminology_file` and the row's new line number.

If the user was asked a clarifying question, the answer they gave was already incorporated into the row. Do not re-narrate the question.

## Failure modes

- **Parse helper exits non-zero.** Surface its stderr verbatim and stop. Do not attempt a fallback hand-edit.
- **Table is malformed (missing header, wrong columns).** Refuse with a one-line diagnosis and suggest `terminology review` to repair. Do not auto-repair from `define`.
- **The user's input is purely conversational ("what's the term for the thing that…")**. This is not a `define` invocation; it is a `get` invocation. Switch modes and proceed, or ask which mode the user wants.
