---
name: update-todos
description: Captures every deferred decision, design inconsistency, convention violation, missing test, open question, unresolved ambiguity, or other action item that emerges during design or implementation work — atomically, with full rehydratable context so a future engineer can act on it without archaeology. Use whenever the user (or you) say "let's not action this now", "capture as a TODO", "file this for later", "we should look at this", "open question for the product owner", or notice a concern that derails the current task. Use this even if phrased casually like "remind me later" or "we'll come back to this". Always project-local: TODOs from one project never bleed into another, even when the skill itself is installed user-scope. Invoke with `capture`, `clarify`, `list`, `resolve`, `review`, or `import`. Do not use for ephemeral session memory or for narrative/decision history — use `developer-diary` for the latter.
---

# update-todos

A universal, project-local TODO inbox. Every observation that would otherwise be lost — between session boundaries, between engineers, between a quick thought mid-refactor and the moment you had bandwidth to act on it — is captured atomically here.

The skill is project-local by design: when invoked inside a project, it writes only into that project's TODO tree, and never leaks into another project's TODOs even if the skill itself is installed at user scope.

## Inputs

```
/update-todos [capture | clarify | list | resolve | review | import]
```

- `capture` — low-friction write of a new TODO into `<root_dir>/inbox/`. Runs deduplication BEFORE writing. Default mode when an observation arises mid-task and should not derail flow.
- `clarify` — promote an inbox item into a fully-articulated atomic note in `<root_dir>/active/`. Enforces ≥1 related link and assigns an expiry.
- `list` — filtered read-only view (next-step, tag, scope, status, priority, staleness, file overlap, orphan, dead-blocker).
- `resolve` — move a TODO to `<root_dir>/archive/` with Resolution notes; update cross-links on related TODOs.
- `review` — forced triage of expired items, orphan detection, dead-blocker detection, index regeneration.
- `import --from <path>` — one-shot migration of a flat markdown bullet list into atomic files.

If no mode is supplied or unrecognised, ask the user which mode to use.

## Configuration

Resolution order (first match wins):

1. Environment variable `UPDATE_TODOS_<UPPERCASE_KEY>` (e.g. `UPDATE_TODOS_ROOT_DIR`).
2. **Project-local** config at `<project_root>/.update-todos/config.yaml`.
3. **User-level** config at `~/.config/update-todos/config.yaml` — applies to non-path keys only (`inbox_wip_limit`, `active_wip_limit`, `default_expiry_days`). The `root_dir` is project-bound and is **never** read from this layer.
4. Built-in default (for non-path keys only).

The `root_dir` key is project-only by design. If a user installs `update-todos` in their home directory and invokes it across many repositories, each project keeps its own TODO tree. There is no fallback to a user-home location — that would mix one project's TODOs into another.

**Configure**

```sh
# First-time project setup (interactive)
python3 scripts/configure.py --scope project

# Non-interactive
python3 scripts/configure.py --scope project --root-dir doc/TODOs

# User defaults for non-path keys (applies across projects)
python3 scripts/configure.py --scope user --inbox-wip-limit 25

# Inspect resolution
python3 scripts/configure.py --print
```

**First-use flow.** If `root_dir` cannot be resolved (no env var, no project-local config), the agent must:

1. Detect the project root via `python3 scripts/find_project_root.py`. If it returns a path, suggest `<project_root>/doc/TODOs` as the default.
2. Ask the user "Where should TODOs live in this project? [default: <suggestion>]".
3. Persist the answer with `python3 scripts/configure.py --scope project --root-dir <answer>`.
4. Re-resolve and proceed. The prompt will not recur in this project.

If no project root is detected, refuse with the configure command and a one-line hint. Never fall back to a user-home location.

See [`references/config-schema.md`](references/config-schema.md) for the full schema.

## Workflow

Every invocation begins with:

**Step 0 — Resolve configuration.** Run `python3 scripts/resolve_config.py --all` and parse the `key=value` lines. Use the resolved `<root_dir>`, `<inbox_wip_limit>`, `<active_wip_limit>`, and `<default_expiry_days>` for every read and write below. If `root_dir` is empty, run the first-use flow above before continuing.

After Step 0, follow the action file matching the requested mode (paths relative to this SKILL.md):

- `capture`  → [`actions/capture.md`](actions/capture.md)
- `clarify`  → [`actions/clarify.md`](actions/clarify.md)
- `list`     → [`actions/list.md`](actions/list.md)
- `resolve`  → [`actions/resolve.md`](actions/resolve.md)
- `review`   → [`actions/review.md`](actions/review.md)
- `import`   → [`actions/import.md`](actions/import.md)

## Folder layout

Status is encoded by folder path. Path-based priors beat flat+index for LLM retrieval on long-lived corpora.

```
<root_dir>/
├── README.md                 # Generated from resources/README.md.tpl on first write
├── index.md                  # Auto-regenerated table of all TODOs; edited by review or any write
├── inbox/                    # Captured, not yet clarified — status = inbox
├── active/                   # Clarified, ready to action — status = open
├── blocked/                  # Waiting on another TODO or external event — status = blocked
├── deferred/                 # Someday/maybe, not currently actionable — status = deferred
└── archive/                  # Resolved or wont-fix — status = resolved | wont-fix | discarded
```

File naming: `TODO-YYYYMMDD-NNNN-<kebab-title-slug>.md`. The ID is permanent even if the file is moved between folders.

## Theoretical grounding

The skill operationalises Zettelkasten (atomic notes, permanent IDs, explicit links), GTD (capture → clarify, mandatory next-action, forced triage), and PARA (project / area / resource scopes). Citations and the mechanism-level mapping are in [`references/grounding.md`](references/grounding.md).

## Controlled `next-step` vocabulary (exactly 9)

Reject unknown values at capture time.

| Value | Meaning |
|---|---|
| `spec-update` | Change a requirement spec (subsumes design-update and in-spec documentation). |
| `implementation` | Change source code. |
| `diary-update` | Add historical context or lesson-learned to the developer-diary. |
| `brainstorm` | Needs ideation session (feeds into a brainstorming skill). |
| `refactor` | Code quality / naming / structural cleanup; no behavior change. |
| `investigate` | Research spike, decidability check, academic lookup. |
| `test` | Add or fix test coverage. |
| `decide` | Needs human (product-owner) decision. |
| `reproduce` | Bug-flavored; needs a reliable repro before anything else. |

Note: `review` is a **mode of this skill**, not a next-step. `documentation` is subsumed by `spec-update` or `diary-update` depending on whether the change belongs in the project's spec or the engineering narrative.

## Boundary with `developer-diary` (strict orthogonality)

**developer-diary** = time-indexed narrative of what happened in a subsystem. Answers "how did we get here, what did we try, what did we learn?"

**update-todos** = action-indexed pointers to future work. Answers "what remains to be done, why, and by whom?"

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
- A design smell, naming issue, or orthogonality violation.
- An unproven invariant or soundness question (`next-step: investigate`).
- A TODO or FIXME you encounter in source that lacks structured context.

Do NOT invoke `capture` for concerns that belong in:

- Developer diary (historical narrative, decision journal) — use `developer-diary update` instead.
- The spec itself (when the decision IS made and just needs documenting) — edit the spec.
- This session's task plan (still in scope, still being worked) — track inline, not in TODOs.
- **Anything that takes <2 minutes to fix** — just fix it. The 2-minute rule (Allen 2015) applies.
- **Anything that fits as an inline `// TODO` comment** — one-line, one-file, teammate can action in <30 minutes, context obvious from surrounding code. External capture is reserved for concerns that span files, specs, layers, or decisions.

## WIP limits (prevent corpus rot)

Kanban-style work-in-progress limits keep the system healthy. Defaults are configurable via the `inbox_wip_limit` and `active_wip_limit` keys:

- `<root_dir>/inbox/` ≤ `<inbox_wip_limit>` (default `20`).
- `<root_dir>/active/` ≤ `<active_wip_limit>` (default `15`).

If either limit is exceeded, `capture` refuses and tells the user to run `clarify` and `review` first. Capture is cheap only when downstream drains.

## Dedup, clarify, and review discipline

These are load-bearing. Details in action files. Summary:

- **Dedup at capture time** (action file). Hard signal: same file+line reference (±10 lines) as an existing TODO. Soft signal: Jaccard token similarity on `title + raw observation` ≥ ~0.55, with explicit weak-match warning. Never auto-merge — always surface candidates to the user.
- **Link density at clarify time** (action file). Refuse to promote a TODO from `inbox/` to `active/` without at least one `related` link to another TODO, a diary node, or a spec section.
- **Forced triage at review time** (action file). `review` cannot proceed past an expired TODO without recording extend / resolve / wont-fix / discard.

## Optional integrations

If the project uses other skills (e.g. project-context, project-audit, planning, brainstorming, debugging), they MAY consume signals from the TODO corpus. The integration contract is documented in [`references/integrations.md`](references/integrations.md). Honour it where present, ignore it otherwise.

## Quality bar

A TODO is well-written when a new engineer with zero session context can read it and know:

1. What the concern is (Summary + Problem).
2. Why it was deferred rather than actioned immediately (Rationale for deferral).
3. What files and spec sections they must read first (Required references).
4. What a plausible next action looks like (Proposed approach, very-next-action).
5. What "done" looks like (Acceptance criteria).

If any of these five are missing after `clarify`, the TODO is not ready to leave `inbox/`.

## Final behaviour

Treat `<root_dir>/` as a first-class project artefact. It lives under version control, it is regenerated on every write, and it is reviewed on cadence. Never edit a TODO file by hand without running `review` afterward to regenerate the index and verify bidirectional links.

## References

- [`references/config-schema.md`](references/config-schema.md) — full configuration schema and CLI usage.
- [`references/grounding.md`](references/grounding.md) — Zettelkasten / GTD / PARA citations and mechanism mapping.
- [`references/integrations.md`](references/integrations.md) — optional cross-skill integration contract.
- [`actions/capture.md`](actions/capture.md), [`actions/clarify.md`](actions/clarify.md), [`actions/list.md`](actions/list.md), [`actions/resolve.md`](actions/resolve.md), [`actions/review.md`](actions/review.md), [`actions/import.md`](actions/import.md) — per-mode procedures.
