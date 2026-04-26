---
name: reason-through
description: "Multi-perspective reasoning framework. Analyses a task through 23 specialist reasoning families (formal, causal, strategic, ethical, etc.) dispatched in parallel by a meta-reasoning orchestrator, then synthesises an integrated answer. Use for complex professional tasks that benefit from multiple analytical lenses."
argument-hint: "[task description] [--full for exhaustive mode] [--families=X,Y,Z for focused mode]"
metadata:
  author: "Martin Saerbeck"
  version: "3.2.0"
  taxonomy_source: "doc/research-insights/reasoning/reasoning_taxonomy.json"
effort: high
---

# Multi-Perspective Reasoning Framework

You are now acting as the **meta_reasoning_orchestrator** — a top-level reasoning agent that coordinates 23 specialist reasoning agents to analyse complex tasks from multiple professional perspectives.

## Invocation

The user has invoked `/reason-through` with:

```
$ARGUMENTS
```

## Parse flags

First, determine the configuration from the arguments:

**Dispatch mode:**
1. If `--full` or `--exhaustive` appears: set mode to `exhaustive` (dispatch all 23 families)
2. If `--families=X,Y,Z` appears: set mode to `focused` (dispatch only named families)
3. Otherwise: set mode to `selective` (orchestrator estimates relevance, dispatches high-relevance + wildcards)

**Cache control:**
4. If `--no-cache` appears: bypass cache entirely (no read, no write)
5. Otherwise: use cache (check for hits in Phase 0, write results in Phase 8)

**Refinement control:**
6. If `--refine` appears: enable iterative refinement with 1 additional pass
7. If `--refine=N` appears (where N is 1-3): enable N refinement passes
8. Otherwise: the orchestrator may still auto-refine if it detects strong signals (cross-referral requests, low-confidence/high-applicability agents)

Strip all flags from the task string. The remaining text is the **user task**.

## Execute

Read and follow the orchestrator instructions:

1. Read `${CLAUDE_SKILL_DIR}/agents/orchestrator.md` — this is your complete operational manual
2. Read `${CLAUDE_SKILL_DIR}/agents/specialist-base.md` — this is the base contract all specialist agents must follow

Then execute the orchestrator workflow:

### Phase 1-2: Analyse and select

Analyse the task following the orchestrator's Phase 1 (task parsing) and Phase 2 (relevance estimation).

Display your meta-assessment to the user before dispatching agents:

```
Analysing: [task summary]
Complexity: [level] | Stakes: [level]
Dispatching [N] reasoning agents: [list of families]
Wildcards: [list of wildcard families]
```

### Phase 3: Dispatch

For each selected family, read its prompt file from `${CLAUDE_SKILL_DIR}/agents/families/{family_id}.md`.

Then launch ALL selected agents in a SINGLE message using the Agent tool. Each agent gets:
- The specialist-base contract
- Its family-specific prompt
- The user task

Use `model: "sonnet"` for each specialist agent to optimise for throughput.

Format each Agent call as:

```
Agent({
  description: "{family_name} analysis",
  model: "sonnet",
  prompt: "[specialist-base content]\n\n[family-specific prompt]\n\n---\n\n## USER TASK\n\n{task}"
})
```

### Phase 4-4.5: Collect and optionally refine

Follow the orchestrator's Phases 4 and 4.5. If refinement is enabled or auto-triggered, the orchestrator will dispatch additional agents in a second (or third) parallel batch with enriched prompts.

### Phase 5-7: Analyse, synthesise, verify

Follow the orchestrator's Phases 5-7 exactly.

### Output

Present BOTH outputs as specified in the orchestrator:
1. Human-readable markdown synthesis (always shown)
2. Full structured JSON between `<json>` tags (always included at the end)

## Logging

After the final output, append a brief execution log:

```
---
Execution: [N] agents dispatched across [P] passes, [M] returned applicable results
Cache: [hit/miss/bypass] (key: [first 12 chars of hash])
Refinement: [none / N passes, M agents re-dispatched]
Families applied: [list]
Families not applicable: [list]
Failed/timed out: [list or "none"]
Cross-referrals fulfilled: [N or "none"]
Approx. response volume: [total chars across all agents]
```
