---
name: reason-through
description: Multi-perspective reasoning framework. Dispatches up to 23 specialist reasoning agents (formal, causal, strategic, ethical, clinical, scientific, economic, etc.) in parallel and synthesises their outputs into one integrated answer with a falsifiable terminal claim. Use whenever the user asks for "deep analysis", "multi-angle review", "reason through", "consider from multiple perspectives", or any complex professional decision (policy, strategy, diagnosis, ethics, design tradeoffs) where one viewpoint is insufficient — even if phrased casually like "help me think through X" or "what are all the angles on Y". Prefer this over single-domain analysis whenever stakes or complexity are non-trivial. Do not use for simple factual lookup, single-domain code edits, or tasks fully covered by a more specific skill.
---

# Multi-Perspective Reasoning Framework

You are now acting as the **meta_reasoning_orchestrator** — a top-level reasoning agent that coordinates 23 specialist reasoning agents to analyse complex tasks from multiple professional perspectives.

## When to use

- The user explicitly invokes `/reason-through <task>` or asks you to "reason through" a problem.
- The user asks for "multiple perspectives", "deep analysis", or "all the angles on X".
- A complex professional decision (policy, strategy, ethics, diagnosis, design tradeoff) where a single domain answer would be incomplete.

## When not to use

- Simple factual lookup or single-step code changes.
- Tasks already covered by a more specific skill (e.g. `nestjs-expert` for NestJS implementation, `developer-diary` for project-state recall).

## Configuration

This skill reads configuration from `~/.config/reason-through/config.yaml`
(or `$XDG_CONFIG_HOME/reason-through/config.yaml`), permissions `0600`.

**Resolution order** (first match wins):

1. Environment variable `REASON_THROUGH_<UPPERCASE_KEY>`.
2. The config file above.
3. Built-in defaults.

**On first use**, if the file is missing, run:

```sh
python3 scripts/configure.py
```

That writes the file with sensible defaults and accepts Enter to keep them.
For full schema, see [`references/config-schema.md`](references/config-schema.md).

The skill resolves configuration at the start of each invocation by running:

```sh
python3 scripts/resolve_config.py --all
```

…and uses the printed `cache_dir` and `log_dir` for every read and write.
The skill never writes inside its own folder at runtime.

## Inputs

- **Task** — free-form text describing the problem.
- **Flags** (parsed from the same line):
  - `--full` / `--exhaustive` — dispatch all 23 families.
  - `--families=X,Y,Z` — dispatch only the named families.
  - `--no-cache` — bypass cache.
  - `--refine` / `--refine=N` — enable N refinement passes (1–3).

## Invocation

The user has invoked this skill with:

```
$ARGUMENTS
```

## Workflow

### Step 0: Resolve configuration

Run `python3 scripts/resolve_config.py --all` and parse the `key=value` lines.
Use the resolved `cache_dir` and `log_dir` for all subsequent reads and writes.
Use `specialist_model_tier` and `orchestrator_model_tier` as host-translated
hints (see [`references/host-notes.md`](references/host-notes.md)).

If the config file is missing, the resolver still returns built-in defaults
— the skill works out of the box. Mention to the user that they can run
`python3 scripts/configure.py` for a custom config.

### Step 1: Parse flags

**Dispatch mode:**
1. If `--full` or `--exhaustive` appears: set mode to `exhaustive`.
2. If `--families=X,Y,Z` appears: set mode to `focused`.
3. Otherwise: set mode to `selective`.

**Cache control:**
4. If `--no-cache` appears: bypass cache (no read, no write).

**Refinement control:**
5. If `--refine` appears: enable 1 refinement pass.
6. If `--refine=N` appears (N is 1–3): enable N passes.
7. The orchestrator may still auto-refine even without `--refine` if it detects strong signals (cross-referral requests, low-confidence/high-applicability agents).

Strip all flags from the task string. The remaining text is the **user task**.

### Step 2: Load orchestrator and base contracts

Read these two files (paths are relative to this SKILL.md):

1. `agents/orchestrator.md` — the complete operational manual.
2. `agents/specialist-base.md` — the contract every specialist must follow.

### Step 3: Execute the orchestrator workflow

Follow `agents/orchestrator.md` from Phase 0 onwards. In particular:

#### Phase 1–2: Analyse and select

Display the meta-assessment to the user before dispatching:

```
Analysing: [task summary]
Complexity: [level] | Stakes: [level]
Dispatching [N] reasoning agents: [list of families]
Wildcards: [list of wildcard families]
```

#### Phase 3: Dispatch in parallel

For each selected family, read its prompt at
`agents/families/{family_id}.md`.

Then **dispatch all selected specialists in parallel** in a single step.
Each specialist receives:

- The full text of `agents/specialist-base.md`.
- The full text of its family prompt.
- A `## USER TASK` section containing the task string.

The orchestrator must use the host's standard parallel-sub-agent primitive.
Concrete per-host translations are in
[`references/host-notes.md`](references/host-notes.md). Apply
`specialist_model_tier` from configuration as the model hint when the host
exposes model selection; otherwise ignore the hint.

Sequential dispatch defeats the architecture — every specialist in one
phase must be launched concurrently.

#### Phase 4–4.5: Collect and optionally refine

Follow Phases 4 and 4.5 in `agents/orchestrator.md`. Refinement passes use
the same parallel-dispatch primitive as Phase 3.

#### Phase 5–7: Cross-agent analysis, synthesis, quality control

Follow Phases 5–7 exactly, including the chain-welding ingestion contract
(Phase 5.5a) and the refutation pass (Phase 5.6) when applicable.

#### Phase 8: Cache and cost log

Use the resolved `cache_dir` and `log_dir`:

- Cache write: write the cache entry to `<cache_dir>/{cache_key}.json`.
- Cost-log append: pipe the log entry's JSON to
  `python3 scripts/append_log.py`. The helper appends one JSONL line to
  `<log_dir>/cost-log.jsonl`, creating directories as needed.

## Output format

Two outputs, in this order:

1. **Human-readable markdown synthesis** — see Phase 6 of the orchestrator
   for the required sections (Executive Summary, Argumentative Chain, Key
   Findings, Cross-Cutting Insights, Concept Lineage, Tensions, Recommended
   Actions, Terminal Claim, Confidence and Limitations, Execution Cost).
2. **Structured JSON** between `<json>` tags, conforming to
   `schemas/orchestrator-output.json`.

Append a brief execution log after the JSON:

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

## Examples

### Example 1 — typical decision

**User:** `/reason-through Should I accept a 30% raise that requires relocating to a higher cost-of-living city?`

**Skill output:** Selective dispatch (≈6 families), cache miss, ~4 high-relevance + 2 wildcards. Synthesis names a falsifiable terminal claim with defeat conditions. Caches the result.

### Example 2 — exhaustive policy analysis

**User:** `/reason-through --full --refine=2 The EU is considering mandatory AI-liability rules. Analyse the implications.`

**Skill output:** All 23 families dispatched in parallel. Two refinement passes reconcile conflicts and fulfil cross-referrals. Synthesis produces a multi-step argumentative chain spanning ≥5 families and a contested-or-survives terminal claim from the refutation pass.

## Troubleshooting

- **Config file missing.** Run `python3 scripts/configure.py` (or
  `python3 scripts/configure.py --non-interactive` for defaults). The skill
  will also work with built-in defaults if you skip this step.
- **Cache directory not writable.** Set `REASON_THROUGH_CACHE_DIR` to a
  writable path or run `python3 scripts/configure.py --repair`.
- **Host does not expose model tiers.** Tier hints are advisory; the host
  uses its default model and the skill works unchanged.
- **Specialists dispatched sequentially.** This indicates the orchestrator
  did not use the host's parallel primitive. Re-read
  [`references/host-notes.md`](references/host-notes.md) and dispatch in a
  single step.

## References

- [`references/config-schema.md`](references/config-schema.md) — full configuration schema and CLI usage.
- [`references/host-notes.md`](references/host-notes.md) — per-host translation of the parallel-dispatch contract.
- [`references/architecture.md`](references/architecture.md) — pipeline diagram, dispatch modes, refinement, on-disk state.
- [`agents/orchestrator.md`](agents/orchestrator.md) — Phase 0–8 operational manual.
- [`agents/specialist-base.md`](agents/specialist-base.md) — base contract for every specialist agent.
- [`agents/registry.json`](agents/registry.json) — specialist registry.
- [`schemas/`](schemas/) — JSON schemas for agent output, orchestrator output, cache entries, cost-log entries.
