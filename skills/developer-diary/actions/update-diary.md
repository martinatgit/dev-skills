

# Update developer diary


# When to update the developer diary

Use this procedure when explicitly asked to create or update a developer diary entry or after meaningful implementation or design work has been completed and the context and memory of executing it is still fresh.


## 1. Rich context capture

Before editing any diary files, produce a comprehensive internal context dump. This is the most important step — everything you write into the diary flows from this. Do NOT skip items; do NOT summarise prematurely. Capture:

### What happened
- What task was performed and what motivated it (the "why", not just the "what")
- What was the starting state? What existed before you began?
- What was the end state? What exists now?

### What was in your context
- Which specification sections did you read or reference?
- Which source files did you read, modify, or create?
- Which test files did you run? What were the results (pass counts, specific failures)?
- Which error messages did you encounter? (Include the actual text, not just "there was an error")
- Which diary nodes, design docs, or requirements did you consult?

### What you tried
- What approaches did you consider? Why did you choose this one?
- What did you try that DIDN'T work? Why did it fail?
- What alternatives were rejected? Why? What would make you reconsider?

### What surprised you
- What behaved differently than expected?
- What non-obvious interactions did you discover?
- What was harder or easier than anticipated? Why?

### Your confidence assessment
- What feels solid and well-tested?
- What feels fragile, under-tested, or like it might break?
- What assumptions did you make (explicit and implicit)?
- What questions remain unanswered?
- What does the next engineer need to know that ISN'T obvious from the code?

### Your internal state
- What are you proud of in this work?
- What are you uncertain about?
- Where did you take a shortcut or make a pragmatic compromise?
- What would you do differently with more time?
- What "gut feeling" do you have about risks or missing pieces?

Use this context dump to decide which diary node owns the information AND to write the rich content that follows.

The user might have given specific hints where and what to update. Look specifically for references to child nodes, diary entries, child entry, peer entry, subdirectory, and topic keywords that give an indication where in the software hierarchy a component is located. Sometimes the user might give the title of the diary entry, its index (e.g. R.3.4.1), or a short description that is diagnostic to identify context. Understand the user intent from the identified content.


## 2. Content quality standards

The diary is an engineer's personal notebook — not a status report. Write as if you're briefing a trusted colleague who will continue your work tomorrow. They need to understand not just WHAT you did, but HOW you thought about it, WHAT you considered, and WHERE the bodies are buried.

### Quality bar: before and after

**BAD entry (sparse, useless for continuation):**
```md
## Progress made
- Implemented PropagatorEngine with fixpoint propagation
- Added 30 tests

## Problems encountered
- None

## Notes and commentary
- Source: src/aiqeung-core/propagator.ts
```

**GOOD entry (rich, enables seamless continuation):**
```md
## Progress made
- Implemented PropagatorEngine (981 lines, `src/aiqeung-core/propagator.ts`).
  Core design follows Schulte/Gecode event-based scheduling but adapted for
  immutable-value semantics (no trailing — snapshot IS the value). Deliberate
  departure from Gecode's mutable model because aiqeung uses reference-based
  backtracking (see Layer 0 solver).
- Fixpoint loop schedules propagators by priority (unary > binary > linear >
  quadratic > expensive), fires until no domain changes. Event hierarchy
  (ground ⊂ bounds ⊂ domain) prevents redundant propagation.
- 30 tests covering: basic domain ops, constraint posting, fixpoint convergence,
  checkpoint/restore round-trip, empty domain (wipeout) detection, event hierarchy
  ordering. Coverage gap: no stress test with >50 variables.

## Problems encountered
- **Domain intersection with symbolic bounds was tricky.** `inf`/`sup` meant
  I couldn't use `Math.min/max`. Wrote `Bound.lt()` comparator. Initially got
  `[inf, 5] ∩ [3, sup]` wrong (returned `[inf, sup]` — both comparisons
  short-circuited on symbolic values). Fixed by treating `inf` as always-less
  and `sup` as always-greater. Added regression test.
- **Fixpoint termination:** Could the loop cycle? No — every propagator only
  narrows (monotonic) and finite domains have finite narrowing chains. Added
  max-iterations guard (1000) as safety net. Hasn't fired in any test.

## Notes and commentary

### Decision journal
- **Immutable vs. mutable engine:** Chose immutable because aiqeung's
  backtracking is reference-based (restore = reassign pointer). Mutable would
  need undo trail. Tradeoff: slower for large domains (full copy on narrow).
  Acceptable for current scale (<100 vars). Can add mutable-trailing behind
  same interface later — API doesn't expose mutation. **Confidence: high.**
- **Event hierarchy over flat events:** Schulte's model. ~40% fewer wake-ups.
  15 lines of code (Set inclusion check). No downside. **Confidence: very high.**

### Session context
- Spec: `doc/proposed-layer4-5-specification.md` §10B.1
- References: Schulte "Programming Constraint Services", Triska SWI-CLP(Z),
  Michel MiniCP
- Created: `src/aiqeung-core/propagator.ts` (981 lines)
- Tests: `tests/aiqeung-core/propagator.test.ts` (30 tests, all pass)

### Uncertainties and risks
- `all_different` uses naive O(n²) pairwise `neq`, not Régin (1994). Correct
  but weak. Fine for small sets; needs Régin for Layer 6 large enumerations.
- `sum_eq` assumes integer domains. Real-valued domains would need different
  propagation. Safe for now (only CLP(Z) planned).
```

### Anti-patterns — what NOT to write

| Anti-pattern | Why it's harmful | Write this instead |
|---|---|---|
| "Implemented X" | No context on why, how, or what was hard | "Implemented X because Y; the key insight was Z; took approach W after rejecting V" |
| "No problems encountered" | Almost certainly false — you debugged something | "Initial approach worked cleanly" OR describe what you debugged even if the fix was quick |
| "Tests pass" | Which tests? How many? What do they cover? | "N tests in `path/to/test.ts` covering: [scenarios]. Gap: [what's not tested]" |
| Empty "Notes and commentary" | The most valuable section, left blank | Always write: decision journal + session context + uncertainties |
| Design decisions without alternatives | "We chose X" — why? What else existed? | "Chose X over Y and Z because [reason]. Would reconsider if [condition]" |
| "Next steps: implement Y" | No context on priority, dependencies | "Next: Y (blocked on Z, priority: high because W)" |
| Bare source file listings | "Source: `foo.ts`" — git shows that | "Source: `foo.ts` — critical function is `bar()` which handles [tricky case]" |


## 3. Find the relevant diary entry node

Locate the relevant diary entry node by trying the below methods sequentially. First decide if the method is applicable (e.g. that you have relevant information to use the method). If not applicable skip and try the next listed method. If applicable, but the method does not yield a result, try the next method.

Methods to try to find the relevant diary entry node:
1. follow explicitly mentioned node references and retrieve nodes accordingly
2. walk the developer-diary hierarchy:
  a) mentally plan what to look for based on given information (e.g. node title, content, key words, etc) and where in the developer diary hierarchy you would expect to find the content
  b) start by reading the root node and review listed child nodes
  Repeat the following:
    b1) Review all listed child nodes of the current node including their descriptions. Decide which path to take in the hierarchy, i.e. which child likely contains the relevant information. If no child exists, or no child matches, return the current node
    b2) if a child matches, open and read the referenced `child_X/diary-entry.md` file. Take this as your new current node. repeat steps from b1.
  c) Return the node that most closely matches the requested context.

Ownership rule:
- update the most specific existing node that should remain the single source of truth for the information.
- If asked to create new entry node, identify the parent where to add the node. Create the new node and update the parent accordingly

If no existing node cleanly owns the concern:
- find the best fit in the developer-diary tree hierarchy
- create a new child under the nearest correct parent.


## 4. Evaluate whether to create a child node

Before writing content into the target node, evaluate whether the work should go into a new child instead of the current node. The goal is proactive decomposition — do not wait for the 4000-token hard limit to split.

**Create a child node when ANY of these signals apply:**

### Signal 1 — New source directory
The work introduced or substantially fills a new source directory (e.g., `src/aiqeung-core/verification/`, `src/aiqeung-core/context/`). A directory boundary in code usually corresponds to a concern boundary in the diary. If the parent node already covers the parent directory, the new sub-directory gets its own child node.

### Signal 2 — Multiple distinct API surfaces
The update would record 3 or more independently usable public API surfaces (e.g., `PropagatorEngine`, `TheoryRegistry`, `kInduction`) within a single node. Each distinct API surface that could be described, tested, and maintained independently likely deserves its own node.

### Signal 3 — Approaching size limit
The node is estimated above 60% of the 4000-token guideline AND the content covers 2+ separable sub-topics. Do not wait for the hard limit. Split proactively — surgical splitting of an oversized node is harder than creating children early.

### Signal 4 — Dedicated spec or design section
A specification document, requirements document, or design document has a dedicated subsection for this concern (e.g., a spec with §10B.1 through §10B.4 maps to 4 potential child nodes). The diary hierarchy should mirror the spec hierarchy where the spec captures real architectural decomposition.

### Signal 5 — Temporal milestone with distinct scope
A significant implementation phase completed (e.g., "Phase 1: Layer 0 Propagator Engine") that represents a coherent body of work distinct from ongoing work in the same node. If the completed phase and the next phase address different concerns, the completed work should be in its own child.

**Decision rule:** When uncertain, prefer creating a child. An unnecessary child that can be merged later is cheaper than an oversized parent that must be surgically split later. A node with 3 children that each cover one concern is always easier to navigate than one node covering all three.

If you decide to create children, proceed to step 8 (Creating a new child node) before writing content. Route the current update content into the appropriate new child, and update the parent to summarize and route.


## 5. Decide whether to update or split

If the target node already owns the concern and can stay below the size limit:
- update the existing node.

If the target node is becoming too broad or too large:
- split the concern into a new child node,
- keep the parent as a summary and routing layer.


## 6. Write the entry content

Apply changes to the target node carefully. Make sure no content is accidentally lost. If new information is available to update outdated content, update accordingly.

**Content-first rule:** For each section you update, refer back to your Step 1 context dump. Ask: "Have I transferred all the relevant context from my working memory into this diary entry?" If not, keep writing. Rich content in 5 sections beats sparse content in 12 sections.

### Verification rule

When recording quantitative claims (test counts, file counts, line counts, export counts), verify them with a quick command before writing. Examples:
- Test count: `npx vitest run 2>&1 | tail -3`
- File count: `ls src/path/*.ts | wc -l`
- Source exists: `ls src/path/file.ts`

Do not run full test suites or expensive commands. Use the fastest command that confirms the number. If verification is impractical, prefix the claim with "approximately" or "estimated."

### Section-by-section guidance

Update these sections as appropriate. Sections are listed in **order of importance for content richness**, not in schema order.

#### Notes and commentary — THE MOST IMPORTANT SECTION

This is the heart of the diary entry. It captures the internal monologue — what a good colleague would tell you over coffee. **Never leave this empty.** Structure it with these subsections:

**Decision journal** — For each non-trivial decision made during the session:
- What was decided
- What alternatives were considered
- Why this choice was made (the real reason, not the rationalisation)
- What would change the decision (future conditions that might invalidate it)
- Confidence level (high / medium / low)

**Session context** — What was referenced during this work session:
- Spec sections read (with section numbers)
- Source files read, modified, or created (with line counts or key functions)
- Test results (pass/fail counts, specific failures if any)
- Error messages encountered (actual text, not just "there was an error")
- External references consulted (papers, docs, other projects)
- Other diary nodes read (with their indices)

**Uncertainties and risks** — What the next engineer should be careful about:
- What feels fragile or under-tested
- What assumptions might be wrong
- What edge cases weren't considered
- What performance concerns exist
- What would you red-team if you had more time

**Observations and insights** (when applicable):
- Patterns noticed across the codebase
- Emerging architectural concerns
- Ideas for future improvement (clearly marked as ideas, not commitments)
- Things that went surprisingly well (and why — so the pattern can be repeated)

#### Design decisions made
Don't just list decisions — capture the reasoning. For each decision:
- State the decision clearly
- Name at least one alternative that was considered
- Explain why the chosen approach won
- Note the tradeoff accepted

Use prose or structured bullets, not bare one-liners.

#### Problems encountered
Record real problems AND their resolution. Include:
- What happened (the symptom)
- What you investigated (the diagnosis process)
- What the root cause was
- How you fixed it (or why you deferred)
- How to recognise if the same problem recurs

Never write "No problems encountered" unless the implementation was truly trivial (<30 min, zero debugging). If you spent time debugging, describe what happened even if the fix was a one-liner.

#### Progress made
Record concrete progress with context:
- What was implemented, including WHY it was needed (not just "implemented X")
- Key implementation details that aren't obvious from the code
- Test coverage (which scenarios are tested, which aren't)
- Integration points with other layers/modules
- Commit references where helpful

#### Relevant context
Update when the durable understanding of the node has changed. This section should give the reader enough context to understand everything below it without needing to read parent nodes beyond the direct path.

#### Outstanding items
Keep as the durable remaining work list. For each item, include enough context that a new engineer can understand the scope and priority.

**Cleanup rule:** Remove completed items (marked `[x]` or with strikethrough) from `Outstanding items`. They are already captured in `Progress made`. Keep only open items. This prevents token waste and attention pollution from historical completions.

#### What works well
Capture what is stable, proven, or low risk. This tells the next engineer what they can rely on without re-verifying.

#### Next steps
Record the most immediate unfinished follow-up work. For each step:
- What needs to be done
- Why it's next (priority, dependency, blocking status)
- Any context needed to execute it (specs to read, constraints to observe)
- Estimated complexity (trivial / moderate / complex / research-level)

#### Last updated
Always set this to today's date (YYYY-MM-DD) when modifying a node. This enables staleness detection during read operations.

#### Peers
Update if the node's boundaries relative to siblings changed.

#### Special instructions for next reader
Use only for urgent handoff items that need immediate attention.
Do not store long-term information here. Remove or migrate once consumed.


## 7. Parent and peer maintenance

Whenever a new child is added or sibling boundaries change:

- update the parent `Child nodes` table,
- update the new child's `Peers` section,
- update affected sibling `Peers` sections when needed so the sibling set remains consistent.

Also ensure:
- all peer files in the same parent directory are represented in the parent `Child nodes` table,
- peer scoping is mutually coherent,
- descriptions are selective enough to support future reading.

**Cross-reference rule:** If the work involved nodes outside the current branch (e.g., Layer 0 changes made while implementing Layer 4), add a row to `Relevant related diary nodes` in both the current node and the referenced node, with a one-sentence description of the relationship. This ensures developers can discover cross-cutting dependencies by reading either node.

**Feature routing:** If the update introduces a new architecturally identifiable feature, renames an existing one, or changes its diary node location, update `doc/developer-diary/feature-routing.md` accordingly. For bulk updates, defer to the next `/developer-diary review` cycle which regenerates the full table.


## 8. Creating a new child node

If a new child node is needed:

1. identify the parent node,
2. choose the next available child number under that parent,
3. create a directory named `child_<n>`,
4. create `diary-entry.md` in that directory,
5. assign the child index by appending `.<n>` to the parent index,
6. add a row to the parent `Child nodes` table.

### New node template

Use this exact template:

```md
## Index

<index>

## Last updated

<today's date YYYY-MM-DD>

## Title

<short title>

## Relevant context

<durable context for this concern>

## Design decisions made

-

## Peers

<scope relative to sibling nodes>

## Progress made

-

## Outstanding items

-

## Problems encountered

-

## What works well

-

## Next steps

-

## Child nodes
| Index | File name | Description |
| --- | --- | --- |

## Relevant related diary nodes
| Index | File name | Description |
| --- | --- | --- |

## Notes and commentary

### Decision journal

### Session context

### Uncertainties and risks

## Special instructions for next reader
```


## 9. Size-limit enforcement

Estimate whether the updated node exceeds the 4000-token guideline.

**Important:** The 4000-token limit exists to prevent context pollution during reading, NOT to encourage brevity. A 3900-token entry that is 80% rich narrative is far more valuable than a 1500-token entry that is 100% dry bullet points. When you need to trim for size, remove structural overhead and repetition first — never sacrifice decision context, reasoning traces, or uncertainty documentation.

If yes:
- split the node into child concerns:
    - identify the topics and concerns that are orthogonal and mutually independent that can be split into individual child nodes of the diary (apply software engineering expertise to modularise, decouple and identify separable boundaries (e.g. module, component, class, function, artefact, etc))
    - mentally plan how many children to produce, give each child topic an identifiable type and scope, and what content aggregates and summarises over all children to keep in current node
    - plan minimally necessary cross references between the children (peers)
    - review and verify your plan, adjust if needed
    - create the child_X subdirectories for each planned child (where X is the ID of the child node)
    - create in each child directory a `diary-entry.md` file and set the correct ID and title content
    - then for each planned child do the following:
      - populate the content of the child_X/diary-entry.md file with the planned child contents,
      - review that the content is accurate and minimises overlap to other peer children and cross links
- modify the parent as a concise summary and router, only leave content in the parent that is common across all child diary-entries.
- Make sure all child nodes are properly referenced with id and matching short description in parent node.


## 10. Final validation before finishing

After editing, re-read every file you changed and check:

- heading schema is complete and in the correct order,
- index is correct,
- child and related-node tables are valid markdown,
- all referenced files exist,
- parent-child relationships are consistent,
- peer descriptions remain coherent,
- the update reflects the work accurately,
- **Notes and commentary is not empty** (if it is — you skipped the most important section; go back),
- **Design decisions include reasoning** (not just bare statements),
- **Problems encountered is honest** (reflects actual debugging effort, not just "none").


## 11. Finish with an update summary

When done, produce a concise summary of:
- which nodes were updated or created,
- what knowledge was added or changed,
- any structural changes made,
- and any follow-up review that is still needed.
