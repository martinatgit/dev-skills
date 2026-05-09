---
name: formal-methods-expert-overview
description: >
  Navigation map, cross-domain boundary table, decidability quick-reference,
  key formal results, top pitfalls by sub-domain, and bibliography for the
  formal-methods-expert knowledge base. Load first when unsure which reference
  file to consult.
type: reference
---

# Formal Methods Expert — Navigation Overview

*Entry point for the 8-file knowledge base. Read this file to route to the right reference, verify cross-domain boundaries, or get the one-paragraph answer quickly.*

---

## Topic → Reference File Routing

| Topic | Load |
|---|---|
| DPLL, CDCL, two-watched literals, 1-UIP, VSIDS, LBD deletion, Luby restarts, phase saving, resolution proofs | `01-sat-foundations.md` |
| Z3 internals, CDCL(T) main loop, EUF congruence closure, Nelson-Oppen, theory solvers by fragment, UserPropagator, nuZ MaxSMT, TypeScript/WASM bindings | `02-smt-z3.md` |
| CLP(X) framework, propagator fixpoint engine, trailing, domain representations, global constraints (all_different, table CT), views, LCG order encoding, CHR, OR-Tools | `03-clp-cp.md` |
| TLA+ syntax/semantics, LTL/CTL, Büchi automaton, TLC BFS/fingerprinting/symmetry, Apalache KerA+, TLAPS, PlusCal, Quint | `04-tla-temporal.md` |
| Isabelle/HOL Isar, Sledgehammer, Dafny WP calculus, Lean4 CIC+tactics, PAT CSP refinement, Coq, AFP | `05-theorem-proving.md` |
| BMC, k-Induction, IC3/PDR, SMPT state equation, synchronous observers, Kind2 | `06-model-checking-algorithms.md` |
| Z3 WASM TypeScript API, neuro-symbolic pipeline, constraint store integration, Petri net → SMT, reactive → model checker, UserPropagator hybrid | `07-integration-patterns.md` |
| Undecidability traps, performance cliffs, completeness gaps, theory combination failures, trailing bugs, TypeScript traps, decidable fragment table | `08-pitfalls-risks.md` |

---

## Cross-Domain Boundary Table

| Question | This Expert | Delegate |
|---|---|---|
| CDCL(T) algorithm internals, theory solver interface design | formal-methods-expert | — |
| EUF, Nelson-Oppen, theory combination correctness | formal-methods-expert | — |
| Z3 for Petri net state equations (algorithm) | formal-methods-expert | `petri-net-expert` (PN application) |
| k-Induction / IC3/PDR algorithm theory | formal-methods-expert | — |
| k-Induction applied to synchronous Lustre/Scade nodes | formal-methods-expert (algorithm) | `srs-expert` (SRS application) |
| TLA+ specification design for reactive systems | formal-methods-expert | `srs-expert` if Layer 3 tick semantics involved |
| Petri net decidability, net contracts, P/T firing rules, soundness | `petri-net-expert` | — |
| PN reachability via state equation (SMT encoding) | formal-methods-expert + `petri-net-expert` jointly | — |
| Clock calculus, three-phase tick, causality, ReactiveExpr | `srs-expert` | — |
| CLP propagators for synchronous scheduling | formal-methods-expert (propagator engine) | `srs-expert` (SRS semantics) |

**Routing rule**: State the boundary explicitly before answering cross-domain questions. Never silently absorb a PN or SRS question; flag and delegate the non-formal-methods portion.

---

## Quick-Reference Decidability Table

| Fragment / Problem | Decidability | Complexity | Notes |
|---|---|---|---|
| Propositional SAT | Decidable | NP-complete (Cook-Levin 1971) | CDCL complete for finite instances |
| QF_LIA (quantifier-free linear integer arithmetic) | Decidable | NP-complete | Preferred SMT fragment; dual simplex |
| QF_LRA (linear real arithmetic) | Decidable | PSPACE-complete | Simplex; QF_LIA preferred for integers |
| QF_NIA (non-linear integer arithmetic) | **Undecidable** | — | Z3 heuristic only; may not terminate |
| QF_NRA (non-linear real arithmetic) | Decidable (CAD) | Doubly exponential | Cylindrical algebraic decomposition |
| QF_BV (bit-vectors, fixed width) | Decidable | NP-complete | Bit-blasting to SAT |
| QF_UF / EUF (equality + uninterpreted functions) | Decidable | NP-complete | Congruence closure |
| QF_AX (arrays) | Decidable | NP-complete | McCarthy theory |
| QF_UFLRA (EUF + LRA) | Decidable | NP-complete (Nelson-Oppen) | Convex; equality sharing sufficient |
| First-order logic (with ∀/∃) | **Semi-decidable** | r.e. (Gödel) | Z3 incomplete over quantified formulas |
| LTL model checking (finite state) | Decidable | PSPACE-complete | Büchi automaton product |
| CTL model checking (finite state) | Decidable | P-complete | BDD fixpoint |
| P/T Petri net reachability | Decidable | **Ackermann-complete** (Czerwinski 2021) | Non-elementary; practically infeasible |
| PN reachability (inhibitor arcs) | **Undecidable** | — | Reduces to halting problem |
| CLP(FD) consistency | Decidable (for finite domains) | NP-complete | Propagation + labeling |

---

## Key Formal Results at a Glance

### SAT / CDCL
- **Cook-Levin theorem** (1971): SAT is NP-complete — the canonical hardness result.
- **GRASP / CDCL** (Marques-Silva & Sakallah, 1996): Conflict-Driven Clause Learning; non-chronological backjumping.
- **Chaff** (Moskewicz et al., 2001): Two-watched literals + VSIDS; practical CDCL dominance.
- **1-UIP lemma**: The first Unique Implication Point produces the asserting clause that forces a unit propagation one level below the conflict level.

### SMT / CDCL(T)
- **CDCL(T) soundness/completeness** (Nieuwenhuis, Oliveras & Tinelli, JACM 2006): Complete for quantifier-free formulas in decidable theories with the T-propagation and T-explanation callbacks implemented correctly.
- **Z3** (de Moura & Bjørner, TACAS 2008): Industrial CDCL(T) solver; fragment selection determines decidability.
- **Nelson-Oppen** (1979): Combination of convex theories via equality sharing; non-convex requires case splits.
- **EUF congruence closure** (Downey, Sethi & Tarjan, 1980): O(n log n); union-find + signature table.

### CLP / CP
- **CLP(X) framework** (Jaffar & Lassez, 1987): Parametric constraint logic programming over arbitrary constraint systems.
- **Propagation engines** (Schulte & Stuckey, TOPLAS 2008): Propagator fixpoint correctness + propagator composition.
- **Lazy Clause Generation** (Feydy & Stuckey, 2009): Order encoding + explanation clauses → SAT-guided CP; complete + stronger conflict learning than arc consistency alone.
- **Hall's theorem** (Hall, 1935): all_different arc consistency iff for every subset S of variables, |S| ≤ |⋃ dom(S)|.

### Temporal Logic / TLA+
- **TLA+** (Lamport, 1994; Specifying Systems, 2002): Action-based temporal specification; stuttering-closed semantics.
- **TLC symmetry unsoundness** (Lamport & Merz): Symmetry reduction unsound for liveness — only use for safety properties.
- **AWS formal methods** (Newcombe et al., CACM 2015): 35-step safety violations found by TLA+; industrial validation.
- **Apalache** (Konnov et al., 2019): Symbolic bounded model checker for TLA+; KerA+ fragment + SMT arena encoding.

### Model Checking Algorithms
- **BMC** (Biere, Cimatti, Clarke & Zhu, 1999): SAT-based bounded model checking; sound but **not complete** — failing to find a counterexample at bound k ≠ property holds.
- **k-Induction** (Sheeran, Singh & Stålmarck, 2000): Base + inductive step — UNKNOWN ≠ property fails; auxiliary invariants resolve most false UNKNOWN results.
- **IC3/PDR** (Bradley, 2011): Property-Directed Reachability; complete for finite-state; frame array + cube blocking.
- **Petri net Ackermann-completeness** (Czerwinski, Lasota, Lazic, Leroux & Mazowiecki, 2021): Reachability decidable but of Ackermann complexity — practically infeasible for large nets.

### Theorem Proving
- **Curry-Howard correspondence**: Propositions-as-types, proofs-as-programs; foundation of Lean4, Coq.
- **Sledgehammer** (Paulson & Blanchette, 2010): ATPs (Vampire, E, Zipperposition) + SMT (Z3, CVC4) from within Isabelle/HOL.
- **Dafny** (Leino, 2010): WP calculus + Boogie + Z3; loop invariants required for all loops (not inferred).
- **PAT refinement hierarchy**: Trace ⊇ Failures ⊇ Failures-Divergence — T refinement is incomplete for liveness (requires FD).

---

## Top Implementation Pitfalls by Sub-Domain

| Sub-domain | Pitfall 1 | Pitfall 2 | Pitfall 3 |
|---|---|---|---|
| **SAT/CDCL** | Two-watched literals broken after conflict: must re-establish invariant (exactly one watch ≤ last decision level) before resuming | Assertion level error: asserting clause has UIP at a level other than current — causes incorrect unit propagation | Clause deletion removes the asserting clause: solver loses the learned unit → stale watch list, unsound state |
| **SMT/Z3** | QF_NIA usage: non-linear integer arithmetic is undecidable — Z3 uses heuristic, may return `unknown` or loop | Nelson-Oppen without purification: alien subterms (EUF terms inside LIA atom) cross theory boundary → incorrect result | UserPropagator `push/pop` not implemented: Z3 calls push/pop around branches; missing implementation → stale propagation state |
| **CLP/CP** | TypeScript propagator in hot loop: 10–50× slower than native; global constraint + explanation rewrites needed | Trailing magic number collision: integer overflow or domain-tag collision causes spurious domain restoration | LCG `explain()` returns wrong literals: explanation clause not unit after backjump → proof obligation violated, incorrect pruning |
| **TLA+ / temporal** | TLC symmetry with liveness check: `SYMMETRY` is UNSAFE for liveness — produces false "property holds" verdict | PlusCal label placement: every while-loop body needs at least one label or the PlusCal-to-TLA+ translation is wrong | `ASSUME` vs `INVARIANT`: `ASSUME` is checked at parse time on constants only; `INVARIANT` is checked during model checking |
| **Theorem proving** | Dafny loop invariant not established before loop: Dafny requires invariant holds *before* entry, not just maintained | Isabelle `simp` divergence: `simp` loops on equations like `f x = g (f x)` — add `[simp del]` or use `subst` | Lean4 `omega` scope: `omega` handles linear arithmetic over `Nat`/`Int` only — `ring`/`linarith` for real/polynomial goals |
| **Model checking** | BMC SAT → counterexample exists: BMC UNSAT only means no counterexample ≤ k — not a proof of correctness | k-Induction UNKNOWN state: agents often incorrectly conclude property fails — UNKNOWN means induction step failed, not property false | IC3/PDR CTI generalization over-approximation: generalizing a cube too aggressively creates a frame clause that blocks real initial states |

---

## Algorithm Selection Guide

| Goal | Recommended | Decidable? | Complete? |
|---|---|---|---|
| Check finite-state safety invariant | k-Induction or IC3/PDR | Yes (finite state) | Yes |
| Find counterexamples quickly | BMC | Yes (≤ k) | No (incomplete) |
| Verify infinite-state system | TLA+/TLC + Apalache | Undecidable in general | TLC finite abstractions only |
| Integer constraint solving | Z3 QF_LIA | Yes | Yes |
| Mixed integer / non-linear | Z3 QF_NIA (with caution) | **No** | No |
| CP scheduling / optimization | OR-Tools CP-SAT + LCG | Yes (finite dom) | Yes (complete search) |
| Petri net reachability (small) | SMPT state equation (QF_LIA) | UNSAT ⊂ unreachable | SAT is spurious (incomplete) |
| Interactive theorem proving | Isabelle/HOL or Lean4 | Semi-decidable | Human-guided; no auto guarantee |
| Verification-by-construction | Dafny | Decidable (WP goals) | Requires manual invariants |
| Concurrency / protocol checking | TLA+ + TLC | Yes (finite) | Yes (finite model) |

---

## Bibliography

### SAT / CDCL
1. Cook, S.A. (1971). The complexity of theorem-proving procedures. *STOC 1971*.
2. Marques-Silva, J.P. & Sakallah, K.A. (1996). GRASP — A search algorithm for propositional satisfiability. *ICCAD 1996*.
3. Moskewicz, M. et al. (2001). Chaff: Engineering an efficient SAT solver. *DAC 2001*.
4. Audemard, G. & Simon, L. (2009). Predicting learnt clauses quality in modern SAT solvers. *IJCAI 2009*. *(LBD metric)*
5. Eén, N. & Sörensson, N. (2003). An extensible SAT-solver. *SAT 2003*. *(MiniSAT)*

### SMT / Z3
6. Nieuwenhuis, R., Oliveras, A. & Tinelli, C. (2006). Solving SAT and SAT modulo theories. *JACM 53(6)*.
7. de Moura, L. & Bjørner, N. (2008). Z3: An efficient SMT solver. *TACAS 2008*.
8. Nelson, G. & Oppen, D.C. (1979). Simplification by cooperating decision procedures. *TOPLAS 1(2)*.
9. Downey, P., Sethi, R. & Tarjan, R. (1980). Variations on the common subexpression problem. *JACM 27(4)*. *(Congruence closure)*
10. Bjørner, N., Phan, A.D. & Fleckenstein, L. (2015). νZ — An optimizing SMT solver. *TACAS 2015*. *(nuZ MaxSMT)*

### CLP / CP
11. Jaffar, J. & Lassez, J.L. (1987). Constraint logic programming. *POPL 1987*.
12. Schulte, C. & Stuckey, P.J. (2008). Efficient constraint propagation engines. *TOPLAS 31(1)*.
13. Feydy, T. & Stuckey, P.J. (2009). Lazy clause generation reengineered. *CP 2009*.
14. Régin, J.C. (1994). A filtering algorithm for constraints of difference in CSPs. *AAAI 1994*. *(all_different)*
15. Pesant, G. (2004). A regular language membership constraint for finite sequences. *CP 2004*. *(table/regular)*

### TLA+ / Temporal Logic
16. Lamport, L. (1994). The temporal logic of actions. *TOPLAS 16(3)*.
17. Lamport, L. (2002). *Specifying Systems*. Addison-Wesley.
18. Newcombe, C. et al. (2015). How Amazon Web Services uses formal methods. *CACM 58(4)*.
19. Konnov, I. et al. (2019). TLA+ model checking made symbolic. *TACAS 2019*. *(Apalache)*
20. Vardi, M.Y. & Wolper, P. (1986). An automata-theoretic approach to automatic program verification. *LICS 1986*. *(Büchi automaton MC)*

### Model Checking Algorithms
21. Biere, A., Cimatti, A., Clarke, E.M. & Zhu, Y. (1999). Symbolic model checking without BDDs. *TACAS 1999*. *(BMC)*
22. Sheeran, M., Singh, S. & Stålmarck, G. (2000). Checking safety properties using induction and a SAT solver. *FMCAD 2000*. *(k-Induction)*
23. Bradley, A.R. (2011). SAT-based model checking without unrolling. *VMCAI 2011*. *(IC3/PDR)*
24. Czerwinski, W., Lasota, S., Lazic, R., Leroux, J. & Mazowiecki, F. (2021). The reachability problem for Petri nets is not elementary. *JACM 68(1)*. *(Ackermann-completeness)*

### Theorem Proving
25. Nipkow, T., Paulson, L.C. & Wenzel, M. (2002). *Isabelle/HOL: A Proof Assistant for Higher-Order Logic*. Springer LNCS 2283.
26. Paulson, L.C. & Blanchette, J.C. (2010). Three years of experience with Sledgehammer. *PAAR 2010*.
27. Leino, K.R.M. (2010). Dafny: An automatic program verifier for functional correctness. *LPAR 2010*.
28. de Moura, L. et al. (2021). The Lean 4 theorem prover and programming language. *CADE 2021*.
29. Sun, J., Liu, Y., Dong, J.S. & Pang, J. (2009). PAT: Towards flexible verification under fairness. *CAV 2009*.
