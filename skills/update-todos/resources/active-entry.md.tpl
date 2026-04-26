---
id: TODO-{{YYYYMMDD}}-{{NNNN}}
title: {{imperative concise title, ≤ 12 words}}
status: open
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
next-step: {{one of: spec-update | implementation | diary-update | brainstorm | refactor | investigate | test | decide | reproduce}}
priority: {{low | medium | high}}
effort: {{small | medium | large | unknown}}
scope: {{project | area | resource}}
tags: [{{tag1}}, {{tag2}}, ...]
expires: {{YYYY-MM-DD, default = created + 90 days}}
very-next-action: {{one imperative sentence — the literal next physical action}}
references:
  - path: {{relative/file/path}}
    lines: {{start-end or omit}}
    anchor: {{§4.2.1 or omit}}
    note: {{what's at this reference}}
related:
  - {{TODO-id OR doc/developer-diary/.../diary-entry.md OR doc/requirements/.../spec.md#§x.y}}
blocks: [{{TODO-ids that cannot start until this resolves}}]
blocked-by: [{{TODO-ids that must resolve before this can start}}]
discovered-in-task: {{preserved verbatim from inbox}}
discovered-by: {{preserved verbatim from inbox}}
diary-node: {{preserved verbatim from inbox, or added at clarify-time}}
---

# {{Title}}

## Summary

{{≤ 3 sentences — the TODO stated crisply. Distil the discovery-context if it rambles.}}

## Discovery context

{{Preserved VERBATIM from the inbox phase. Do not rewrite; it is the timestamped record of the observation moment.}}

## Raw observation

{{Preserved VERBATIM from the inbox phase.}}

## Problem / opportunity

{{What goes wrong if we do nothing? Where is the asymmetry, gap, or violation? Cite evidence — quote code, quote spec text, show the contradiction. Ground every claim (CLAUDE.md §3).}}

## Rationale for deferral

{{Why not fix this now? ("Out of scope", "blocks a refactor not yet planned", "needs product-owner decision", "spec must be updated first", etc.) If you cannot articulate a deferral rationale, this is probably in-scope work — tell the user.}}

## Proposed approach(es)

{{Sketch one or more directions. Name alternatives where they exist (CLAUDE.md §8 mandates alternatives for design decisions). This is NOT a plan — a plan belongs to superpowers:writing-plans at action time. This is a trailhead.}}

## Acceptance criteria

{{How will we know this TODO is done? Concrete and verifiable — a passing test, a spec section added, a naming convention documented, a product-owner decision recorded in the diary.}}

## Required references

{{All files, spec sections, diary nodes, commits, external links an engineer needs to fully rehydrate. Duplicate-with-expansion from frontmatter `references[]` is fine — this is the human-readable version.}}

## Open questions

{{What genuinely remains undecided? Each question SHOULD have a hypothesised answer or a decision owner (e.g. "Martin to decide").}}

## Resolution notes

{{Leave empty until resolve-time. `resolve` action will fill this.}}
