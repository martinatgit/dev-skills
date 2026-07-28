# SRS Expert — Reference Overview

*Navigation map for `skills/srs/references/`. Load this file first;
it routes to the correct reference for each topic.*

---

## Topic → File Routing

| Topic | File |
|---|---|
| Synchronous hypothesis, Esterel, Lustre, Signal, Kahn networks | `01-foundations.md` |
| Constructive semantics, clock calculus, fixpoint theory, absence reasoning, tagged signal model | `02-mathematical-foundations.md` |
| Observer pattern, Kind2, Lesar, Astree, Velus, LOLA | `03-verification.md` |
| Three-phase tick, ReactiveExpr, par/race/until, spec-execution duality, aiqeung Layer 3 | `04-aiqeung-layer3.md` |
| Compliance observers, GDPR experiments, deadline counters, evidence tracking | `05-compliance-modeling.md` |
| Constructive fixpoint algorithm, Must/Can propagation, clock inference, superdense time | `06-algorithms.md` |
| Causality errors, schizophrenia problem, intra-tick traps, clock pitfalls, performance | `07-pitfalls-risks.md` |

---

## Key Formal Results — Quick Reference

| Result | Statement | Primary source |
|---|---|---|
| Synchronous hypothesis | A reaction is instantaneous: in each tick, all inputs sampled, program computes, all outputs produced before next input. Computation takes zero logical time. Valid when WCET ≪ min inter-arrival time. | Berry & Gonthier 1992 |
| Constructive fixpoint | Kleene iteration on {⊥,0,1}^n starting from ⊥ reaches the constructive fixpoint in ≤n steps (n = number of signals). Each step resolves at least one signal from ⊥ to 0 or 1. | Berry 2002 |
| Causality criterion | A program has a causality error iff the constructive fixpoint contains ⊥ (some signal status remains unknown after convergence). Statically verifiable in polynomial time. | Berry 2002 |
| Clock calculus typing | Clocks are types. A stream with clock `base when C` is definitively absent when C is false — a compile-time guarantee, not a runtime test. Clock inference uses ML-style unification. | Colaço & Pouzet 2003 |
| Determinism | Same inputs always produce same outputs. Guaranteed by construction — synchronous model eliminates scheduling-dependent behavior. No race conditions, no locks needed. | Berry & Gonthier 1992 |
| Endochrony non-compositionality | Parallel composition of two endochronous programs is NOT guaranteed endochronous. Isochrony (flow-preserving under desynchronization) is the compositional alternative. | Benveniste et al. 2003 |
| Observer pattern correctness | A safety property P holds iff a synchronous observer node watching for P violations never emits true. Verification reduces to reachability on (system ∥ observer). | Halbwachs et al. 1992 |
| Astree result | Zero runtime errors in Airbus A340 flight control software (132,000 lines C generated from SCADE), zero false alarms. Abstract interpretation on synchronous code. | Cousot et al. ESOP 2005 |
| Velus end-to-end correctness | A formally verified Lustre compiler in Coq (extends CompCert) — generated C code provably faithful to the synchronous specification end-to-end. | Bourke et al. PLDI 2017 |
| LOLA bounded memory | Runtime monitors for synchronous systems can be implemented in constant space per tick (bounded memory, independent of trace length). | D'Angelo et al. TIME 2005 |

---

## Aiqeung Layer 3 — Synchronous Concept Mapping

| Synchronous concept | Layer 3 construct | Semantics |
|---|---|---|
| Tick / logical instant | `runtime.tick` (number), `step()` | One complete snapshot-compute-commit cycle |
| Synchronous hypothesis | All `par` branches see same frozen snapshot | Guarantees determinism across branch execution orders |
| Signal | `Signal<A>` with double-buffered `current`/`next` | Sequence of values indexed by tick number |
| Absence | `ABSENT` sentinel on `Signal.next` | Closed-world: absence is definite, not "not yet arrived" |
| `\|\|` (parallel) | `par` in `ReactiveExpr` | Both branches execute against frozen snapshot in same tick |
| `abort` / preemption | `race` in `ReactiveExpr` | First branch to complete wins; loser's writes discarded |
| `await` / temporal loop | `until` in `ReactiveExpr` | Body runs once per tick; condition checked at tick boundary |
| Lustre node definition | `ReactiveExpr` AST | The specification; interpreter = compiler + runtime |
| Synchronous observer | `ObligationObserver` | Monitors frozen state each tick; emits status signal |
| Superdense time | `Tag = { tick: number, microstep: number }` | Orders causally dependent events within a single tick |

---

## Design Recommendations in Force (reactive-system-insights.md §7)

| ID | Recommendation | Priority |
|---|---|---|
| DR-1 | Three-phase tick architecture (snapshot-compute-commit) | Critical |
| DR-2 | Double-buffered signals with ABSENT sentinel | Critical |
| DR-7 | `par` as synchronous parallel composition over frozen snapshot | Critical |
| DR-3 | Multi-solver orchestration via frozen ClauseDB snapshots | High |
| DR-8 | `race` as Esterel-style preemption with transaction forking | High |
| DR-5 | Obligation observers following synchronous observer pattern | High |
| DR-6 | Free monad interpreted by multiple backends (sync, sim, verify) | Medium |
| DR-9 | Static clock analysis pass on ReactiveExpr AST | Medium |
| DR-10 | Zero-cost tick rollback via ClauseDB immutability | Medium |

---

## Petri Nets / SRS Boundary

Petri nets (Layer 2, petri-net-theory skill) and synchronous observers are **complementary**:

| Dimension | Petri Nets | Synchronous Observers |
|---|---|---|
| Core abstraction | Concurrent state: tokens in places | Stream processing: signals at each tick |
| Models well | Workflow routing, resource allocation, concurrent state transitions | Continuous monitoring, deadline tracking, evidence presence/absence |
| Verification question | **Reachability**: can we reach a bad state? | **Safety**: is the invariant always maintained? |
| Absence reasoning | Weak: no token ≠ temporal precision | Strong: absence at a specific tick is definitive |
| Time model | Untimed (basic) or timed (extensions) | Logical clock ticks with precise deadline arithmetic |

**Integration pattern:** Petri nets model compliance **process** (workflow of activities); synchronous observers model compliance **invariants** (properties that must always hold at every tick).

For PN-side questions (firing rules, reachability, CPN/HCPN design): load **petri-net-theory** skill.
For SRS-side questions (observer design, signal semantics, tick semantics): this skill.

---

## Bibliography — Core Papers

- Berry, G. & Gonthier, G. (1992). The Esterel synchronous programming language: design, semantics, implementation. *Science of Computer Programming*, 19(2):87-152.
- Berry, G. (2002). *The Constructive Semantics of Pure Esterel*, Draft Version 3.
- Halbwachs, N., Caspi, P., Raymond, P., Pilaud, D. (1991). The synchronous data flow programming language LUSTRE. *Proc. IEEE*, 79(9):1305-1320.
- Colaço, J.-L. & Pouzet, M. (2003). Clocks as First Class Abstract Types. *EMSOFT 2003*, Philadelphia.
- Lee, E.A. & Sangiovanni-Vincentelli, A. (1998). A Framework for Comparing Models of Computation. *IEEE Trans. CAD*, 17(12):1217-1229.
- Benveniste, A. et al. (2003). The Synchronous Languages 12 Years Later. *Proc. IEEE*, 91(1):64-83.
- Champion, A., Mebsout, A., Sticksel, C., Tinelli, C. (2016). The Kind 2 Model Checker. *CAV 2016*.
- Cousot, P. et al. (2005). The Astree Analyzer. *ESOP 2005*.
- Bourke, T., Brun, L., Dagand, P.-E., Leroy, X., Pouzet, M., Rieg, L. (2017). A Formally Verified Compiler for Lustre. *PLDI 2017*.
- D'Angelo, B. et al. (2005). LOLA: Runtime Monitoring of Synchronous Systems. *TIME 2005*.
- Lohstroh, M. et al. (2021). Toward a Lingua Franca for Deterministic Concurrent Systems. *ACM TECS*, 20(4).
