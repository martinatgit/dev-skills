# reason-through: Multi-Perspective Reasoning Framework

A Claude Code skill that analyses complex professional tasks through 23 specialist reasoning families, coordinated by a meta-reasoning orchestrator.

## Usage

```
/reason-through Should we open-source our core library?

/reason-through --full A patient presents with chest pain, elevated troponin, and normal ECG

/reason-through --families=decision_action,ethical_beyond_formal_norms,economic_institutional_design Should we lay off 15% of the engineering team to hit quarterly targets?
```

```
# With caching disabled
/reason-through --no-cache Should we open-source our core library?

# With iterative refinement (1 extra pass)
/reason-through --refine Should we open-source our core library?

# With 2 refinement passes, exhaustive mode, no cache
/reason-through --full --refine=2 --no-cache The EU is considering mandatory AI liability rules
```

## Dispatch modes

| Mode | Flag | Behavior |
|------|------|----------|
| **Selective** (default) | none | Orchestrator estimates relevance, dispatches ~6-10 high-relevance agents + 2-3 wildcards |
| **Exhaustive** | `--full` | Dispatches all 23 specialist agents in parallel |
| **Focused** | `--families=X,Y,Z` | Dispatches only the named families (comma-separated IDs) |

## Feature flags

| Flag | Default | Behavior |
|------|---------|----------|
| `--no-cache` | cache on | Bypass the cache — always run fresh analysis |
| `--refine` | off | Enable 1 iterative refinement pass after initial dispatch |
| `--refine=N` | off | Enable N refinement passes (max 3) |

Flags can be combined: `--full --refine=2 --no-cache`

## Architecture

```
/reason-through <task> [--full] [--refine] [--no-cache]
        |
        v
  ┌─────────────────────┐
  │   SKILL.md           │  Parse flags, read prompts
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
  │ Phase 3: Dispatch    │  Launch N agents in parallel (pass 1)
  └─────────┬───────────┘
     ┌──────┼──────┬──── ... ────┐
     v      v      v              v
   [F1]   [F2]   [F3]  ...    [FN]     Specialist agents
     └──────┴──────┴──── ... ────┘
            v
  ┌─────────────────────┐
  │ Phase 4: Collect     │  Parse JSON, filter, rank
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 4.5: Refine?   │──── NO ────→ Phase 5
  │ (cross-referrals,   │
  │  low-confidence,    │  YES: re-dispatch with enriched prompts
  │  conflicts)         │──→ [Agent] ──→ merge ──→ loop or Phase 5
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 5-7: Analyse,  │  Cross-agent analysis, synthesis,
  │ synthesise, verify   │  quality control
  └─────────┬───────────┘
            v
  ┌─────────────────────┐
  │ Phase 8: Cache write │  Write cache entry + append cost log
  │ + cost log           │
  └─────────────────────┘
            v
     Human-readable markdown + structured JSON
```

## Directory structure

```
.claude/skills/reason-through/
├── SKILL.md                          # Skill entry point
├── README.md                         # This file
├── agents/
│   ├── registry.json                 # Agent registry and dispatch config
│   ├── orchestrator.md               # Meta-reasoning orchestrator prompt
│   ├── specialist-base.md            # Shared contract for all specialists
│   └── families/                     # One prompt per reasoning family
│       ├── formal_truth_preserving.md
│       ├── structural_classification.md
│       ├── explanation_discovery.md
│       ├── uncertainty_evidence.md
│       ├── constraint_search.md
│       ├── temporal_dynamic.md
│       ├── decision_action.md
│       ├── normative_legal.md
│       ├── scientific_model.md
│       ├── clinical_medical.md
│       ├── strategic_adversarial.md
│       ├── social_communication.md
│       ├── philosophical_conceptual.md
│       ├── engineering_systems.md
│       ├── economic_institutional_design.md
│       ├── historical_contextual.md
│       ├── embodied_experiential.md
│       ├── creative_generative.md
│       ├── aesthetic.md
│       ├── affective_interpersonal.md
│       ├── ethical_beyond_formal_norms.md
│       ├── learning_adaptation.md
│       └── orchestration.md
├── cache/                                # Cached results (JSON, keyed by task hash)
│   └── .gitkeep
├── logs/                                 # Execution cost logs (JSONL, append-only)
│   └── .gitkeep
└── schemas/
    ├── agent-output.json             # JSON schema for specialist output
    ├── orchestrator-output.json      # JSON schema for orchestrator output
    ├── cache-entry.json              # Cache entry schema
    └── cost-log-entry.json           # Cost log entry schema
```

## Reasoning families

| # | ID | Family | Modes |
|---|---|---|---|
| 1 | formal_truth_preserving | Formal and Truth-Preserving | 12 |
| 2 | structural_classification | Structural and Classification | 10 |
| 3 | explanation_discovery | Explanation, Discovery, Understanding | 10 |
| 4 | uncertainty_evidence | Uncertainty, Evidence, Belief | 12 |
| 5 | constraint_search | Constraint, Search, Possibility-Space | 9 |
| 6 | temporal_dynamic | Temporal and Dynamic-System | 9 |
| 7 | decision_action | Decision, Optimisation, Action | 13 |
| 8 | normative_legal | Normative, Legal, Compliance | 12 |
| 9 | scientific_model | Scientific and Model-Based | 11 |
| 10 | clinical_medical | Clinical and Medical | 9 |
| 11 | strategic_adversarial | Strategic, Adversarial, Conflict | 17 |
| 12 | social_communication | Social, Rhetorical, Communicative | 9 |
| 13 | philosophical_conceptual | Philosophical and Conceptual | 16 |
| 14 | engineering_systems | Engineering, Design, Systems | 10 |
| 15 | economic_institutional_design | Economic, Organisational, Institutional | 8 |
| 16 | historical_contextual | Historical, Contextual, Documentary | 3 |
| 17 | embodied_experiential | Embodied, Heuristic, Experiential | 6 |
| 18 | creative_generative | Creative and Generative | 5 |
| 19 | aesthetic | Aesthetic | 5 |
| 20 | affective_interpersonal | Affective and Interpersonal | 5 |
| 21 | ethical_beyond_formal_norms | Ethical Beyond Formal Norms | 5 |
| 22 | learning_adaptation | Learning and Adaptation | 5 |
| 23 | orchestration | Orchestration | 5 |
| **Total** | | **23 families** | **206 modes** |

## Output format

The skill always produces:
1. **Human-readable synthesis** — structured markdown with executive summary, findings, tensions, and next steps
2. **Structured JSON** — full machine-readable output between `<json>` tags conforming to `schemas/orchestrator-output.json`

## Caching

Results are cached to disk in `.claude/skills/reason-through/cache/` as JSON files keyed by SHA-256 of the normalised task string. Cache entries expire after 24 hours (configurable in `registry.json`).

- **Cache hit**: Returns the cached result instantly without dispatching any agents
- **Partial hit**: If the cached result used a different dispatch mode and the current request asks for additional families, only the missing families are dispatched fresh
- **Cache miss**: Full dispatch, result written to cache after synthesis
- **Bypass**: `--no-cache` skips both reading and writing

Cache files can be manually deleted to force re-analysis.

## Iterative refinement

When enabled, the orchestrator evaluates first-pass results and may re-dispatch specific agents with enriched context:

1. **Low-confidence agents**: Agents with high applicability but low output confidence get re-dispatched with relevant context from higher-confidence agents
2. **Cross-referral fulfilment**: When Agent A requests input from Agent B, the orchestrator injects B's findings into A's prompt and re-dispatches A
3. **Conflict resolution**: When two agents contradict each other, both are re-dispatched with each other's findings

The orchestrator may auto-refine even without `--refine` if it detects strong signals (cross-referral requests from high-confidence agents). Maximum 3 passes to prevent loops.

## Agent-to-agent cross-referral

Specialist agents can include `cross_referral_requests` in their output to request input from other specialists. Example: the ethical reasoning agent might request input from the normative/legal agent about regulatory requirements.

Cross-referrals are fulfilled during refinement passes. Rules:
- Maximum 2 cross-referral requests per agent
- The target agent must be a valid family ID from the registry
- Requests are only fulfilled if refinement is enabled or auto-triggered

## Cost tracking

Every invocation appends a cost log entry to `.claude/skills/reason-through/logs/cost-log.jsonl`. Each entry records which agents were dispatched, response sizes, whether agents contributed to synthesis, and cache hit status.

The orchestrator uses cost history to inform wildcard selection — families that rarely apply are deprioritised as wildcards (but never skipped if relevance estimation says HIGH).

## Extending the framework

To add a new reasoning family:

1. Add a category to `doc/research-insights/reasoning/reasoning_taxonomy.json`
2. Run `_generate_agents.py` to regenerate the family prompt file
3. Add an entry to `agents/registry.json` under `specialist_agents`
4. The orchestrator will automatically pick it up via the registry

To disable a family: set `"enabled": false` in `agents/registry.json`.

## Taxonomy source

All reasoning families and modes are derived from:
- `doc/research-insights/reasoning/reasoning_taxonomy.md` (human-readable)
- `doc/research-insights/reasoning/reasoning_taxonomy.json` (machine-readable, 237 modes across 25 categories)

## Design principles

- **Composable, not exclusive**: Multiple reasoning families can apply simultaneously
- **Honest uncertainty**: Agents report confidence honestly; the orchestrator does not inflate
- **Depth over breadth**: One strong insight beats five generic ones
- **Structured outputs**: JSON schemas ensure machine-readability throughout
- **Extensible**: New families can be added without changing the orchestrator
- **Graceful degradation**: Timeouts and failures are logged, not fatal

## Example test cases

### Simple decision task
```
/reason-through Should I accept a job offer that pays 30% more but requires relocating to a city with higher cost of living?
```
Expected: decision_action, economic_institutional_design, affective_interpersonal, creative_generative (as wildcard)

### Complex policy analysis
```
/reason-through --full The EU is considering mandatory AI liability rules that would make deployers strictly liable for AI system harms. Analyse the implications.
```
Expected: All 23 families dispatched. High relevance from normative_legal, economic_institutional_design, ethical_beyond_formal_norms, strategic_adversarial, engineering_systems.

### Technical diagnosis
```
/reason-through Our distributed system is experiencing intermittent data inconsistencies that correlate with peak traffic but not with any specific service deployment.
```
Expected: explanation_discovery, engineering_systems, temporal_dynamic, uncertainty_evidence, constraint_search.
