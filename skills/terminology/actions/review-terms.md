# `review` — audit the glossary for drift, contradiction, overlap, and bloat

Triggered by `terminology review [--validate]`.

Read-only by default. Produces a structured report. The user decides what to act on. Never silently rewrites the file.

If `--validate` was passed, run this procedure end-to-end, then run [`validate-terms.md`](validate-terms.md) on standards-derived entries and append its output as the report's `Validation` section.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all`. If `terminology_file` is empty, run the first-use flow in `SKILL.md` before continuing. If the file does not exist, refuse with a one-line message — there is nothing to review.

## 1. Parse the glossary

Use `python3 scripts/parse_glossary.py --read <terminology_file>` to get all rows. If the helper exits non-zero, surface its stderr verbatim — a malformed table is itself a review finding, and the user must repair it by hand before the rest of the review is meaningful.

Capture three things up front:

- The full list of rows.
- The motivation prose (everything between `## Motivation` and `## Glossary`).
- The status blockquote at the top of the file.

## 2. Drift check

For every entry, scan `Definition` and `Comments on use` for tokens that look like code symbols, file paths, type names, or spec section identifiers. Conservatively: any `CamelCaseToken`, `snake_case_token`, `path/segment.ext`, or `§X.Y` style reference.

For each such token:

1. Search the repository for it (use a fast portable search — `git grep` if available, otherwise the host agent's grep tool).
2. If nothing is found, flag the entry under **Drift**. Cite the missing token, the row's `Term`, and the file/section the row appears in.

Do not auto-rewrite. Report only. A token might be missing because the code was renamed, removed, or never landed — the user is the one who knows which.

## 3. Contradiction check

Pairwise across rows, look for definitions that are mutually inconsistent. Concretely:

- Two rows whose `Definition` fields describe the same artefact with incompatible properties.
- Two rows whose `Comments on use` give incompatible capitalisation or abbreviation rules.
- A `Disambiguate from` graph that contains contradictions: row A says "disambiguate from B" while row B's definition is *exactly* the same concept (i.e. the disambiguation pointer is bogus), or a cycle of `Disambiguate from` references where the cycle implies all participants are mutually distinct *and* mutually equivalent.

Flag each pair under **Contradictions** with both rows quoted and a one-sentence diagnosis. Do not pick a winner.

## 4. Overlap / near-paraphrase check

Pairwise across rows, look for definitions that are near-paraphrases — different `Term` values whose `Definition` and `Comments on use` describe substantially the same concept.

Heuristic: if you could swap the two `Definition` cells without changing what the rows mean, they overlap.

For each overlapping pair, flag under **Overlap** with both rows and a one-line recommendation (merge into one entry; or keep both and add a cross-link in `Disambiguate from`). The user decides.

## 5. Inferability check

For every entry, ask: *could a reader infer this row's content from a one-line web search, with no project-specific knowledge?*

If yes, the entry is bloat. Flag under **Inferability** with the row and a one-line justification. Examples that fail this check: `array`, `database`, `git`, `REST`, `JSON` (unless the project gives any of these a non-standard meaning, which the row's `Comments on use` should make obvious — if it does, the entry passes).

Be honest. An entry that looks project-specific because of branding (e.g. `MyCompanyJSON`) but is actually just `JSON` is still bloat.

## 6. Stale-disambiguation check

For every row that has content in `Disambiguate from`:

- Confirm every referenced term still exists in the glossary. If not, flag under **Stale-disambiguation** as a broken reference.
- Confirm the referenced term is genuinely a confusable neighbour. If the two rows are about wholly different concepts that no one would confuse, the disambiguation is noise — flag for removal.

## 7. Motivation-prose freshness

Skim the motivation prose. Flag (without quoting at length) if it:

- References tooling, code, or specs that the **Drift** check showed are gone.
- Reads as generic template prose that was never voiced for this project (i.e. it still sounds like the scaffold seed).
- Contradicts the actual contents of the table (e.g. it claims a discipline the table does not exhibit).

The skill never rewrites the prose. The user does.

## 8. Output format

Produce a single markdown report with these sections, in this order. Omit a section entirely if it has no findings.

```md
# Terminology review — <ISO date>

Source: <absolute path to terminology_file>
Entries reviewed: <N>

## Drift
- **<Term>** — `<missing token>` not found in repo. Row at line <L>.
  Suggested action: confirm whether the token was renamed, removed, or never landed.

## Contradictions
- **<Term A>** vs **<Term B>** — <one-sentence diagnosis>.

## Overlap
- **<Term A>** and **<Term B>** — near-paraphrase. Consider merging, or
  adding `Disambiguate from` cross-links.

## Inferability
- **<Term>** — generic public knowledge; no project-specific meaning evident.
  Consider removal.

## Stale-disambiguation
- **<Term>** — `Disambiguate from: <Other>` references a row that no longer exists / is not a genuine neighbour.

## Motivation prose
- <one line per finding, no long quotes>

## Validation
<populated only if invoked with --validate; see actions/validate-terms.md>
```

End the report with a one-line summary of total findings per section.

## 9. Failure modes

- **Repo search not available.** Skip the Drift section, note its absence at the top of the report, and continue. Do not silently produce a report that looks complete but isn't.
- **Glossary is empty (only the scaffold).** Emit a report with one line: "No entries to review." Do not flag the empty table as a finding.
- **Parse helper reports a malformed table.** Stop after surfacing the parse error. A malformed table makes the rest of the review unreliable.
