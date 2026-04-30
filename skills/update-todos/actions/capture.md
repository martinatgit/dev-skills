# Capture — write a new TODO to `<root_dir>/inbox/`

Low-friction entry point. This is the default mode when a deferred concern arises mid-task. Keep it cheap so it is actually used.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all` and use the resolved `<root_dir>`, `<inbox_wip_limit>`, and `<active_wip_limit>` for every read and write below. If `root_dir` is empty, follow the first-use flow in SKILL.md before continuing.

## Iron rules

1. **Run deduplication BEFORE writing.** An unchecked capture pollutes the corpus.
2. **Apply the 2-minute rule BEFORE capturing.** If the concern can be actioned in under 2 minutes of uninterrupted work, just do it — filing it is higher-cost than fixing it. Only capture what genuinely needs deferral.
3. **Prefer inline `// TODO` for concerns that meet all three:** (a) fit on one line, (b) a teammate could action in <30 minutes, (c) context is obvious from the surrounding code. `<root_dir>/` is for concerns that require rehydration beyond the immediate file. Rationale: inline TODOs stay with the code that needs to change; external TODOs stay with concerns that span files, specs, or decisions.
4. **Capture backpressure.** If `<root_dir>/inbox/` has more than `<inbox_wip_limit>` unclarified entries OR `<root_dir>/active/` has more than `<active_wip_limit>` open entries, REFUSE to capture. Instead, tell the user: "Inbox/active over WIP limit — run `update-todos review` and `update-todos clarify` before capturing more." Kanban WIP limits prevent corpus decay; the capture funnel is cheap only when the downstream is drained.

## Required inputs (from the user's prompt or current context)

At minimum:
- `title` — one imperative sentence, under ~12 words. If absent, synthesise from the observation and confirm with the user only if ambiguous.
- `discovery-context` — verbatim description of what task was in flight, which files were open, which spec section was being read, and what triggered the observation. Copy salient conversation fragments or error text literally.
- `references[]` — every file, spec section, diary node, or commit that an engineer will need to rehydrate this TODO. Each entry is `{path, lines?, anchor?, note}`.
- `next-step` — best guess from the controlled 9-value vocabulary (see SKILL.md). If unclear, pick `decide` and document the ambiguity in the body.

Do NOT demand the full `active/` schema at capture time. Anything more than the above is filler and will degrade corpus quality (LLMs fill empty headings with plausible noise).

## Step 1 — dedup

Index all existing TODO frontmatter across `inbox/`, `active/`, `blocked/`, `deferred/` (NOT `archive/` — those are resolved).

### Hard signal (auto-surface to user)
A candidate duplicate exists if any existing TODO has a `references[]` entry whose `path` matches the new capture's `path` and whose line range overlaps (±10 lines). Same file+location = near-certain duplicate.

**Missing line numbers.** If either the new capture's reference OR the existing TODO's reference lacks a `lines` field, the ±10-line overlap test is indeterminate. Treat as a path-match-only signal and escalate to soft-signal review for that pair — do NOT auto-fire the hard signal alone.

### Soft signal (surface with weak-match warning)
Compute token Jaccard similarity over `title + raw observation` vs existing `title + Summary` (or `Raw observation` for inbox items). Threshold ~0.55.

**Tokenizer (must be deterministic across invocations):**
- Lowercase the string.
- Strip punctuation (`[^a-z0-9\s-]`).
- Split on whitespace and hyphens.
- Drop tokens of length ≤2.
- Drop stopwords from this fixed list: `the a an and or of to in on at by for with from is are was were be been being has have had do does did this that these those it its into as at not no but if then else when while which who whom whose how why where what there here over under between among via per use uses used using`.
- Do NOT stem. (Stemming improves recall but makes the computation non-deterministic across LLM invocations.)

**Threshold is advisory, not empirical.** 0.55 was picked by design review, not by corpus calibration. When the corpus reaches ~50 TODOs, run `update-todos review --calibrate-dedup` (see review.md — TODO for future work). Until then, always surface soft matches with explicit "weak match" language so the user judges.

**Embedding escalation.** If an embedding tool is available in the environment, prefer cosine similarity on `title + discovery-context` with threshold ~0.85 as a tiebreaker when Jaccard is borderline (0.40–0.70). Document the substitution in the run output. Otherwise fall back to Jaccard alone. Published practice (NVIDIA NeMo SemDedup, Obsidian Smart Connections) converges on embedding-cosine 0.85–0.90 for near-dup; fold this in when you have the tool.

### Soft signal (tag overlap — advisory only)
Tag overlap ≥ 2 is **not** sufficient to flag a duplicate — false-positive storm for broad tags like `layer-6`. Only use it to enrich the candidate list when other signals fire.

### Presenting candidates
If any candidate fires, show the user:
```
Possible duplicate(s) found:
  - [TODO-20260410-0003] Fix snake_case violation in parser
    (hard match: references src/parser.ts:42-48)
    (soft match: 0.71 token Jaccard on title+summary)
Options:
  (a) Append this discovery context to that TODO (recommended)
  (b) Link the new TODO as `related` to that one
  (c) Replace the existing TODO with this new one
  (d) Create a new TODO anyway (mark as distinct concern)
  (e) Cancel capture
```

Never auto-merge. Always surface candidates to the user; the user is the final authority on dedup decisions.

## Step 2 — generate ID

`TODO-YYYYMMDD-NNNN` where `YYYYMMDD` is today and `NNNN` is the zero-padded next counter for today. Scan all TODO files (**all folders including `archive/`** — because IDs are permanent and must not be reused even after resolution) for existing ids to pick the next counter. The ID is permanent — even if the file moves between folders or the title is renamed.

Note: this is a different scan from the dedup scan in Step 1, which deliberately excludes `archive/` because resolved concerns should not shadow live captures. ID scan is for uniqueness; dedup scan is for semantic overlap.

## Step 3 — slugify title

Lowercase, replace non-alphanumeric with `-`, collapse repeats, trim. Truncate to 50 chars.

Filename: `TODO-YYYYMMDD-NNNN-<slug>.md`.

## Step 4 — capture current session state

Extract from the active conversation:
- Current task (what the assistant was asked to do).
- Files read in this session that are relevant to the observation.
- Files edited in this session that are relevant.
- Specs / diary nodes consulted.
- Error messages or test failures that triggered the observation (verbatim).
- The diary node (if any) whose work produced this TODO — put in `diary-node` frontmatter.

Be generous. Rehydration is the whole point.

## Step 5 — write the file

Use `resources/inbox-entry.md.tpl`. Fill only the inbox-phase fields listed in the template. Do NOT pre-populate Problem/opportunity, Rationale for deferral, Proposed approach, Acceptance criteria, or Open questions — those are clarify-phase fields.

Write to `<root_dir>/inbox/TODO-YYYYMMDD-NNNN-<slug>.md`.

## Step 6 — update the index

Append a row to the **Inbox (unclarified)** section of `<root_dir>/index.md` (create it from `resources/index.md.tpl` if absent). The Inbox table schema is `ID | Created | Next-step (guess) | Discovery summary`:
```
| TODO-20260416-0003 | 2026-04-16 | spec-update | Snake_case violation in src/parser.ts:42-48 |
```

Do not regenerate the full index on capture — that is `review`'s job. Append-only is enough here.

## Step 7 — report

One-line summary to the user:
```
Captured TODO-20260416-0003 → <root_dir>/inbox/TODO-20260416-0003-fix-snake-case-violation.md (next-step: spec-update; dedup: no matches)
```

If this TODO was discovered during work that is being recorded in a diary entry, remind the user: "consider linking this TODO from the diary node via `related-todos: [TODO-20260416-0003]`."

## Red flags — STOP before writing

- Writing without running dedup. Corpus decay starts here.
- Filling in clarify-phase sections with plausible filler when the information genuinely was not in context.
- Capturing something that is actually in scope for the current task (that belongs in TaskCreate, not here).
- Capturing a narrative that is really diary material (belongs in developer-diary).
- Inventing a `next-step` value outside the 9-value vocabulary.
- Capturing something that meets the 2-minute rule (just do it).
- Capturing something that fits as an inline `// TODO` comment (put it there; external capture is for cross-file/cross-spec concerns).
- Capturing when inbox or active bucket is over the WIP limit — triage first.

If any of these flags fire: stop, ask the user.

## Example: ambiguous `next-step` on spec-vs-code drift

Observation: a file uses `CamelCase` but the spec mandates `snake_case`. Three plausible next-steps:
- `refactor` — fix the code to match the spec (chosen when the spec is authoritative).
- `spec-update` — change the spec if the code was intentional (chosen when the violation reveals the spec is wrong).
- `decide` — ask the product owner which is canonical (chosen when you cannot determine intent).

Default to `refactor` when the project's convention is "spec drives implementation". Escalate to `decide` only if the spec is ambiguous or silent on the point.
