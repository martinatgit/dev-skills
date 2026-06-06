---
name: terminology
description: Curates a project's shared technical vocabulary in a single glossary file (default doc/terminology.md). Invoke with `define` to capture or update a term (triggered by /define-term <free-form term>), `get` to retrieve one or more terms in a paste-ready format, `review` to scan the glossary for drift, contradictions, semantic overlap, and easily-inferable entries, or `validate` to sanity-check standards-derived terms against their cited sources (degrades gracefully offline). Use whenever the user types /define-term, says "add a term to the glossary", "define X in this project", "what does X mean here", "fix the terminology", "the glossary is out of date", "review terminology for drift", or otherwise refers to project-specific vocabulary, naming, or definitions — even if phrased casually like "write down what we mean by X". Prefer this skill over ad-hoc edits to doc/terminology.md or to any file named glossary/vocabulary/terms; the skill enforces the table schema, prose framing, and de-duplication logic that hand-edits routinely break. Do not use for engineering decisions, design notes, or session handoff — that is `developer-diary`. Do not use for action items, deferred decisions, or TODOs — that is `update-todos`. Terminology is neither of those; it is the durable shared dictionary that makes both of those legible.
---

# Terminology

A single living glossary of the project's technical vocabulary. One markdown file, one table, one heading per term. The skill captures terms (`define`), retrieves them (`get`), audits them (`review`), and optionally sanity-checks standards-derived entries against their cited source (`validate`).

The default target is `doc/terminology.md` relative to the project root. Path is overridable via env var (`TERMINOLOGY_FILE`) and project-local config (`<project_root>/.terminology/config.yaml`). The skill never writes outside the project tree or `~/.config/terminology/`.

## What belongs in the glossary

Include:

- Terms that carry a narrow, project-specific meaning.
- Words that look ordinary but have been overloaded inside this project.
- Acronyms unique to this project or to its problem domain.
- Entities and artefacts referenced by name in code, specs, or contracts.
- Concepts whose misuse would degrade design reviews, spec reviews, or planning.

Exclude:

- Widely-known public knowledge (standard CS concepts, common framework names, generic English). If the entry could be inferred from a one-line web search, it does not belong here.
- Terms that have no project-specific meaning and are not at risk of being misused.

The exclusion rule is load-bearing. A glossary that documents `array` or `database` trains readers to ignore it, which defeats the entire point.

## Tone

Match the register of a senior engineer writing for other engineers. Definitions are precise, project-specific, and slightly opinionated about correct usage. Example: "Always capitalise *Run* when it refers to the persisted artefact; lowercase *run* is acceptable for the everyday English verb only." Never dictionary tone, never marketing tone.

## When to use

- The user typed `/define-term <text>` (or asked you to "define this term", "add this to the glossary", "use word X for the project").
- The user asked what a specific term means *in this project* and you should consult the glossary first.
- The user asked you to retrieve one or more terms for use elsewhere (commit message, spec section, review comment).
- The user asked you to review, clean up, or audit the glossary; or you noticed concrete drift while doing other work and want to surface it.

## When not to use

- The user wants engineering history, decision rationale, or session handoff context. Use [`developer-diary`](../developer-diary/SKILL.md).
- The user wants to track a deferred action item, missing test, or open question. Use [`update-todos`](../update-todos/SKILL.md).
- The user wants to look up a generic, public-knowledge term with no project-specific meaning. Answer from general knowledge; do not pollute the glossary.

## Inputs

The skill is invoked as:

```
/terminology [define | get | review | validate] [arguments]
```

Or, equivalently for the most common path, via the user-facing slash command:

```
/define-term <free-form term description>
```

Which the host agent maps to `terminology define <free-form term description>`.

Mode-specific arguments are documented in the per-mode action files (see [References](#references)).

If no mode is supplied or the value is unrecognised, ask the user which mode to use. Do not guess.

## Configuration

Resolution order (first match wins):

1. Environment variable `TERMINOLOGY_<UPPERCASE_KEY>` (notably `TERMINOLOGY_FILE` for the glossary path).
2. Project-local config at `<project_root>/.terminology/config.yaml`.
3. User-level config at `~/.config/terminology/config.yaml` — **non-path keys only**. The `terminology_file` key is project-bound by design and is never read from the user layer.
4. Built-in default (for non-path keys only).

Path-typed keys are project-only. A user-installed skill must never read one project's `terminology_file` into another project.

**Configure**

```sh
# Project-scope (writes <project_root>/.terminology/config.yaml)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --terminology-file doc/terminology.md

# User defaults (non-path keys only, e.g. validation_timeout)
python3 scripts/configure.py --scope user

# Inspect resolution
python3 scripts/configure.py --print
```

**First-use flow.** If `terminology_file` cannot be resolved (no env var, no project-local config) when a mode actually needs to read or write the file, the agent must:

1. Detect the project root via `python3 scripts/find_project_root.py`. If it returns a path, suggest `<project_root>/doc/terminology.md`.
2. Ask the user: "Where should the project's terminology live? [default: <suggestion>]".
3. Persist the answer with `python3 scripts/configure.py --scope project --terminology-file <answer>`.
4. Re-resolve and proceed. The prompt will not recur in this project.

If no project root is detected, refuse with the configure command and a one-line hint. Never fall back to a user-home location for `terminology_file` — that would mix glossaries across projects.

See [`references/config-schema.md`](references/config-schema.md) for the full schema, env-var table, and CLI surface.

## Workflow

Every invocation begins with:

**Step 0 — Resolve configuration.** Run `python3 scripts/resolve_config.py --all` and parse the `key=value` lines. Use the resolved `terminology_file` for every read and write below. If `terminology_file` is empty and the requested mode needs the file (i.e. anything other than a pure help query), run the first-use flow above before continuing.

After Step 0, follow the action file matching the requested mode (paths relative to this SKILL.md):

- `define`     → [`actions/define-term.md`](actions/define-term.md)
- `get`      → [`actions/get-term.md`](actions/get-term.md)
- `review`   → [`actions/review-terms.md`](actions/review-terms.md)
- `validate` → [`actions/validate-terms.md`](actions/validate-terms.md)

`validate` is structured as a sub-mode of `review`: a full `review` invocation may opt into validation by passing `--validate`, in which case it runs `review` end-to-end and then runs `validate` on entries that look standards-derived. Either mode may be run on its own.

## Glossary file structure

When `define` is invoked against a non-existent `terminology_file`, the skill creates the file from this exact scaffold. The skill never silently rewrites existing prose — only the table is updated programmatically.

```md
# Project Terminology

> **Status.** Living document. No fixed version. The glossary records the project's
> *current* shared vocabulary; where it disagrees with current code or specs, that is
> a discrepancy to flag (via `terminology review` or a TODO), not authority to follow.

## Motivation

<two to four short paragraphs explaining why a shared vocabulary matters for THIS
project. The seed prose below is a starting point; tighten and re-voice it during
the first real `define` invocation so it sounds like the project, not a template.>

Ordinary English words carry narrow technical meanings in this codebase. Where the
same word means something different in the wider world, the project meaning wins
inside the project — and the glossary is what makes that meaning legible.

Consistent terminology is a precondition for reliable spec-vs-implementation review.
If a reviewer and an implementer attach different meanings to the same word, the
review reports false agreement (or false disagreement) and the bug ships.

Contributors should propose new entries here rather than coin synonyms in passing.
Two names for one concept is more expensive than one slightly-wrong name. If a
term is missing, add it; if a term is wrong, fix it; if two terms have collapsed
into one, surface the collision in `review`.

The `Disambiguate from` column is intentionally sparse. Populate it only for
genuinely confusable neighbours — terms a reader is likely to actually mix up.
Filling it for every entry trains readers to ignore it.

## Glossary

| Term | Abbreviations | Definition | Comments on use | Disambiguate from |
|---|---|---|---|---|
```

Authoring rules the skill enforces on the table:

- Entries sorted alphabetically by `Term`, case-insensitive, with stable tie-breaking by the original casing.
- Empty cells are permitted and meaningful — especially in `Abbreviations`, `Comments on use`, and `Disambiguate from`. Do not invent content to fill them.
- `Term` is the canonical name as it should appear in prose and code. If the project capitalises it a specific way, that capitalisation is the entry.
- `Abbreviations` is a comma-separated list. Use only for abbreviations the project actually uses.
- `Definition` is one sentence in the project's voice. It states what the thing *is*, not how it is used.
- `Comments on use` is short, prescriptive, and opinionated about correct usage. Examples: "Always capitalise when referring to the persisted artefact"; "Reserve for the public API; the internal type is `RawX`"; "Use the abbreviation only after the term has been spelled out in the same document".
- `Disambiguate from` references another row by its `Term` value. Use only for genuinely confusable neighbours.

The motivation prose and status block are written once and edited prose-style. The skill leaves them alone except in `review` mode, where it may *report* that they look stale, but never rewrites them silently.

## Output format

Mode-specific. Detailed in each action file. Summary:

- `define` — emits a unified-diff-style summary of the row written, plus a single confirmation line. If a load-bearing field was ambiguous, asks exactly one clarifying question first.
- `get` — emits the requested entries in the caller-selected format (`row`, `definition-only`, or `blockquote`). Default is `row`.
- `review` — emits a structured report with sections: Drift, Contradictions, Overlap, Inferability, Stale-disambiguation. Never writes the file. The user decides what to act on.
- `validate` — emits a Validation section appended to the `review` report (or standalone if called alone). Each finding is one line: term, source cited, sanity-check result, confidence.

## Examples

### Example 1 — `/define-term Run is the persisted artefact for one engine execution; abbreviated R; not the verb`

`define` parses out:

- Term: `Run`
- Abbreviations: `R`
- Definition: "The persisted artefact produced by one engine execution."
- Comments on use: "Always capitalise *Run* when referring to the artefact. Lowercase *run* is acceptable only for the everyday English verb."
- Disambiguate from: *(blank — no genuinely confusable neighbour in the current glossary)*

If `doc/terminology.md` does not exist, the skill creates it from the scaffold and inserts the row. If a row already exists for `Run`, the skill diffs the new content against the existing row, merges, and surfaces any conflict to the user before committing.

### Example 2 — `get Run, Engine, Snapshot --format blockquote`

The skill emits a single markdown blockquote per term, suitable for pasting into a spec or review comment. Unknown terms produce an explicit "not in glossary" line with a one-line suggestion to `/define-term` them.

### Example 3 — `review`

The skill reads `terminology_file`, grep-scans the repo for code symbols and file paths mentioned in `Definition` and `Comments on use`, cross-references definitions for pairwise overlap, walks the `Disambiguate from` graph for stale or contradictory links, and flags entries whose definitions look like generic public knowledge. Output is a structured markdown report. Nothing is rewritten on disk.

## Troubleshooting

- **`terminology_file` is empty and the mode needs it.** Run the first-use flow above. Either set `TERMINOLOGY_FILE`, or `python3 scripts/configure.py --scope project --terminology-file <path>`.
- **No project root found.** The skill refuses rather than falling back to user-home. Either `cd` into the project, or set `TERMINOLOGY_FILE` to an absolute path inside the project.
- **Config file exists but is missing a key.** Run `python3 scripts/configure.py --repair`.
- **Permission denied reading config.** Expected mode is `0600` on POSIX; `chmod 600 ~/.config/terminology/config.yaml`.
- **`validate` can't reach the network.** Expected; the mode degrades gracefully and reports each unreachable source as `unchecked (offline)`. It never hard-fails.
- **The motivation prose is stale.** `review` will flag it. Edit it by hand; the skill never rewrites prose.

## Companion agent

A dispatchable subagent, `terminology-curator`, runs the same workflow in isolation — useful when a long-running task wants terminology curation done as a parallel subtask without polluting the main context. The agent file lives at `.claude/agents/terminology-curator.md` in projects that adopt this skill; it delegates to this skill rather than re-implementing it.

## References

- [`references/config-schema.md`](references/config-schema.md) — configuration schema, env vars, CLI surface.
- [`references/file-format.md`](references/file-format.md) — full specification of `terminology_file`: scaffold, table semantics, motivation-prose contract, what `review` is allowed to touch.
- [`actions/define-term.md`](actions/define-term.md) — `define` procedure.
- [`actions/get-term.md`](actions/get-term.md) — `get` procedure.
- [`actions/review-terms.md`](actions/review-terms.md) — `review` procedure.
- [`actions/validate-terms.md`](actions/validate-terms.md) — `validate` procedure.
