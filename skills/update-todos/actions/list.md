# List — filtered view of TODOs

Read-only. Does not modify files.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all` and use the resolved `<root_dir>` for every read below. If `root_dir` is empty, follow the first-use flow in SKILL.md before continuing.

## Filters

Accept any combination of:
- `--status inbox|open|blocked|deferred|resolved|wont-fix|discarded`
- `--next-step <one of the 9 values>`
- `--tag <tag>` (repeatable)
- `--scope project|area|resource`
- `--priority low|medium|high`
- `--stale <N>` — `updated` older than N days
- `--expires-within <N>` — `expires` within N days (defaults to 7)
- `--path <file-path>` — TODOs whose `references[]` include this path
- `--orphan` — TODOs with no inbound or outbound `related` links
- `--blocked-by-resolved` — TODOs in `blocked/` whose `blocked-by` all resolved

Default (no filters): list all TODOs grouped by status folder, sorted by `expires` ascending.

## Implementation sketch

1. Glob `<root_dir>/**/TODO-*.md`.
2. Parse frontmatter of each into a table.
3. Apply filters.
4. Render as markdown table to stdout (the user's conversation).

Columns: `id | status | next-step | priority | scope | expires | very-next-action | file`.

For `--path` queries, include a note column showing which `reference` matched.

For `--orphan`, compute inbound links across the whole corpus and show only TODOs where both in-degree and out-degree are zero.

## Usage examples

```
update-todos list --next-step decide
  → all TODOs needing product-owner decision
update-todos list --path src/parser.ts
  → all TODOs touching this file, for context before editing
update-todos list --expires-within 14
  → upcoming forced-triage deadlines
update-todos list --orphan
  → Zettelkasten health check
```

## Output format

Use a compact markdown table. If more than 30 rows match, paginate or suggest narrower filters.

Always append a one-line summary: `N TODOs matched; M with priority high; K expiring within 7 days`.

## No writes

`list` does not modify `index.md` or any TODO file. If the user wants to act on a listed TODO, point them to `clarify` / `resolve` / `review`.
