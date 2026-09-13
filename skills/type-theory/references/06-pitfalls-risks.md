# Type System Pitfalls & Risks

## Severity Guide
- 🔴 **Unsoundness** — breaks type safety; runtime errors or wrong behavior despite type checking
- 🟠 **Decidability trap** — type checker diverges or becomes undecidable
- 🟡 **Performance cliff** — type checking becomes exponentially slow
- 🔵 **Implementation trap** — wrong output without error; silent correctness failure

---

## 🔴 Unsoundness Hazards

### 1. Type-in-Type / Impredicativity Without Restriction
**Violation:** Adding `Type : Type` to any type theory.
**Consequence:** Girard's paradox (1972) — type theory becomes inconsistent. Russell's paradox is encodable. Non-termination of type checking.
**Fix:** Universe stratification (`Type₀ : Type₁ : Type₂ : ...`) or universe polymorphism (Agda/Lean style).
**Formal citation:** Coquand's encoding of Burali-Forti paradox in CC with Type:Type (1986).

### 2. Generalizing Mutable References Without Value Restriction
**Violation:** Applying HM let-generalization to expressions that are not syntactic values when mutation is present.
**Consequence:** `let r = ref [] in (r := [1]; !r : bool list)` — the ref's type is polymorphically generalized to `∀a. ref(list a)`, then specialized inconsistently.
**Fix:** Wright's value restriction (1995) — only generalize syntactic values (variable, lambda, constructor application), not arbitrary expressions.
**Formal citation:** Wright, A.K. "Simple Imperative Polymorphism." LISP and Symbolic Computation, 1995.

### 3. Covariant Mutable Containers
**Violation:** Treating `Array<Cat>` as a subtype of `Array<Animal>` when Array is mutable.
**Consequence:** Java's covariant arrays: `String[] ss = new String[1]; Object[] os = ss; os[0] = 42;` → `ArrayStoreException` at runtime despite static type safety.
**Fix:** Invariance for mutable type parameters. TypeScript `Array<T>` is intentionally bivariant (unsound by design). Use `ReadonlyArray<T>` for covariant read-only access.

### 4. Omitting the Occurs Check in Unification
**Violation:** Unifying `α` with `α → α` without occurs check.
**Consequence:** Produces infinite type `α = α → α → α → ...`; unification diverges or produces a garbage substitution.
**Fix:** Check `occursIn(α, τ)` before binding `α ↦ τ` in every unification step. Cost: O(size(τ)) per binding — worth it.

### 5. Gradual Typing with Unchecked Dynamic Boundaries
**Violation:** Allowing `any` to propagate without inserting runtime casts at static/dynamic boundaries.
**Consequence:** Type errors deferred to runtime without clear blame attribution. Violates the gradual guarantee (Siek-Taha).
**Fix:** Blame calculus — every `any` boundary is a cast with a blame label. Runtime failure reports which cast was responsible (Wadler-Findler).

### 6. Linear Type Violations Through Aliasing
**Violation:** Allowing a linear value to be stored in multiple locations (aliased).
**Consequence:** Use-after-free (resource used twice or not at all) despite type-checking passing.
**Fix:** Linear type system enforces exchange/weakening/contraction rules. Track usage through the context — variable must appear exactly once.

---

## 🟠 Decidability Traps

### 7. Higher-Rank Polymorphism Without Bidirectional Checking
**Violation:** Adding rank-2+ polymorphism to HM without switching to bidirectional inference.
**Consequence:** Type inference becomes undecidable (Wells 1999: ∀α.τ at rank ≥ 2 in System F → undecidable inference). Type checker loops.
**Fix:** Use bidirectional type checking with strategic annotation requirements (Dunfield-Krishnaswami 2013). Alternatively restrict to rank-1 (HM).

### 8. Full System F<: Subtyping
**Violation:** Implementing the full System F<: subtype relation as specified in Pierce's TAPL.
**Consequence:** Subtype checking undecidable (Pierce 1994). Compiler hangs.
**Fix:** Use kernel F<: (reflexivity and transitivity only for quantified types) — decidable. Or use structural subtyping without bounded quantification on type variables.

### 9. TypeScript Type-Level Recursion Without Bound
**Violation:** Writing deeply recursive conditional types without a base case the TypeScript checker can recognize as terminating.
**Consequence:** TypeScript hits the recursive type instantiation depth limit (default: ~100). Error: "Type instantiation is excessively deep and possibly infinite."
**Fix:** Use tuple-length-based recursion with explicit depth counter. Or switch to runtime computation for non-trivial type-level arithmetic.

### 10. Overlapping Type Class Instances
**Violation:** Defining two instances `Foo<Int>` and `Foo<a>` that overlap.
**Consequence:** Instance resolution becomes non-deterministic. Coherence lost — same expression can have different types in different contexts.
**Fix:** GHC's `OVERLAPPABLE`/`INCOHERENT` are escape hatches, not solutions. Design instances to be non-overlapping. Use newtype wrappers to disambiguate.

### 11. Dependent Types With General Recursion
**Violation:** Adding unrestricted general recursion to a dependently typed language.
**Consequence:** Type checking undecidable. Every type inhabitation problem reduces to the halting problem.
**Fix:** Require structural recursion (size decreasing), guardedness (corecursion), or sized types. This is the basis of Agda's totality checker and Coq's Fixpoint guardedness check.

---

## 🟡 Performance Cliffs

### 12. Exponential Type Blowup from Nested Let-Polymorphism
**Violation:** Deep nesting of let-polymorphic bindings in HM.
**Consequence:** Each let-binding can double the type size through instantiation. O(2^n) in pathological cases (Mairson 1990). DEXPTIME-complete in the worst case.
**Reality:** Realistic programs rarely trigger this. Near-linear in practice because deep polymorphic nesting is uncommon.
**Fix:** If you see exponential blowup: reduce let-nesting depth, or switch to constraint-based inference with explicit sharing.

### 13. Explicit Substitution Composition
**Violation:** Implementing Algorithm W with explicit `Map<TypeVar, Type>` substitutions and composing them eagerly.
**Consequence:** Each `compose(s1, s2)` applies `s2` to all bindings in `s1`, making the total cost O(n²) in the number of unifications.
**Fix:** Use union-find (Algorithm J variant) — path compression + union by rank → O(n · α(n)) where α is the inverse Ackermann function. Kiselyov's levels trick eliminates most free-variable computation during generalization.

### 14. Full Normalization of Open Terms in Large Environments
**Violation:** Running NbE `normalize` on open terms with large evaluation environments at every type-equality check.
**Fix:** Cache evaluated values at binders. Use lazy Val representation — don't evaluate under lambdas until forced. Memoize neutral terms.

---

## 🔵 Implementation Traps

### 15. Wrong Substitution Composition Order
**Violation:** `compose(s1, s2)` where the intended meaning is "apply s1 first, then s2" but you implement it as "apply s2 first, then s1".
**Consequence:** Wrong types inferred silently. No type error. Tests may still pass if test cases don't exercise the ordering difference.
**Fix:** Document the convention at the `compose` definition. The standard: `compose(s1, s2)(x) = s2(s1(x))` — apply s1 first. Test with a non-commutative case: `s1 = {α ↦ β}`, `s2 = {β ↦ Int}` → `compose(s1,s2)(α) = Int` (correct); reversed gives `α ↦ β` (wrong).

### 16. Variable Capture During Instantiation
**Violation:** Instantiating a type scheme by substituting without first α-renaming captured variables.
**Consequence:** Free variables in the instantiated type accidentally refer to bound variables in the environment.
**Fix:** Always generate fresh type variable names during instantiation. Never re-use variable names across instantiation sites. A counter (`let _n = 0; const fresh = () => \`t${_n++}\``) suffices.

### 17. Coverage Checking With GADTs — Structural Pattern Match Is Insufficient
**Violation:** Checking GADT pattern exhaustiveness using only structural matching (without constraint propagation per branch).
**Consequence:** A pattern that is structurally exhaustive may be non-exhaustive for the GADT — some constructor combinations are impossible at a given type but the checker doesn't know.
**Fix:** Propagate the type constraints implied by each GADT constructor pattern into the checking context for that branch. Cockx-Abel 2018 sheaf semantics gives the formal treatment.

### 18. Bidirectional Checking Missing the Subsumption Rule
**Violation:** Implementing bidirectional checking without the `[Chk-Sub]` rule: if `e ⇒ A` and `A <: B` then `e ⇐ B`.
**Consequence:** The synthesized type is never checked against the expected type. Type annotations are ignored during checking mode.
**Fix:** Always include subsumption as a fallback in the checking judgment: if direct checking fails, synthesize and compare with subtyping.

### 19. Iso-Recursive Types Without Explicit Fold/Unfold at Every Site
**Violation:** Forgetting to insert `fold`/`unfold` coercions at every recursive type introduction/elimination site.
**Consequence:** Type errors at every use site of the recursive type. Or, if fold/unfold is implicit in the IR, silent type confusion.
**Fix:** Add a linting pass that checks every constructor application for a recursive type is wrapped in a fold, and every destructor is wrapped in an unfold. Equi-recursive types (TypeScript, Java) avoid this by making fold/unfold transparent.

### 20. Row Polymorphism — Forgetting the `lacks` Constraint
**Violation:** Implementing row-polymorphic record extension without the `lacks` (absence) constraint.
**Consequence:** Duplicate field names become possible. `extend({x: 1}, {x: 2})` type-checks but produces a record with two `x` fields.
**Fix:** Every row variable `ρ` extended with field `x : τ` must carry the constraint `ρ \ x` (ρ lacks x). Rémy's encoding makes this explicit in the constraint system.

---

## Cross-Domain Risks

### Session Types + Reactive Scheduling
Linear types for channel use must be enforced by the scheduler. If the reactive scheduler can duplicate or drop a channel operation (e.g., in a `par` branch that races and loses), the linear discipline for session types is broken.
→ Consult `srs` for correct handling of linear channel operations under synchronous scheduling.

### Type Constraints in SMT Encoding
Encoding type constraints (e.g., refinement type predicates) as SMT formulas requires identifying the decidable fragment: QF_LIA for linear arithmetic, QF_NIA for nonlinear (often undecidable). Mixing quantified formulas into the constraint language may make the SMT query undecidable.
→ Consult `formal-methods` for fragment identification and Z3 encoding strategies.
