# reason-through architecture

## Pipeline

```
/reason-through <task> [--full] [--families=...] [--refine[=N]] [--no-cache]
        |
        v
  ┌─────────────────────┐
  │   SKILL.md          │  Parse flags, resolve config, read prompts
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 0: Cache check │──── HIT ────→ Return cached result
  └─────────┬───────────┘
         MISS
            v
  ┌─────────────────────┐
  │ Phase 1-2: Analyse   │  Meta-assessment, relevance estimation,
  │ + select families    │  cost-aware wildcard selection
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 3: Dispatch    │  Launch N specialists in parallel (pass 1)
  └─────────┬───────────┘
     ┌──────┼──────┬──── ... ────┐
     v      v      v              v
   [F1]   [F2]   [F3]  ...    [FN]      Specialist agents
     └──────┴──────┴──── ... ────┘
            v
  ┌─────────────────────┐
  │ Phase 4: Collect     │  Parse JSON, filter, rank
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 4.5: Refine?   │──── NO ────→ Phase 5
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 5-7: Synthesis │  Cross-agent analysis, chain construction,
  │ + quality control    │  refutation, terminal claim
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 8: Cache write │  Write cache entry; append cost-log line
  └─────────────────────┘
            v
     Human-readable markdown + structured JSON
```

## Dispatch modes

| Mode | Flag | Behaviour |
|---|---|---|
| Selective | (default) | Orchestrator estimates relevance, dispatches ~6–10 high-relevance agents + 2–3 wildcards. |
| Exhaustive | `--full` | Dispatches all 23 specialist agents in parallel. |
| Focused | `--families=X,Y,Z` | Dispatches only the named families (comma-separated IDs). |

## Feature flags

| Flag | Default | Behaviour |
|---|---|---|
| `--no-cache` | cache on | Bypass the cache — always run fresh analysis. |
| `--refine` | off | Enable 1 iterative refinement pass after initial dispatch. |
| `--refine=N` | off | Enable N refinement passes (max 3). |

Flags can be combined: `--full --refine=2 --no-cache`.

## Reasoning families

23 families covering 206 modes. The full table with diagnostic triggers is
the first section of [`agents/orchestrator.md`](../agents/orchestrator.md).

## State on disk

Two locations only, both resolved from configuration (see
[`config-schema.md`](config-schema.md)):

- **Cache:** `<cache_dir>/{sha256}.json`, one file per task. Conforms to
  `schemas/cache-entry.json`. Expires after `cache_ttl_seconds`.
- **Cost log:** `<log_dir>/cost-log.jsonl`, append-only. Each line conforms
  to `schemas/cost-log-entry.json` and records dispatch counts, response
  sizes, contribution, refinement, and cache status for one invocation.

The skill never writes inside its own folder at runtime. The only writes
under the skill folder are dev-time, via `scripts/_generate_specialists.py`.

## Iterative refinement

When enabled, the orchestrator evaluates first-pass results and may
re-dispatch specific agents with enriched context:

1. **Low-confidence agents** (high applicability, low output confidence) get
   re-dispatched with relevant context from higher-confidence agents.
2. **Cross-referral fulfilment**: when agent A requests input from agent B,
   the orchestrator injects B's findings into A's prompt and re-dispatches
   A. If B was not dispatched, B is dispatched fresh first.
3. **Conflict resolution**: when two agents contradict each other, both are
   re-dispatched with each other's findings as context.

The orchestrator may auto-refine even without `--refine` if it detects
strong signals (cross-referral requests from high-confidence agents).
Maximum of `max_refinement_passes` passes (config-bounded; hard ceiling 3).

## Cross-agent referral

Specialists can include `cross_referral_requests` in their output to ask
another family for input. Rules:

- At most 2 referral requests per agent.
- The target agent must be a valid family ID listed in
  [`agents/registry.json`](../agents/registry.json).
- Requests are only fulfilled if refinement is enabled or auto-triggered.

## Extensibility

To add a new reasoning family:

1. Add a category to your taxonomy JSON.
2. Run `python3 scripts/_generate_specialists.py --taxonomy <path>` to
   regenerate the family prompt files.
3. Add an entry to `agents/registry.json` under `specialist_agents`.
4. The orchestrator picks it up automatically via the registry.

To disable a family: set `"enabled": false` in `agents/registry.json`.
