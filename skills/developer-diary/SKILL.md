---
name: developer-diary
description:  Manages persistent engineering knowledge across sessions in a developer-diary. Reads diary before design/implementation tasks, updates it after, and reviews it for structural repair. Invoke with read, update, or review. Use this skill before a design or implementation task starts to 'read' the developer diary and get relevant context. Use this skill to 'update' the developer diary after a completing a design or implementation task to update the diary and retain notes on progress and lessons learned. Use this skill to 'review' for maintaining and repairing issues with the developer diary. 
allowed-tools: Bash Read Grep Glob Write Edit
effort: medium
context: fork
agent: general-purpose
argument-hint: "[read|update|review]"
---


## Invocation modes
You are invoked in **$ARGUMENTS** mode.

- If mode is `read`:  follow the instructions in `${CLAUDE_SKILL_DIR}/actions/read-diary.md`. This is executed before an implementation or design task to selectively get relevant context information. 
- If mode is `update`: follow the instructions in `${CLAUDE_SKILL_DIR}/actions/update-diary.md`. This is executed after completion of an implementation or design task when context is still fresh o update the developer diary with all relevant information. 
- If mode is `review`: follow the instructions in `${CLAUDE_SKILL_DIR}/actions/review-diary.md`. This is executed occasionally to review and repair the diary structure in order to maintain integrity, consistency, and accurateness of the information. 
- If no mode is provided or mode is unrecognised: ask the user which mode to use.



You maintain the developer diary as your personal engineering notebook — the place where you write down everything a trusted colleague needs to know to continue your work. You write like a conscientious engineer clocking off for the day: not just what was done, but how you thought about it, what you tried, what surprised you, what you're unsure about, and what the next person should watch out for. You capture your internal monologue — doubts, reasoning traces, alternatives considered, "aha" moments, things that feel fragile, gut feelings about risks.

You are keenly aware that your context window is limited and the next engineer reading your notes starts with zero context. You write with enough richness that reading a diary node feels like getting a thorough handoff from the person who did the work — not like reading a change log.

**The quality bar:** If a new LLM reads your diary entry and still needs to read every source file and spec section you referenced to understand the decisions and trade-offs, your entry is too sparse. The diary should transfer understanding, not just facts.

When executing a task, you always use the diary to remind yourself of where you left off, past progress and lessons learned. The same holds for team members that come and go. New team members can use the diary to quickly get the relevant background to execute their tasks. As the knowledge becomes large, the diary is organised in a tree hierarchy. The purpose is to get to relevant details efficiently, without polluting the context window or exceeding cognitive load. The strategy is a combination of abstraction and divide-and-conquer. The tree hierarchy helps to avoid reading irrelevant information.

Each node abstracts and summarises over all its children. Hence, the root node contains an overarching summary of the entire project. For example, at root-level the "Relevant context" section summarises the entire software project, what the library is about, motivation and intentions, and references requirements.


## Diary location and file layout

The root node is always:

`doc/developer-diary/developer-diary.md`

Each child node is stored in a numbered child directory with file name:

`diary-entry.md`

Examples:
- `doc/developer-diary/child_1/diary-entry.md`
- `doc/developer-diary/child_3/child_6/diary-entry.md`

The diary hierarchy mirrors the software architecture. Higher nodes (closer to root) contain routing and abstraction. Lower nodes contain narrower implementation detail.

Each diary-entry.md node must strictly follow a fixed schema with all required section headings present, though only Index, Last updated, Title, and Relevant Context must always contain meaningful content. Each section serves a specific role, including uniquely identifying the node and providing sufficient technical context, tracking decisions, progress, issues, and next steps—ensuring developers can continue work seamlessly based on the node’s position in the hierarchy. Nodes should remain modular, under ~4000 tokens, and organized into child nodes when necessary, with clear relationships, no duplication, and a single source of truth across the developer diary structure.



## Node-writing principles

### Content richness (highest priority)
- **"Notes and commentary" is the most important section.** It captures the internal monologue — decision reasoning, session context, uncertainties, observations. Never leave it empty. Structure it with subsections: Decision journal, Session context, Uncertainties and risks.
- **Design decisions must include alternatives.** Never write "We chose X" without naming at least one alternative and explaining why X won.
- **Problems must include the diagnosis story.** Never write "No problems encountered" unless the work was truly trivial. Describe what you debugged, even if the fix was quick.
- **Progress entries must include WHY, not just WHAT.** "Implemented X because Y; the key insight was Z" — not just "Implemented X."
- Include what was referenced during the session: spec sections, source files, test results, error messages, other diary nodes read.
- Include confidence assessments: what feels solid, what feels fragile, what assumptions might be wrong.
- Write durable engineering knowledge, not chat transcripts — but durable knowledge includes reasoning, not just conclusions.

### Structure and scope
- Keep each node focused on a single architectural concern.
- Assume the reader already understands the nodes on the direct path from root to the current node.
- Do not duplicate large amounts of information from parent or sibling nodes.
- Prefer a single source of truth. Use `Relevant related diary nodes` for cross-references instead of duplicating content.
- Make sure that relevant knowledge that is in context window while writing the diary is explicitly referenced.
- Put immediate handoff instructions in `Special instructions for next reader`. Remove or migrate them once consumed.
- Keep markdown easy to scan and navigate.

## Size limit and splitting

A single diary-entry node should remain below an estimated 4000 tokens.

If a node would exceed that size:
1. split it into independent child concerns,
2. keep the parent as an abstraction and routing layer,
3. move detailed content into new child nodes,
4. add the children to the parent `Child nodes` table,
5. update peer scoping where needed.

Prefer low coupling between peers. Avoid unnecessary cross-links between unrelated branches.


## Quick deep access reference

At top level, maintain a quick reference where to find features (file doc/developer-diary/feature-routing.md). 
The file contains a tabular index of identifiable units of the architecture (e.g. packages, modules, components, functions, features, etc)
The table structure is as follows (example): 
```md
| Feature name | Index | Description |
| --- | --- | --- |
| HM Type System | R.1.2.1 | `MonoType`, `PolyType`, `Linearity`; Algorithm W (Milner 1978) inference; `typeCheck(db)`; `typeof/2` clauses in ClauseDB; advisory, non-blocking |
```
When updating (mode update) the developer diary, also update the feature-routing.md table accordingly. 


## Final behavior

Treat the diary as a shared engineering memory:
- read it before meaningful implementation or design work,
- update it after meaningful implementation or design work,
- review and repair it when explicitly asked or when a concrete inconsistency is discovered.

