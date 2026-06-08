# Type Theory in aiqeung — Worked Examples

Concrete applications of type-theory concepts to the aiqeung implementation.
All code snapshots are taken from aiqeung v0.5.1.0 (2026-04). Source paths are given
for orientation only — verify against the live codebase before referencing.

---

## 1. Layer 5 Module Functor as ML-Style Parameterized Module

**Type-theory concept:** ML-style module system with parameterized modules (functors),
theory parameters, and theory morphisms (views). Applicative functor semantics.

**Reference:** Harper & Mitchell 1993 ("On the Type Structure of Standard ML");
Leroy 1994 ("Manifest Types, Modules, and Separate Compilation");
Dreyer, Crary & Harper 2003 ("A Type System for Higher-Order Modules").

### Formal correspondence

An ML functor `F(X: SIG) : SIG'` maps module-with-signature to module-with-signature.
In applicative semantics, `F(A) = F(B)` whenever `A = B` (path-equality), as opposed
to generative semantics where each application creates a fresh abstract type.

aiqeung Layer 5 `ModuleFunctor` directly instantiates this structure:

```typescript
// Source path: src/aiqeung-core/module/types.ts (v0.5.1.0)
// [SNAPSHOT — verify against live codebase]

/** Predicate signature — functor/arity pair. Corresponds to an SML val declaration. */
interface PredicateSignature {
  readonly functor: string
  readonly arity: number
  readonly description?: string
}

/** Theory parameter: a named set of required predicate signatures.
 *  Corresponds to an SML signature. */
interface TheoryParameter {
  readonly name: string
  readonly requiredPredicates: readonly PredicateSignature[]
}

/** Module functor — a module template parameterized by theory parameters.
 *  Corresponds to: functor F(X: SIG) : SIG' = struct ... end
 *  Uses applicative semantics: F(A)::pred/2 from one context is the same
 *  predicate as F(A)::pred/2 from another. */
interface ModuleFunctor {
  readonly name: string
  readonly parameters: readonly TheoryParameter[]
  readonly template: ModuleSpec
}

/** A view maps a theory parameter to a concrete module.
 *  Views are theory morphisms: they verify the actual module exports
 *  all required predicates. Corresponds to SML 'where type' constraint. */
interface ModuleView {
  readonly parameter: string
  readonly module: Module
  readonly mappings?: readonly PredicateMapping[]
}
```

**Type-theory analysis:**

- `TheoryParameter` is a **signature** in ML terminology: it specifies an interface
  (set of predicate/arity declarations) that an argument module must satisfy.
- `ModuleFunctor` is an **SML functor**: it has zero or more theory parameters and
  a template body.
- `ModuleView` is a **theory morphism** (in algebraic specification terminology) or
  a **structure matching a signature** (in SML): it maps formal parameter names to
  concrete module predicates, satisfying the signature constraints.
- The comment "applicative functor semantics (OCaml style, not SML generative)" is
  precise: OCaml's module system is applicative (F(A) = F(B) when A = B structurally),
  while SML is generative (each application creates fresh abstract types). aiqeung
  chooses OCaml semantics to ensure that two contexts loading the same vocabulary module
  share the same predicate identity.

**When to invoke type-theory for this area:**
- Deciding between applicative and generative module semantics for Layer 5
- Soundness of the view/theory-morphism check (does the mapping preserve all required predicates?)
- Type-checking module composition (protecting/extending/including and their substructural meanings — see §2 below)

---

## 2. CompositionMode as Substructural Type Disciplines

**Type-theory concept:** Substructural type systems (linear, affine, relevant, unrestricted)
control how resources may be used. Applied to module composition, they control how one
module's solutions may be extended by another.

**Reference:** Walker 2005 ("Substructural Type Systems", in Pierce, ATTAPL);
Girard 1987 ("Linear Logic"); Reynolds 2002 ("Separation Logic").

### Formal correspondence

aiqeung's `CompositionMode` directly encodes three points on the substructural lattice:

```typescript
// Source path: src/aiqeung-core/module/types.ts (v0.5.1.0)
// [SNAPSHOT — verify against live codebase]

/**
 * Composition mode for module loading. Adapted from Maude's theory importation modes.
 *   - protecting: no new solutions for existing predicates (additive namespace only)
 *   - extending: may add solutions but never remove them (safe additive composition)
 *   - including: unrestricted composition
 * Default is "extending".
 */
type CompositionMode = "protecting" | "extending" | "including"
```

**Substructural mapping:**

| CompositionMode | Substructural discipline | Meaning for solver |
|---|---|---|
| `protecting` | **Relevant** (must use, cannot weaken) | Protected module's predicate set is frozen; importer can only ADD new predicates, never add clauses to existing ones |
| `extending` | **Affine** (may discard, cannot duplicate) | Importer may add new solutions (clauses) to existing predicates, but existing solutions can never be removed; monotone growth |
| `including` | **Unrestricted** (no constraints) | Importer may add, override, or extend anything; full structural rules |

Note: "protecting" in Maude is not quite "relevant" in the linear logic sense — the mapping
is an analogy for understanding the design intent, not a formal embedding.

**Type-theory analysis:**

The choice of `"extending"` as the default corresponds to a key semantic guarantee: the
solver's closed-world assumption (CWA) applied to individual modules. If module A concludes
`foo(1)` under `protecting(B)`, then loading C with mode `including` cannot retroactively
change B's semantics and invalidate A's conclusion. This is the **monotonicity invariant**
that `extending` mode enforces.

From a substructural perspective, `protecting` is analogous to the comonadic modality `!`
in linear logic: it marks a resource as "definitely available and unmodified". `extending` is
affine: the resource (module predicate set) may grow but not shrink. `including` drops the
substructural restriction entirely.

**When to invoke type-theory for this area:**
- Verifying that a proposed composition sequence maintains the monotonicity invariant
- Deciding which mode to use when combining two vocabularies that share predicate names
- Formal soundness of the composition algebra (does the mode lattice form a coherent partial order?)

---

## 3. Layer 6 Vocabulary Modules as Tagless-Final Algebras

**Type-theory concept:** Tagless-final (or "finally tagless") interpretation is a technique
for embedding DSLs without an intermediate syntax tree. Terms are represented as elements of
a type class / algebra, and interpretations are instances of that algebra.

**Reference:** Carette, Kiselyov & Shan 2009 ("Finally Tagless, Partially Evaluated");
Kiselyov 2012 ("Typed Tagless Final Interpreters").

### Formal correspondence

Each Layer 6 vocabulary module follows a consistent structure:

```typescript
// Source path: src/aiqeung-core/vocab/deontic.ts (v0.5.1.0)
// [SNAPSHOT — simplified to show the pattern; verify against live codebase]

// The "algebra" has two components:
//   assert.*  — constructors for user-input facts (terms in the DSL)
//   query.*   — constructors for derived query terms

// Obligation constructor — an element of the "obligation" algebra
const obligationTo = (subject: Term, action: Term): Term =>
  t.compound("obligation_to", subject, action)

// Query — an element of the "compliance" algebra
const compliant = (subject: Term): Term =>
  t.compound("compliant", subject)

// The module exposes two namespaces:
//   deontic.assert.obligationTo  — algebra constructor for user input
//   deontic.query.compliant      — algebra constructor for derived queries
```

**Type-theory analysis:**

In tagless-final style, the "syntax" of a DSL is a TypeScript interface (or type class):

```typescript
// Hypothetical tagless-final interface for the deontic DSL
interface DeonticSyntax<T> {
  obligationTo(subject: T, action: T): T
  prohibitionTo(subject: T, action: T): T
  performed(subject: T, action: T): T
}
```

The aiqeung Layer 6 implementation does not literally use this interface, but the `assert.*`
builders are exactly the constructors of a tagless-final algebra where `T = Term`. The
`query.*` builders are the "observer" operations that read back derived terms from the
algebra.

The **F-algebra** perspective (category theory): each vocabulary defines a functor
`F(X) = obligationTo(X, X) + prohibitionTo(X, X) + ...` and the `Term` type is an
`F`-algebra `F(Term) → Term` via `t.compound(...)`. The initial algebra (`μF`, the least
fixed point) is the term syntax itself; the deontic clauses loaded into the solver are one
specific F-algebra morphism (the "evaluator") from syntax to solver facts.

**When to invoke type-theory for this area:**
- Deciding whether a new vocabulary should expose `assert.*` vs `query.*` builders vs both
- Proving that the F-algebra composition of two vocabularies is coherent (no shared functor
  constructors with conflicting arities)
- Analysing whether the tagless-final encoding allows polymorphic interpretation across
  different solvers

---

## 4. Modal Operators as Type-Level Modalities

**Type-theory concept:** Modal type theory interprets necessity (□) and possibility (◇) as
type-level modalities. S4 modal logic corresponds (via Curry-Howard) to a comonad (□ is a
comonad); S5 adds the condition that the comonad is also a monad; intuitionistic S4
corresponds to staged computation (Pfenning & Davies 2001).

**Reference:** Pfenning & Davies 2001 ("A Judgmental Reconstruction of Modal Logic");
Davies & Pfenning 2001 ("A Modal Analysis of Staged Computation");
Bierman & de Paiva 2000 ("On an Intuitionistic Modal Logic").

### Formal correspondence

aiqeung's modal logic vocabulary implements Kripke semantics for K, T, S4, S5, D:

```typescript
// Source path: src/aiqeung-core/vocab/modal.ts (v0.5.1.0)
// [SNAPSHOT — verify against live codebase]

interface ModalOptions {
  /** Which modal logic to configure.
   *  K  — minimal (no frame constraints)
   *  T  — reflexive accessibility
   *  S4 — reflexive + transitive
   *  S5 — reflexive + transitive + symmetric (equivalence relation)
   *  D  — serial (every world has a successor)                       */
  logic?: "K" | "T" | "S4" | "S5" | "D"
  facts?: ReadonlyArray<Term>
}
```

**Type-theory analysis:**

The frame conditions correspond to structural properties of the modal comonad:

| Modal logic | Frame property | Type-theoretic meaning |
|---|---|---|
| K | (none) | Minimal modal comonad; no structural rules |
| T | Reflexive (wRw) | Counit: □A → A (can always use a necessity) |
| S4 | Reflexive + transitive | Idempotent comonad: □A → □□A (stages can be nested) |
| S5 | Equivalence relation | □A ↔ ¬◇¬A; comonad is also a monad |
| D | Serial | □A → ◇A (obligations are satisfiable; deontic use) |

For aiqeung's **deontic vocabulary** (`vocab/deontic.ts`), the D-axiom □A → ◇A is the
formal expression of satisfiability: every obligation can be fulfilled. The deontic module
operates in a single normative world (no possible-world quantification), which is a
**degenerate case** of K with one world — essentially propositional obligation logic
without the modal comonad structure.

For aiqeung's **modal vocabulary** (`vocab/modal.ts`), S4 corresponds to staged
computation: a term that is necessarily true at world w is also necessarily true at any
accessible world. This is the foundation for using S4 modal logic to reason about
multi-step inference chains where validity must propagate across reasoning steps.

The **Pfenning-Davies correspondence** (2001) gives a direct Curry-Howard reading:
- □A ≅ "A holds in all accessible worlds" ≅ "A is available at the current stage and all future stages" ≅ the type of a term that is safe to use in any compiled stage
- ◇A ≅ "A holds in some accessible world" ≅ "A will be available at some future stage" ≅ a promise or future value

This gives a path to typed staging in aiqeung: if Layer 6 vocabularies are assigned modal
types (□ for stable, universally-available knowledge; ◇ for eventually-derived conclusions),
the modal logic vocabulary becomes the type system for knowledge propagation across reasoning
contexts.

**When to invoke type-theory for this area:**
- Deciding which modal logic (K/T/S4/S5/D) to use for a given reasoning context
- Formal analysis of the D-axiom requirement for deontic vocabularies
- Designing typed staging semantics for multi-context reasoning chains using the Pfenning-Davies correspondence

---

## 5. Layer 5 Module Composition and the Module Type as a Record Type

**Type-theory concept:** Record types (product types with labeled fields) are the standard
type-theoretic model for module signatures. Module subtyping corresponds to width and depth
subtyping for records. Module sealing ("opaque" ascription) corresponds to existential
quantification.

**Reference:** Pierce 2002, TAPL, Chapter 11 (Records) and Chapter 24 (Existential Types);
Leroy 1994; Dreyer et al. 2003.

### Formal correspondence

```typescript
// Source path: src/aiqeung-core/module/types.ts (v0.5.1.0)
// [SNAPSHOT — verify against live codebase]

interface Module {
  readonly name: string
  readonly version: string
  readonly metadata: ModuleMetadata
  readonly children: readonly Module[]       // child modules: nested namespaces
  readonly exports: readonly ExportDeclaration[]
  readonly imports: readonly ImportDeclaration[]
  readonly open: ReadonlySet<string>         // open predicates: extensible slots
  readonly contributes: readonly ContributionDeclaration[]
  readonly clauses: readonly Clause[]
  readonly assets: ReadonlyMap<string, ModuleAsset>
  readonly builtins: ReadonlyMap<string, BuiltinHandler>
  readonly hooks: ModuleHooks
  readonly metaPredicates: readonly MetaPredicateDeclaration[]
}
```

**Type-theory analysis:**

`Module` is a **record type** in Pierce's sense. Each field corresponds to a component of
the module's "signature." The design note "Modules are values, not containers — immutable
once assembled" directly instantiates the **value restriction** from ML module semantics:
once sealed, a module's abstract types are fixed.

**Width subtyping:** A module with more exports is a subtype of one with fewer (it satisfies
all the obligations of the smaller interface). `ExportDeclaration` controls which predicates
are visible — adding exports grows the record type, corresponding to width subtyping in the
presence of covariant field access.

**Depth subtyping:** `CompositionMode` controls whether extension is allowed. `protecting`
mode is analogous to **invariant** positions (no sub- or super-typing allowed); `extending`
is analogous to **covariant** positions (additions permitted); `including` is analogous to
**bivariant** positions (no constraint).

**Existential types and sealing:** The `open: ReadonlySet<string>` field marks predicates
that are "open for contribution" — this is conceptually an **existential type abstraction**:
the open predicate is abstract from the consumer's perspective until all contributions are
collected and the module is "sealed" at load time. After sealing, the predicate's extension
is fixed and the existential is eliminated.

**When to invoke type-theory for this area:**
- Formal soundness of the export algebra (is the covariance of `open` predicates sound?)
- Analysing whether the `protecting/extending/including` lattice is a coherent subtype lattice
- Designing a type-level check that catches predicate arity mismatches across contributions

---

## Summary: Type-Theory Concept Map for aiqeung

| aiqeung construct | Type-theory concept | Reference section |
|---|---|---|
| `ModuleFunctor` / `TheoryParameter` / `ModuleView` | ML parameterized modules, theory morphisms | §1 |
| `CompositionMode` protecting/extending/including | Substructural disciplines (relevant/affine/unrestricted) | §2 |
| `vocab/X.ts` `assert.*` / `query.*` builders | Tagless-final algebras, F-algebras | §3 |
| `ModalOptions` K/T/S4/S5/D | Modal comonads, Pfenning-Davies correspondence | §4 |
| `Module` record type, `open`, sealing | Record types, width/depth subtyping, existential types | §5 |
| Layer 6 vocabulary strata (0–3) | Graded types / stratified type systems | See `06-pitfalls-risks.md` for NAF-stratification; formal-methods for constraint strata |

---

*All code snapshots are from aiqeung v0.5.1.0 and may become stale as the codebase evolves.
Verify against the live source before referencing in implementation work.*
