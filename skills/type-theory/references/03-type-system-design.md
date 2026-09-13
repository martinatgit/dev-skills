# Type System Design Reference

This reference is organized around the question "when and why would you choose this feature?" — not academic taxonomy.
Each section covers a specific design decision with formal foundations, algorithm, pragmatics, pitfalls, and cross-references.

---

## Design Decision Reference Table

| Design decision | Option A | Option B | Trade-off | When to use A | When to use B |
|---|---|---|---|---|---|
| Polymorphism | HM rank-1 | Bidirectional rank-n | Decidability vs. expressiveness | ML/OCaml: full inference | Haskell/Scala: annotations tolerable |
| Subtyping | Structural | Nominal | Open-world vs. discipline | TS, OCaml: duck typing | Java, Haskell: explicit subtype |
| Recursive types | Equi-recursive | Iso-recursive | Transparency vs. explicitness | TypeScript, Java | ML, Haskell newtypes |
| Effect tracking | Monadic | Algebraic effects | Library vs. language-level | Haskell mtl | OCaml 5, Koka, Effekt |
| ADT encoding | Tagged unions | Type classes (tagless) | Simplicity vs. extensibility | Most cases | Expression problem contexts |
| Type identity | Structural | Branded/nominal | Duck typing vs. safety | Default TS | Newtypes, unit safety |
| Resource tracking | Unrestricted | Linear/affine | Simplicity vs. safety | Most languages | Rust (affine), Granule (linear) |

---

## 1. Subtyping & Bounded Quantification (System F<:)

### 1.1 Formal Foundations

System F<: (Cardelli, Martini, Mitchell, Scedrov 1991–1994) extends System F with a subtyping relation. Types: `T ::= X | Top | T1 -> T2 | forall X <: T1 . T2`. Subtyping judgement `Gamma |- S <: T`:

```
(S-Top)    Gamma |- S <: Top
(S-Refl)   Gamma |- X <: X
(S-Trans)  Gamma |- S <: U,  Gamma |- U <: T  =>  Gamma |- S <: T
(S-TVar)   (X <: T) in Gamma  =>  Gamma |- X <: T
(S-Arrow)  Gamma |- T1 <: S1,  Gamma |- S2 <: T2  =>  Gamma |- S1->S2 <: T1->T2
(S-All)    Gamma |- T1 <: S1,  Gamma, X <: T1 |- S2 <: T2  =>
             Gamma |- (forall X <: S1 . S2) <: (forall X <: T1 . T2)
```

Key typing rules: `(T-Sub)`, `(T-TAbs)`, `(T-TApp)`. Subsumption rule `T-Sub` is computationally silent (erasure-compatible).

**Decidability**: Full F<: subtype checking is **undecidable** (Pierce 1992, reduction from 2-counter machines). Kernel F<: (S-All requires equal bounds: `S1 = T1`) is decidable but PSPACE-hard (Vorobyov 1995). Use kernel F<: in practice.

### 1.2 Core Algorithm

Kernel F<: algorithmic subtyping — the assumption set absorbs transitivity:

```typescript
function isSubtype(s: Type, t: Type): boolean {
  if (t.tag === 'Top') return true;
  if (s.tag === 'Bot') return true;
  if (s.tag === 'Record' && t.tag === 'Record')
    return t.fields.every(([k, tv]) => {
      const sf = s.fields.find(([k2]) => k2 === k);
      return sf !== undefined && isSubtype(sf[1], tv); // covariant fields
    });
  if (s.tag === 'Arrow' && t.tag === 'Arrow')
    return isSubtype(t.param, s.param)   // contravariant param
        && isSubtype(s.ret, t.ret);       // covariant return
  if (s.tag === 'Ref' && t.tag === 'Ref')
    return typeEqual(s.inner, t.inner);   // invariant for mutable refs
  return typeEqual(s, t);
}
```

For type variables: `SA-Trans-TVar` — if `X <: U` in context, check `U <: T` recursively. This absorbs transitivity and ensures termination in kernel F<: (context strictly grows, chain length bounded).

Full kernel F<: includes context (type variable bounds):
```typescript
// SA-Trans-TVar: X <: T iff bound(X) <: T
if (s.tag === 'TVar') {
  const bound = ctx.get(s.name);
  return isSubtype(ctx, bound, t);
}
// SA-All (Kernel): bounds must be syntactically equal
if (s.tag === 'Forall' && t.tag === 'Forall') {
  if (!typeEquals(s.bound, t.bound)) return false;
  const extCtx = new Map(ctx);
  extCtx.set(s.param, s.bound);
  return isSubtype(extCtx, s.body, t.body);
}
```

### 1.3 Pragmatic Implementation

TypeScript directly encodes bounded quantification via `extends`:
- `<T extends Animal>` = `forall T <: Animal . ...`
- Structural subtyping is the default — `{a: number, b: string} <: {a: number}`
- F-bounded quantification: `interface Ord<T extends Ord<T>>` works natively
- Multiple bounds via intersection: `<T extends Animal & { id: number }>`

Use `in`/`out` annotations (TS 4.7+) for explicit variance on type parameters.

### 1.4 Common Pitfalls

1. **Variance confusion**: Arrow types are contravariant in domain, covariant in codomain. Reversing this is the most common subtyping bug.
2. **Transitivity in algorithm**: Never include a separate transitivity rule in an algorithmic system — it causes non-termination. Absorb it into `SA-Trans-TVar`.
3. **Alpha-equivalence**: Bound type variables in `forall` require alpha-renaming; skipping this gives false negatives.
4. **Full vs. kernel**: Implementing full F<: (different bounds in `S-All`) is undecidable. Explicitly choose kernel F<:.
5. **Memoization neglected**: Cache `(Gamma, S, T) -> bool` for large type hierarchies.

### 1.5 Cross-References

Related: Row Types (alternative to subtyping for records), Intersection & Union Types (interact with F<:), Variance (covariance/contravariance rules), Existential Types (bounded existentials in F<:-sub), Recursive Types (F<: + recursive types = undecidable subtyping).

---

## 2. Row Types & Record Calculi

### 2.1 Formal Foundations

Row types (Wand 1987; Rémy 1989–1994) model extensible records via type-level sequences of labelled fields. A row `R ::= rho | (l : phi ; R) | Empty`, where `phi` is a field presence flag (`pre(tau)` = present with type `tau`, or `abs` = absent). Record types are `{R}`.

Key rules in Rémy's system:
```
(T-Select)  Gamma |- e : {l : pre(tau) ; rho}  =>  Gamma |- e.l : tau
(T-Extend)  Gamma |- e : {l : abs ; rho},  Gamma |- e' : tau
            =>  Gamma |- {l = e' | e} : {l : pre(tau) ; rho}
(T-Restrict) Gamma |- e : {l : pre(tau) ; rho}  =>  e\l : {l : abs ; rho}
```

Row commutativity (equational axiom): `(l1 : phi1 ; l2 : phi2 ; R) = (l2 : phi2 ; l1 : phi1 ; R)` when `l1 ≠ l2`.

**Row polymorphism** achieves structural subtyping without a subtyping relation. A function `forall rho . {l : pre(tau) ; rho} -> tau` accepts any record with at least field `l` — equivalent to width subtyping but via parametric polymorphism.

**Principal types theorem** (Rémy 1994): every typeable expression has a principal type, unlike Wand's original system (which lacked principal types due to label overwriting).

### 2.2 Core Algorithm

Row unification extends Algorithm W. The key is `extractLabel`:

```typescript
function unifyRows(s: Row, t: Row, subst: Substitution): Substitution {
  // Row variable: bind it
  if (s.tag === 'RowVar') return extendSubst(subst, s.name, t);
  if (t.tag === 'RowVar') return extendSubst(subst, t.name, s);
  if (s.tag === 'RowExtend' && t.tag === 'RowExtend') {
    if (s.label === t.label) {
      const s2 = unifyFields(s.field, t.field, subst);
      return unifyRows(s.rest, t.rest, s2);
    } else {
      // Commutativity: find s.label in t, extract it, unify rests
      const { field: tField, rest: tRest } = extractLabel(s.label, t);
      const s2 = unifyFields(s.field, tField, subst);
      return unifyRows(s.rest, tRest, s2);
    }
  }
  // ... RowEmpty cases
}
```

Complexity: O(n · α(n)) amortized — same as standard first-order unification.

### 2.3 Pragmatic Implementation

TypeScript's utility types are row operations:
- `Pick<R, K>` = row projection (select labels K from R)
- `Omit<R, K>` = row restriction (remove labels K from R)
- `R & Record<K, V>` = row extension (add field K:V to R)
- Generic constraint `<R extends { x: number }>` approximates a row variable

Row polymorphism for middleware composition:
```typescript
type Middleware<R extends object, Added extends object> = (ctx: R) => R & Added;
function pipe<A extends object, B extends object, C extends object>(
  m1: Middleware<A, B>, m2: Middleware<A & B, C>): Middleware<A, B & C>;
```

Full row polymorphism (first-class row variables) requires PureScript or OCaml. Effect rows (Koka, Frank) use row types for polymorphic effect tracking.

### 2.4 Common Pitfalls

1. **Label collision in `&`**: `{a: string} & {a: number}` silently gives `{a: never}` — check disjointness explicitly.
2. **Row variable escape**: A row variable bound in a function type must not escape via the occurs check.
3. **No true absence constraint in TS**: `EnsureAbsent<R, K>` workarounds are brittle; row extension without absence check can shadow fields.
4. **Recursive rows**: Allow only contractive recursive row types to preserve decidability.

### 2.5 Cross-References

Related: Subtyping F<: (alternative for records), Intersection & Union Types (row restriction ≈ intersection with a mask), Higher-Kinded Types (Gaster & Jones kind-indexed rows), Effect Systems (Koka effect rows).

---

## 3. Algebraic Data Types (ADTs)

### 3.1 Formal Foundations

An ADT is a (possibly recursive) sum of products. Formal grammar:
```
T ::= 1 | T1 * T2 | 0 | T1 + T2 | mu X. F(X)
```

A general ADT is `data T = C1(T11 * ... * T1n) | ... | Ck(Tk1 * ... * Tkp)`. The type is "algebraic" because `|A * B| = |A| × |B|`, `|A + B| = |A| + |B|`, with distributive law `A * (B + C) ~ A*B + A*C`.

Typing rules:
```
(T-Con)    Gamma |- e1:T1 ... Gamma |- en:Tn  =>  Gamma |- Ci(e1,...,en) : T
(T-Match)  Gamma |- e:T;  each Gamma, xs:Tis |- ei:S  =>  Gamma |- match e with ...  : S
(T-Fold)   Gamma |- e : F(mu X. F(X))  =>  Gamma |- fold(e) : mu X. F(X)
(T-Unfold) Gamma |- e : mu X. F(X)  =>  Gamma |- unfold(e) : F(mu X. F(X))
```

**Initial algebra theorem**: `(mu F, in : F(mu F) -> mu F)` is the initial F-algebra. **Lambek's lemma**: `in` is an isomorphism. The **catamorphism** (fold) is the unique morphism from the initial algebra to any other F-algebra.

**Church encoding**: `mu X. F(X) ~ forall R. (F(R) -> R) -> R`. **Scott encoding**: `mu X. F(X) ~ forall R. (each constructor field -> R) -> R`.

### 3.2 Core Algorithm

Exhaustiveness checking (Maranget 2008) via decision tree compilation:

```typescript
function compileMatch(scrutinees: AccessPath[], clauses: Clause[]): DecisionTree {
  if (clauses.length === 0) return { tag: 'fail' };
  if (allVariables(clauses[0])) return leafFrom(clauses[0]);
  const col = selectColumn(scrutinees, clauses); // heuristic: most ctors
  // Group clauses by constructor in chosen column
  // Recursively compile each group with specialized scrutinees
  // Build switch tree
}
```

### 3.3 Pragmatic Implementation

TypeScript discriminated unions with `readonly tag` literal:
```typescript
type Shape = { tag: 'Circle'; radius: number } | { tag: 'Rect'; w: number; h: number };
```

**Exhaustiveness pattern** — required to catch new constructors:
```typescript
function assertNever(x: never): never { throw new Error('Unhandled: ' + JSON.stringify(x)); }
```

Use `ts-pattern` library for nested pattern matching. Use `cata` (catamorphism) to separate recursion from logic:
```typescript
type ExprAlgebra<R> = { Lit: (n: number) => R; Add: (l: R, r: R) => R; };
function cata<R>(expr: Expr, alg: ExprAlgebra<R>): R { ... }
```

### 3.4 Common Pitfalls

1. **No exhaustiveness by default**: Without `assertNever` and `strictNullChecks`, adding a constructor breaks nothing at compile time.
2. **Mutation breaks invariants**: Mark all ADT fields `readonly` to prevent tag/payload mismatch.
3. **Structural leakage**: Extra fields are valid in TS structural typing — `{tag:'Circle', radius:1, extra:true}` is a valid `Circle`.
4. **Deep recursion**: Recursive ADT traversals can overflow the stack. Use iterative traversal for large structures.

### 3.5 Cross-References

Related: GADTs (generalize ADTs), Refinement Types (datasort refinements partition constructors), Recursive Types (ADTs are iso-recursive with named constructors), Row Types (closed ADTs vs. row-polymorphic variants).

---

## 4. GADTs — Generalized Algebraic Data Types

### 4.1 Formal Foundations

A GADT allows each constructor to specialize the return type parameter (Xi, Chen, Chen 2003; Cheney, Hinze 2003):
```
data Expr a where
  LitInt  : Int -> Expr Int
  LitBool : Bool -> Expr Bool
  Add     : Expr Int -> Expr Int -> Expr Int
  If      : Expr Bool -> Expr a -> Expr a -> Expr a
```

Constructor introduction:
```
(T-GADT-Con) Gamma |- ei : Ti[theta] where theta unifies fresh vars
             => Gamma |- Ci(e1,...,en) : T(si[theta])
```

Pattern matching (T-Case) requires constraint propagation per branch:
```
(T-GADT-Match) Gamma |- e : T(tau)
  For each Ci : forall bs. ... -> T(si):
    theta = unify(tau, si)  -- introduces type equalities locally
    Gamma, xs:Tis[theta], (tau ~ si[theta]) |- ei : S
  => Gamma |- match e ... : S
```

**OutsideIn principle** (Vytiniotis et al. 2011): type information flows from the scrutinee's known type into branches, never outward. This makes inference syntax-directed and decidable for annotated programs.

**Key results**: (1) Principal types do not exist for GADT match expressions. (2) Type inference without annotations is undecidable. (3) GADTs are not (even lax) functors in general (Johann, Ghiorzi, Jeffries 2021) — `fmap` is not always definable.

### 4.2 Core Algorithm

OutsideIn(X) type inference with implication constraints:

```typescript
case 'GADTMatch': {
  const scrutType = inferExpr(gamma, expr.scrutinee);
  const resultVar = freshTVar();
  for (const branch of expr.branches) {
    const ctorSig = freshen(lookupConstructor(branch.constructor));
    const matchConstraint = CEq(scrutType, ctorSig.resultType);
    const given = CConj([matchConstraint, ...ctorSig.givenConstraints]);
    const { type: bodyType, wanted: wBody } = inferExpr(extendEnv(...), branch.body);
    // Key: CImpl makes given constraints LOCAL to this branch
    branchWanteds.push(CImpl(ctorSig.tvars, given, CConj([...wBody, CEq(bodyType, resultVar)])));
  }
}
```

Constraint solving: flatten → unify simples → solve implications under given assumptions → check no-escape invariant.

### 4.3 Pragmatic Implementation

TypeScript GADT encoding via conditional types and smart constructors:
```typescript
type Expr<A> =
  | { tag: 'LitInt';  value: number; readonly _a?: A }   // A ~ number
  | { tag: 'LitBool'; value: boolean; readonly _a?: A }  // A ~ boolean
  | { tag: 'Add';     left: Expr<number>; right: Expr<number>; _a?: A }
  | { tag: 'If';      cond: Expr<boolean>; then_: Expr<A>; else_: Expr<A> };

function evaluate<A>(expr: Expr<A>): A {
  switch (expr.tag) {
    case 'LitInt':  return expr.value as A;  // sound cast: constructor ensures A~number
    case 'LitBool': return expr.value as A;  // sound cast: constructor ensures A~boolean
    case 'Add':     return (evaluate(expr.left) + evaluate(expr.right)) as A;
    case 'If':      return evaluate(expr.cond) ? evaluate(expr.then_) : evaluate(expr.else_);
  }
}
```

The `as A` casts are sound (GADT structure guarantees them) but not compiler-verified. Prefer **tagless-final** (interpreter pattern) for TS when avoiding casts matters:
```typescript
interface ExprSym<R> { litI(n: number): R; litB(b: boolean): R; add(l:R, r:R): R; }
```

### 4.4 Common Pitfalls

1. **Unsafe casts unavoidable in TS**: Nothing prevents a wrong cast. Bugs in the GADT definition silently break type safety.
2. **Non-exhaustive GADT matching in TS**: TS cannot determine that matching `Expr<number>` need not cover `LitBool`. All branches always required.
3. **Existential variables in constructors**: Encoding `exists a. Show a => a` requires closures or continuation-passing.
4. **Forgetting annotations**: GADT match expressions need a type annotation in Haskell; in TS each level needs its own casts.

### 4.5 Cross-References

Related: ADTs (GADTs generalize), Dependent Types (GADTs ~ inductive families without full dependency), Existential Types (GADT constructors pack existentials), Phantom Types (GADTs make phantom params meaningful).

---

## 5. Recursive Types

### 5.1 Formal Foundations

A recursive type is formed via `mu alpha. tau` with two interpretations:

**Equi-recursive**: `mu alpha. tau === tau{mu alpha. tau / alpha}`. Types are infinite trees; equality is bisimulation on the tree. TypeScript uses this — recursive type aliases and interfaces are transparent.

**Iso-recursive**: `mu alpha. tau` and `tau{mu alpha. tau / alpha}` are distinct but isomorphic, connected by explicit coercions:
```
(Fold)   Gamma |- e : tau{mu a. tau / a}  =>  Gamma |- fold[mu a. tau] e : mu a. tau
(Unfold) Gamma |- e : mu a. tau  =>  Gamma |- unfold e : tau{mu a. tau / a}
```

ML/Haskell `data` declarations are implicitly iso-recursive (fold/unfold are implicit in constructors).

**Contractiveness**: `mu alpha. tau` is well-formed only if `alpha` appears under at least one type constructor (prevents degenerate `mu alpha. alpha`).

**Decidability** (Amadio-Cardone 1991, Brandt-Henglein 1998):
- Equi-recursive type equality: decidable O(n log n) via Hopcroft partition refinement on finite automaton representation.
- Equi-recursive subtyping with function types: decidable O(n²) via coinductive simulation.
- Equi-recursive + bounded quantification: **undecidable** (reduces to full F<:).

### 5.2 Core Algorithm

Coinductive equality/subtyping with assumption set:

```typescript
function typeEqual(s: Type, t: Type, assumptions: Set<string> = new Set()): boolean {
  const key = canonical(s, t);
  if (assumptions.has(key)) return true;  // coinductive hypothesis — cycle means equal
  const s1 = unfold(s), t1 = unfold(t);
  const next = new Set(assumptions);
  next.add(canonical(s1, t1));
  if (s1.tag === 'fun' && t1.tag === 'fun')
    return typeEqual(s1.param, t1.param, next) && typeEqual(s1.ret, t1.ret, next);
  // product, base cases...
}
```

**Invariant**: assumption set grows monotonically; at most O(n²) pairs → algorithm terminates.

### 5.3 Pragmatic Implementation

TypeScript is equi-recursive — use interfaces for recursive types (lazily evaluated, no circular alias errors):
```typescript
type List<A> = null | { head: A; tail: List<A> }  // equi-recursive, transparent
type Json = string | number | boolean | null | Json[] | { [k: string]: Json }
```

For catamorphisms over recursive types, define the base functor separately:
```typescript
type ListF<A, R> = null | { head: A; tail: R };
function cata<A, R>(alg: (layer: ListF<A, R>) => R, list: List<A>): R { ... }
```

Libraries: `io-ts` uses `t.recursion()`, `Zod` uses `z.lazy()`, `Effect` uses `Schema.suspend()`.

### 5.4 Common Pitfalls

1. **Infinite loops without assumption set**: Naive structural comparison of recursive types diverges. Always maintain the coinductive assumption set.
2. **Non-contractive types**: `mu a. a` and `mu a. mu b. a` are degenerate. Enforce contractiveness at definition time.
3. **TS depth limits**: Conditional type recursion has ~50 level limit. Use interface indirection to avoid `Type instantiation is excessively deep`.
4. **Variance in recursive positions**: Contravariance in recursive function types must flip the subtyping direction consistently.

### 5.5 Cross-References

Related: Subtyping F<: (equi-recursive + bounded quantification = undecidable), ADTs (iso-recursive with named constructors), Gradual Typing (recursive types need special handling for gradual guarantee), Coinductive Types (greatest fixed points).

---

## 6. Intersection & Union Types

### 6.1 Formal Foundations

Coppo-Dezani intersection types (1978–1980) and Frisch-Castagna-Benzaken semantic subtyping (2008).

Types: `T ::= B | T->T | T AND T | T OR T | NOT T | Top | Bottom`

**Intersection typing rules**:
```
(AND-Intro)  Gamma |- e:S,  Gamma |- e:T  =>  Gamma |- e : S AND T
(AND-Elim-L) Gamma |- e : S AND T  =>  Gamma |- e : S
(AND-Elim-R) Gamma |- e : S AND T  =>  Gamma |- e : T
(OR-Intro-L) Gamma |- e:S  =>  Gamma |- e : S OR T
(OR-Intro-R) Gamma |- e:T  =>  Gamma |- e : S OR T
(OR-Elim)    Gamma |- e : S OR T;  Gamma,x:S |- e':U;  Gamma,x:T |- e':U  =>  Gamma |- U
```

Subtyping forms a distributive lattice:
- `S AND T <: S`, `S AND T <: T` (meet)
- `S <: S OR T`, `T <: S OR T` (join)
- Distributive law: `S AND (T OR U) = (S AND T) OR (S AND U)`

**Semantic subtyping** (Frisch-Castagna 2008): `S <: T` iff `S AND NOT T` is empty. Decidability reduces to checking emptiness of a type expression (intersection of atoms and negations).

Key algorithm: convert to **Disjunctive Normal Form** of atoms and negations, then check inhabitability per clause. For function types: `(A1->B1) AND NOT(A2->B2)` is empty iff for all types `C <: A1 AND A2`, either `C` is empty or `B1 AND NOT B2` with domain restricted to `C` is empty.

### 6.2 Core Algorithm

Semantic subtyping checks `S <: T` as emptiness of `S AND NOT T`:

```typescript
function isSubtype(s: Type, t: Type): boolean {
  return isEmpty(intersect(s, negate(t)));
}

function isEmpty(t: Type): boolean {
  const dnf = toDNF(t);  // union of clauses, each clause = intersection of atoms+negations
  return dnf.clauses.every(clause => isClauseEmpty(clause));
}

function isClauseEmpty(clause: DNFClause): boolean {
  // Contradiction in base types
  if (clause.posBase.size > 0 && [...clause.posBase].some(b => clause.negBase.has(b))) return true;
  // Check arrow clause emptiness (the complex case)
  return checkArrowEmptiness(clause.posArrow, clause.negArrow);
}
```

### 6.3 Pragmatic Implementation

TypeScript has **first-class** union (`|`) and intersection (`&`) types:

```typescript
// Intersection = all properties of both
type AB = { a: number } & { b: string };  // { a: number; b: string }

// Union = one of the alternatives; narrowing needed before use
type Str = string | number;

// Discriminated union (ADT pattern)
type Shape = { kind: 'circle'; r: number } | { kind: 'rect'; w: number; h: number };

// Type narrowing works with intersection (& narrows inward)
function process(x: (string | number) & { label: string }): void {
  if (typeof x === 'string') x.toUpperCase();  // narrowed to string & {label}
}
```

**Distributive conditional types**: `T extends U ? A : B` distributes over unions when `T` is a naked type parameter — this is semantic union elimination.

### 6.4 Common Pitfalls

1. **Intersection collapse**: `string & number = never`. Check compatibility before intersecting.
2. **Union access without narrowing**: Can only access properties common to all union members.
3. **Distributive conditional types surprise**: `type F<T> = T extends string ? 'yes' : 'no'` with `T = string | number` gives `'yes' | 'no'`, not just `'no'`.
4. **Function intersection vs overloading**: `(A -> B) & (C -> D)` uses first-match overload resolution, not best-match.

### 6.5 Cross-References

Related: Subtyping F<: (intersection types interact with bounded quantification), Row Types (row restriction ≈ intersection with a mask), Refinement Types (intersection of refinements), Gradual Typing (union types with dynamic type).

---

## 7. Refinement Types & Liquid Types

### 7.1 Formal Foundations

A refinement type `{x : B | phi(x)}` restricts base type `B` with predicate `phi`. Freeman-Pfenning (1991) introduced datasort refinements for ML; Rondon-Kawaguchi-Jhala (2008) introduced **Liquid Types**.

Liquid types restrict refinements to **conjunctions of qualifiers** from a finite set `Q = {q1, ..., qn}`:
```
{v : B | q_i1 /\ q_i2 /\ ... /\ q_ik}   where each q_ij in Q
```

Typing rules:
```
(T-Refine-Intro)  Gamma |- e:B,  Gamma |- phi[e/v]  =>  Gamma |- e : {v:B|phi}
(Sub-Refine)      Gamma, v:B |- phi => psi  =>  Gamma |- {v:B|phi} <: {v:B|psi}
(T-Fun-Refine)    Gamma, x:{v:Tx|phi_x} |- e:{v:Tr|phi_r}
                  =>  Gamma |- (lam x.e) : (x:{v:Tx|phi_x}) -> {v:Tr|phi_r}
(T-App-Refine)    Gamma |- f:(x:{v:S|p})->{v:T|q},  Gamma |- e:{v:S|p}
                  =>  Gamma |- f e : {v:T|q[e/x]}
```

Subtype checking reduces to SMT validity: `Gamma |- {v:B|phi} <: {v:B|psi}` iff `(phi => psi)` is valid in the refinement logic (QF-LIA for linear arithmetic).

**Liquid type inference** (Algorithm):
1. HM inference → generate templates with fresh qualifier variables
2. Each qualifier variable starts as the full set Q
3. Iterative weakening: remove qualifiers not implied by constraints (via SMT)
4. Termination: qualifier sets only shrink (monotonic) → finite lattice → converges

### 7.2 Core Algorithm

Liquid type inference via iterative qualifier weakening:

```typescript
function inferLiquidTypes(program: Program, qualifiers: Qualifier[]): Map<Expr, RefinedType> {
  const hmTypes = hindleyMilnerInfer(program);
  // Assign fresh qualifier variables, initialized to full Q
  const liquidVars = new Map(hmTypes, () => new Set(qualifiers));
  const constraints = generateConstraints(program, liquidVars);
  // Iterative weakening
  let changed = true;
  while (changed) {
    changed = false;
    for (const { env, lhs, rhs } of constraints) {
      for (const q of rhs.qualifiers) {
        if (!smtIsValid(`${encodeEnv(env)} /\ ${conjoin(lhs)} => ${q.formula}`)) {
          rhs.qualifiers.delete(q);
          changed = true;
        }
      }
    }
  }
  return liquidVars;
}
```

Predicate language: **QF-LIA** (quantifier-free linear integer arithmetic) — supports `v >= 0`, `v < len`, `v = x + 1`, etc. Checking one SMT query uses Z3 or CVC5.

### 7.3 Pragmatic Implementation

TypeScript approximation via **branded types**:
```typescript
declare const __brand: unique symbol;
type Brand<B, T> = T & { readonly [__brand]: B };

type PositiveInt = Brand<'PositiveInt', number>;
type EmailAddress = Brand<'EmailAddress', string>;

// Smart constructor = refinement introduction (checks predicate at runtime)
function mkPositiveInt(n: number): PositiveInt {
  if (!Number.isInteger(n) || n <= 0) throw new RangeError(`Expected positive int, got ${n}`);
  return n as PositiveInt;
}

// Usage: precondition statically enforced
function divide(a: number, b: PositiveInt): number { return a / b; }
```

Production tools: `Effect-TS Brand.refined`, `Zod .brand<T>()`, `io-ts t.brand`. True liquid type checking for Haskell: **LiquidHaskell** (mature, production-ready). For Rust: **Flux** (research prototype).

### 7.4 Common Pitfalls

1. **Brand forgery**: `n as PositiveInt` bypasses the predicate. Keep brand symbol private to module.
2. **Serialization boundary**: `JSON.parse` returns `any`, silently stripping brands. Re-validate after deserialization.
3. **No predicate propagation**: `positiveInt + 1` returns `number`, not `PositiveInt`. Provide branded arithmetic helpers.
4. **TS is not LiquidHaskell**: Brands are a convention, not a proof. The compiler does not verify predicates statically.
5. **Refinement + general recursion**: Without termination checking, a non-terminating expression vacuously satisfies any refinement. LiquidHaskell requires termination proofs.

### 7.5 Cross-References

Related: Dependent Types (refinements are predicates, not arbitrary terms), Intersection Types (refinements can be seen as intersection with predicate witnesses), ADTs (datasort refinements partition constructors), Subtyping (refinements induce a subtyping lattice).

---

## 8. Substructural Types (Linear, Affine, Ordered)

### 8.1 Formal Foundations

Substructural type systems restrict the structural rules of the sequent calculus (Girard 1987; Wadler 1990):

| System | Weakening | Contraction | Exchange | Usage |
|---|---|---|---|---|
| Unrestricted | yes | yes | yes | any number of times |
| Relevant | no | yes | yes | at least once |
| Affine | yes | no | yes | at most once |
| Linear | no | no | yes | exactly once |
| Ordered | no | no | no | exactly once, in order |

Girard's **linear logic** (1987): the exponential modality `!A` ("of course A") recovers unrestricted behavior — only `!A`-typed values can be weakened or contracted. Context splitting for multiplicatives:

```
[Lam]   Gamma, x:A |- e : B  =>  Gamma |- lam x.e : A -o B
[App]   Gamma1 |- e1 : A -o B,  Gamma2 |- e2 : A  =>  Gamma1,Gamma2 |- e1 e2 : B
        (context SPLIT: each variable in exactly one subcontext)
[Pair]  Gamma1 |- e1:A,  Gamma2 |- e2:B  =>  Gamma1,Gamma2 |- (e1,e2) : A (x) B
[!]     !Gamma |- e:A  =>  !Gamma |- !e : !A   (all assumptions must be !)
```

**Affine** adds `[Affine-Weaken]`: any variable can be discarded but not duplicated. This is Rust's ownership model.

**Key theorem**: Deadlock freedom (Wadler 2012 "propositions as sessions") — classical linear logic proofs correspond to deadlock-free concurrent processes (session types ↔ linear logic).

**RustBelt** (Jung et al. 2017): Rust's borrow checker is sound with respect to an affine type discipline, formally proven in Iris/Coq.

### 8.2 Core Algorithm

Linear type checker with context tracking:

```typescript
class LinearTypeChecker {
  check(ctx: Context, expr: Expr, expected: LinearType): Context {
    switch (expr.tag) {
      case 'Var': {
        const idx = ctx.findIndex(e => e.name === expr.name && !e.used);
        if (idx === -1) throw new Error(`${expr.name} not available (already consumed)`);
        return ctx.map((e, i) => i === idx ? { ...e, used: true } : e);
      }
      case 'Lam': {  // context is extended; param must be consumed in body
        const extended = [...ctx, { name: expr.param, type: expected.from, used: false }];
        const afterBody = this.check(extended, expr.body, expected.to);
        const paramEntry = afterBody.find(e => e.name === expr.param);
        if (!paramEntry?.used) throw new Error(`Linear var ${expr.param} not consumed`);
        return afterBody.filter(e => e.name !== expr.param);
      }
      case 'App': {  // context flows through fn, then arg (sequential split)
        const [fnType, afterFn] = this.infer(ctx, expr.fn);
        return this.check(afterFn, expr.arg, fnType.from);
      }
    }
  }
  typecheck(ctx: Context, expr: Expr, ty: LinearType): void {
    const remaining = this.check(ctx, expr, ty);
    const unconsumed = remaining.filter(e => !e.used && e.type.tag !== 'Bang');
    if (unconsumed.length > 0) throw new Error('Unconsumed linear vars: ' + ...);
  }
}
```

### 8.3 Pragmatic Implementation

TypeScript cannot enforce linearity at the type level — phantom state types simulate the discipline:

```typescript
class FileHandle<S extends 'open' | 'closed'> {
  private consumed = false;
  _consume() { if (this.consumed) throw new Error('Use-after-move'); this.consumed = true; }
}
function writeFile(h: FileHandle<'open'>, data: string): FileHandle<'open'> {
  h._consume(); return new FileHandle('open'); // state preserved
}
function closeFile(h: FileHandle<'open'>): FileHandle<'closed'> {
  h._consume(); return new FileHandle('closed');
}
// closeFile(closedHandle) → TYPE ERROR: 'closed' not assignable to 'open'
```

For true linearity: **Linear Haskell** (GHC 9.0+, `a %1 -> b`), **Idris 2** (QTT with multiplicities 0, 1, ω), **Rust** (affine ownership + lifetimes), **Granule** (full graded linearity).

TS 5.2+ `using` declarations with `Symbol.dispose` provide RAII-like resource cleanup (weak approximation).

### 8.4 Common Pitfalls

1. **Incorrect context splitting**: If both subexpressions of `App` share a linear variable, it is used twice. Context splitting must be a strict partition.
2. **Multiplicative vs. additive confusion**: Tensor `A ⊗ B` splits context; With `A & B` shares it. Getting this wrong silently breaks linearity.
3. **Closures capture linear variables**: A closure capturing a linear variable consumes it at closure creation, not at call site.
4. **Exceptions bypass linearity**: An exception thrown before consuming a linear resource leaves it unconsumed. Use bracket/mask patterns or structured concurrency.

### 8.5 Cross-References

Related: Session Types (session types ARE linear types for channels), Graded Types (linear + usage annotation semiring), Separation Logic (shared resource-aware reasoning), Rust Ownership (affine types + lifetimes), Effect Systems (linear effect handlers).

---

## 9. Gradual Typing

### 9.1 Formal Foundations

Gradual typing (Siek & Taha 2006) extends a static type system with **dynamic type `?`** (or `*`/`any`). The key innovation: replace type equality with a **consistency relation `~`**:

```
tau ~ tau           (reflexivity)
? ~ tau             (? is consistent with any type)
tau ~ ?             (any type is consistent with ?)
S1 ~ T1,  S2 ~ T2  =>  (S1 -> S2) ~ (T1 -> T2)
```

**Critical**: consistency is reflexive and symmetric but **NOT transitive**. If transitive, `Int ~ ? ~ Bool` would imply `Int ~ Bool`, destroying static safety.

Typing rules for `lambda_?->`:
```
(App)  Gamma |- e1 : tau1,  tau1 ~> (tau11 -> tau12),  Gamma |- e2 : tau2,  tau2 ~ tau11
       =>  Gamma |- e1 e2 : tau12
```
where `~>` is the **matching function relation**: `(tau1 -> tau2) ~> (tau1 -> tau2)` and `? ~> (? -> ?)`.

**Gradual guarantee** (Siek et al. 2015): adding/removing type annotations does not change program behavior on well-typed inputs. More static types = more static errors caught (precision monotonicity).

**Blame calculus** (Wadler-Findler 2009): runtime casts are annotated with blame labels. When a cast fails, the blame label identifies which party (typed or untyped) violated the contract.

**Cast normalization (threesome calculus)**: chaining casts `(? -> Int) -> (String -> ?)` creates O(n) wrapper chains. Coerce via intermediate type to normalize to a single wrapper.

### 9.2 Core Algorithm

Gradual type checker with cast insertion:

```typescript
function check(ctx: Context, expr: Expr, expected: Type): CastExpr {
  const { type: inferred, cast: e2 } = infer(ctx, expr);
  if (!consistent(inferred, expected))
    throw new TypeError(`Cannot cast ${print(inferred)} to ${print(expected)}`);
  if (typeEqual(inferred, expected)) return e2;
  return { tag: 'cast', source: inferred, target: expected, blame: freshLabel(), inner: e2 };
}

function consistent(s: Type, t: Type): boolean {
  if (s.tag === 'dyn' || t.tag === 'dyn') return true;
  if (s.tag === 'fun' && t.tag === 'fun')
    return consistent(s.param, t.param) && consistent(s.ret, t.ret);
  return typeEqual(s, t);
}
```

### 9.3 Pragmatic Implementation

TypeScript's `any` is the gradual type `?`. TypeScript's `unknown` is the safe **top type** (requires explicit narrowing before use).

```typescript
let x: any = 42;
let y: string = x;  // Implicit cast ? -> string (unsound but allowed)

// 'unknown' is safer: requires narrowing
let u: unknown = 42;
if (typeof u === 'string') { let v: string = u; }  // OK after narrowing

// Migration path: gradually annotate legacy code
declare function legacyApi(): any;  // start with 'any', gradually refine
```

Practical gradual typing strategies:
- Enable `strict` mode incrementally per file
- Use `// @ts-check` in JS files for opt-in checking
- Use `unknown` instead of `any` for safe boundaries
- Use `noImplicitAny` to force annotation of implicit `any`

### 9.4 Common Pitfalls

1. **Transitivity trap**: Never treat consistency as transitive. `Int ~ ?` and `? ~ Bool` do NOT give `Int ~ Bool`.
2. **`any` infection**: `any` propagates through type inference, silently disabling checks in distant code. Contain with `unknown` or explicit annotations.
3. **Cast accumulation**: Chaining higher-order casts creates unbounded wrapper chains (O(n) overhead per call). Use coercion normalization.
4. **Missing blame labels**: Without blame tracking, runtime cast errors give no indication of where untyped data entered. Always annotate gradual boundaries.
5. **Gradual guarantee violations**: `any`/`?` can change program behavior when added (TypeScript intentionally violates the full gradual guarantee for performance).

### 9.5 Cross-References

Related: Subtyping (consistency relation ≈ relaxed subtyping), Recursive Types (gradual recursive types need careful consistency definition), Flow-Sensitive Typing (narrowing eliminates `any` / `?` checks), Refinement Types (gradual refinement types).

---

## 10. Flow-Sensitive Typing / Type Narrowing

### 10.1 Formal Foundations

**Occurrence typing** (Tobin-Hochstadt & Felleisen 2008/2010) assigns types to each *occurrence* of a variable based on the control flow path reaching that use. Each expression is typed with two **propositions**:

```
e : tau ;  psi_+  |  psi_-
```

where `psi_+` holds when `e` is truthy and `psi_-` holds when `e` is falsy. Propositions:
```
psi ::= (x : tau)    -- x has type tau
      | (x : ~tau)   -- x does NOT have type tau (negative type)
      | psi1 AND psi2
      | psi1 OR psi2
      | TRUE | FALSE
```

Key rule for `if`:
```
(If)  Gamma |- e : tau ; psi_+ | psi_-
      Gamma + psi_+  |- e1 : tau1      (then-branch uses positive proposition)
      Gamma + psi_-  |- e2 : tau2      (else-branch uses negative proposition)
      =>  Gamma |- if e then e1 else e2 : tau1 | tau2
```

Type guard rule:
```
(TypePredicate)  typeof x === 'string'  :  bool ; (x : string) | (x : ~string)
```

The narrowing operation `Gamma + psi` restricts variable types according to `psi` using **type subtraction**: `tau AND ~sigma` = `tau` minus the overlapping part of `sigma`.

### 10.2 Core Algorithm

Control-flow graph based narrowing:

```typescript
type FlowNode =
  | { kind: 'start'; type: Type }
  | { kind: 'assignment'; variable: string; assignedType: Type; prev: FlowNode }
  | { kind: 'narrowing'; guard: NarrowingGuard; trueBranch: FlowNode; falseBranch: FlowNode }
  | { kind: 'join'; sources: FlowNode[] };  // union of incoming types

function getTypeAtNode(variable: string, node: FlowNode): Type {
  switch (node.kind) {
    case 'start': return node.type;
    case 'assignment':
      if (node.variable === variable) return node.assignedType;
      return getTypeAtNode(variable, node.prev);
    case 'narrowing':
      const baseType = getTypeAtNode(variable, node.prev);
      return applyNarrowing(variable, node.guard, baseType); // narrow in true branch
    case 'join':
      return unionTypes(node.sources.map(s => getTypeAtNode(variable, s)));
  }
}
```

Narrowing operations: `typeof` → base type narrowing; `instanceof` → class type narrowing; discriminant field check → union narrowing; user-defined type guard → custom narrowing.

### 10.3 Pragmatic Implementation

TypeScript implements occurrence typing natively. All narrowing constructs:

```typescript
// typeof narrowing
if (typeof x === 'string') { x.toUpperCase(); }  // x: string

// Discriminated union narrowing
if (shape.kind === 'circle') { shape.radius; }  // shape: { kind:'circle'; radius:number }

// instanceof narrowing
if (e instanceof Error) { e.message; }  // e: Error

// Truthiness narrowing
if (x) { /* x: NonNullable<typeof x> */ }

// User-defined type guard
function isString(x: unknown): x is string { return typeof x === 'string'; }

// Assertion function
function assertDefined<T>(v: T | undefined): asserts v is T { if (!v) throw new Error(); }

// satisfies operator (TS 4.9): narrowing without widening
const config = { port: 8080 } satisfies Partial<ServerConfig>;
```

**TypeGuard** (TS 3.7+) and **assertion functions** (TS 3.7+) allow user-defined narrowing that persists across function calls.

### 10.4 Common Pitfalls

1. **Mutation invalidates narrowing**: Narrowing a variable, then calling a function that may mutate the object invalidates the narrow. TypeScript conservatively invalidates narrowing after function calls on let-bound variables.
2. **Closure capture resets narrowing**: Narrowing does not persist into closures for `let`-bound variables. Use `const` or extract to a local `const`.
3. **`typeof null === 'object'`**: Narrowing `typeof x === 'object'` does NOT exclude `null`. Always check `x !== null` separately.
4. **Discriminant must be a literal type**: Discriminated union narrowing requires the discriminant field to have literal types, not general `string`.
5. **Control flow annotation loss**: Reassigning a variable between narrowing and use resets the type. Avoid reassignment in narrowed blocks.

### 10.5 Cross-References

Related: Intersection & Union Types (narrowing decomposes union types), Gradual Typing (narrowing eliminates `any`), Refinement Types (flow-sensitive narrowing ≈ path-sensitive refinement), ADTs (discriminated union narrowing).

---

## 11. Existential Types

### 11.1 Formal Foundations

An existential type `∃X. T` (written `exists X. T`) is the **dual** of the universal `∀X. T`. The witness type is chosen by the **producer**, hidden from the consumer. Mitchell & Plotkin (1985/1988): "Abstract Types Have Existential Type."

Introduction (pack):
```
(T-Pack)  Gamma |- e : T[X := U]  =>  Gamma |- pack[U, e] as exists X. T : exists X. T
```

Elimination (unpack):
```
(T-Unpack)  Gamma |- e1 : exists X. T1
            Gamma, X type, x : T1 |- e2 : T2
            X not free in T2              -- scope restriction: hidden type cannot escape
            =>  Gamma |- unpack[X, x] = e1 in e2 : T2
```

Computation rule: `unpack[X, x] = (pack[U, v]) in e` → `e[X := U][x := v]`

**Church encoding** in System F: `∃X. T = ∀R. (∀X. T → R) → R`

**Representation Independence** (Mitchell 1986): parametricity applied to the hidden type variable ensures no client can distinguish two implementations of an abstract type. This is the formal basis for information hiding.

**Bounded existentials** in System F-sub: `∃X <: B. T` — the hidden type must satisfy bound `B`. Subtyping: `Gamma, X <: B |- T1 <: T2  =>  Gamma |- (∃X <: B. T1) <: (∃X <: B. T2)`.

### 11.2 Core Algorithm

Type checking with scope-escape prevention:

```typescript
case 'Unpack': {
  const pkgType = typeCheck(ctx, kinds, expr.package);
  if (pkgType.tag !== 'Exists') throw new Error('Expected existential');
  const { tvar: origX, body: T } = pkgType;
  const newKinds = new Set(kinds); newKinds.add(expr.tvar);
  const newCtx = new Map(ctx);
  newCtx.set(expr.xvar, substType(T, origX, { tag: 'TVar', name: expr.tvar }));
  const resultType = typeCheck(newCtx, newKinds, expr.body);
  // CRITICAL: scope check
  if (freeIn(expr.tvar, resultType))
    throw new Error(`Type variable ${expr.tvar} escapes its scope`);
  return resultType;
}
```

### 11.3 Pragmatic Implementation

TypeScript has no native existential syntax. Use the **CPS encoding** (Church encoding):

```typescript
// exists T. { value: T; show: (t: T) => string }
// = forall R. (forall T. (value: T, show: (t: T) => string) => R) => R
type Showable = <R>(cont: <T>(value: T, show: (t: T) => string) => R) => R;

function packShowable<T>(value: T, show: (t: T) => string): Showable {
  return cont => cont(value, show);
}

// Heterogeneous collection: each element hides its type T
const items: Showable[] = [
  packShowable(42, n => `Number: ${n}`),
  packShowable('hello', s => `String: ${s}`),
];
const strings = items.map(item => item((v, show) => show(v)));
```

**Abstract data type** via existential module:
```typescript
type CounterModule = <R>(use: <Rep>(ops: { zero: Rep; inc: (r: Rep) => Rep; get: (r: Rep) => number }) => R) => R;
```

Alternative: use abstract classes (OOP existentials), ML/OCaml first-class modules, Haskell `ExistentialQuantification`, Rust `dyn Trait`.

### 11.4 Common Pitfalls

1. **Scope extrusion**: Storing the existentially-bound value in an outer closure without going through the continuation violates the scope restriction. The hidden type escapes.
2. **Lost type connections**: Using `unknown` as stand-in for the existential type loses the connection between the value and its operations.
3. **Confusing existentials with union types**: `∃T. F<T>` means "some *specific* unknown T", not "any T from a union". `Array<∃T. T>` is heterogeneous; `Array<string | number>` is a typed union.
4. **Inference failures**: TypeScript struggles with higher-rank types in CPS encoding — manual annotations often required.

### 11.5 Cross-References

Related: System F (existentials = Church encoding via universals), GADTs (constructors pack existentials), Bounded Quantification (bounded existentials in F-sub), Module Systems (ML functors use existential types for abstract signatures), Dependent Types (∃ as non-dependent Σ types).

---

## 12. Variance (Covariance, Contravariance, Invariance)

### 12.1 Formal Foundations

Variance (Cardelli 1988) describes how subtyping between type arguments transfers to parameterized types. For type constructor `F` and `A <: B`:

- **Covariant** (`out T`, `+T`): `A <: B => F<A> <: F<B>` (same direction)
- **Contravariant** (`in T`, `-T`): `A <: B => F<B> <: F<A>` (reversed)
- **Invariant**: no subtyping relationship unless `A = B`
- **Bivariant**: both `F<A> <: F<B>` and `F<B> <: F<A>` (unsound unless F ignores T)

Fundamental variance rule for function types:
```
S-Arrow:  Gamma |- A2 <: A1,  Gamma |- B1 <: B2
          =>  Gamma |- (A1 -> B1) <: (A2 -> B2)
          (contravariant in domain, covariant in codomain)
```

**Variance composition** (like sign multiplication):
- covariant ∘ covariant = covariant
- contravariant ∘ contravariant = covariant (double negation!)
- covariant ∘ contravariant = contravariant
- invariant absorbs everything

Variance checking: walk the type expression, flip variance at each domain position, check type parameter occurrences.

**Java's covariant arrays** (`Dog[] <: Animal[]`) is a famous unsoundness — allows storing a `Cat` in a `Dog[]`.

### 12.2 Core Algorithm

Variance inference by type expression traversal:

```typescript
type Variance = 'covariant' | 'contravariant' | 'invariant' | 'bivariant';

function composeVariance(outer: Variance, inner: Variance): Variance {
  if (outer === 'invariant' || inner === 'invariant') return 'invariant';
  if (outer === 'bivariant' || inner === 'bivariant') return 'bivariant';
  if (outer === inner) return 'covariant';  // same direction = positive
  return 'contravariant';                    // opposite = negative
}

function inferVariance(T: Type, param: string, currentVariance: Variance): Variance {
  if (T.tag === 'TVar') return T.name === param ? currentVariance : 'bivariant';
  if (T.tag === 'Arrow')
    return joinVariances(
      inferVariance(T.domain, param, flip(currentVariance)),  // flip in domain
      inferVariance(T.codomain, param, currentVariance)
    );
  if (T.tag === 'Ref') return inferVariance(T.inner, param, 'invariant');  // mutable → invariant
  // ...
}
```

### 12.3 Pragmatic Implementation

TypeScript 4.7+ explicit variance annotations:
```typescript
interface Producer<out T> { produce(): T; }    // covariant: T only in output
interface Consumer<in T>  { consume(t: T): void; }  // contravariant: T only in input

// Cat <: Animal => Producer<Cat> <: Producer<Animal>  (covariant)
const catProducer: Producer<Cat> = new CatProducer();
const animalProducer: Producer<Animal> = catProducer;  // OK

// Cat <: Animal => Consumer<Animal> <: Consumer<Cat>  (contravariant)
const animalConsumer: Consumer<Animal> = { consume: (a) => { a.name; } };
const catConsumer: Consumer<Cat> = animalConsumer;  // OK

// Mutable container: invariant (ReadonlyArray is covariant, Array is invariant)
const cats: Cat[] = [new Cat()];
const animals: Animal[] = cats;  // TS allows this (unsound!) — Java array problem
animals.push(new Dog());  // runtime error!
// Use ReadonlyArray<Cat> for safe covariance
```

Variance checking rule: `in` position (parameter) = contravariant; `out` position (return) = covariant; read+write (mutable field) = invariant.

### 12.4 Common Pitfalls

1. **Mutable container covariance**: Treating `Array<Dog>` as `Array<Animal>` is unsound. Use `ReadonlyArray<T>` for covariant containers.
2. **Method bivariance trap**: Method declarations `m(x: T): void` are bivariant in TS (even with `strictFunctionTypes`). Use property function syntax `m: (x: T) => void` for strict contravariance.
3. **Double negation**: `Consumer<Consumer<T>>` is COVARIANT in T (contravariant ∘ contravariant). Counterintuitive.
4. **Variance annotation inconsistency**: If `in T` is used but T appears in a covariant position, TS emits a variance error. Fix by removing the annotation and letting TS infer, or restructure the type.

### 12.5 Cross-References

Related: Subtyping F<: (variance is the mechanism for parameterized type subtyping), Recursive Types (variance in recursive positions must be consistent), Nominal vs. Structural Typing (structural subtyping relies on covariance of fields).

---

## 13. Nominal vs. Structural Typing

### 13.1 Formal Foundations

**Structural typing**: `T1 <: T2` iff `T1` structurally contains all members of `T2` with compatible types. Identity determined by shape.

Width + depth subtyping for records:
```
S-RcdWidth:  {l1:T1,...,ln:Tn, extra...} <: {l1:T1,...,ln:Tn}
S-RcdDepth:  all Ti <: Ui  =>  {l1:T1,...,ln:Tn} <: {l1:U1,...,ln:Un}
S-RcdPerm:   field reordering is subtyping
```

**Nominal typing**: `T1 <: T2` iff `T1` is explicitly declared to extend/implement `T2`. Identity determined by declaration site and name.
```
S-Nom:      class C extends D (declared)  =>  C <: D
S-NomTrans: C <: D,  D <: E  =>  C <: E  (transitive closure)
```

TypeScript is primarily structural; Java/C# are nominal; Haskell/Rust are structural for data but nominal for traits/typeclasses.

**Hybrid approaches**: Scala has both structural (anonymous structural types) and nominal (class hierarchy). OCaml uses structural for records/polymorphic variants, nominal for regular variants.

**Branded types** simulate nominal typing in structural systems:
```typescript
type USD = number & { readonly __brand: 'USD' };
type EUR = number & { readonly __brand: 'EUR' };
// USD ≠ EUR even though both are number-compatible
```

### 13.2 Core Algorithm

Structural subtype check (coinductive for recursive types):
```typescript
function structuralSubtype(a: Type, b: Type, assumed: Set<string> = new Set()): boolean {
  const key = `${typeId(a)}<:${typeId(b)}`;
  if (assumed.has(key)) return true;
  assumed.add(key);
  if (a.tag === 'Record' && b.tag === 'Record')
    // width subtyping: b must be a subset of a's fields
    return [...b.fields].every(([k, bType]) => {
      const aType = a.fields.get(k);
      return aType !== undefined && structuralSubtype(aType, bType, assumed);
    });
  if (a.tag === 'Arrow' && b.tag === 'Arrow')
    return structuralSubtype(b.param, a.param, assumed)  // contravariant
        && structuralSubtype(a.ret, b.ret, assumed);
  if (a.tag === 'Branded' && b.tag === 'Branded')
    return a.brand === b.brand && structuralSubtype(a.base, b.base, assumed);
  if (a.tag === 'Nominal' && b.tag === 'Nominal')
    return nominalSubtype(a.name, b.name, hierarchy);
  // ...
}
```

### 13.3 Pragmatic Implementation

TypeScript default: structural. Branded types for nominal discipline:

```typescript
// Problem: structural typing allows accidental compatibility
type UserId = string;
type PostId = string;
getUser('post-123' as UserId);  // compiles fine, probably wrong

// Solution: branded types
declare const __brand: unique symbol;
type UserId = string & { readonly [__brand]: 'UserId' };
type PostId = string & { readonly [__brand]: 'PostId' };

const mkUserId = (s: string): UserId => s as UserId;  // boundary check here
function getUser(id: UserId): void { /* ... */ }
getUser('post-123');  // TYPE ERROR: string is not UserId
```

`unique symbol` ensures brand uniqueness across modules. Alternative: class-based nominal types with private constructor:
```typescript
class UserId { private constructor(readonly value: string) {} static of(s: string) { return new UserId(s); } }
```

### 13.4 Common Pitfalls

1. **Structural compatibility surprises**: Two interfaces with the same shape ARE the same type in TS, regardless of name.
2. **Brand collision**: Two types with the same brand string but different base types share the brand — use `unique symbol` for module-scoped uniqueness.
3. **Branded values across JSON**: `JSON.parse` strips brands (they are compile-time fiction). Re-validate after deserialization.
4. **Excess property checking inconsistency**: `const x: {a: number} = {a: 1, b: 2}` is an error for fresh literals but not for variables — structural typing only checks required fields for variables.
5. **Interface merging**: Declaration merging silently adds fields across files, changing structural compatibility.

### 13.5 Cross-References

Related: Existential Types (encapsulation ≈ existential hiding), Variance (structural subtyping relies on field variance), Row Types (structural subtyping via width subtyping), Refinement Types (brands approximate refinements).

---

## 14. Graded Types & Coeffects

### 14.1 Formal Foundations

Graded modal types (Petricek, Orchard, Mycroft 2013; Atkey 2018 QTT) extend linear types with **modalities indexed by a semiring** `(R, +, 0, *, 1, ≤)`. The graded necessity modality `Box_r A` tracks that `r` copies of `A` are available:

- `r = 0`: unused (can be discarded)
- `r = 1`: exactly once (linear)
- `r = ω`: unrestricted
- `r = [lo, hi]`: interval usage
- `r = security level`: information-flow security

Typing rules for graded lambda calculus (Granule-style):
```
Contexts: Gamma = x1 :_r1 A1, ..., xn :_rn An

T-Var:   ---------------------------
         0*Gamma, x :_1 A |- x : A

T-Abs:   Gamma, x :_r A |- e : B
         ---------------------------
         Gamma |- lam x. e : A ->{r} B

T-App:   Gamma1 |- e1 : A ->{r} B,    Gamma2 |- e2 : A
         -----------------------------------------------
         Gamma1 + r * Gamma2 |- e1 e2 : B

T-Box:   r * Gamma |- e : A
         ----------------------
         Gamma |- [e] : Box_r A

T-Unbox: Gamma1 |- e1 : Box_r A,    Gamma2, x :_r A |- e2 : B
         -------------------------------------------------------
         Gamma1 + Gamma2 |- let [x] = e1 in e2 : B
```

Context operations: `(Gamma1 + Gamma2)_i = r1_i + r2_i` and `(r * Gamma)_i = r * ri`.

**Graded monad `M_r(A)`** for effects: combines coeffects (how context is used) with effects (what is produced). `QTT` (Atkey 2018, implemented in Idris 2) uses multiplicities `{0, 1, ω}` in dependent types.

### 14.2 Core Algorithm

Graded type checker with semiring context arithmetic:

```typescript
interface Semiring<R> { zero: R; one: R; add(a: R, b: R): R; mul(a: R, b: R): R; leq(a:R, b:R): boolean; }

function checkGraded<R>(ctx: GradedCtx<R>, expr: Expr, expected: Type, SR: Semiring<R>): GradedCtx<R> {
  switch (expr.tag) {
    case 'Var': {
      const [grade, ty] = ctx.lookup(expr.name);
      assertSubtype(ty, expected);
      // consume variable: return context with grade 1 at that variable, 0 elsewhere
      return ctx.withGrade(expr.name, SR.one).withAllOtherZero();
    }
    case 'App': {
      // e1 e2 where e1 : A ->{r} B
      const [funGrade, afterFn] = inferGraded(ctx, expr.fn, SR);
      const argCtxUsage = checkGraded(ctx, expr.arg, funType.domain, SR);
      // combine: Gamma_fn + r * Gamma_arg
      return addCtx(afterFn, scaleCtx(funType.grade, argCtxUsage, SR), SR);
    }
  }
}
```

Semiring examples: `(Nat, +, 0, *, 1, ≤)` for exact counting; `({0,1,ω}, +, 0, *, 1, ≤)` for linearity; `(Security levels, join, ⊥, meet, T, ≤)` for information flow.

### 14.3 Pragmatic Implementation

TypeScript has no native graded types. Approximate with phantom semiring parameters:

```typescript
type Linearity = 'zero' | 'one' | 'many';
interface Graded<R, A> { grade: R; value: A; }

// Track usage via phantom type
type Once<A> = { readonly _once: true; value: A };
type Many<A> = { readonly _many: true; value: A };

function useOnce<A>(x: Once<A>): [A, 'consumed'] { return [x.value, 'consumed']; }
```

Production graded type systems: **Granule** (full graded linear types), **Idris 2** (QTT with 0/1/ω multiplicities), **Linear Haskell** (GHC 9.0+ with `%1` multiplicity annotation), **Haskell mtl** (graded monad via monad transformer stack).

### 14.4 Common Pitfalls

1. **Semiring choice matters**: `Nat` semiring requires SMT for constraint solving; `{0,1,ω}` is simpler but less precise.
2. **Grade erasure**: Grades are static-only in Granule; TS encodings require runtime grade tracking (overhead).
3. **Effect-coeffect interaction**: Combining graded effects (Diamond) and coeffects (Box) requires distributive laws. Not all combinations are coherent.
4. **Grade polymorphism**: Quantifying over grades (`forall r. Box_r A -> ...`) requires constraint solving over the semiring, which can be expensive.

### 14.5 Cross-References

Related: Substructural Types (graded types generalize linear/affine), Session Types (graded effects for protocol tracking), Refinement Types (Liquid types as graded over a predicate semiring), Dependent Types (QTT unifies graded + dependent).

---

## 15. Session Types

### 15.1 Formal Foundations

Session types (Honda 1993) describe communication protocols on typed channels. Binary session type grammar:
```
S ::= !T.S    -- send value T, continue as S
    | ?T.S    -- receive value T, continue as S
    | S1 + S2 -- internal choice (we select)
    | S1 & S2 -- external choice (partner selects)
    | mu X. S -- recursive session
    | X       -- session variable
    | end     -- termination
```

**Duality**: the key correctness property — every send is matched by a receive:
```
dual(!T.S)      = ?T.dual(S)
dual(?T.S)      = !T.dual(S)
dual(S1 + S2)   = dual(S1) & dual(S2)
dual(S1 & S2)   = dual(S1) + dual(S2)
dual(end)       = end
dual(mu X. S)   = mu X. dual(S)
```

Process typing: `Gamma; Delta |- P :: c:S` where `Gamma` is unrestricted context, `Delta` is linear channel context.

```
T-Send:   Gamma; Delta |- P :: c:S,  Gamma |- v:T
          =>  Gamma; Delta |- c.send(v); P :: c:!T.S

T-Recv:   Gamma; Delta, x:T |- P :: c:S
          =>  Gamma; Delta |- x <- c.recv(); P :: c:?T.S

T-Cut:    Gamma; D1 |- P :: c:S,  Gamma; D2 |- Q :: c:dual(S)
          =>  Gamma; D1,D2 |- (P | Q) :: end
```

**Curry-Howard correspondence**: session types ↔ linear logic propositions (Wadler 2012 "propositions as sessions"). `!T.S` corresponds to tensor `T ⊗ S`; `?T.S` corresponds to par `T ⅋ S`; `end` corresponds to `1`.

**Deadlock freedom**: well-typed session programs are deadlock-free (by the linear discipline — no circular wait is possible in the linear typing).

### 15.2 Core Algorithm

Session type checker with linearity:

```typescript
function checkProcess(ctx: LinearCtx, process: Process, channel: string, session: SessionType): LinearCtx {
  switch (process.tag) {
    case 'PSend': {
      if (session.tag !== 'Send') throw new TypeError('Expected Send session');
      checkExpr(ctx, process.value, session.payload);  // check value type
      return checkProcess(ctx, process.cont, channel, session.cont);  // advance session
    }
    case 'PRecv': {
      if (session.tag !== 'Recv') throw new TypeError('Expected Recv session');
      const extCtx = ctx.extend(process.binder, session.payload);
      return checkProcess(extCtx, process.cont, channel, session.cont);
    }
    case 'PClose': {
      if (session.tag !== 'End') throw new TypeError('Expected End session');
      return ctx;  // channel consumed
    }
    // ...
  }
}
```

### 15.3 Pragmatic Implementation

TypeScript session type encoding via continuation-passing:

```typescript
interface Send<T, Next> { send(v: T): Next; }
interface Recv<T, Next> { recv(): [T, Next]; }
interface End { close(): void; }

// Protocol: send number, receive string, done
type Protocol = Send<number, Recv<string, End>>;

// Typed channel enforces protocol order
class Channel<S> implements Send<any, any>, Recv<any, any>, End {
  send<T, Next>(this: Channel<Send<T, Next>>, v: T): Channel<Next> { /*...*/ return this as any; }
  recv<T, Next>(this: Channel<Recv<T, Next>>): [T, Channel<Next>] { /*...*/ return [{} as T, this as any]; }
  close(this: Channel<End>): void { /*...*/ }
}

const ch = new Channel<Protocol>();
const ch2 = ch.send(42);        // ch2: Channel<Recv<string, End>>
const [msg, ch3] = ch2.recv();  // msg: string, ch3: Channel<End>
ch3.close();
// ch.send(99);  // TYPE ERROR: Channel<Protocol> not assignable to Channel<Send<number,Recv<string,End>>>
```

Production tools: **STScript** (multiparty session types for TypeScript), **Scribble** (session type specification language), **GV** (functional session types in Haskell), **Effect-TS Fiber** (structured concurrency approximating session safety).

### 15.4 Common Pitfalls

1. **Channel aliasing**: Using a channel reference after advancing its state. Always use continuation-passing style — each operation returns a new channel reference.
2. **Deadlock from cyclic dependencies**: Two processes each waiting to receive from the other. The linear discipline prevents this in theory; TypeScript encoding cannot enforce it.
3. **Resource leaks**: An exception thrown mid-protocol leaves the partner hanging. Use try/finally with protocol cancellation.
4. **Non-exhaustive branch handling**: Callback-based offer pattern doesn't give compile-time exhaustiveness — structured type carefully.

### 15.5 Cross-References

Related: Substructural Types (session types ARE linear types for channels), Graded Types (graded effects for protocol tracking), Linear Logic (Curry-Howard for sessions), Recursive Types (recursive session types for looping protocols).

---

## 16. Modal Type Theory (Fitch-style, S4)

### 16.1 Formal Foundations

Modal type theory extends a base type theory with modalities from modal logic. **Fitch-style S4** (Clouston 2018; Gratzer, Sterling, Birkedal 2019 MTT):

Contexts include **lock tokens** `μ`: `Γ ::= · | Γ, x:A | Γ.μ`

**Variable restriction**: a variable `x:A` is accessible only if there is no lock `μ` between its binding and the current position.

Key rules:
```
[Var]        x:A in Gamma, no μ between x and end
             ----------------------------------------
             Gamma |- x : A

[Box-Intro]  Gamma.mu |- t : A     (t typed with all local vars locked)
             ----------------------------------------
             Gamma |- box(t) : []A

[Box-Elim]   Gamma |- t : []A,  Gamma, x:A |- u : C
             ----------------------------------------
             Gamma |- let box x = t in u : C
             (x: accessible in u as if unboxed)
```

Modal axioms (S4):
- **T**: `[]A -> A` (necessity implies truth)
- **4**: `[]A -> [][]A` (positive introspection)
- **K**: `[](A -> B) -> ([]A -> []B)` (distribution)

**Computational interpretation of `[]A`**:
- `[]A` = "A holds in all accessible worlds" = value available at all stages
- **Staged computation**: `[]A` values are stage-1 (macro) expressions that produce stage-2 (runtime) code
- **Cross-stage persistence**: values in `[]A` can be used across stage boundaries
- **Idempotency**: `[][]A = []A` (S4 axiom 4) — double-boxing collapses

**MTT** (Gratzer et al. 2020): Multi-Modal Type Theory unifies CwF (categories with families) with multiple modalities under a uniform framework.

**◇A (possibility/diamond)**: dual to `[]A`. Corresponds to "eventually A" or exception/partiality effect. Less common in PL use.

### 16.2 Core Algorithm

Fitch-style modal type checker with lock-aware context:

```typescript
type CtxEntry = { tag: 'Binding'; name: string; ty: Type } | { tag: 'Lock' };
type Ctx = CtxEntry[];

function isAccessible(ctx: Ctx, targetName: string): boolean {
  // Variable accessible only if no Lock appears after it in the context
  let foundVar = false;
  for (let i = ctx.length - 1; i >= 0; i--) {
    const entry = ctx[i];
    if (entry.tag === 'Lock') return false;  // lock blocks access
    if (entry.tag === 'Binding' && entry.name === targetName) { foundVar = true; break; }
  }
  return foundVar;
}

function typeCheck(ctx: Ctx, term: Term): Type {
  switch (term.tag) {
    case 'Var':
      if (!isAccessible(ctx, term.name)) throw new Error(`${term.name} inaccessible (behind lock)`);
      return ctx.find(e => e.tag === 'Binding' && e.name === term.name)?.ty!;
    case 'Box':
      // Add lock, type body in locked context
      return { tag: 'BoxTy', inner: typeCheck([...ctx, { tag: 'Lock' }], term.body) };
    case 'Unbox':
      const innerTy = typeCheck(ctx, term.arg);
      if (innerTy.tag !== 'BoxTy') throw new Error('Expected boxed type');
      return innerTy.inner;
    case 'LetBox':
      const boxedTy = typeCheck(ctx, term.bound);
      if (boxedTy.tag !== 'BoxTy') throw new Error('Expected boxed type');
      return typeCheck([...ctx, { tag: 'Binding', name: term.name, ty: boxedTy.inner }], term.body);
  }
}
```

### 16.3 Pragmatic Implementation

TypeScript encoding of `[]A` via branded types:

```typescript
declare const BOX_BRAND: unique symbol;
interface Box<A> { readonly [BOX_BRAND]: true; readonly value: A; }

function box<A>(value: A): Box<A> { return { [BOX_BRAND]: true, value } as Box<A>; }
function unbox<A>(b: Box<A>): A { return b.value; }
// S4 axiom 4: []A -> [][]A
function rebox<A>(b: Box<A>): Box<Box<A>> { return box(b); }

// Staged computation: Box<A> = "A is a macro value, not runtime"
type CompileTimeValue<A> = Box<A>;
// Cross-stage persistence: use a macro value in runtime code
function spliceInto<A>(macro: CompileTimeValue<A>): A { return unbox(macro); }
```

Key applications:
- **Staged computation / metaprogramming** (MetaOCaml, Template Haskell, Lean 4 macros)
- **Distributed computation**: `[]A` = "A is available at every node"
- **Code generation**: `[]A` = "A is a code fragment" (phase distinction)
- **Synchronization**: in synchronous reactive programming, `[]A` = "A holds at every tick"

Use `[]A` (box) when: a value must be available in multiple stages/phases/worlds. Use `◇A` (diamond/possibility) when: a computation may produce `A` in some future state (partiality, exceptions, continuations).

### 16.4 Common Pitfalls

1. **Missing lock check during variable lookup**: The core modal invariant. Without it, boxed terms capture local state, breaking the necessary modality.
2. **Incorrect substitution across locks**: When substituting into a term under a lock, the substituted term must not reference variables behind the lock.
3. **Conflating S4 with K4**: In S4, `[]A -> A` (axiom T) holds; in K4 it does not. Using the wrong axioms causes unsoundness.
4. **Lock idempotency**: `Gamma.μ.μ` should behave as `Gamma.μ`. Failing to normalize double locks gives overly restrictive typing.
5. **Mutable references crossing stage boundaries**: `Box` should only contain pure values. Allowing mutable refs in `[]A` breaks the stage separation.

### 16.5 Cross-References

Related: Dependent Types (MTT unifies modalities with dependent types), Substructural Types (lock semantics resembles context splitting), Staged Computation (box/unbox = stage brackets), Graded Types (graded box modality in coeffect systems), Recursive Types (modal fixed-points for recursive staged computation).

---

## Summary: When to Use What

| Feature | Use when | Avoid when |
|---|---|---|
| System F<: | Need bounded polymorphism; TS generics with `extends` | Need full F<: with different bounds (undecidable) |
| Row types | Need extensible records with structural open-world typing | Need closed record types with nominal identity |
| ADTs | Closed domain with exhaustive pattern matching | Open-ended extensibility needed (use tagless-final) |
| GADTs | Type-indexed constructors, type-safe ASTs | Avoiding unsafe casts in TS; prefer tagless-final |
| Recursive types (equi) | Transparent mutual recursion; TS default | Explicit fold/unfold boundaries needed |
| Recursive types (iso) | Explicit representation change (ML/Haskell data) | Overhead of explicit coercions unacceptable |
| Intersection types | Combine multiple interfaces; type-level AND | Incompatible types (result is `never`) |
| Union types | Sum over known alternatives; discriminated unions | Alternatives need exhaustive tracking at type level |
| Refinement/Liquid | Statically verify numeric invariants | Arbitrary predicates (use LiquidHaskell, not TS) |
| Linear types | Resource safety, protocol enforcement, no GC leaks | GC-managed runtime; overhead unacceptable |
| Gradual typing | Migrating JS to TS; interop with untyped APIs | Need full soundness guarantees |
| Flow-sensitive | Refinement from runtime checks (typeof, instanceof) | Complex control flow that defeats narrowing |
| Existential types | Information hiding, abstract data types, heterogeneous collections | TS native (prefer abstract classes) |
| Variance annotations | Explicit covariance/contravariance for generic interfaces | Inferred variance sufficient (TS 4.7+ infers it) |
| Nominal/branded types | Unit safety (USD vs EUR), ID types, semantic types | Structural duck typing is the correct behavior |
| Graded types | Fine-grained resource/security tracking in a research language | Complexity unacceptable; use linear types instead |
| Session types | Typed protocols for concurrent/distributed communication | Simple async patterns suffice |
| Modal types | Staged computation, cross-stage persistence, distributed values | Single-stage computation; overhead unjustified |
