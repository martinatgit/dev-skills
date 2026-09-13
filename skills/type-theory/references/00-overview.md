# Type Theory Expert — Overview & Navigation

## Quick Routing

| Question type | Load this file |
|---|---|
| "What is X", theory, proofs, Curry-Howard, HoTT, lambda cube | `01-theory-foundations.md` |
| Inference algorithms (HM, bidirectional, unification), "how to infer types" | `02-inference-checking.md` |
| Type system design, subtyping, GADTs, effects, variance, row types | `03-type-system-design.md` |
| Category theory (monads, functors, adjunctions, Yoneda, profunctors) | `04-category-theory.md` |
| Implementation patterns (NbE, elaboration, encodings, TS pseudocode) | `05-implementation-toolkit.md` |
| Pitfalls, soundness hazards, decidability traps | `06-pitfalls-risks.md` |

## Peer Expert Routing

| Topic | This agent | Defer to |
|---|---|---|
| Type system soundness, inference algorithms, lambda calculi | ✓ | — |
| Z3/SMT encoding of type constraints | ✓ type side | `formal-methods` for solver side |
| Session types as communication protocol types | ✓ | `srs` for reactive scheduling |
| Petri net type encodings / typed place invariants | ✓ | `petri-net-theory` for net semantics |
| Dependent types for trace provenance in debugger | ✓ | `debugger` for trace semantics |

## Lambda Cube — One Glance

```
          λω (System Fω)      λPω (CoC)
         /                  /
        /                  /
   λ2 (System F)      λP2
      |                  |
      |                  |
   λ→ (STLC)       λP (LF / dependent)
```
- **λ→** STLC: function types only. Terms depend on terms.
- **λ2** System F: add polymorphism (∀α.τ). Types depend on types (universal quantification).
- **λω** System Fω: add type operators (κ). Types depend on types at higher kinds.
- **λP** LF: add dependent types (Πx:A.B). Types depend on terms.
- **λPω (CoC)**: all three. The Calculus of Constructions (Coquand-Huet 1988). Basis for Coq.
- **MLTT**: Martin-Löf Type Theory — dependent types with universes; basis for Agda, Lean, Idris.

## Key Decidability Results

| System | Type checking | Type inference | Notes |
|---|---|---|---|
| STLC | Decidable, linear | Decidable, near-linear (unification) | Strongly normalizing |
| System F | Decidable | **Undecidable** (Wells 1999) | Rank ≥ 2 → undecidable |
| HM (rank-1 System F) | Decidable | Decidable, DEXPTIME-complete (Mairson 1990) | Near-linear in practice |
| Bidirectional (rank-2+) | Decidable | Decidable with annotations | Practical for most needs |
| MLTT / dependent types | Decidable | Undecidable with general recursion | Requires structural recursion |
| Full System F<: | **Undecidable** (Pierce 1994) | — | Kernel F<: is decidable |
| First-order unification | Decidable | — | Near-linear with union-find (Martelli-Montanari) |
| Higher-order unification (HOU) | **Undecidable** (Goldfarb 1981) | — | Pattern fragment is decidable (Miller 1991) |
| TypeScript type system | **Undecidable** (Turing-complete, Hediet 2017) | — | Recursive conditional types cause divergence |

## Curry-Howard-Lambek Triple

| Logic | Type Theory | Category Theory |
|---|---|---|
| Proposition | Type | Object |
| Proof | Term / Program | Morphism |
| Implication A ⊃ B | Function type A → B | Exponential Bᴬ |
| Conjunction A ∧ B | Product type A × B | Product A × B |
| Disjunction A ∨ B | Sum type A + B | Coproduct A + B |
| True (⊤) | Unit type | Terminal object 1 |
| False (⊥) | Empty type | Initial object 0 |
| Universal ∀x:A.P(x) | Dependent Π-type | Right adjoint to substitution |
| Existential ∃x:A.P(x) | Dependent Σ-type | Left adjoint to substitution |

## When to Choose Which Inference Algorithm

| Need | Algorithm | Why |
|---|---|---|
| Full inference, no annotations, rank-1 | HM / Algorithm W | Principal types; complete; standard for ML/OCaml/Haskell |
| Higher-rank polymorphism | Bidirectional (Dunfield-Krishnaswami 2013) | Decidable with strategic annotations |
| Subtyping + inference combined | SimpleSub / algebraic subtyping | Avoids constraint explosion; simpler than MLsub |
| Type classes / overloading | HM + qualified types (Jones 1992) | Extends principal types to constrained polymorphism |
| Open-world, TypeScript-style | Constraint-based (HM(X)) | Flexible; loses principal types |
| Dependent types | Elaboration + metavariable solving | NbE for equality; higher-order unification for metas |
