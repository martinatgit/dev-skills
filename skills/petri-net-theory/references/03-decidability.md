---
name: petri-net-decidability
description: Decidability classes and computational complexity for all Petri net
  formalisms and analysis problems. Stratum table (0-3) mapping analysis methods
  to complexity classes. Expressiveness comparison across PN extensions. Critical
  architectural constraint: strata-3 analysis must NEVER run inline in fire().
type: reference
---

# Petri Net Decidability Map

The constraint stratification in aiqeung maps precisely to complexity classes:

| Stratum | Analysis Method | Complexity | aiqeung Layer | Safe to call inline? |
|---|---|---|---|---|
| 0 | Structural (token presence, arc absence) | O(1) | Layer 2.5 `fire()` step-wise | **YES** |
| 1 | P-invariant / LP boundedness | Polynomial | Layer 0 CLP(PN) | **YES** |
| 2 | Causal ordering, firing counts (P-invariant) | Polynomial | Layer 0 CLP(PN) | **YES** |
| 3 | Reachability, liveness, WF-net soundness | **EXPSPACE-hard** / Ackermann-complete | Layer 3 obligations only | **NO — NEVER INLINE** |

**Critical design principle:** Never trigger strata-3 checks inside the SLD loop or
`fire()` method. Strata-3 computation inline would be catastrophic (Ackermann for
reachability, EXPSPACE for soundness/coverability).

**The Ackermann-completeness result (Czerwinski 2021) supersedes the earlier EXPSPACE lower
bound (Lipton 1976). Do NOT assume EXPSPACE is a tight bound for reachability.**

---

## Comparative Expressiveness

| Extension | Reachability | Boundedness | Liveness | Key value for aiqeung |
|---|---|---|---|---|
| Inhibitor arcs | **Undecidable** | **Undecidable** | **Undecidable** | Prohibition modelling |
| PrT-Nets | Decidable (finite) | Decidable (finite) | Decidable (finite) | Conditional requirements |
| Object nets | **Undecidable** | Decidable (elementary) | **Undecidable** | Hierarchical entities |
| Algebraic PN | Decidable (bounded+finite) | Decidable (finite) | Decidable (finite) | **Tokens as Terms — direct match** |
| Stochastic PN | Same as base | Same as base | Same as base | Risk quantification |
