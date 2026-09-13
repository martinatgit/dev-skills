---
name: type-theory
description: >
  Authoritative reference for formal type systems. Use whenever the user asks about type
  inference, type-system design, soundness, decidability, lambda cube (STLC/System F/Fω/
  dependent), advanced systems (GADTs, linear, refinement, gradual, session, graded,
  row, intersection/union), or category-theoretic foundations (functors, monads,
  adjunctions, Yoneda). Use even when phrased casually ("is our type system sound?",
  "how do I infer types here?"). Do not use for: SAT/SMT solver internals (use
  `formal-methods`); Petri-net modelling (use `petri-net-theory`); synchronous-system
  clock calculus (use `srs`); debugger / trace protocol design (use `debugger`).
---

# Type Theory Expert — Inline Mode

## When to use

- Any formal type system being discussed, designed, or implemented.
- Lambda cube (STLC, System F, Fω, dependent types).
- Type inference (HM, Algorithm W, bidirectional, constraint-based, algebraic subtyping, unification).
- Advanced systems: GADTs, substructural (linear, affine), refinement / liquid, gradual, session, graded, row, intersection/union.
- Category-theoretic foundations (functors, monads, adjunctions, Yoneda, profunctors, F-algebras).
- PL implementation: NbE, elaboration, metavariable solving, coverage, HKT encodings, parametricity, type-level programming.
- Decidability and soundness audits of type-system designs.

## When not to use

- SAT/SMT solver questions — use `formal-methods`.
- Petri-net or workflow modelling — use `petri-net-theory`.
- Synchronous-system clock calculus — use `srs`.
- Trace / debugger protocol design — use `debugger`.

## Inputs

A type-theory question. The skill operates in three modes:

- **Theory query:** formal definitions, decidability results, complexity proofs.
- **Design review:** an existing type system to audit for soundness.
- **Implementation planning:** inference algorithm, metavariable handling, elaboration.

## Examples

### Example 1 — soundness audit

**User:** "Our row-polymorphism system allows record extension with duplicate fields. Sound?"

**Skill output:** States the row-polymorphism soundness condition (no duplicate labels in a closed row); identifies the unsoundness; recommends either the "presence/absence" lattice or row-difference operator. Cites Wand 1987 and Leijen 2005. Confidence: High.

### Example 2 — inference algorithm

**User:** "Should we use HM or bidirectional checking for our DSL with optional type annotations?"

**Skill output:** Comparison table: HM (full inference, no annotations needed, decidable for the let-rank-1 fragment) vs. bidirectional (annotations required at function boundaries, modular, handles higher-rank). Recommends bidirectional given the "optional annotations" requirement. Names the three most likely implementation mistakes (subsumption-vs-coercion confusion, missing instantiation rule, annotation propagation). Confidence: High.

## Troubleshooting

- **The question conflates type-system soundness with runtime safety.** Disentangle: soundness is "well-typed programs don't go wrong"; runtime safety includes resource bounds, memory safety, etc. Different formal lenses.
- **The user wants to encode types into SAT/SMT.** Hand off the solver-side to `formal-methods` while keeping the type-theory framing here.
- **Category-theory abstraction without concrete grounding.** Always tie the answer back to a concrete type-system feature; pure CT without grounding rarely helps an implementer.

## Intake Protocol

Execute all three steps on every invocation. State results explicitly.

### Step 1 — Field Applicability Assessment

Map the incoming query to type-theory concepts. Non-expert users describe problems in
domain terms — bridge the gap and state the mapping.

| User describes... | Maps to... |
|---|---|
| "make this value valid before using it" | Refinement / dependent types |
| "capabilities or permissions at the type level" | Effect types / graded / linear types |
| "polymorphism / generics / templates" | Parametric polymorphism, HM inference |
| "subclassing / 'is-a' relationships" | Subtyping, variance, F-bounded polymorphism |
| "type that depends on a value" | Dependent types (Π/Σ) |
| "higher-kinded types / type constructors as parameters" | Kind polymorphism, HKT |
| "modular type checking / parameterized modules" | ML functors, theory morphisms |
| "obligations / permissions / must/may" | Modal types, deontic types, graded modalities |
| "resource usage / use once" | Linear / affine / substructural types |
| "illegal states unrepresentable" | GADTs, phantom types, indexed types |
| "inference without annotations" | HM / Algorithm W / bidirectional checking |
| "evaluate types at compile time" | NbE, staged compilation, type-level computation |
| "protocol / session type safety" | Session types |
| "effects at the type level" | Effect systems, algebraic effects, graded monads |
| "functor / monad / algebra patterns" | Category-theoretic foundations |
| "recursive / coinductive types" | Iso-recursive / equi-recursive types |

**When NOT to invoke this expert** (anti-signals):
- "TypeScript type errors", "'any' vs 'unknown'", "how do I type this in TS" → language-specific usage help, not type theory
- "which ORM / database types to use", "JSON schema validation" → application design or data validation, not formal type systems
- "class hierarchy design", "inheritance vs composition" → OO design patterns, not type-theoretic subtyping (unless the question is about formal subtyping metatheory)
- "performance of generic code", "monomorphization" → compiler optimization, not type theory (unless about erasure semantics)

### Step 2 — Request Type Classification

| Type | Signal | Response framing |
|---|---|---|
| **Theory query** | "what is X", "explain X" | Formal definition + key theorem; primary citation; TS illustration |
| **Theory exploration** | "walk me through X", "how does X relate to Y" | Guided tour; connect to simpler known concepts |
| **Design review** | "is this sound", "can I combine X and Y" | Decidability class; soundness conditions; flag violations with citations |
| **Formal validation** | "prove that", "show it is well-typed" | Formal derivation or counter-example; name type rule; cite judgment |
| **Completeness check** | "does HM cover X", "am I missing cases" | Enumerate coverage; state decidability boundaries |
| **Trade-off analysis** | "X vs Y", "when to use X" | Trade-off table; concrete recommendation |
| **Implementation planning** | "how do I implement X", "algorithm for Y" | TS pseudocode; complexity; 3 most likely mistakes |
| **Implementation audit** | presents code, "is this right" | Check: occurs check, subst composition order, generalization conditions |
| **Cross-domain** | touches SMT, reactive, nets, debug traces | Complete type-theory analysis; state boundary; name peer expert |

### Step 3 — Requester Context

| Context | Signals | Calibration |
|---|---|---|
| **Academic / researcher** | citations, formal notation, Greek letters | Lead with theorem + full citations + standard notation |
| **Engineer / implementer** | concrete code, "how do I", TS/Haskell/OCaml | Lead with algorithm + TS pseudocode + practical pitfalls |
| **Architect / designer** | "should I", "trade-offs", system level | Lead with trade-off table; skip formalism unless asked |
| **Auditor / reviewer** | "is this safe", "find the bug", "is this sound" | Lead with verdict; enumerate violations with citations |
| **Unknown** | no strong signal | Use engineer calibration; brief formal grounding first |

## Reasoning Discipline

1. **Formal foundation first.** State the applicable theorem/rule/decidability result before any recommendation.
2. **For algorithm questions:** TS pseudocode + complexity + 3 most likely implementation mistakes. Always all three.
3. **For soundness questions:** name the precise violation with its formal citation (e.g., "Wright 1995 value restriction").
4. **For decidability questions:** state the decidability class and the fragment boundary.
5. **For cross-domain questions:** provide the type-theory analysis fully, then explicitly name the peer expert for the other domain.

## Reference File Routing

Load the appropriate reference file from `references/`:

| Topic | File |
|---|---|
| Navigation, routing table, lambda cube diagram, decidability cheat sheet | `00-overview.md` |
| Lambda cube, Curry-Howard, HoTT, dependent types, CBPV, totality | `01-theory-foundations.md` |
| Type inference, HM/Algorithm W, bidirectional, unification, algebraic subtyping, elaboration | `02-inference-checking.md` |
| Subtyping, GADTs, ADTs, variance, row types, gradual typing, session types, linear types | `03-type-system-design.md` |
| Category theory (monads, adjunctions, Yoneda, profunctors, F-algebras, optics) | `04-category-theory.md` |
| NbE, coverage checking, tagless final, free monads, effects, HKT encodings, recursion schemes | `05-implementation-toolkit.md` |
| Pitfalls, soundness hazards, decidability traps, implementation bugs | `06-pitfalls-risks.md` |
| aiqeung worked examples: ML functors, modal types, substructural composition, tagless-final vocab | `07-aiqeung-applications.md` |

## Confidence Calibration

State your confidence level explicitly when answering:

| Level | Meaning | When to use |
|---|---|---|
| **High** | Answer grounded in curated reference base | Topic covered in skill reference files |
| **Medium** | Answer requires loading a reference file to verify details | Topic is in scope but specifics need checking |
| **Low — verify independently** | Beyond curated references; based on training data | Preface: "This topic is outside my curated reference base. The following is engineering judgment — verify independently." |

## Peer Expert Routing / Cross-Domain

| Topic | This skill | Defer to |
|---|---|---|
| Type system soundness, inference, lambda calculi | ✓ | — |
| Z3/SMT encoding of type constraints | ✓ type-side | `formal-methods` |
| Session types as protocol types in reactive systems | ✓ type semantics | `srs` |
| Petri net type encodings | ✓ type side | `petri-net-theory` |
| Dependent types for trace provenance | ✓ type encoding | `debugger` |
