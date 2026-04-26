# doc/TODOs — universal inbox for AIQEUNG

This folder is the canonical home of every deferred decision, design inconsistency, convention violation, improvement opportunity, missing test, open question, and other action item that emerges during design or implementation work in the AIQEUNG project. It is managed by the `update-todos` skill.

> **Do not edit `index.md` by hand.** It is auto-regenerated.
> **Do not edit TODO files by hand** without running `update-todos review` afterward — cross-links and the index will drift.

## Why this folder exists

Governance rule 6 of CLAUDE.md mandates being explicit about assumptions, compromises, and deferred decisions. This folder is the deferred-decision surface. Every observation that would otherwise be lost — between session boundaries, between engineers, between a quick thought mid-refactor and the moment you had bandwidth to act on it — is captured here atomically, with enough context that a future engineer can rehydrate without archaeology.

## Theoretical grounding

| Source | Principle | Mechanism |
|---|---|---|
| Zettelkasten (Luhmann, 1981) | Atomic notes, permanent IDs, explicit links | One TODO per file; permanent `TODO-YYYYMMDD-NNNN` ids; ≥1 `related` link enforced at clarify-time; orphans flagged in review. |
| Getting Things Done (Allen, 2015) | Capture → Clarify → Organise → Reflect → Engage | Two-phase flow (capture→clarify); mandatory `very-next-action` at clarify-time; `review` mode forces weekly-style sweep. |
| Second Brain / PARA (Forte, 2022) | Projects vs Areas vs Resources vs Archives | `scope` frontmatter field; `archive/` folder. |
| GTD forced-triage | Nothing is someday without an expiry | `expires` (default +90 days); `review` refuses to proceed past expired items without decision. |

## Folder layout

```
doc/TODOs/
├── README.md         ← this file
├── index.md          ← auto-regenerated; run `update-todos review`
├── inbox/            ← captured, not yet clarified
├── active/           ← clarified, ready to action
├── blocked/          ← waiting on another TODO or external event
├── deferred/         ← someday/maybe, not currently actionable
└── archive/          ← resolved, wont-fix, or discarded
```

Status is encoded by folder path. The `status` frontmatter field mirrors the folder and is updated whenever a file moves.

## File schema

Filename: `TODO-YYYYMMDD-NNNN-<kebab-title>.md`. The id is permanent even if the file moves or the title is renamed.

See `.claude/skills/update-todos/resources/inbox-entry.md.tpl` and `active-entry.md.tpl` for the two phase-specific schemas.

## The 9 next-step values

Exactly these — no other values are valid:

- `spec-update` — change a requirement spec.
- `implementation` — change source code.
- `diary-update` — add to `doc/developer-diary/`.
- `brainstorm` — needs ideation.
- `refactor` — code quality; no behavior change.
- `investigate` — research spike.
- `test` — add or fix test coverage.
- `decide` — needs product-owner decision.
- `reproduce` — bug-flavored; needs repro.

`review` is a **mode** of the skill, not a next-step. `documentation` is subsumed by `spec-update` (per CLAUDE.md §4 where spec IS the design authority) or `diary-update`.

## Boundary with `doc/developer-diary/`

**developer-diary** = time-indexed narrative. Answers: "how did we get here, what did we try, what did we learn?"

**doc/TODOs/** = action-indexed pointers. Answers: "what remains to be done, why, and by whom?"

Enforced bidirectional contract:
- Every TODO's `discovered-in-task` frontmatter should identify the diary node where the observation surfaced (when applicable).
- Every diary-entry "Open questions" or "Special instructions for next reader" item must either (a) reference a TODO id, or (b) be resolved inline in that session.
- `update-todos review` validates both directions and reports violations in `index.md`.

When writing, prefer migrating action items *out* of diary entries and *into* TODOs. Narrative stays in the diary; action items live here.

## Usage

```
/update-todos capture       # on observation (runs dedup first)
/update-todos clarify <id>  # promote inbox → active
/update-todos list [filters]
/update-todos resolve <id>  # archive with closure notes
/update-todos review        # forced triage + index regen
/update-todos import        # one-shot migration from doc/martin-TODOs.md
```

Invoke `capture` proactively. Flow is cheap to preserve if you do not derail for anything you can document in 30 seconds.

## References

- Allen, D. (2015). *Getting Things Done: The Art of Stress-Free Productivity* (rev. ed.). Penguin.
- Forte, T. (2022). *Building a Second Brain*. Atria Books.
- Luhmann, N. (1981). "Kommunikation mit Zettelkästen. Ein Erfahrungsbericht." Reprinted in *Universität als Milieu*. Bielefeld: Haux, 1992.
- Project CLAUDE.md governance rules §2 (user is final authority), §3 (ground claims), §4 (specs drive implementation), §6 (explicit assumptions/deferrals), §9 (orthogonality).
