# Health — corpus-health report (metadata-only, cheap)

Cheap, on-demand snapshot of corpus health. Pure metadata; no file reads of cited references (that is `maintenance`'s job). Safe to run frequently.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all` and use the resolved `<root_dir>`, `<health_tier_healthy_max>`, `<health_tier_guidance_max>`, and `<health_tier_strong_threshold>` for every read and write below. If `root_dir` is empty, follow the first-use flow in [`../SKILL.md`](../SKILL.md) before continuing.

## What the report contains

Scan `<root_dir>/inbox/`, `<root_dir>/active/`, `<root_dir>/blocked/`, `<root_dir>/deferred/`. Do not read excerpts; do not open referenced files. Read only TODO frontmatter and the file's mtime / location.

1. **Per-bucket counts + tier classification.**
   - For each bucket, count files (excluding `index.md`, `README.md`, `health.md`).
   - Classify per the resolved thresholds: `healthy` (≤ `<health_tier_healthy_max>`), `guidance` (≤ `<health_tier_guidance_max>` but above healthy), `strong` (above `<health_tier_strong_threshold>`).
2. **Top 5 oldest-`updated` open TODOs.** Sort `active/`, `blocked/`, `deferred/` by `updated` frontmatter ascending; show the first 5 with id, bucket, and `updated` date. These are drift candidates — surface them as a pointer to run `maintenance`.
3. **`last-checked` aging count.** Number of TODOs in `active/`+`blocked/`+`deferred/` whose `last-checked` is unset OR older than 30 days. Two counts: `unset` and `> 30 days`.
4. **`legacy-backfill: true` count.** Number of TODOs carrying the legacy provenance flag.
5. **Suggested next actions.** One-line bullet per bucket in `guidance` or `strong`, e.g.:
   - `inbox: 24 (guidance). Consider clarify on the oldest inbox items.`
   - `active: 87 (strong). Run maintenance --filter oldest:20.`

## Output

Print the report to stdout. Also write the same content to `<root_dir>/health.md`, overwriting any prior file. The file is regenerated each run; do not append.

Report layout:

```markdown
# update-todos health

Generated: <ISO timestamp>

## Per-bucket

| Bucket | Count | Tier |
|---|---|---|
| inbox | 24 | guidance |
| active | 18 | healthy |
| blocked | 3 | healthy |
| deferred | 7 | healthy |

## Drift candidates (top 5 oldest-updated)

| ID | Bucket | Updated |
|---|---|---|
| TODO-... | active | 2025-11-03 |

## Aging

- `last-checked` unset: 4 TODOs
- `last-checked` > 30 days: 9 TODOs
- `legacy-backfill: true`: 2 TODOs

## Suggested next actions

- inbox: 24 (guidance). Consider clarify on the oldest inbox items.
```

## What this action does NOT do

- Open referenced files. That is `maintenance`'s responsibility.
- Modify any TODO file. Health is read-only.
- Trigger forced triage. That is `review`'s responsibility.

## Red flags

- Reading excerpts or running drift checks. Health is metadata-only by design.
- Listing every TODO instead of the top-5 candidates. Health is a summary, not an index — for the full table see `index.md`.
