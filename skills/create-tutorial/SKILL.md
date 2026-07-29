---
name: create-tutorial
description: Generate a comprehensive, textbook-style technical tutorial for a newly implemented or modified software component. Use whenever the user types /create-tutorial <topic>, asks for "a tutorial on X", says "write a textbook chapter for this module", or similar. The topic is passed as the first argument; prefer this skill over ad-hoc explanations whenever the goal is a durable, self-contained artefact (not a chat answer). Do not use for inline explanations, short notes, or session handoff — use developer-diary for the latter.
---

# Create a Technical Tutorial

Create a technical tutorial for the topic supplied by the user (see Inputs below).

A technical tutorial serves as:
- A long-term knowledge artifact for developers
- A validation layer ensuring implementation aligns with intent and requirements
- A structured reference for both human engineers and LLM agents

The tutorial must be **self-contained**, requiring no external context to understand the system.

---

## When to use

- The user types `/create-tutorial <topic>` or asks for "a tutorial on X".
- The user wants a durable, self-contained walkthrough of a component, feature, or subsystem — not a chat answer.
- A new module, API surface, or workflow has just landed and needs textbook-style documentation for future engineers.

## When not to use

- Inline chat explanations (just answer).
- Short notes or session handoff — use `developer-diary` instead.
- API reference docs only (the tutorial format is broader; use a tighter reference doc if reference is all you need).
- Bug fixes or how-to-troubleshoot writeups — those belong elsewhere.

---

## Configuration

Resolution order (first match wins):

1. Environment variable `CREATE_TUTORIAL_TUTORIALS_DIR`.
2. Project-local config at `<project_root>/.create-tutorial/config.yaml`.
3. Shared conventions file at `<project_root>/.agents/dev-skills.yaml` — composes `tutorials_dir` as `<docs_root>/skills.create-tutorial.subdir`, defaulting to `<docs_root>/tutorials`.
4. Built-in default `doc/tutorials`.

See [`references/config-schema.md`](references/config-schema.md).

## Inputs

The user provides a topic — a component, feature, or subsystem to document. Acceptable shapes:

- A folder or file path (`src/auth/middleware.ts`).
- A symbolic name (`event-stream-processor`).
- A free-text description (`the new tenant-isolation module`).

Optionally, the user may supply a target filename. If absent, derive a kebab-case filename from the topic.

## Workflow

**Step 0 — Resolve configuration.** Run `python3 scripts/resolve_config.py --all` and parse the `key=value` lines. Use the resolved `tutorials_dir` as the destination directory for every write below. If `tutorials_dir` is empty (no env var, no project config, no shared file), run the first-use flow: `python3 scripts/configure.py --scope project` and re-resolve.

Then follow the structure below to produce the tutorial.

---

## Inputs & Assumptions

Before generating the tutorial:
- Use all available context (code, APIs, comments, architecture, requirements)
- If critical information is missing, explicitly state assumptions
- Infer design intent where necessary, but clearly label inferred vs explicit behavior

---

## Output Requirements

Write a **textbook-style technical tutorial** with the following structure:

### 1. Introduction
- Problem the software solves
- Motivation and use cases
- Design philosophy and guiding principles
- Constraints and tradeoffs

### Prerequisites
- What should the reader already know
- What must be installed
- Necessary and available configuration

### 2. System Architecture
- High-level architecture overview
- Role of this component within the system
- Interaction with other components
- Data flow and control flow

### 3. Core Concepts
- Key abstractions and mental models
- Terminology definitions
- Important invariants
- Relevant fix points

### 4. API and Functional Overview
For each major API / function:
- Purpose
- Inputs / outputs
- Preconditions / postconditions
- Side effects
- Error handling behavior

### 5. Worked Examples
- Realistic multiple usage scenarios covering distinct domains
- Step-by-step walkthroughs
- Include edge cases and failure modes

### 6. Implementation Insights
- Key algorithms and data structures
- Complexity analysis (time/space where relevant)
- Design tradeoffs vs alternative approaches
- Deviations from standard practices (if any)

### 7. Comparative Analysis
- How this approach compares to common patterns or libraries
- Strengths and weaknesses
- When NOT to use this component

### 8. Integration Guidance
- How other components/layers should interface with this
- Extension points and customization
- Common integration pitfalls

### 9. Outlook
- Future improvements or scalability considerations
- Potential evolution of the component

### 10. Testing Strategy
- Unit tests
- Integration tests
- Edge cases covered

---

## Style Guidelines

- Write for **senior developers and LLM agents**
- Be precise, not verbose
- Prefer clarity and being explicit to minimise ambiguity
- Prefer explicit descriptions over implicit assumptions
- Avoid ambiguous references like "this" or "that"
- Use consistent terminology
- Use markdown formatting:
  - headings
  - bullet points
  - code blocks for examples
- Avoid vague language like “simple” or “easy”
- Include ASCII or mermaid diagrams where helpful

---

## Examples

### Example 1 — typical case

**User:** "Write a tutorial for the new tenant-isolation middleware."

**Skill output:** A markdown file at `<tutorials_dir>/tenant-isolation-middleware.md` containing all 11 sections (Introduction, Prerequisites, System Architecture, Core Concepts, API and Functional Overview, Worked Examples, Implementation Insights, Comparative Analysis, Integration Guidance, Outlook, Testing Strategy). The tutorial reads as a self-contained textbook chapter; no external context is required to understand it.

### Example 2 — edge case (component without code)

**User:** "Tutorial for the event-stream-processor — I have the spec but no code yet."

**Skill output:** Same structure, but the Implementation Insights and Testing Strategy sections clearly label inferred-from-spec content vs. implemented behavior, per the Inputs & Assumptions guidance above (state assumptions explicitly; label inferred vs. explicit behavior).

## Troubleshooting

- **`tutorials_dir` not resolved.** First-use path: run `python3 scripts/configure.py --scope project` and answer the prompt, or set the env var `CREATE_TUTORIAL_TUTORIALS_DIR`, or add `docs_root` to `.agents/dev-skills.yaml`.
- **Topic too narrow.** If the user says "write a tutorial for `parseDate()`" — that's reference docs territory, not a tutorial. Ask whether they want a reference instead.
- **File would overwrite an existing tutorial.** The skill overwrites by default. If unwanted, ask the user for a different filename before writing.

---

## Saving the Tutorial

- Save as a markdown file in the resolved `tutorials_dir` (Step 0 of Workflow).
- File name rules:
  - Use concise, kebab-case naming
  - Reflect the main component or feature
  - Example: `event-stream-processor.md`
- If a filename is explicitly provided, use it
- Ensure the directory exists (create if necessary)
- Overwrite existing file with the same name

---

