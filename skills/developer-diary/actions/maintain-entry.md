# Maintain a single developer-diary entry

Use this procedure to verify a single existing diary entry against the current state of code, requirements, and surrounding diary nodes, then propose narrative-preserving amendments behind an explicit approval gate.

You operate as a strict linear pipeline. Do not skip phases. Do not write anything before the Phase 9 approval gate has been cleared.

## Resolve configuration first

Before doing anything else, resolve config by running:
```
python3 scripts/resolve_config.py --all
```

Hold `root_dir`, `feature_routing_file`, `node_token_limit`, `requirements_dir`, `todos_inbox_dir`, `todos_archive_dir` for use throughout. If `root_dir` is empty, follow the first-use flow in SKILL.md before continuing.

`requirements_dir` is optional and independent: when empty, requirement-ID drift checks are silently skipped throughout Phases 3, 4, and 5. `todos_inbox_dir` and `todos_archive_dir` are an optional coupled pair: when both are empty, TODO-ID drift checks are silently skipped; when both are set, TODO-ID drift checks run; when only one is set, the action stops at config-resolution time and reports the inconsistency (see the Edge cases table).

## Argument resolution

Resolve `$ARGUMENTS` to a diary-entry path in the following order:

1. **Direct path.** If the argument ends in `diary-entry.md`, use it as-is.
2. **Hierarchical index** (e.g. `R.2.2.9`). Split the index by `.` into segments. Start at `<root_dir>/developer-diary.md`. Find the row in its "Child nodes" table whose Index column matches the two-segment prefix `R.2`. Read that child's `diary-entry.md`. Repeat: in each intermediate file's "Child nodes" table, find the row matching the next-deeper segment (`R.2.2`, then `R.2.2.9`), and read it. The path of the last file read is the resolved target. If at any step the next segment is not present in the parent's child table, report the resolution attempt and stop.
3. **Shortform** (e.g. `child_23` or `child_2/child_2/child_9`). Prefix with `<root_dir>/` and suffix with `/diary-entry.md`.

**Reject** if the resolved path is `<root_dir>/developer-diary.md` (the root). The root is a routing/abstraction layer and is maintained as a side effect of child maintenance. Tell the user to invoke `developer-diary review` instead and stop.

**Reject** if the resolved path does not exist on disk. Report the resolution attempt and stop.

## Phase 1 — Load target

Read the resolved path. Parse the entry into its required schema sections:

- Index
- Last updated
- Title
- Relevant context
- Design decisions made
- Peers
- Progress made
- Outstanding items
- Problems encountered
- What works well
- Next steps
- Child nodes
- Relevant related diary nodes
- Notes and commentary
- Special instructions for next reader

If any required section is missing, **stop**. Report `STRUCTURAL DEFECT: missing section <name>` and recommend `developer-diary review`. Do not attempt structural repair — that is review-mode's job.

## Phase 2 — Surround-view gather

Read, in this order:

1. **Parent.** The `diary-entry.md` one directory level up. If the target is a direct child of the root (e.g. `<root_dir>/child_23/diary-entry.md`), the parent is `<root_dir>/developer-diary.md`.
2. **Children.** Every path listed in the target's "Child nodes" table. If the table is empty, skip with no error.
3. **Referenced peers.** Two sources, different extraction rules. (a) **"Peers" is prose** in actual diary entries (e.g. "Peer nodes that intersect: R.4 (CommonModule), R.1 (AppModule)..."). Extract diary index pointers from it using the same regex Phase 3 uses for diary indices (`R(\.\d+)+`). Resolve each match to a path via the argument-resolution procedure above. (b) **"Relevant related diary nodes" is a markdown table.** Read each row's `File name` column entry. Read every distinct node identified by either source. If both yield nothing, skip with no error.
4. **Routing context.** The resolved `feature_routing_file` (full file) and the `<root_dir>/developer-diary.md` "Last updated" section. These surface successor narratives that may discharge the target's claims without the target itself knowing.

Hold all surround-view content in working context for the drift analysis in Phase 4.

## Phase 3 — Inventory references

Extract every external reference cited in the target entry into a working table. Reference types and their detection:

| Reference type | Detection rule |
| --- | --- |
| File path | Anything matching `src/**`, `doc/**`, `test/**`, `scripts/**` |
| Identifier | Class / function / method names appearing in or near a file-path citation (example shape: an identifier `ClassOrFunctionName` cited next to `path/to/file.ext`) |
| Schema field | A field name cited in the same sentence as a schema file path (e.g. `serial_id` cited near `src/schemas/job.schema.ts`). Distinguished from generic identifiers by being declared as a typed schema property rather than a function/method. |
| Requirement ID | Regex `[A-Z]{3,}-\d{3,}` (example shapes: `AUTH-021`, `BILLING-103`). **Exclude** matches whose prefix names an external standards body: `ISO`, `IEC`, `RFC`, `CVE`, `SHA`, `IEEE`, `OWASP`, `ANSI`, `ITU`, `NIST`, `W3C`. A match qualifies as an internal requirement ID only if its prefix appears as a section identifier somewhere under `<requirements_dir>/**` (cheap to verify with a single `grep -r "<PREFIX>-" <requirements_dir>/`). **Inventoried only if `requirements_dir` is set; otherwise skip the type entirely.** |
| TODO ID | Regex `TODO-\d{8}-\d{4}`. **Inventoried only if `todos_inbox_dir` is set; otherwise skip the type entirely.** |
| Diary index pointer | Regex `R(\.\d+)+` |
| Commit SHA | Regex `\b[0-9a-f]{7,40}\b` in commit context — flagged immutable, no verification needed |

Record each reference's location in the entry (section name + paragraph index or line context) so Phase 6 can target edits precisely.

## Phase 4 — Drift checks

For each inventoried reference, run exactly one verification and record the result:

| Reference type | Check | Drift signal |
| --- | --- | --- |
| File path | `Glob` for the exact path. If missing, `Glob` for the basename across the repo. | Exact-path miss → possible rename or removal. **Single** basename hit elsewhere → likely move; record the new path. **Multiple** basename hits → ambiguous; record all candidate paths and flag for D-orphan classification in Phase 5. Never silently pick one. Basename miss → record as orphan. |
| Identifier | `Grep` the identifier in the cited file. If the file moved, `Grep` repo-wide. | Not found at cited site → rename/removal candidate. |
| Schema field | `Read` the cited schema file and look for the field declaration. | Missing field or different declared type → record as drift. |
| Requirement ID | `Grep` under `<requirements_dir>/**` for the ID. **Skipped entirely if `requirements_dir` is unset.** | Missing → drift. Present but status changed or wording diverged from the claim → drift with note. |
| TODO ID | `Glob` `<todos_inbox_dir>/<id>*.md` then `<todos_archive_dir>/<id>*.md`. **Skipped entirely if `todos_inbox_dir` is unset.** | Inbox → still open. Archive → discharged. Missing from both → orphan. |
| Diary index pointer | Resolve via root child table and parent child tables. | Missing → broken pointer. |

Commit SHAs are not verified — record them and move on.

## Phase 5 — Discharge mapping

Every drifted claim is classified into exactly one discharge bucket. This determines the amendment shape in Phase 6.

| Bucket | Meaning | Default amendment |
| --- | --- | --- |
| **D-spec** | Current spec captures or amends the claim. | Outward annotation pointing at the requirement section + date. |
| **D-code** | Current code matches what the entry flagged as planned/pending. | Outward annotation referencing the current site. |
| **D-diary** | A successor diary entry (peer, child, parent, or root-log mention) describes the new state. | Add row to "Relevant related diary nodes" and add an inline parenthetical annotation. |
| **D-todo-resolved** | Referenced TODO now in `<todos_archive_dir>`. *(Only reachable when `todos_inbox_dir` / `todos_archive_dir` are configured.)* | Outward annotation referencing the archived TODO. |
| **D-todo-open** | Referenced TODO still in `<todos_inbox_dir>`. *(Only reachable when `todos_inbox_dir` / `todos_archive_dir` are configured.)* | No action — claim is still live. |
| **D-reference-only** | Substantive claim still true; only the external reference token moved. | Inline token rewrite in place. No narrative change. |
| **D-orphan** | Claim has drifted but nothing else picks up the thread. | Surface as outstanding; optionally propose a new TODO. **Never blind-rewrite.** |

When discharge is ambiguous between two buckets, default to **D-orphan** rather than guessing.

## Phase 6 — Build amendment plan

Translate the Phase 5 discharge mapping into a concrete set of edits to the **target entry only**. Edits fall into exactly three categories:

1. **Reference-token rewrites.** Substitute the moved file path, renamed identifier, or shifted schema field name in place at the cited location. Narrative around the token is untouched.
2. **Outward-link annotations.** Additive. Either a short parenthetical at the end of the relevant paragraph or a new bullet appended to "Outstanding items" / "Relevant related diary nodes". Example annotation: `(Discharged 2026-MM-DD — superseded by R.x.y; see also requirement YYY-NNN amended on 2026-MM-DD.)`
3. **Structural updates.** Add/remove/rewrite rows in the "Child nodes", "Peers", or "Relevant related diary nodes" tables. Prepend a new dated line to the "Last updated" section summarising the maintenance pass.

**Hard rules — these constraints are non-negotiable.** Refuse to produce any amendment that violates them.

- **Never modify narrative prose** in `Relevant context`, `Design decisions made`, `Progress made`, `Problems encountered`, `What works well`, `Notes and commentary` (including its `Decision journal`, `Session context`, and `Uncertainties and risks` subsections per developer-diary's node-writing principles), or `Special instructions for next reader`. Narrative is history.
- Sections that **may** be amended by this action: metadata (`Index`, `Last updated`, `Title`), table-shaped sections (`Peers`, `Outstanding items`, `Next steps`, `Child nodes`, `Relevant related diary nodes`). All other sections are narrative-protected.
- **Never modify existing "Last updated" entries.** Only **prepend** a new dated maintenance line.
- **Never edit any file other than the target diary entry**, with one exception: when Phase 11's split handoff produces a new child node, the parent's "Child nodes" table row for the new child is the only other write, and that write is performed by `developer-diary update`, not by this skill.
- **Never blind-rewrite a D-orphan claim.** Annotate it; let the user decide.

## Phase 7 — Size estimate

Estimate the post-amendment token count using `ceil(<char count> / 4)`. Count is computed against the full entry text after all Phase 6 edits would be applied.

If the estimate exceeds the resolved `node_token_limit`, mark the plan `requires split` and route to Phase 11. Otherwise route to Phase 10.

The threshold is the resolved `node_token_limit` config value — the same constant `update` and `review` use as the per-node soft limit. Do not deviate.

**Split proposal.** When `requires split` is flagged, also produce a concrete split proposal: name the specific subsection(s) of the target entry that should migrate to a new child node, with one-sentence rationale per chosen subsection (e.g. "internally coherent block, no inbound cross-references from this node's other sections"). Prefer migrating leaf-like content (a specific sub-feature, a single sprint's narrative) over generic prose. This proposal becomes the `<X>` substitution in Phase 11's handoff brief. Without it, Phase 11 cannot proceed.

## Phase 8 — Report (chat output)

Produce a fixed-format report to the user. The report is ephemeral — chat only, not written to disk. The persisted record of the pass is the new "Last updated" maintenance line added in Phase 10/11.

Sections, in order:

````
# Maintenance pass — <entry path> (<index>)

## 1. Surround view consulted
- Parent: <path>
- Children: N nodes [<paths>]
- Peers: N nodes [<paths>]
- Routing context: <feature_routing_file>, root Last-updated log

## 2. Reference inventory
- Files: N
- Identifiers: N
- Requirement IDs: N    (0 if requirements_dir is unset)
- TODO IDs: N           (0 if todos_inbox_dir is unset)
- Diary index pointers: N
- Commit SHAs: N (not verified)

## 3. Drift findings
[no-drift case: print exactly `No drift detected.` and OMIT the table entirely.]
[drift-found case: print the table below with one row per drifted reference, every column populated; do NOT print the no-drift sentence.]
| Reference | Type | Drift | Discharge bucket | Evidence |
| --- | --- | --- | --- | --- |
| <one row per drifted reference, all 5 columns populated> |

## 4. Discharge mapping summary
- D-spec: N
- D-code: N
- D-diary: N
- D-todo-resolved: N
- D-todo-open: N (no action — claim still live)
- D-reference-only: N (token rewrites)
- D-orphan: N (surfaced below)

## 5. Proposed amendments (grouped by section of entry)
### <Section name>
+ PREPEND / + APPEND / ~ TOKEN REWRITE / ~ STRUCTURE UPDATE: <exact text>

## 6. Out-of-scope observations
- Suggested new TODO: "<title>" — covers D-orphan item N
- Edits to peer R.x.y — NOT applied; flagged for a separate `/developer-diary maintain` pass

## 7. Size assessment
Estimated post-edit: ~N tokens (under limit; direct apply path)
[OR: ~N tokens — exceeds node_token_limit (<value>); split required. Recommended split: <content X> → new child node <proposed index>]
````

Every row in §3 must trace back to a Phase 4 verification. The no-drift and drift-found presentations are mutually exclusive per the inline note in §3. In the no-drift case §4-§6 are correspondingly empty; the pass still runs through to Phase 9 so the user sees the surround-view summary and can confirm "no action needed."

## Phase 9 — Approval gate

**Hard stop.** Ask the user exactly:

> Approve amendment plan as-is / approve with edits / reject and re-analyse?

Wait for an explicit response. Do not write anything to disk yet.

- **Approve as-is** → route to Phase 10 (or Phase 11 if Phase 7 flagged a split).
- **Approve with edits** → capture the user's edits, present the revised amendment plan section once more (do not re-run §1-§4 of the report), wait for one explicit confirmation, then route.
- **Reject** → stop. Do not write. Offer to refine the analysis with specific feedback.

No write happens before this gate is cleared. A pre-emptive Edit is a contract violation; refuse it even if the amendment seems obviously safe.

## Phase 10 — Apply (direct path)

Apply in the strict sub-step order below. The ordering is a safety invariant, not a convenience: it guarantees that an interrupted pass is *detectable* rather than silently half-written.

### 10a — Re-read and re-anchor (mandatory, before any write)

The Phase 9 approval gate introduces an arbitrary pause between the Phase 1 read and the first write. The file may have changed in that window (the user, another tool, or a git operation). **Re-read the target entry from disk now** and compare it against the Phase 1 content:

- If the regions you are about to edit are byte-identical to what Phase 1 saw, proceed — re-derive every `old_string` anchor against this fresh read.
- If any cited region changed since Phase 1, **stop**. Report `STALE TARGET: entry changed since analysis` and tell the user to re-run `/developer-diary maintain` so the amendment plan is rebuilt against current content. Never apply a plan built on stale text.

### 10b — Apply content amendments (every category EXCEPT the "Last updated" stamp)

For each content amendment in the approved plan, perform a single `Edit` call. **Construct `old_string` with enough leading context (typically at least the preceding sentence, or the full table-row anchor) that the match is unique within the file.** If still ambiguous after one sentence of leading context, expand further before invoking `Edit`. Never use `replace_all` unless the token is genuinely unique repo-context-free (rare).

- **Reference rewrites:** exact-string substitution at the cited line. The token itself plus its leading context forms `old_string`; `new_string` substitutes the moved token only.
- **Outward-link annotations:** match `old_string` against the targeted paragraph tail with leading context per the uniqueness rule above; `new_string` is `<existing tail><space><annotation>`. Same rule for list-item annotations: include the preceding bullet's anchor text.
- **Structural updates** ("Child nodes" / "Peers" / "Relevant related diary nodes" tables): edit the relevant table row, using the row's Index/Feature-name column as the leading anchor.

**Mid-sequence failure is a hard stop — there is no transaction.** If any `Edit` in this sub-step fails to match (anchor not found, or not unique), **stop immediately**. Do not continue with the remaining amendments. Do not proceed to 10c. Report `PARTIAL APPLY: amendment <N> of <M> failed`, list exactly which amendments were applied and which were not, and tell the user the recourse is `git restore <entry path>` to return to a clean state, then re-run the pass. Because the "Last updated" stamp (10c) is not yet written, the absence of a new maintenance line is the reliable signal that the pass did not complete.

### 10c — Stamp "Last updated" LAST

Only after every content amendment in 10b has succeeded, prepend a new dated maintenance line above the existing top entry. `old_string` anchors on the heading `## Last updated\n\n` plus the first existing dated line for uniqueness. This is deliberately the final write: the new line's presence means the pass completed; its absence means it did not.

### 10d — Verify schema

After all amendments, re-read the entry and verify every required schema section is still present (the same list as Phase 1). If a section disappeared, report `POST-EDIT STRUCTURAL DEFECT` and stop — do not attempt repair. The user's recourse is `git restore` followed by `developer-diary review`.

The "Last updated" maintenance line format:

```
2026-MM-DD (maintenance pass: <one-sentence summary of what was annotated / discharged / relinked>)
```

## Phase 11 — Apply (split handoff path)

When Phase 7 flagged `requires split`:

1. Pause. Surface the split proposal from report §7 as a single user-facing summary: which content moves where, suggested new child index, and why the split is needed.
2. Wait for explicit user approval of the split itself. Reject → stop.
3. After approval, invoke the `developer-diary` skill in `update` mode via the `Skill` tool with this brief:

   > Maintenance pass on `<target entry>` identified content `<X>` that should split into a new child concern. Please create the child node at the proposed location under `<root_dir>`, migrate the listed content, and update the parent's "Child nodes" table. Do not modify parent narrative beyond the table update; this maintenance pass will then resume to apply the remaining amendments to the parent.

4. After the handoff returns, re-read the target entry. Re-run Phase 7's size estimate.
5. If now under the limit, proceed to Phase 10 for the remaining amendments. If still over, surface the failure: report which content remains in the parent and recommend a second-pass review with the user. Do not recurse into another split — the next split decision is user-facing.

## Phase 12 — Verify and close

- Re-read the target entry.
- Confirm all required schema sections (Phase 1 list) are present.
- Confirm the new "Last updated" maintenance line is at the top of the "Last updated" section.
- Confirm no narrative section was modified.

Produce a one-paragraph chat summary of what changed, referencing the Phase 8 report sections (§5 amendments, §6 out-of-scope) for detail. This is the closing message of the pass.

## Edge cases

| Case | Behaviour |
| --- | --- |
| Target resolves to `<root_dir>/developer-diary.md` | Reject at argument-resolution; point at `developer-diary review`. |
| Target has no children | Phase 2 step 2 is empty; no error. |
| Target has no peers or related nodes | Phase 2 step 3 is empty; no error. |
| Referenced peer's file does not exist | Report as `broken diary pointer`; classify D-orphan; propose annotation. Never silently remove a structural pointer. |
| Inventoried file path cannot be located by basename | Report as D-orphan with the cited basename; propose annotation. Never blind-rewrite. |
| Drift detected but discharge is ambiguous | Default to D-orphan rather than guessing. |
| User rejects the amendment plan | Stop. Do not write. Offer to refine the analysis. |
| Schema validation fails after apply | Report explicitly. Do not attempt auto-repair (belongs to `developer-diary review`). |
| Target entry changed during the Phase 9 approval pause | Phase 10a re-read detects it. Report `STALE TARGET` and stop; user re-runs the pass so the plan rebuilds against current content. |
| An `Edit` fails mid-sequence in Phase 10b | Hard stop — no transaction. Report `PARTIAL APPLY: amendment <N> of <M>`, list applied vs unapplied, recourse is `git restore <entry path>`. The "Last updated" stamp is written last, so its absence proves the pass did not complete. |
| Required section missing in target entry on load | Report structural defect and stop. |
| Argument cannot be resolved to a valid path | Report the resolution attempt and stop. |
| Reference of type requirement/TODO encountered but corresponding config key unset | Silently exclude from inventory; do not warn. The exclusion is reported as `0` in the Phase 8 "Reference inventory" section. |
| `todos_inbox_dir` set but `todos_archive_dir` unset (or vice versa) | Configure.py rejects this at write time. If encountered at runtime (manual config edit), report the inconsistency and stop before Phase 3. |

## Hard rules (recap)

These constraints apply across every phase. Violating any one of them is a contract failure — refuse the action and report it to the user.

1. **No write before Phase 9 approval.** Read-only-until-approved is the strongest invariant.
2. **Never modify narrative prose** in `Relevant context`, `Design decisions made`, `Progress made`, `Problems encountered`, `What works well`, `Notes and commentary` (including its `Decision journal`, `Session context`, and `Uncertainties and risks` subsections), or `Special instructions for next reader`. Sections that **may** be amended: `Index`, `Last updated`, `Title`, `Peers`, `Outstanding items`, `Next steps`, `Child nodes`, `Relevant related diary nodes`.
3. **Never modify existing "Last updated" entries.** Only prepend a new dated maintenance line.
4. **Never edit any file other than the target diary entry**, except indirectly via the Phase 11 `developer-diary update` handoff.
5. **Never blind-rewrite a D-orphan claim.** Annotate it.
6. **Never silently delete a structural pointer** (peer, child, related node) just because its target moved. Annotate; let the user decide.
7. **Never attempt structural repair** of a malformed entry. That is `developer-diary review`'s job.
