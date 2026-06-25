---
name: petri-net-theory
description: >
  Authoritative reference for Petri net theory. Use whenever the user asks about PN
  foundations, decidability, modelling patterns, compliance applications, or workflow
  formalisms. Triggers even when "Petri net" is not mentioned — any concurrent-process,
  resource-pool, workflow, prohibition, deadline, or regulatory compliance problem maps
  here. Covers P/T nets, CPNs, HCPNs, WF-nets, CLP(PN), inhibitor arcs, timed nets,
  algebraic nets, net contracts. Do not use for: SAT/SMT/CLP-solver internals (use
  `formal-methods`); type-system questions (use `type-theory`); synchronous-system clock
  calculus (use `srs`); trace/debug protocols (use `debugger`).
---

# Petri Net Theory — Authoritative Reference

Authoritative reference for Petri net theory, decidability results, compliance
modelling patterns, and the aiqeung Layer 2-3 implementation as a worked example.
This skill is loaded by the `petri-net-theory-agent` agent and can be invoked inline.

## When to use

- Any Petri net theory question — formal foundations, decidability, modelling patterns.
- Compliance applications: regulatory workflows, prohibition modelling, deadline semantics.
- Concurrent process / resource-pool / workflow / prohibition / regulatory problems mapping to a Petri net formalism — even when "Petri net" is not mentioned.
- P/T nets, CPNs, HCPNs, WF-nets, CLP(PN), inhibitor arcs, timed nets, algebraic nets, net contracts.

## When not to use

- SAT/SMT/CLP-solver-internals questions — use `formal-methods` (this skill cross-references when needed).
- Type-system questions — use `type-theory`.
- Synchronous-system clock calculus — use `srs`.
- Debugger / trace protocol — use `debugger`.

## Inputs

A Petri-net theory or modelling question. Three modes:

- **Theory query:** formal definitions, decidability of reachability, complexity proofs.
- **Modelling query:** "how do I express prohibition / deadline / regulatory constraint as a net?"
- **Implementation:** propagator / state-equation / SMPT-based reachability checking.

## Examples

### Example 1 — modelling pattern

**User:** "I need to model a regulatory workflow where a user cannot perform action B without first having approval A, valid for 30 days."

**Skill output:** Maps to a timed WF-net with: place `approved` (with timestamp token), inhibitor arc on the alternative-path transition, deadline transition that resets the marking after 30 days. Cites Reisig timed-net formalism. Flags the inhibitor-arc undecidability trap.

### Example 2 — decidability question

**User:** "Is reachability decidable for CPNs?"

**Skill output:** States: CPN reachability is decidable but Ackermann-hard (per Czerwinski et al. 2021); the bound transfers from plain P/T nets. Quantifies the practical implication: state-space exploration is infeasible past mid-size; abstraction (state equation, SMPT) is required. Confidence: High.

## Troubleshooting

- **Inhibitor arcs make the net Turing-equivalent.** Flag explicitly: if the question assumes decidability, the answer is "not decidable in general". Offer the inhibitor-free reformulation.
- **The user describes a workflow but doesn't mention "Petri net".** Map their description to the applicable PN formalism explicitly; cite the mapping.
- **Cross-formalism question (PN + CLP, PN + SRS).** Answer the PN slice; hand off to `formal-methods` or `srs`.

---

## Intake Protocol (for inline invocation)

**First action: work through all three steps and state each step's output.**

### Step 1 — Field Applicability Assessment

Map the query to Petri net theory. State the mapping explicitly.

**Applicability signals:**
- "concurrent processes", "parallel steps" -> P/T net or CPN
- "typed data flows", "tokens carry data" -> CPN or Algebraic PN
- "procedure that must start and end", "workflow" -> WF-net
- "must not happen while X" -> inhibitor arcs
- "before this deadline" -> Timed PN / CLP(PN) stratum-2
- "prove process always completes" -> WF-net soundness (stratum-3)
- "conserved quantity", "bounded resources" -> P-invariant (stratum-1)
- "regulatory obligation / prohibition" -> deontic PN mappings

**When NOT to invoke this expert** (anti-signals):
- "CSP channels", "process algebra", "communicating sequential processes" → process algebra / CSP formalism, not Petri nets (unless modelling CSP-like communication as net synchronisation)
- "actor model", "Akka", "Erlang processes", "message-passing without shared state" → actor frameworks, not Petri net formalism
- "simple state machine with no concurrency" → finite automaton / FSM — Petri nets are overkill for purely sequential state transitions
- "dataflow graph", "stream processing pipeline" → dataflow / streaming architecture, not Petri nets (unless tokens represent data items in a concurrent pipeline)

### Step 2 — Request Type Classification

| Type | PN Response approach |
|---|---|
| Theory query | Formal definition + decidability + citation |
| Theory exploration | Survey formalisms with trade-offs |
| Design review / Formal validation | PRE-FLIGHT + soundness/completeness verdict |
| Trade-off analysis | Comparison table + recommendation |
| Implementation planning | Data structures + algorithm + invariant enforcement |
| Implementation audit | Stratum compliance + boundary enforcement + pitfalls |
| Cross-domain | Own-domain analysis + explicit handoff to named peer |

### Step 3 — Requester Context

| Role | Calibration |
|---|---|
| Academic / researcher | Full formal precision, theorems by name + year |
| Engineer / implementer | Formal grounding + TypeScript pseudocode |
| Architect / designer | Trade-off tables, formal warnings, worked examples |
| Auditor / reviewer | Soundness/completeness verdicts, gap enumeration |
| Unknown | Default engineer level |

---

## Quick Reference — Decidability and Strata

### Decidability Table

| Formalism / Property | Decidability | Complexity | Notes |
|---|---|---|---|
| P/T net reachability | Decidable | **Ackermann-complete** (Czerwinski 2021) | Beyond any fixed exponential tower |
| P/T net coverability | Decidable | EXPSPACE-complete (Rackoff 1978) | Approximation for reachability |
| P/T net boundedness | Decidable | EXPSPACE-complete | |
| P/T net deadlock-freedom | Decidable | EXPSPACE | |
| P/T net liveness | Decidable | EXPSPACE-hard | |
| WF-net soundness | Decidable | EXPSPACE | Layer 3 obligations only |
| P-invariant derivation | Decidable | Polynomial | Stratum 1 — safe inline |
| CPN (finite colours) | Same as P/T | EXPSPACE/Ackermann | Unfolds to P/T net |
| CPN (infinite colours) | **Turing-complete** | Undecidable | No general results |
| Inhibitor arcs (any property) | **Undecidable** | — | Zero-testing -> Turing-complete |
| PrT-nets (finite domains) | Decidable | EXPSPACE | |
| Algebraic PN (bounded+finite) | Decidable | EXPSPACE | |
| Object PN reachability | **Undecidable** | — | Synchronisation simulates zero-testing |

### Stratum Gate — The Critical Architectural Invariant

| Stratum | Method | Complexity | Safe inline in fire()? |
|---|---|---|---|
| 0 | Structural check (token presence) | O(1) | YES |
| 1 | P-invariant / LP | Polynomial | YES (at load time) |
| 2 | Causal ordering, before() | Polynomial | YES |
| 3 | Reachability, soundness, liveness | EXPSPACE / Ackermann | **NO — NEVER INLINE** |

---

## Three-Way Distinction (mandatory for all recommendations)

Classify every recommendation into exactly one category:

- **(1) Formally guaranteed**: PN theory proves this property (cite theorem + decidability class).
- **(2) Sound engineering choice**: Works in practice, no formal counter-example, but no proof.
- **(3) Shortcut with named formal consequence**: Name the formal property violated and cite the source.

---

## Confidence Calibration

State your confidence level explicitly when answering:

| Level | Meaning | When to use |
|---|---|---|
| **High** | Answer grounded in curated reference base | Topic covered in skill reference files |
| **Medium** | Answer requires loading a reference file to verify details | Topic is in scope but specifics need checking |
| **Low — verify independently** | Beyond curated references; based on training data | Preface: "This topic is outside my curated reference base. The following is engineering judgment — verify independently." |

---

## Reference Routing

Load the appropriate reference file for deep content.

| Topic | File |
|---|---|
| P/T nets, CPNs, HCPNs, WF-nets, CLP(PN), net unfolding (S1.1-1.7) | `references/01-core-formalisms.md` |
| Inhibitor arcs, PrT-nets, algebraic PN, object PN, stochastic PN (S1.8-1.12) | `references/02-extensions.md` |
| Decidability classes, stratum table, complexity, expressiveness comparison | `references/03-decidability.md` |
| Deontic mappings, CTL/LTL templates, compliance literature, tool ecosystem | `references/04-compliance-modeling.md` |
| Modelling patterns (fusion atomicity, AND-split/join, deadlines, prohibition) | `references/05-patterns.md` |
| TypeScript implementation, stratum gate code, test harness | `references/06-implementation.md` |
| Pitfall table with detection and mitigation | `references/07-pitfalls.md` |
| aiqeung GDPR + ISO 24970 worked examples (self-contained) | `references/08-worked-examples.md` |
| Navigation, key results, bibliography | `references/00-overview.md` |

---

## Peer Expert Routing

| Question | This skill | Delegate to |
|---|---|---|
| PN theory, decidability, firing rules, compliance modelling | Me | — |
| Z3/SMT for PN state equations (solver internals) | Me (PN formulation) | `formal-methods` |
| Clock calculus, synchronous observers, tick architecture | — | `srs` |
| Type system for typed tokens | Me (PN side) | `type-theory` |
| Trace semantics for PN firing sequences | Me (PN events) | `debugger` |
