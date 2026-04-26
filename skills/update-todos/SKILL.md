---
name: update-todos
description: Use when a deferred decision, design inconsistency, convention violation, improvement opportunity, missing test, open question, unresolved ambiguity, or any other action item emerges during design or implementation that should not be actioned immediately. Captures it as an atomic markdown note in doc/TODOs/ with full rehydratable context so a future engineer can act on it without archaeology. Invoke with capture, clarify, list, resolve, review, or import.
allowed-tools: Bash Read Grep Glob Write Edit
effort: medium
context: fork
agent: general-purpose
argument-hint: "[capture|clarify|list|resolve|review|import]"
---

## Invocation modes

You are invoked in **$ARGUMENTS** mode.

- If mode is `capture`: follow `${CLAUDE_SKILL_DIR}/actions/capture.md`. Low-friction write of a new TODO into `doc/TODOs/inbox/`. Runs deduplication BEFORE writing. This is the default when an observation arises mid-task and should not derail flow.
- If mode is `clarify`: follow `${CLAUDE_SKILL_DIR}/actions/clarify.md`. Promotes an inbox item into a fully-articulated atomic note in `doc/TODOs/active/`. Enforces ≥1 related link and assigns an expiry.
- If mode is `list`: follow `${CLAUDE_SKILL_DIR}/actions/list.md`. Filter by next-step, tag, scope, status, priority, staleness, or file-reference overlap.
- If mode is `resolve`: follow `${CLAUDE_SKILL_DIR}/actions/resolve.md`. Move to `archive/` with Resolution notes; update cross-links on related TODOs.
- If mode is `review`: follow `${CLAUDE_SKILL_DIR}/actions/review.md`. Forced triage of expired items, orphan detection, dead-blocker detection, index regeneration.
- If mode is `import`: follow `${CLAUDE_SKILL_DIR}/actions/import.md`. One-shot migration of the legacy `doc/martin-TODOs.md` bullet list into atomic files.
- If no mode is provided or mode is unrecognised: ask the user which mode to use.

## Purpose

This skill operationalises a **universal inbox** for the AIQEUNG project. Every observation that you or the user would otherwise lose — a naming mismatch, a spec gap, a deferred refactor, a "we should test this later", an open design question — is captured atomically, in context, so it survives session boundaries and team handovers.

Governance rule 6 (CLAUDE.md) mandates being explicit about assumptions, compromises, and deferred decisions. This skill is the deferred-decision surface.

## Theoretical grounding

Each technique below is operationalised in a specific mechanism — not namedropped.

| Source | Principle | Mechanism in this skill |
|---|---|---|
| Zettelkasten (Luhmann, 1981) | Atomic notes, permanent IDs, explicit links | One TODO per file; `id: TODO-YYYYMMDD-NNNN` never changes; `related[]` requires ≥1 link at clarify-time; orphans flagged in review. |
| Getting Things Done (Allen, 2015) | Capture → Clarify → Organise → Reflect → Engage | Two-phase flow: `capture` writes to `inbox/`; `clarify` promotes to `active/`. `very-next-action` is mandatory at clarify-time. `review` mode forces weekly-style sweep. |
| Second Brain / PARA (Forte, 2022) | Projects vs Areas vs Resources vs Archives | `scope: project \| area \| resource` frontmatter field; `archive/` folder. |
| GTD forced-triage | Nothing is "someday" without an expiry | `expires` field (default +90 days). `review` refuses to proceed past an expired TODO without decision. |

Citations live here so the grounding is verifiable per governance rule 3 (ground every claim in verifiable fact).

## Folder layout

Status = folder path (not frontmatter). Path-based priors beat flat+index for LLM retrieval on long-lived corpora.

```
doc/TODOs/
├── README.md                 # Taxonomy, conventions, theoretical grounding, boundary with developer-diary
├── index.md                  # Auto-regenerated table of all TODOs; always edited via review or any write
├── inbox/                    # Captured, not yet clarified — status = inbox
├── active/                   # Clarified, ready to action — status = open
├── blocked/                  # Waiting on another TODO or external event — status = blocked
├── deferred/                 # Someday/maybe, not currently actionable — status = deferred
└── archive/                  # Resolved or wont-fix — status = resolved | wont-fix | discarded
```

File naming: `TODO-YYYYMMDD-NNNN-<kebab-title-slug>.md`. ID is permanent even if the file is moved between folders.

## Controlled `next-step` vocabulary (exactly 9)

Reject unknown values at capture time.

| Value | Meaning |
|---|---|
| `spec-update` | Change a requirement spec (CLAUDE.md §4 makes spec the design authority; subsumes design-update and in-spec documentation). |
| `implementation` | Change source code under `src/`. |
| `diary-update` | Add historical context or lesson-learned to `doc/developer-diary/`. |
| `brainstorm` | Needs ideation session (feeds into `superpowers:brainstorming`). |
| `refactor` | Code quality / naming / structural cleanup; no behavior change. |
| `investigate` | Research spike, decidability check, academic lookup. |
| `test` | Add or fix test coverage. |
| `decide` | Needs human (product-owner) decision per governance rule 2. |
| `reproduce` | Bug-flavored; needs a reliable repro before anything else. |

Note: `review` is a **mode of this skill**, not a next-step. `documentation` is subsumed by `spec-update` (per CLAUDE.md §4) or `diary-update`.

## Boundary with developer-diary (orthogonality per governance rule 9)

**Developer-diary** = time-indexed narrative of what happened in a subsystem. Answers "how did we get here, what did we try, what did we learn?"

**Update-todos** = action-indexed pointers to future work. Answers "what remains to be done, why, and by whom?"

Enforced bidirectional contract:
- Every TODO's `discovered-in-task` frontmatter points to the diary node where the observation surfaced (if any).
- Every diary-node "Open questions" or "Special instructions for next reader" item must either (a) reference a TODO id, or (b) be resolved inline in that session.
- `review` mode validates this contract when regenerating `index.md` and flags violations.

If you are about to write an "Open question" in a diary entry, invoke this skill in `capture` mode instead and link the resulting TODO from the diary. Narrative stays narrative; action items migrate out.

## Capture trigger (when to invoke without being asked)

Invoke `capture` proactively whenever, mid-task, you observe any of:

- A convention violation in a file you are not currently refactoring.
- A design inconsistency between two specs, or between spec and code.
- A missing test, error-handling gap, or edge case you cannot address now.
- An ambiguity in the spec that needs product-owner decision (`next-step: decide`).
- A refactor opportunity that would derail the current task.
- A design smell, naming issue, or orthogonality violation (CLAUDE.md §9).
- An unproven invariant, undecidable fragment concern, or soundness question (`next-step: investigate`).
- A TODO or FIXME you encounter in source that lacks structured context.

Do NOT invoke `capture` for concerns that belong in:
- Developer diary (historical narrative, decision journal) — use `developer-diary update` instead.
- The spec itself (when the decision IS made and just needs documenting) — edit the spec.
- This session's task plan (still in scope, still being worked) — use TaskCreate.
- **Anything that takes <2 minutes to fix** — just fix it. The 2-minute rule (Allen 2015) applies.
- **Anything that fits as an inline `// TODO` comment** — one-line, one-file, teammate can action in <30 minutes, context obvious from surrounding code. External capture is reserved for concerns that span files, specs, layers, or decisions.

## WIP limits (prevent corpus rot)

Kanban-style work-in-progress limits keep the system healthy:
- `inbox/` ≤ 20 unclarified entries.
- `active/` ≤ 15 open entries.

If either limit is exceeded, `capture` refuses and tells the user to run `clarify` and `review` first. Capture is cheap only when downstream drains.

## Dedup, clarify, and review discipline

These are load-bearing. Details in action files. Summary:

- **Dedup at capture time** (action file). Hard signal: same file+line reference (±10 lines) as an existing TODO. Soft signal: Jaccard token similarity on `title + raw observation` ≥ ~0.55, with explicit weak-match warning. Never auto-merge — always surface candidates to the user.
- **Link density at clarify time** (action file). Refuse to promote a TODO from `inbox/` to `active/` without at least one `related` link to another TODO, a diary node, or a spec section.
- **Forced triage at review time** (action file). `review` cannot proceed past an expired TODO without recording extend / resolve / wont-fix / discard.

## Integration contract (document, do not hard-code)

Other skills SHOULD but need not honour these:

- `project-context` (session start) surfaces: open-TODO count, clarify-pending count, blocked-with-resolved-blocker count, expiring-within-7-days count, orphan count.
- `developer-diary update` scans TODOs whose `references[]` overlap edited files and prompts: "does this change resolve / touch TODO-X?"
- `project-audit` emits one TODO per identified spec/implementation gap.
- `superpowers:brainstorming` picks up `next-step: brainstorm`.
- `superpowers:writing-plans` picks up `priority: high` + `next-step: implementation`.
- `superpowers:systematic-debugging` picks up `next-step: reproduce`.

## Quality bar

A TODO is well-written when a new engineer with zero session context can read it and know:
1. What the concern is (Summary + Problem).
2. Why it was deferred rather than actioned immediately (Rationale for deferral).
3. What files and spec sections they must read first (Required references).
4. What a plausible next action looks like (Proposed approach, very-next-action).
5. What "done" looks like (Acceptance criteria).

If any of these five are missing after `clarify`, the TODO is not ready to leave `inbox/`.

## Final behaviour

Treat `doc/TODOs/` as a first-class project artifact. It lives under version control, it is regenerated on every write, and it is reviewed on cadence. Never edit a TODO file by hand without running `review` afterward to regenerate the index and verify bidirectional links.
