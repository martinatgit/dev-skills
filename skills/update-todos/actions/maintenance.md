# Maintenance — deep, one-TODO-at-a-time content verification

`maintenance` opens a TODO's cited files, compares verbatim excerpts pinned at clarify time against current content, and produces a verdict the user approves. It runs only on TODOs in `active/`, `blocked/`, or `deferred/` — inbox items have no excerpts to compare against.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all` and use the resolved `<root_dir>` for every read and write below.

## Inputs

```
update-todos maintenance                                  # default ranking, picks top candidate
update-todos maintenance TODO-YYYYMMDD-NNNN               # explicit id
update-todos maintenance --filter oldest:N
update-todos maintenance --filter latest:N
update-todos maintenance --filter stale:N                 # days since last-checked
update-todos maintenance --filter legacy                  # only legacy-backfill: true TODOs
update-todos maintenance --filter bucket:active|blocked|deferred
update-todos maintenance --filter tag:<name>
update-todos maintenance --include-rejected               # surface backfill-rejected TODOs (excluded by default)
update-todos maintenance --dry-run [...any of the above]  # preview, no writes
```

Filters combine with `+` (e.g. `--filter oldest:20+bucket:active`).

## Candidate ranking (used by default invocation and `list --maintenance-candidates`)

Score each open TODO in `active/`, `blocked/`, `deferred/` (not archive, not inbox):

| Signal | Weight |
|---|---|
| `last-checked` unset on any reference | 5 |
| `last-checked` > 60 days on any reference | 4 |
| `last-checked` 30-60 days | 2 |
| Any referenced file's git log shows commits touching it since `clarified-at-sha` | 3 per affected reference |
| Status = `blocked` and all `blocked-by[]` ids are resolved | 3 |
| `discovered-in-task` linking a diary node whose `updated` is newer than the TODO's `updated` | 2 |
| `maintenance-suggested` frontmatter field set (deferred from auto-trigger) | 3 |

`legacy-backfill: true` does NOT bias the ranking (provenance only). To surface legacy items deliberately, use `--filter legacy`.

**Backfill-rejected TODOs are excluded by default.** A TODO carrying `legacy-backfill-rejected-at: <YYYY-MM-DD>` (top-level frontmatter, written when the user rejects a legacy backfill prompt — see [Legacy backfill rejection](#legacy-backfill-rejection) below) is dropped from the candidate set entirely, regardless of other signals. Pass `--include-rejected` to surface them again (typically when the user is ready to revisit).

Ties broken by oldest `last-checked`.

## Per-TODO pass — Phase 1: Rehydrate

Re-read the TODO file. Load `references[]`. For each reference:

Invoke `python3 skills/update-todos/scripts/check_reference_drift.py --todo <todo-path>` once for the whole TODO. The script handles, per reference:

1. Existence check. If the file at `path` is missing AND a rename can be detected (`git log --diff-filter=R --name-status` since `clarified-at-sha`, or all history if the SHA isn't set), the script records `renamed-from: <old-path>`, updates the reported `path` to the new location, and continues drift detection at the new path. If no rename is found, the finding is `missing-file`.
2. SHA-reachability check. If `clarified-at-sha` is set but the SHA is no longer in the repo (rebased away), the script records `sha-unreachable: true` on the finding. Drift detection still runs against current HEAD content; surface the flag in the Phase 3 prompt.
3. Diary short-circuit. References with `kind: diary` get existence-only checking (no excerpt comparison) — diary nodes are append-only by contract.
4. Normalization (LF endings, per-line right-trim) and matching (exact match, then similarity fallback at token Jaccard ≥ 0.85, with multi-match disambiguation by closest-to-original-line).

The script's YAML output is what you consume. You do NOT run `git log --follow` manually — the script does that work.

## Per-TODO pass — Phase 2: Verdict (recommendation)

**Mechanical verdicts** — deterministic from Phase 1 findings alone:

| Aggregate findings | Verdict |
|---|---|
| All references `unchanged` AND no `ambiguous-match` | `still-valid` |
| All references `missing-file` or `gone` AND no successor surfaced by rename detection | `obsolete` |

**Judgment verdicts** — agent picks based on Phase 1 findings AND the TODO's `Problem / opportunity` text:

- `drifted-still-relevant` — references shifted but the concern in `Problem / opportunity` is still observable in the new content.
- `superseded` — the cited code/spec has been refactored such that the original concern no longer applies (the buggy function is deleted, the violated rule was removed from the spec, etc.).
- `needs-rewrite` — references still exist but the TODO body's claims about them are no longer accurate (the violation is fixed but a different issue emerged, or the framing was wrong).

**Evidence-citation requirement.** For any judgment verdict, the Phase 3 prompt MUST include:

1. A direct quote of the TODO's `Problem / opportunity` section.
2. A direct quote of the new content at the resolved reference location.
3. A one-sentence reasoning line linking the two. Example: "The cited rule from §4.2.1 was removed in commit b71e003; the concern no longer applies."

If you cannot produce all three, default to the most conservative verdict (`drifted-still-relevant`) and surface the missing evidence in the prompt so the user knows the judgment is weak.

## Per-TODO pass — Phase 3: Present to user

```
TODO-20260415-0003 "Fix snake_case violation in token emitter"
  Verdict (recommended): drifted-still-relevant
  Findings:
    - src/parser.ts:42-48 — drifted (similarity 0.91 against current lines 58-64; one match)
  Evidence (judgment verdict):
    > Problem: "emitToken accepts camelCaseName but spec §4.2.1 mandates snake_case for token-layer identifiers."
    > Current src/parser.ts:58-64:
    >   function emitToken(camelCaseName) { ... if (camelCaseName.match(/[A-Z]/)) warn(...); }
    > The cited violation persists at the new line range; concern still observable.
  Proposed changes:
    - references[0].lines: 42-48 → 58-64
    - Refresh excerpt at lines 58-64
    - Set last-checked: <today>
    - Advance clarified-at-sha: a3f9c12 → b71e003
    - Append maintenance-history entry
  Approve? [y / n / different-verdict / dry / abort]
```

- `y` — apply proposed changes; append `maintenance-history` entry; move to next TODO if batch.
- `n` — do not write proposed changes; DO append a `maintenance-history` entry recording the rejection (so the next pass does not silently re-propose without a record). **If the TODO is a legacy item** (no excerpts, missing snapshot fields — see [Legacy backfill rejection](#legacy-backfill-rejection)), also write `legacy-backfill-rejected-at: <today>` to the TODO's top-level frontmatter so default-mode maintenance excludes the item entirely on future runs.
- `different-verdict` — user picks one of the other four; agent recomputes proposed changes for that verdict and re-prompts.
- `dry` — show the would-be diff for the file without writing; re-prompt.
- `abort` — stop the entire run (batch terminates).

**Every verdict requires explicit `y`.** Even `still-valid` (metadata-only refresh) prompts, because the approval itself is the record we want logged.

## Per-TODO pass — Phase 4: Apply + log

On `y`:

1. Write the proposed frontmatter changes (`path`, `lines`, `excerpts`, `last-checked`, `clarified-at-sha`).
2. **Append the maintenance event to the `maintenance-history:` frontmatter array** (create the key if absent):
   ```yaml
   maintenance-history:
     - ts: <ISO timestamp>
       verdict: drifted-still-relevant
       approved-by: user
       changes:
         - src/parser.ts:42-48 → 58-64; excerpts refreshed
         - clarified-at-sha advanced from a3f9c12 to b71e003
   ```
   Append-only; never overwrites prior entries.
3. Re-render the `## Pinned references` body section (the human-readable mirror of the frontmatter excerpts; see [`../resources/active-entry.md.tpl`](../resources/active-entry.md.tpl)). The "Last maintenance:" line at the top of each ref's sub-section reflects the most-recent `maintenance-history` entry.
4. If verdict is `superseded` → invoke `resolve` with `resolution-type: superseded-by-drift` and a pre-filled Resolution notes section quoting the maintenance findings. The final `maintenance-history` entry lives on the archived TODO.
5. If verdict is `obsolete` → invoke `resolve` with `resolution-type: discarded-obsolete`.
6. If verdict is `needs-rewrite` → **move the TODO file from `active/` back to `inbox/`** (or `blocked/` → `inbox/`, etc.). Set `status: inbox` in the frontmatter. Drop clarify-phase frontmatter fields (`priority`, `effort`, `scope`, `expires`, `very-next-action`); preserve everything else, including the existing `excerpts` and `maintenance-history`. Update `<root_dir>/index.md` to reflect the move. Prompt the user to run `clarify` on this TODO when ready (do not force it immediately).

## On rejection (`n`)

Write the rejection record to `maintenance-history`:

```yaml
maintenance-history:
  - ts: <ISO timestamp>
    verdict: <the recommended verdict>
    approved-by: user-rejected
    changes: []
    note: <if user supplied a free-form reason at the prompt>
```

This is intentional: rejection IS a lifecycle event worth logging. It is the only case where `n` causes a write. Mention this explicitly when prompting if the run has any judgment verdicts.

## On dry-run

`--dry-run` suppresses ALL writes — including the rejection record above. Output is the same Phase 3 prompt framed as "would do" without soliciting a keystroke. Useful for batch previews. Differs from `n` in that no rejection trace remains.

## Legacy backfill rejection

A "legacy" TODO is one missing the snapshot fields the maintenance machinery needs (no `excerpts`, no `clarified-at-sha`, no `last-checked` on its references). The first time `maintenance` opens such a TODO, it offers to **backfill the baseline** from current file state — see the Phase 3 prompt for backfill. If the user accepts (`y`), the TODO gains synthetic excerpts and `legacy-backfill: true`, and subsequent passes treat it normally.

If the user **rejects** the backfill (`n`), the prompt would otherwise re-fire on every future maintenance run for that TODO, since nothing about its state has changed. To avoid this loop:

1. Write `legacy-backfill-rejected-at: <today>` to the TODO's top-level frontmatter (alongside `discovered-in-task`, `discovered-by`, etc.).
2. Append the standard rejection entry to `maintenance-history` (`approved-by: user-rejected`, `verdict: still-valid (legacy-backfill)`).
3. Default-mode `maintenance` and `list --maintenance-candidates` then **exclude this TODO from the candidate set entirely.** The exclusion is a hard skip, not a low rank — backfill-rejected TODOs do not bubble up under any default ranking.

To revisit a rejected TODO later, the user runs `maintenance --include-rejected` (re-prompts for backfill) or `maintenance <id> --include-rejected` (re-prompts for a specific id).

To **permanently clear** the rejection (the user has decided to backfill after all), accepting the backfill prompt on the next `--include-rejected` pass auto-removes the `legacy-backfill-rejected-at` field as part of the Phase 4 frontmatter write. There is no manual `--clear-rejection` flag.

### Why hard skip rather than ranking penalty

A ranking penalty would still surface the TODO eventually (once nothing else ranks higher), re-firing the prompt. The user already said no. Hard skip honors that decision until the user explicitly opts back in via `--include-rejected`.

### Why a separate field rather than reusing maintenance-history

The history array grows append-only; checking it for a rejection requires scanning every entry. A top-level field makes the candidate-ranking step O(1) per TODO and keeps the exclusion rule one line: `if 'legacy-backfill-rejected-at' in frontmatter and not args.include_rejected: skip`.

## End-of-run report

```
Maintenance run complete:
  TODOs scanned: 10
  still-valid: 4 (logged)
  drifted-still-relevant: 3 (applied)
  superseded: 1 (resolved as superseded-by-drift)
  obsolete: 1 (discarded)
  needs-rewrite: 1 (moved to inbox; user to re-clarify)
  user-rejected: 0
  aborted: 0
```

## Auto-trigger from `resolve` (opt-in)

When `auto_maintenance_on_resolve: true` (config key) OR `--with-maintenance` is passed to `resolve`, a Phase-1-only drift scan runs on the resolving TODO's `related[]`, `blocks[]`, and `blocked-by[]` neighbors (capped at the first 20). If any neighbor shows `moved`/`drifted`/`gone`/`missing-file` findings, the user is prompted:

```
Resolving this TODO may affect related items:
  TODO-20260301-0007 — references src/parser.ts:42-48 (now moved to 58-64)
Run maintenance on it? [y / n / later]
```

- `y` — invoke `maintenance` on that neighbor immediately.
- `n` — no action.
- `later` — set `maintenance-suggested: <today>` on the neighbor's frontmatter (boosts ranking +3).

Default behavior (no opt-in) makes no such scan; `resolve` is fast and predictable.

## Red flags

- Running maintenance on an inbox TODO. Inbox items have no excerpts; the run is meaningless. Refuse.
- Applying a judgment verdict without all three evidence components. Default to the most conservative verdict instead.
- Silently re-snapshotting on `n` (the rejection branch still writes a maintenance-history entry; only `--dry-run` is fully read-only).
- Overwriting `maintenance-history`. Always append.
- Auto-applying any verdict without explicit `y`. The user is the final authority on every lifecycle change.
