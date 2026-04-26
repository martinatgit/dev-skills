# Review — forced-triage sweep and index regeneration

This is the heart of the GTD discipline. Without `review`, the corpus silently degrades into a write-only graveyard.

## When to run

- On user request ("weekly review", "triage TODOs").
- Automatically at session start via `project-context` (when that integration is wired).
- After any `import`.
- Before any release (forced-triage of expired items blocks ship).

## Hard rule: forced triage

**Review cannot proceed past an expired TODO without recording a decision.**

For each TODO with `expires < today`:
```
EXPIRED: TODO-20260115-0004 "Investigate tabling cycles in SLD solver"
  next-step: investigate | priority: medium | created: 2026-01-15 | expired: 2026-04-14
  Decide one:
    (a) extend — set new expires date and continue
    (b) resolve — this is actually done; invoke resolve with ref
    (c) wont-fix — explicit decision to drop, record reason
    (d) discard — rotted / no longer relevant
  No other action can proceed until every expired TODO is triaged.
```

Pause review until the user decides. Do NOT silently auto-extend.

## Phase 1 — scan

Load all TODO frontmatter across all folders.

Compute:
- `expired` — `expires < today` and `status ∉ {resolved, wont-fix, discarded}`.
- `expiring-soon` — `expires` within 7 days.
- `stale` — `updated` older than 30 days and status is not resolved/wont-fix/discarded.
- `orphan` — no inbound or outbound `related` links (across open/blocked/deferred).
- `dead-blockers` — TODOs in `blocked/` whose `blocked-by[]` are all resolved. Offer to move to `active/`.
- `inbox-overflow` — `inbox/` has >5 items. Prompt user to run `clarify` on each.
- `invalid-next-step` — any TODO whose `next-step` is not in the 9-value vocabulary.
- `bidirectional-link-violations` — TODOs referencing diary nodes that do not reference them back, and vice versa (scan `doc/developer-diary/**/*.md` for `related-todos` frontmatter).

## Phase 2 — forced triage

Walk `expired` list. For each, prompt and update per user's decision. Halt on no-response.

## Phase 3 — advisory prompts

Walk `expiring-soon`, `stale`, `orphan`, `dead-blockers`, `inbox-overflow`, `invalid-next-step`, `bidirectional-link-violations` lists. For each, show the TODO and a suggested action. The user may address them now or defer until next review.

Dead-blocker cascade: if the user accepts moving blocked→active, update the file and rerun Phase 1 (new dead-blockers may emerge from the unblock).

## Phase 4 — regenerate index

Rewrite `doc/TODOs/index.md` from scratch. Structure:

```markdown
# TODO index

Regenerated: 2026-04-16T14:30:00

## Summary

- **Open:** 12 (active) + 3 (blocked) + 5 (deferred) = 20 total
- **Inbox:** 2 unclarified
- **Archive:** 47 resolved, 4 wont-fix, 1 discarded
- **Expiring within 7 days:** 3
- **Stale (>30d without update):** 4
- **Orphans:** 1
- **Dead-blockers:** 0

## Active

| ID | Next-step | Priority | Scope | Expires | Very-next-action |
|---|---|---|---|---|---|
| TODO-... | spec-update | high | area | 2026-04-22 | Draft §4.2.1 of v7.3 |
| ... |

## Blocked

| ID | Blocked by | Next-step | Expires |
|---|---|---|---|

## Inbox (unclarified)

| ID | Created | Next-step (guess) | Discovery summary |
|---|---|---|---|

## Deferred (someday/maybe)

| ID | Expires | Tags |
|---|---|---|

## Archive (most-recent 20)

| ID | Resolution type | Resolved in |
|---|---|---|

## Warnings

- Orphans: TODO-X (no related links after 7 days)
- Bidirectional link violations: diary node R.6.3.2 references TODO-Y which does not link back
```

Sort each section by `expires` ascending, then `priority` descending.

## Phase 5 — report

```
Review complete:
  expired triaged: 2 (1 extended, 1 resolved)
  dead-blockers unblocked: 1
  orphans: 1 (TODO-20260301-0002 — user chose to defer)
  stale flagged: 4 (not actioned)
  index regenerated: 20 open TODOs
```

## Red flags

- Skipping forced triage "because the user is busy". The whole point is that stale TODOs block ship. The user should be busy triaging.
- Auto-extending expired TODOs without asking. That is exactly how the corpus rots.
- Regenerating the index without running Phases 1-3. The index without triage is cosmetics.
- Silently fixing bidirectional link violations. Surface them to the user — the break may indicate a real inconsistency, not a bookkeeping miss.
