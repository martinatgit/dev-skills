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
expires: {{YYYY-MM-DD, default = created + default_expiry_days (default 90)}}
very-next-action: {{one imperative sentence — the literal next physical action}}
references:
  - path: {{relative/file/path}}
    lines: {{start-end or omit}}
    anchor: {{§4.2.1 or omit}}
    note: {{what's at this reference}}
    kind: {{code | spec | diary — defaults to code; omit if code}}
    captured-at-sha: {{preserved verbatim from inbox, or null}}
    captured-at: {{preserved verbatim from inbox}}
    clarified-at-sha: {{git short SHA at clarify, or null}}
    last-checked: {{YYYY-MM-DD; equals clarified-at on first write}}
    excerpts:
      - lines: {{start-end, auto-derived from the reference's lines}}
        text: |
          {{verbatim file content at clarify time — omitted entirely for kind: diary}}
related:
  - {{TODO-id OR <root_dir of developer-diary>/.../diary-entry.md OR <project>/requirements.md#§x.y}}
blocks: [{{TODO-ids that cannot start until this resolves}}]
blocked-by: [{{TODO-ids that must resolve before this can start}}]
discovered-in-task: {{preserved verbatim from inbox}}
discovered-by: {{preserved verbatim from inbox}}
diary-node: {{preserved verbatim from inbox, or added at clarify-time}}
maintenance-history: []   # appended by `update-todos maintenance` on every approved pass
legacy-backfill: false    # set to true by maintenance if the first baseline was synthetic
# legacy-backfill-rejected-at: {{YYYY-MM-DD}}  # uncomment if user rejected legacy backfill; excludes from default maintenance
---

# {{Title}}

## Summary

{{≤ 3 sentences — the TODO stated crisply. Distil the discovery-context if it rambles.}}

## Discovery context

{{Preserved VERBATIM from the inbox phase. Do not rewrite; it is the timestamped record of the observation moment.}}

## Raw observation

{{Preserved VERBATIM from the inbox phase.}}

## Problem / opportunity

{{What goes wrong if we do nothing? Where is the asymmetry, gap, or violation? Cite evidence — quote code, quote spec text, show the contradiction. Ground every claim.}}

## Rationale for deferral

{{Why not fix this now? ("Out of scope", "blocks a refactor not yet planned", "needs product-owner decision", "spec must be updated first", etc.) If you cannot articulate a deferral rationale, this is probably in-scope work — tell the user.}}

## Proposed approach(es)

{{Sketch one or more directions. Name alternatives where they exist. This is NOT a plan — a plan belongs to a planning skill (e.g. superpowers:writing-plans) at action time. This is a trailhead.}}

## Acceptance criteria

{{How will we know this TODO is done? Concrete and verifiable — a passing test, a spec section added, a naming convention documented, a product-owner decision recorded in the diary.}}

## Required references

{{All files, spec sections, diary nodes, commits, external links an engineer needs to fully rehydrate. Duplicate-with-expansion from frontmatter `references[]` is fine — this is the human-readable version.}}

## Open questions

{{What genuinely remains undecided? Each question SHOULD have a hypothesised answer or a decision owner (e.g. "<owner> to decide").}}

## Pinned references

{{Human-readable mirror of the references[] excerpts. One sub-section per reference, format:

### {{ref-path}}:{{ref-lines}}

> Last maintenance: {{ts of most-recent maintenance-history entry, or "never" if maintenance-history is empty}} — {{verdict, or "—"}}

```
{{verbatim excerpt content (from frontmatter excerpts[].text)}}
```

Generated from the frontmatter at clarify time; refreshed by maintenance when excerpts change. Do not edit by hand — edit the frontmatter and re-render.}}

## Resolution notes

{{Leave empty until resolve-time. `resolve` action will fill this.}}
