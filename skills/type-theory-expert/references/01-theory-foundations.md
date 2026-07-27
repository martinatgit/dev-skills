# Type Theory Foundations

*Sources: Simply_Typed_Lambda_Calculus_STLC.json, System_F_Polymorphic_Lambda_Calculus.json, System_Fomega_Higher_Kinded_Types.json, Curry_Howard_Correspondence.json, Cartesian_Closed_Categories.json, Dependent_Types_Martin_Lof_Type_Theory.json, Homotopy_Type_Theory_HoTT.json, Cubical_Type_Theory.json, Quotient_Types_QIITs.json, Polarity_CBPV.json, Totality_Termination_Productivity.json, Two_Level_Type_Theory.json*

---

## 1. Simply Typed Lambda Calculus (STLC)

### Formal Foundations

**Syntax.** Types: `tau ::= B | tau_1 -> tau_2` (base types B, right-associative arrow). Terms: `e ::= x | lambda x:tau. e | e1 e2`. Typing context Gamma is a finite map from variables to types.

**Typing Rules.** Judgement form: `Gamma |- e : tau`

```
(T-Var)     (x : tau) in Gamma
            ─────────────────
            Gamma |- x : tau

(T-Abs)     Gamma, x : tau1 |- e : tau2
            ───────────────────────────────
            Gamma |- (lambda x:tau1. e) : tau1 -> tau2

(T-App)     Gamma |- e1 : tau1 -> tau2    Gamma |- e2 : tau1
            ──────────────────────────────────────────────────
            Gamma |- e1 e2 : tau2
```

**Bidirectional variant** splits into synthesis (infer, bottom-up) and checking (check, top-down):

```
(Synth-Var)  (x:A) in Gamma             =>  Gamma |- x => A
(Synth-App)  Gamma |- e1 => A -> B,
             Gamma |- e2 <= A            =>  Gamma |- e1 e2 => B
(Synth-Ann)  Gamma |- e <= A             =>  Gamma |- (e : A) => A
(Check-Lam)  Gamma, x:A |- e <= B       =>  Gamma |- (lambda x. e) <= A -> B
(Check-Sub)  Gamma |- e => A,  A = B     =>  Gamma |- e <= B
```

**Key Theorems.**
- **Strong Normalization (Tait 1967):** Every well-typed STLC term is strongly normalizing -- all reduction sequences terminate regardless of strategy. Proved via logical relations (Tait's method / reducibility candidates).
- **Subject Reduction (Type Preservation):** If `Gamma |- e : tau` and `e --> e'`, then `Gamma |- e' : tau`.
- **Progress:** If `|- e : tau` (closed, well-typed), then e is a value or steps. Combined with preservation, yields type safety.
- **Confluence (Church-Rosser):** Beta-reduction is confluent.
- **Decidability of beta-eta-equality:** Beta-eta equivalence of STLC terms is decidable.
- **Curry-Howard-Lambek:** STLC proofs = intuitionistic propositional logic proofs (implicational fragment) = morphisms in cartesian closed categories.

**Metatheory.** Type checking is O(n) in derivation size. Type inference is decidable via unification in quasi-linear time O(n * alpha(n)). Normalization is not elementary recursive (Statman 1979). Inhabitation is PSPACE-complete (Statman 1979). Higher-order unification (2nd order+) is undecidable (Goldfarb 1981).

### Core Algorithm

Bidirectional type checker pseudocode:

```typescript
function synth(ctx: Context, term: Term): Type {
  switch (term.tag) {
    case 'Var': {
      const ty = ctx.get(term.name);
      if (!ty) throw new Error(`Unbound: ${term.name}`);
      return ty;
    }
    case 'Ann': {
      check(ctx, term.term, term.type);
      return term.type;
    }
    case 'App': {
      const funcTy = synth(ctx, term.func);
      if (funcTy.tag !== 'Arrow') throw new Error('Expected arrow');
      check(ctx, term.arg, funcTy.param);
      return funcTy.ret;
    }
    default:
      throw new Error('Cannot synthesize type for lambda; add annotation');
  }
}

function check(ctx: Context, term: Term, expected: Type): void {
  if (term.tag === 'Abs' && expected.tag === 'Arrow') {
    const bodyCtx = new Map(ctx);
    bodyCtx.set(term.param, expected.param);
    check(bodyCtx, term.body, expected.ret);
    return;
  }
  const inferred = synth(ctx, term);
  if (!typeEquals(inferred, expected))
    throw new Error(`Type mismatch: expected ${show(expected)}, got ${show(inferred)}`);
}
```

**Normalization by Evaluation (NbE) sketch:** Evaluate STLC terms into a semantic domain of values (closures + neutral forms), then read back to normal forms. NbE is more efficient than iterated beta-reduction, avoids variable capture issues, and naturally produces beta-eta-normal forms. Key steps: (1) interpret terms into a value domain using an environment, (2) apply semantic values (closures) to arguments, (3) read back semantic values to syntactic normal forms using fresh variables for neutrals.

### Pragmatic Implementation

```typescript
// Type-level STLC in TypeScript:
type BaseType<Name extends string> = { tag: 'Base'; name: Name };
type ArrowType<P extends STLCType, R extends STLCType> = { tag: 'Arrow'; param: P; ret: R };
type STLCType = BaseType<string> | ArrowType<any, any>;

// Runtime bidirectional checker uses discriminated union for terms:
type TermNode = VarTerm | AbsTerm | AppTerm | AnnTerm;

// Use branded types to distinguish base types:
declare const __brand: unique symbol;
type Nat = number & { [__brand]: 'Nat' };

// Use 'as const' + template literals for type-level variable names.
// Use hash-consed types for O(1) equality. Use de Bruijn indices for alpha-equivalence.
```

### Common Pitfalls

1. **Variable capture in naive substitution:** Use de Bruijn indices or locally-nameless representation to avoid capture during beta-reduction.
2. **Church-style vs Curry-style confusion:** Explicitly-typed lambdas (Church) and untyped lambdas (Curry) require fundamentally different algorithms.
3. **Missing occurs check:** When extending to type inference via unification, omitting the occurs check leads to infinite types.
4. **Mutable context leakage:** Extending a shared context map without copying causes scope leakage between branches.

### Cross-References

- Generalizes: untyped lambda calculus (by adding types).
- Specializes: System F (STLC = System F without type quantification), Hindley-Milner (STLC = HM without let-polymorphism).
- Related: Cartesian Closed Categories (CCC semantics), Curry-Howard Correspondence, Bidirectional Type Checking, System Fomega.

---

## 2. System F (Polymorphic Lambda Calculus)

### Formal Foundations

**Syntax.** Types: `tau ::= alpha | tau_1 -> tau_2 | forall alpha. tau`. Terms: `e ::= x | lambda x:tau. e | e1 e2 | Lambda alpha. e | e [tau]`. Context Gamma tracks both term variables (x:tau) and type variables (alpha).

**Typing Rules.**

```
(T-Var)     (x : tau) in Gamma                        =>  Gamma |- x : tau
(T-Abs)     Gamma, x:tau1 |- e : tau2                 =>  Gamma |- (lambda x:tau1. e) : tau1 -> tau2
(T-App)     Gamma |- e1 : tau1->tau2, Gamma |- e2:tau1 =>  Gamma |- e1 e2 : tau2
(T-TAbs/TA-Gen)   Gamma, alpha |- e : tau  (alpha not free in Gamma)
                                                       =>  Gamma |- (Lambda alpha. e) : forall alpha. tau
(T-TApp/TA-Spec)  Gamma |- e : forall alpha. tau       =>  Gamma |- e [tau'] : tau[alpha := tau']
```

**Operational semantics** adds type-level beta: `(Lambda alpha. e) [tau] --> e[alpha := tau]`.

**Key Theorems.**
- **Strong Normalization (Girard 1972):** Via reducibility candidates (candidats de reductibilite), a generalization of Tait's method.
- **Parametricity / Reynolds Abstraction Theorem (Reynolds 1983):** Polymorphic functions behave uniformly across all type instantiations. For `|- e : forall alpha. tau` and any relation R between types A, B, the logical relation `[[tau]](R)` holds between `e[A]` and `e[B]`. Yields "theorems for free" (Wadler 1989).
- **Undecidability of inference (Wells 1999):** Curry-style type inference for System F is undecidable, by reduction from semi-unification. Rank-2 inference is decidable (Kfoury & Wells 1999); rank-k for k >= 3 is undecidable.
- **Representation Theorem (Girard):** System F can encode all functions provably total in second-order Peano arithmetic.
- **Church Encodings:** `Nat = forall alpha. (alpha -> alpha) -> alpha -> alpha`; `Bool = forall alpha. alpha -> alpha -> alpha`.

**Metatheory.** Church-style type checking: decidable in polynomial time. Type inhabitation: undecidable (provability in second-order propositional logic). Beta-eta equivalence of well-typed terms: decidable (by strong normalization + confluence).

### Core Algorithm

```typescript
// Capture-avoiding type substitution is central:
function substType(ty: Type, tyvar: string, replacement: Type): Type {
  switch (ty.tag) {
    case 'TVar': return ty.name === tyvar ? replacement : ty;
    case 'Arrow': return { tag: 'Arrow',
      param: substType(ty.param, tyvar, replacement),
      ret: substType(ty.ret, tyvar, replacement) };
    case 'Forall':
      if (ty.tyvar === tyvar) return ty;  // shadowed
      if (freeTypeVars(replacement).has(ty.tyvar)) {
        const fresh = freshTyVar(ty.tyvar);
        const renamed = substType(ty.body, ty.tyvar, { tag: 'TVar', name: fresh });
        return { tag: 'Forall', tyvar: fresh,
          body: substType(renamed, tyvar, replacement) };
      }
      return { tag: 'Forall', tyvar: ty.tyvar,
        body: substType(ty.body, tyvar, replacement) };
  }
}

// Type checker (Church-style): O(n^2) worst case due to substitution.
function typeCheck(ctx: Context, term: Term): Type {
  // ... T-Var, T-Abs, T-App as STLC ...
  case 'TAbs': {
    const extCtx = { ...ctx, typeVars: new Set([...ctx.typeVars, term.tyvar]) };
    const bodyTy = typeCheck(extCtx, term.body);
    return { tag: 'Forall', tyvar: term.tyvar, body: bodyTy };
  }
  case 'TApp': {
    const termTy = typeCheck(ctx, term.term);
    if (termTy.tag !== 'Forall') throw new Error('Expected forall');
    return substType(termTy.body, termTy.tyvar, term.typeArg);
  }
}
```

### Pragmatic Implementation

```typescript
// TS generics as restricted System F:
// forall alpha. alpha -> alpha  ===  <A>(x: A) => A
const id = <A>(x: A): A => x;

// Church encodings in TS:
type ChurchBool = <A>(t: A, f: A) => A;
const TRUE: ChurchBool = <A>(t: A, _f: A) => t;
const FALSE: ChurchBool = <A>(_t: A, f: A) => f;

type ChurchNat = <A>(s: (x: A) => A, z: A) => A;
const ZERO: ChurchNat = <A>(_s: (x: A) => A, z: A) => z;
const SUCC = (n: ChurchNat): ChurchNat => <A>(s: (x: A) => A, z: A) => s(n(s, z));
```

**TS limitations:** Generics are rank-1 by default; higher-rank requires explicit annotations. TS lacks impredicative polymorphism and type-level lambda. Type narrowing, conditional types, and `any` break parametricity.

### Common Pitfalls

1. **Capture-avoiding substitution is critical:** Substituting into `forall alpha. tau` when the replacement contains alpha free requires renaming the bound variable.
2. **Church vs Curry confusion:** Wells 1999 shows Curry-style inference is undecidable; Church-style checking is polynomial.
3. **Type variable scoping:** Type variables from TAbs must be removed from scope when leaving the body.
4. **Alpha-equivalence in comparison:** `forall a. a -> a` and `forall b. b -> b` must be equal. Use de Bruijn indices.

### Cross-References

- Generalizes: STLC (adds type quantification), Hindley-Milner (HM is rank-1 restriction).
- Specializes: System Fomega (F is Fomega restricted to kind `*`), Calculus of Constructions.
- Related: Lambda Cube, Parametricity, GHC Core (System FC).

---

## 3. System Fomega (Higher-Kinded Types)

### Formal Foundations

**Kind System.** Kinds classify type expressions: `kappa ::= * | kappa_1 => kappa_2`. Kind `*` classifies proper types (types that classify terms). Kind `kappa_1 => kappa_2` classifies type operators.

**Syntax.** Type expressions: `tau ::= alpha | tau_1 -> tau_2 | forall alpha:kappa. tau | lambda alpha:kappa. tau | tau_1 tau_2`. Type-level lambda (`lambda alpha:kappa. tau`) creates type operators; type-level application (`tau_1 tau_2`) applies them.

**Type operator examples:**
- `Maybe : * => *` -- a type constructor taking one type
- `Either : * => * => *` -- a type constructor taking two types
- `Functor : (* => *) => *` -- takes a type constructor, returns a proper type

**Kinding Rules.**

```
(K-Var)     (alpha : kappa) in Delta      =>  Delta |- alpha : kappa
(K-Arrow)   Delta |- tau1 : *, Delta |- tau2 : *
                                          =>  Delta |- tau1 -> tau2 : *
(K-Abs)     Delta, alpha:kappa1 |- tau : kappa2
                                          =>  Delta |- (lambda alpha:kappa1. tau) : kappa1 => kappa2
(K-App)     Delta |- tau1 : kappa1 => kappa2, Delta |- tau2 : kappa1
                                          =>  Delta |- tau1 tau2 : kappa2
(K-Forall)  Delta, alpha:kappa |- tau : *
                                          =>  Delta |- (forall alpha:kappa. tau) : *
```

**Type equivalence** includes beta-reduction at the type level: `(lambda alpha:kappa. tau_1) tau_2 =beta tau_1[alpha := tau_2]`.

**Key Theorems.**
- **Strong Normalization:** Both type-level and term-level computation strongly normalize. Extends Girard's reducibility candidates.
- **Type Equivalence Decidability:** Beta-eta equivalence of well-kinded type expressions is decidable (normalize both sides, compare structurally).
- **Encoding Power:** Subsumes System F; encodes type-level maps, folds, Church-encoded type-level data structures.

**Relationship to HKT in Haskell/fp-ts:** GHC Haskell's Core (System FC) is essentially Fomega + type equality coercions. fp-ts simulates HKTs via URI-based encoding (declaration merging into `URItoKind<A>`). Effect-TS uses a more refined `TypeLambda` encoding.

### Core Algorithm

```typescript
// Kind checker (analogous to STLC type checker at kind level):
function kindCheck(kctx: KindCtx, ty: Type): Kind {
  switch (ty.tag) {
    case 'TVar': return kctx.get(ty.name) ?? error('Unbound type variable');
    case 'Arrow': {
      assertKindStar(kindCheck(kctx, ty.param));
      assertKindStar(kindCheck(kctx, ty.ret));
      return { tag: 'Star' };
    }
    case 'TLam': {
      const ext = extend(kctx, ty.tyvar, ty.kind);
      const bodyK = kindCheck(ext, ty.body);
      return { tag: 'KArrow', from: ty.kind, to: bodyK };
    }
    case 'TApp': {
      const funcK = kindCheck(kctx, ty.func);
      if (funcK.tag !== 'KArrow') throw new Error('Expected type operator kind');
      const argK = kindCheck(kctx, ty.arg);
      if (!kindEquals(funcK.from, argK)) throw new Error('Kind mismatch');
      return funcK.to;
    }
  }
}

// Type-level normalization (terminates by strong normalization):
function normalizeType(ty: Type): Type {
  // ... recursively normalize subterms ...
  case 'TApp': {
    const func = normalizeType(ty.func);
    const arg = normalizeType(ty.arg);
    if (func.tag === 'TLam')
      return normalizeType(substType(func.body, func.tyvar, arg)); // beta-reduce
    return { tag: 'TApp', func, arg };
  }
}

// Type equivalence: normalize both sides, compare structurally.
function typeEquiv(a: Type, b: Type): boolean {
  return structuralEq(normalizeType(a), normalizeType(b));
}
```

### Pragmatic Implementation

```typescript
// HKT simulation in TypeScript (fp-ts style):
interface URItoKind<A> {
  readonly Array: Array<A>;
  readonly Maybe: Maybe<A>;
}
type URIS = keyof URItoKind<unknown>;
type Kind1<F extends URIS, A> = URItoKind<A>[F];

// Functor abstracts over type constructors (kind * => *):
interface Functor<F extends URIS> {
  readonly map: <A, B>(fa: Kind1<F, A>, f: (a: A) => B) => Kind1<F, B>;
}

// Effect-TS style (more sophisticated):
interface TypeLambda { readonly In: unknown; readonly Out1: unknown; readonly Target: unknown; }
interface ArrayTypeLambda extends TypeLambda { readonly Target: Array<this['Out1']>; }
type Apply<F extends TypeLambda, A> = (F & { readonly Out1: A })['Target'];
```

### Common Pitfalls

1. **Kind errors are subtle:** Applying a type of kind `*` where `* => *` is expected produces confusing errors. Implement kind checking before type checking.
2. **Type-level divergence:** Recursive type operators without a termination check can diverge. Fomega's strong normalization only holds for the pure system.
3. **Confusing type-level and term-level abstraction:** `Lambda alpha:kappa` (term-level type abstraction) vs `lambda alpha:kappa` (type-level type operator) are in different syntactic categories.
4. **Expensive conversion rule:** The T-TEquiv rule requires deciding type equivalence at every step. Normalize types eagerly to avoid repeated normalization.

### Cross-References

- Generalizes: System F (adds type operators of higher kinds), Lambda-omega (adds polymorphism).
- Specializes: Calculus of Constructions (Fomega lacks dependent types), Pure Type Systems.
- Related: Lambda Cube, GHC System FC, fp-ts/Effect-TS HKT encodings, Scala 3 type lambdas.

---

## 4. Curry-Howard Correspondence

### Formal Foundations

**The Propositions-as-Types Principle.** A structural isomorphism between formal logic and type theory, operating at three levels:

| Logic (Intuitionistic) | Type Theory | Category Theory (CCCs) |
|---|---|---|
| Proposition A | Type A | Object A |
| Proof of A | Term e : A | Morphism 1 -> A |
| A => B (implication) | A -> B (function type) | Exponential B^A |
| A /\ B (conjunction) | A x B (product type) | Product A x B |
| A \/ B (disjunction) | A + B (sum type) | Coproduct A + B |
| True | Unit (1) | Terminal object 1 |
| False | Void (0) | Initial object 0 |
| not A | A -> Void | -- |
| forall x. P(x) | Pi(x:A).B(x) (dependent function) | Dependent product |
| exists x. P(x) | Sigma(x:A).B(x) (dependent pair) | Dependent sum |
| Proof simplification | Beta-reduction | Composition |
| Cut elimination | Normalization | -- |

**Formal bijection:** `Gamma |-_NJ A  <=>  Gamma |-_STLC e : A` where NJ is intuitionistic natural deduction.

**Key Theorems.**
- **Curry (1934):** Combinators correspond to axiom schemes of Hilbert-style logic (S, K combinators = modus ponens + weakening).
- **Howard (1969/1980):** Full structural correspondence between natural deduction proofs and simply-typed lambda terms.
- **Lambek (1970s):** Extended to cartesian closed categories, yielding the Curry-Howard-Lambek trichotomy.
- **Classical logic extensions:** Griffin (1990) showed `call/cc` gives computational content to Peirce's law `((A -> B) -> A) -> A`, linking classical logic to control operators/continuations.
- **Linear logic (Girard 1987):** Curry-Howard extends to linear lambda calculus, connecting to resource-aware computation and session types.

**Practical API design implications:** "Make illegal states unrepresentable" is Curry-Howard applied to API design. Discriminated unions encode state machines as sum types. `Result<T, E>` encodes propositions with explicit error cases. Branded/phantom types encode type-level invariants as propositions.

### Core Algorithm

```typescript
// Proof search as type inhabitation:
// Given type tau, find a term e such that |- e : tau
function inhabit(ctx: Context, goal: Type): Term | null {
  // 1. Check context for matching variable (axiom rule)
  for (const [name, ty] of ctx) {
    if (typeEquals(ty, goal)) return { tag: 'Var', name };
  }
  // 2. If goal is A -> B, introduce a lambda (=> intro)
  if (goal.tag === 'Arrow') {
    const fresh = freshVar();
    const extended = new Map(ctx).set(fresh, goal.param);
    const body = inhabit(extended, goal.ret);
    if (body) return { tag: 'Abs', param: fresh, paramType: goal.param, body };
  }
  // 3. Try application: find f : A -> goal and a : A in context
  for (const [name, ty] of ctx) {
    if (ty.tag === 'Arrow' && typeEquals(ty.ret, goal)) {
      const arg = inhabit(ctx, ty.param);
      if (arg) return { tag: 'App', func: { tag: 'Var', name }, arg };
    }
  }
  // 4. If goal is A x B, provide both components
  if (goal.tag === 'Product') {
    const fst = inhabit(ctx, goal.fst);
    const snd = inhabit(ctx, goal.snd);
    if (fst && snd) return { tag: 'Pair', fst, snd };
  }
  return null; // unprovable
}
```

### Pragmatic Implementation

```typescript
// Discriminated unions as logical disjunction:
type Shape =
  | { tag: 'circle'; radius: number }      // Circle proof
  | { tag: 'rect'; width: number; h: number }; // Rectangle proof

// Result type as A \/ Error (with proof obligations):
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

// Branded types as type-level propositions:
declare const __validated: unique symbol;
type Validated<T> = T & { [__validated]: true };
function validate(s: string): Result<Validated<string>, Error> { /* ... */ }

// Exhaustive pattern matching enforces proof completeness:
function area(s: Shape): number {
  switch (s.tag) {
    case 'circle': return Math.PI * s.radius ** 2;
    case 'rect': return s.width * s.h;
    // TS error if a case is missing = incomplete proof
  }
}
```

### Common Pitfalls

1. **Type safety != logical soundness:** TS has `any`, `as`, `@ts-ignore` that break the correspondence. Type assertions are not real proofs.
2. **Non-termination violates soundness:** Infinite loops produce values of any type. In logic, all proofs must terminate.
3. **Exceptions as hidden disjunctions:** Throwing is an implicit `OR error` not in the type. Use `Result<T, E>` instead.
4. **Structural typing leaks:** Any object with matching shape satisfies a type, even if not constructed through the intended proof path.
5. **Runtime validation boundary:** Types erase at runtime. External data must be validated at the boundary.
6. **Overcomplicating:** Not every API needs formal proof structure. Apply Curry-Howard to critical invariants (state machines, protocols, authorization), not simple transformations.

### Cross-References

- Generalizes: simple type assignments, type-directed program synthesis (proof search as special case).
- Specializes: Curry-Howard-Lambek correspondence (adds categorical dimension), Computational trinitarianism (logic + types + categories).
- Related: STLC, Dependent Types (MLTT), System F, Cartesian Closed Categories, Linear Logic/Linear Types.

---

## 5. Cartesian Closed Categories & Lambek Correspondence

### Formal Foundations

A **cartesian closed category (CCC)** is a category C equipped with:

1. **Finite products:** For objects A, B, a product A x B with projections `pi_1 : A x B -> A`, `pi_2 : A x B -> B`, and pairing: for `f : C -> A`, `g : C -> B`, a unique `<f, g> : C -> A x B`.

2. **Terminal object 1:** with unique morphism `!_A : A -> 1` for every A.

3. **Exponential objects:** For A, B, an exponential B^A with evaluation morphism:
   ```
   eval : B^A x A -> B
   ```
   satisfying the universal property: for every `f : C x A -> B`, a unique:
   ```
   curry(f) : C -> B^A   such that   eval . (curry(f) x id_A) = f
   ```
   Equivalently: `Hom(C x A, B) ~ Hom(C, B^A)` (the cartesian adjunction `- x A -| (-)^A`).

**STLC interpretation as CCC (Lambek Correspondence):**

| STLC | CCC |
|---|---|
| Type tau | Object [tau] |
| Term `Gamma |- e : tau` | Morphism `[Gamma] -> [tau]` |
| Function type `tau_1 -> tau_2` | Exponential `[tau_2]^[tau_1]` |
| Application `e1 e2` | eval morphism |
| Lambda abstraction `lambda x. e` | curry (universal property of exponentials) |
| Product type `A x B` | Categorical product |
| Unit type | Terminal object 1 |

Every CCC gives rise to an STLC, and every STLC generates a free CCC (syntactic category). This is the **Curry-Howard-Lambek trichotomy**.

**Key morphisms:**
- `eval : B^A x A -> B` (function application)
- `curry(f) : C -> B^A` where `f : C x A -> B` (lambda abstraction)
- `<f, g> : C -> A x B` (pairing)
- `pi_1, pi_2` (projections)

Adding sum types extends to **bicartesian closed categories** (BCCCs).

### Core Algorithm

```typescript
// Free CCC construction: build morphisms from STLC terms
type Morphism =
  | { tag: 'Id' }                              // id : A -> A
  | { tag: 'Compose'; f: Morphism; g: Morphism } // f . g
  | { tag: 'Pair'; fst: Morphism; snd: Morphism } // <f, g>
  | { tag: 'Fst' } | { tag: 'Snd' }            // pi_1, pi_2
  | { tag: 'Curry'; body: Morphism }            // curry(f)
  | { tag: 'Eval' }                             // eval
  | { tag: 'Terminal' };                         // ! : A -> 1

// Translate STLC term to CCC morphism:
function toCCC(ctx: string[], term: Term): Morphism {
  switch (term.tag) {
    case 'Var': return projectVar(ctx, term.name);  // pi chain
    case 'Abs': return { tag: 'Curry', body: toCCC([term.param, ...ctx], term.body) };
    case 'App': return compose(
      { tag: 'Eval' },
      { tag: 'Pair', fst: toCCC(ctx, term.func), snd: toCCC(ctx, term.arg) }
    );
  }
}
```

### Pragmatic Implementation

```typescript
// Every function call is eval, every lambda is curry, every tuple is a product.
// CCC structure in TypeScript:

// Products: tuples
const pair = <A, B>(a: A, b: B): [A, B] => [a, b];
const fst = <A, B>(p: [A, B]): A => p[0];
const snd = <A, B>(p: [A, B]): B => p[1];

// Exponentials: functions
const apply = <A, B>(f: (a: A) => B, a: A): B => f(a);
const curry = <A, B, C>(f: (ab: [A, B]) => C) => (a: A) => (b: B) => f([a, b]);
const uncurry = <A, B, C>(f: (a: A) => (b: B) => C) => (ab: [A, B]) => f(ab[0])(ab[1]);

// Terminal object: void/undefined
const terminal = <A>(_a: A): void => {};

// Verifying the adjunction: curry . uncurry = id, uncurry . curry = id
```

### Common Pitfalls

1. **Cartesian vs tensor product:** CCC products have diagonals (copying) and terminals (discarding). Linear resources need non-cartesian monoidal categories.
2. **Overlooking eta-equality:** Beta-normal forms that are not eta-expanded may represent the same morphism. Always normalize with eta-expansion.
3. **Recursive types break CCCs:** `type F = (x: F) => F` has no CCC interpretation (requires solving domain equations in DCPO).
4. **Structural typing conflation:** CCCs work with objects up to isomorphism. TS's structural typing identifies distinct interfaces with the same shape.
5. **Subtyping complicates the picture:** TS subtyping (`any`, `unknown`, `never`) means `Hom(A, B)` is ordered, not a simple set.

### Cross-References

- Generalizes: STLC (internal language of free CCC), intuitionistic propositional logic (via Curry-Howard-Lambek), combinatory logic (SK = morphisms in CCC).
- Specializes: Symmetric monoidal closed categories (CCC = cartesian tensor), locally cartesian closed categories (LCCCs model dependent types), topoi (CCC + subobject classifier + finite limits).
- Related: Curry-Howard Correspondence, Adjunctions, Functors/Natural Transformations.

---

## 6. Dependent Types -- Martin-Lof Type Theory (MLTT)

### Formal Foundations

**Judgement forms:** (1) `Gamma ctx` (valid context), (2) `Gamma |- A type`, (3) `Gamma |- a : A`, (4) `Gamma |- a = b : A` (definitional equality).

**Pi-types (dependent function):**

```
[Pi-Form]   Gamma |- A type    Gamma, x:A |- B type
            ─────────────────────────────────────────
            Gamma |- Pi(x:A).B type

[Pi-Intro]  Gamma, x:A |- b : B
            ─────────────────────────────────────────
            Gamma |- lambda(x:A).b : Pi(x:A).B

[Pi-Elim]   Gamma |- f : Pi(x:A).B    Gamma |- a : A
            ─────────────────────────────────────────
            Gamma |- f(a) : B[x := a]

[Pi-Comp]   (lambda(x:A).b)(a) = b[x := a] : B[x := a]   (beta)
```

**Sigma-types (dependent pair):**

```
[Sig-Form]  Gamma |- A type    Gamma, x:A |- B type
            ─────────────────────────────────────────
            Gamma |- Sigma(x:A).B type

[Sig-Intro] Gamma |- a : A    Gamma |- b : B[x := a]
            ─────────────────────────────────────────
            Gamma |- (a, b) : Sigma(x:A).B

[Sig-Elim]  Gamma |- p : Sigma(x:A).B
            ──────────────────          ──────────────────────────
            Gamma |- fst(p) : A         Gamma |- snd(p) : B[x := fst(p)]
```

**Identity types (propositional equality):**

```
[Id-Form]   Gamma |- a : A    Gamma |- b : A
            ─────────────────────────────────
            Gamma |- Id_A(a, b) type

[Id-Intro]  Gamma |- a : A
            ─────────────────────────────────
            Gamma |- refl_a : Id_A(a, a)

[Id-Elim/J] Gamma, x:A, y:A, p:Id(x,y) |- C type
            Gamma, z:A |- d : C[x:=z, y:=z, p:=refl_z]
            Gamma |- a:A    Gamma |- b:A    Gamma |- q : Id(a,b)
            ─────────────────────────────────────────────────────
            Gamma |- J(C, d, a, b, q) : C[x:=a, y:=b, p:=q]
```

**W-types (well-founded trees):** Given `A : Type` and `B : A -> Type`, `W(x:A).B(x)` is the type of well-founded trees where each node is labeled by `a : A` and has `B(a)`-many children. Encodes inductive types (Nat, List, etc.) generically.

**Universe hierarchy:** `U_0 : U_1 : U_2 : ...` cumulative, predicative. `Type : Type` leads to Girard's paradox (inconsistency, Hurkens 1995).

**Key Theorems.**
- **Canonicity:** Every closed term of type Nat reduces to a numeral S^n(0).
- **Strong normalization** (without general recursion).
- **Decidability (intensional):** Type checking is decidable; type inference is undecidable.
- **Undecidability (extensional):** Equality reflection makes checking undecidable.
- **Function extensionality is NOT derivable** in intensional MLTT (motivates HoTT/cubical).

### Core Algorithm

```typescript
// Key algorithm: conversion checking (definitional equality of values).
// Uses Normalization by Evaluation (NbE).

type Value = VPi | VLam | VSigma | VPair | VU | VNat | VNeutral | VId | VRefl;
type Closure = { env: Value[]; body: Term };

function applyClosure(c: Closure, v: Value): Value {
  return eval_([v, ...c.env], c.body);
}

// Conversion check: compare two values for definitional equality
function conv(depth: number, v1: Value, v2: Value): boolean {
  if (v1.tag === 'VPi' && v2.tag === 'VPi') {
    if (!conv(depth, v1.paramTy, v2.paramTy)) return false;
    const fresh = mkNeutral(`x${depth}`);
    return conv(depth + 1, applyClosure(v1.closure, fresh),
                           applyClosure(v2.closure, fresh));
  }
  // Eta for functions: compare under a fresh variable
  if (v1.tag === 'VLam') {
    const fresh = mkNeutral(`x${depth}`);
    return conv(depth + 1, applyClosure(v1.closure, fresh), vApp(v2, fresh));
  }
  // Neutrals: compare head and spine structurally
  if (v1.tag === 'VNeutral' && v2.tag === 'VNeutral') {
    return v1.head === v2.head &&
      v1.spine.every((s, i) => conv(depth, s, v2.spine[i]));
  }
  // ... universe, Nat, Refl, Sigma, Pair comparisons ...
}

// Bidirectional: check(ctx, term, type) and infer(ctx, term) -> type
// check delegates to infer + conv for non-introduction forms.
```

### Pragmatic Implementation

```typescript
// Sigma-type approximation in TS:
type Sigma<A, B extends (a: A) => unknown> = { fst: A; snd: ReturnType<B> };

// Dependent function approximation via indexed access:
interface ShapeMap {
  circle: { radius: number };
  rect: { width: number; height: number };
}
function getShape<K extends keyof ShapeMap>(shape: K): ShapeMap[K] {
  // Return type DEPENDS on runtime value of 'shape'
  return shapes[shape];
}

// Length-indexed vectors via recursive conditional types:
type BuildTuple<T, N extends number, Acc extends T[] = []> =
  Acc['length'] extends N ? Acc : BuildTuple<T, N, [...Acc, T]>;

// Type-level arithmetic:
type Add<A extends number, B extends number> =
  [...BuildTuple<unknown, A>, ...BuildTuple<unknown, B>]['length'];

// Printf with dependent argument types:
type ParseFormat<S extends string> =
  S extends `${string}%s${infer Rest}` ? [string, ...ParseFormat<Rest>]
  : S extends `${string}%d${infer Rest}` ? [number, ...ParseFormat<Rest>]
  : [];
function printf<F extends string>(fmt: F, ...args: ParseFormat<F>): string { /* ... */ }
```

### Common Pitfalls

1. **Type checking requires normalization:** You must evaluate terms to compare types. This is fundamental and cannot be skipped.
2. **Non-termination in the checker:** General recursion without a termination checker makes the type checker diverge.
3. **Universe inconsistency (Type : Type):** Leads to Girard's paradox. Always use stratified hierarchy.
4. **Strict positivity violations:** Non-positive recursive occurrences in inductive types cause inconsistency.
5. **Intensional vs extensional equality confusion:** In intensional MLTT, propositionally equal terms are NOT definitionally equal.
6. **Substitution bugs:** Pervasive and error-prone. Use de Bruijn indices or NbE.
7. **Missing eta-expansion:** Required for sound function extensionality in some variants.

### Cross-References

- Generalizes: STLC, System F, Hindley-Milner (all are fragments of MLTT).
- Specializes: HoTT (adds univalence), Cubical Type Theory (adds computational univalence), Observational Type Theory (adds extensional equality with decidable checking).
- Related: Calculus of Constructions, Agda, Lean 4, Coq (CIC), Locally Cartesian Closed Categories.

---

## 7. Homotopy Type Theory (HoTT) & Univalence

### Formal Foundations

HoTT extends MLTT with two key additions:

**1. The Univalence Axiom.** For types A, B in universe U, the canonical map `idToEquiv : (A =_U B) -> (A ~ B)` (sending refl to the identity equivalence) is itself an equivalence:

```
ua : (A ~ B) ~ (A =_U B)
```

Meaning: **two types are equal in the universe iff they are equivalent** (A ~ B iff A = B). This is a strong extensionality principle for the universe.

**2. Higher Inductive Types (HITs).** Inductive types with constructors for both points and paths (and higher paths):

- **Circle S1:** `base : S1` and `loop : base =_{S1} base` (non-trivial self-loop).
- **Suspension:** `Susp(A)` with `north, south : Susp(A)` and `merid : A -> north = south`.
- **Propositional truncation:** `||A||` with `|a| : ||A||` for `a:A` and a path between any two elements (collapses to a proposition).
- **Pushouts, quotients, cell complexes.**

**Foundational interpretation -- types as infinity-groupoids:**
- Types are spaces (homotopy types / infinity-groupoids).
- Terms `a : A` are points in the space A.
- Identity type `Id_A(a, b)` is the path space from a to b.
- Iterated identity types `Id_{Id_A(a,b)}(p, q)` are homotopies between paths (2-cells).
- **n-types** classify truncation level: (-2)-type = contractible, (-1)-type = proposition (at most one element up to path), 0-type = set (UIP holds), 1-type = groupoid, etc.

**Path induction (J rule):** To define a function on all paths, it suffices to define it on `refl`. This is the fundamental elimination principle for identity types.

**Key Theorems.**
- **Univalence implies function extensionality:** `(forall x. f(x) = g(x)) -> f = g`.
- **Univalence is NOT derivable** in plain MLTT.
- **Univalence does NOT compute** in plain HoTT (it is an axiom, not a definition). Terms involving `ua` get "stuck." This motivated cubical type theory.
- **The fundamental theorem of identity types:** characterizes the identity type of any type in terms of its structure.
- **Whitehead's theorem (for n-types):** A map between n-types that induces isomorphisms on all homotopy groups is an equivalence.

### Core Algorithm

```typescript
// Path type operations:
type Path<A, a extends A, b extends A> = { witness: (i: Interval) => A };

// Transport: move data along a path (type-level coercion)
function transport<A, B>(path: Path<Type, A, B>, a: A): B { /* ... */ }

// ap (action on paths): apply a function to a path
function ap<A, B>(f: (a: A) => B, p: Path<A, x, y>): Path<B, f(x), f(y)> { /* ... */ }

// Univalence: equivalence -> path in universe
function ua<A, B>(equiv: Equiv<A, B>): Path<Type, A, B> { /* axiom */ }

// Path induction (J eliminator):
function J<A, a extends A, C extends (b: A, p: Path<A,a,b>) => Type>(
  d: C(a, refl(a)),   // base case: behavior on refl
  b: A,
  p: Path<A, a, b>
): C(b, p) { /* by path induction */ }

// n-truncation levels:
type IsContr<A> = Sigma<A, (a: A) => (b: A) => Path<A, a, b>>;
type IsProp<A> = (a: A, b: A) => Path<A, a, b>;
type IsSet<A> = (a: A, b: A) => IsProp<Path<A, a, b>>;
```

### Pragmatic Implementation

```typescript
// Equivalences in TS (structural):
interface Equiv<A, B> {
  to: (a: A) => B;
  from: (b: B) => A;
  toFrom: (b: B) => b === to(from(b));  // conceptual
  fromTo: (a: A) => a === from(to(a));  // conceptual
}

// Univalence-inspired: isomorphic types are interchangeable
// TS structural typing gives a weak form: if A and B have the same shape, A = B.

// Transport pattern in TS:
function evolveState<S1, S2>(
  migration: Equiv<S1, S2>,
  state: S1
): S2 {
  return migration.to(state);
}

// Higher inductive type (circle) encoding:
type S1Action<R> = {
  base: R;                       // point constructor
  loop: (r: R) => R;             // path constructor: r ~ loop(r)
};
function foldCircle<R>(action: S1Action<R>): (s1: 'base') => R {
  return () => action.base;  // simplified
}
```

### Common Pitfalls

1. **Univalence does not compute without cubical foundations:** In plain HoTT, `ua` is an axiom and normalizing terms with it produces stuck terms. Use cubical type theory for computational univalence.
2. **Propositional vs definitional equality:** Many equalities provable propositionally are not definitional. Path algebra proof obligations can be tedious.
3. **Coherence conditions for HITs:** HIT eliminators must respect path constructors, requiring dependent path arguments that are easy to get wrong.
4. **Universe is NOT a set:** Univalence makes U have non-trivial paths (automorphisms). Code assuming unique type representations will break.
5. **Propositional truncation loses information:** Once truncated, witnesses cannot be recovered except under the elimination principle's restriction to propositions.

### Cross-References

- Generalizes: MLTT (adds univalence + HITs), set-level mathematics (types are infinity-groupoids), groupoids (infinity-groupoid generalization).
- Specializes: Internal language of (infinity,1)-toposes. Cubical Type Theory provides computational refinement.
- Related: Cubical Type Theory, Dependent Types (MLTT), Modal Type Theory, System F.

---

## 8. Cubical Type Theory

### Formal Foundations

Cubical Type Theory (CTT) extends MLTT with primitives for n-dimensional cubes, providing a **computational** interpretation of HoTT where univalence computes (not axiomatic).

**1. Interval type I = [0,1].** A primitive with endpoints `0, 1 : I` and operations forming a De Morgan algebra (CCHM variant):
- `min (r /\ s)`, `max (r \/ s) : I -> I -> I`
- `neg (~r) : I -> I` (CCHM only, absent in cartesian cubical)
- I is NOT a type in the usual sense: one cannot eliminate on it.

**2. Face formulas (F).** Propositions from interval constraints:
- `(r = 0)`, `(r = 1) : F`
- `phi /\ psi`, `phi \/ psi : F`
- Describe boundaries of cubes.

**3. Path types** as functions from the interval:
```
Path A a b  =  { p : I -> A | p(0) = a, p(1) = b }
```
Dependent paths: `PathP (i:I |- A(i)) a b` for A varying over the interval.

**4. Kan operations** (composition and transport): The key computational content.

```
comp^i A [phi -> u] a0 : A(1)
```
Given a line of types `A : I -> Type`, a partial tube `u` defined on face `phi`, and a base `a0 : A(0)` agreeing with `u` at `i=0`, produces an element of `A(1)`. This is the **computational** analogue of HoTT's transport + filling.

**5. Glue types** provide computational univalence:
```
Glue A [phi -> (B, equiv)] : Type
```
At face phi, the glue type equals B (via the equivalence); elsewhere it equals A. Univalence is then **derived, not axiomatized**, by constructing appropriate Glue types.

**Cubical univalence (computational, not axiomatic):** `ua` and `transport` compute on canonical forms, eliminating stuck terms. In Cubical Agda, `ua equiv i` reduces to a Glue type.

**Key distinction: CCHM vs Cartesian cubical.**
- **CCHM (Cohen-Coquand-Huber-Mortberg):** Interval has De Morgan algebra (includes `~i`). Implemented in Cubical Agda.
- **Cartesian cubical (Angiuli-Harper-Licata):** Interval has bounded distributive lattice (no negation). Different composition rules.

### Core Algorithm

```typescript
// Core: Kan composition (the central computational primitive)
interface KanComposition {
  // comp^i A [phi -> u] a0
  // A : I -> Type (line of types)
  // phi : Face (face formula)
  // u : (i: I) -> Partial phi (A i) (partial tube)
  // a0 : A(0) (base, agreeing with u at i=0)
  // result : A(1)
  comp(dimension: string, typeFamily: (i: I) => Type,
       face: Face, tube: PartialTube, base: Value): Value;
}

// Transport: special case of comp with constant partial tube
function transport(A: (i: I) => Type, a: Value): Value {
  return comp('i', A, emptyFace, emptyTube, a);
}

// Path application:
function pathApp(p: PathValue, r: IValue): Value {
  // p : Path A a b, r : I
  // returns p(r) : A, with p(0) = a, p(1) = b
  return evaluate(p.body, extend(p.env, p.ivar, r));
}

// Glue type evaluation (implements computational univalence):
function evalGlue(A: Value, face: Face, equivSys: PartialEquiv): Value {
  if (face.isTrue()) return equivSys.getType(); // on face, equals B
  if (face.isFalse()) return A;                 // off face, equals A
  return { tag: 'VGlue', base: A, face, system: equivSys };
}

// Unglue: extraction from Glue types
function unglue(face: Face, equivSys: PartialEquiv, gel: Value): Value {
  if (face.isTrue()) return applyEquiv(equivSys.getEquiv(), gel);
  return gel; // already base type
}
```

### Pragmatic Implementation

```typescript
// Cubical concepts in TS: interval-parameterized types as function types

// Path as a function from a "parameter" with boundary constraints:
interface CPath<A, a extends A, b extends A> {
  at(t: number): A;        // t in [0,1]
  readonly start: A;       // at(0) = a
  readonly end: A;         // at(1) = b
}

// Interpolation (continuous paths in practice):
function linearPath(a: number, b: number): CPath<number, typeof a, typeof b> {
  return {
    at: (t: number) => a * (1 - t) + b * t,
    start: a,
    end: b,
  };
}

// Transport pattern: migrate data along a type-level path
function transportRecord<K extends string, V1, V2>(
  path: (t: number) => Record<K, unknown>,
  data: Record<K, V1>
): Record<K, V2> { /* ... */ }

// Kan composition pattern: fill in a cube from its boundary
interface CubeBuilder<A> {
  face(dim: number, endpoint: 0 | 1, value: A): CubeBuilder<A>;
  fill(): A; // compute interior from boundary data
}
```

### Common Pitfalls

1. **Kan composition is expensive:** Each composition in a nested type triggers sub-compositions recursively. Deeply nested types cause severe performance issues in Cubical Agda.
2. **Face formula satisfiability:** Checking consistency of face formulas is non-trivial; incorrect handling leads to spurious type errors.
3. **Regularity:** Transport in constant types should be the identity, but some CTT formulations do not guarantee this definitionally.
4. **Boundary matching:** When constructing `<i>t`, the system must verify `t[i:=0]` and `t[i:=1]` match declared endpoints. Off-by-one errors in boundary conditions are common.
5. **CCHM vs cartesian:** Different interval algebras. Code for one variant may not work in the other. The `neg (~i)` operation exists only in CCHM.
6. **Higher coherences:** Elimination into non-truncated types requires coherence conditions for path constructors of HITs, which can be extremely difficult to construct.

### Cross-References

- Generalizes: MLTT (adds interval + Kan operations), Axiomatic HoTT (proves what HoTT postulates, with computation), Extensional type theory (extensional principles with decidable checking).
- Specializes: Internal language of cubical (infinity,1)-toposes, presheaf models on cube categories.
- Related: HoTT & Univalence, Dependent Types (MLTT), Modal Type Theory, Cubical Agda (Vezzosi-Mortberg-Abel 2019).

---

## 9. Quotient Types & QIITs

### Formal Foundations

**Quotient types** allow equating terms at the type level: given `A : Type` and `R : A -> A -> Prop` (equivalence relation), the quotient `A/R` identifies R-related elements.

**Components:**
- **Constructor:** `q : A -> A/R` (quotient map).
- **Equality:** `q(a) = q(b)` whenever `R(a, b)`.
- **Eliminator:** To define `f : A/R -> B`, provide `g : A -> B` such that `R(a,b)` implies `g(a) = g(b)` (well-definedness / respect).
- **Set-truncation:** `A/R` is a set (UIP holds internally for quotients).

**Quotient Inductive Types (QITs):** Inductive types with equality constructors. Example -- integers as a QIT:
- Point constructors: `diff : Nat -> Nat -> Int` (representing a - b).
- Path constructor: `quot : diff(a,b) = diff(a+1, b+1)`.
- This ensures `(3,1)` and `(4,2)` are identified as the same integer 2.

**Quotient Inductive-Inductive Types (QIITs):** Multiple mutually defined types where later types can depend on earlier ones, with both point and path constructors across all types. Canonical example: type theory in type theory.

```
data Ctx : Type
data Ty  : Ctx -> Type      -- types depend on contexts
data Sub : Ctx -> Ctx -> Type -- substitutions

-- Point constructors:
nil  : Ctx
ext  : (Gamma : Ctx) -> Ty Gamma -> Ctx
id   : Sub Gamma Gamma
comp : Sub Delta Theta -> Sub Gamma Delta -> Sub Gamma Theta
pi   : Ty Gamma -> Ty (ext Gamma A) -> Ty Gamma

-- Path constructors (equations):
id-left  : comp id s = s
id-right : comp s id = s
assoc    : comp (comp t s) r = comp t (comp s r)
```

**2-HITs** (higher inductive types with path-of-path constructors): Constructors for 2-cells (homotopies). Example: the torus as a 2-HIT with point, two loops, and a surface filler.

### Core Algorithm

```typescript
// Quotient type implementation with normalization:
class Quotient<A, R extends (a: A, b: A) => boolean> {
  private representative: Map<string, A> = new Map();

  constructor(
    private equiv: R,
    private normalize: (a: A) => A,  // canonical representative
    private hash: (a: A) => string
  ) {}

  inject(a: A): QuotientElement<A> {
    const norm = this.normalize(a);
    const key = this.hash(norm);
    if (!this.representative.has(key)) this.representative.set(key, norm);
    return { repr: this.representative.get(key)!, _quotient: this };
  }

  // Eliminator: must verify respect condition
  elim<B>(f: (a: A) => B, respect: (a1: A, a2: A) => void): (q: QuotientElement<A>) => B {
    return (q) => f(q.repr);
  }
}

// QIIT: integers as Nat pairs mod equivalence
// diff(a, b) ~ diff(a+1, b+1)
function normalizeInt(a: number, b: number): [number, number] {
  const min = Math.min(a, b);
  return [a - min, b - min]; // canonical: at least one component is 0
}
```

### Pragmatic Implementation

```typescript
// Quotient pattern in TS: normalized representatives

// Integers as quotient of Nat x Nat:
class ZInt {
  readonly pos: number;
  readonly neg: number;
  constructor(pos: number, neg: number) {
    // Normalize: canonical representative
    const min = Math.min(pos, neg);
    this.pos = pos - min;
    this.neg = neg - min;
  }
  equals(other: ZInt): boolean {
    return this.pos === other.pos && this.neg === other.neg;
  }
  toNumber(): number { return this.pos - this.neg; }
}
// new ZInt(3, 1).equals(new ZInt(4, 2)) === true (both represent 2)

// Rational numbers as quotient of Int x NonZeroInt:
class QRat {
  readonly num: number;
  readonly den: number;
  constructor(num: number, den: number) {
    const g = gcd(Math.abs(num), Math.abs(den));
    const sign = den < 0 ? -1 : 1;
    this.num = sign * num / g;
    this.den = sign * den / g;
  }
}

// QIIT-style: type theory syntax with equations
interface TySyntax {
  ctx: CtxNode[];
  ty: TyNode[];
  sub: SubNode[];
  // Equations enforced by normalization:
  // comp(id, s) normalizes to s, etc.
}
```

### Common Pitfalls

1. **Forgetting to normalize:** If quotient values are not always in canonical form, equality checks fail for equivalent values.
2. **Non-respect:** Defining operations on quotients that do not respect the equivalence relation leads to inconsistency.
3. **Normalization performance:** For complex quotients (polynomials mod an ideal), normalization can be expensive. Consider lazy normalization or caching.
4. **Effectiveness assumption:** In constructive math, quotients are not always effective (`q(a) = q(b)` does not imply extracting a witness of `R(a,b)`). In HoTT, set quotients are effective.
5. **Forgetting truncation:** In HoTT, not truncating a HIT to a set gives a type with unwanted higher-dimensional structure. QIITs require explicit set-truncation.
6. **Strict positivity:** QIIT constructors with negative occurrences of the defined type lead to inconsistency.

### Cross-References

- Generalizes: simple quotient sets (A/R), inductive types (QIITs without equality constructors = inductive types), inductive-inductive types.
- Specializes: Higher Inductive Types (QITs are set-truncated HITs), Higher Inductive-Inductive Types (QIITs are set-truncated HIITs).
- Related: HoTT, Setoid Type Theory, Inductive Types & W-Types, GADTs, Algebraic Data Types.

---

## 10. Polarity & Call-by-Push-Value (CBPV)

### Formal Foundations

CBPV (Levy 1999/2004, 2025 Alonzo Church Award) is a polarized calculus distinguishing two syntactic categories: **values** (positive, +) and **computations** (negative, -). Core insight: "**values are, computations do.**"

**Two typing judgements:**
1. `Gamma |-_v V : A` (value V has value type A)
2. `Gamma |-_c M : B` (computation M has computation type B)

**Value types (A):**
- Ground types, product types `A1 x A2`, sum types `A1 + A2`
- **Thunk types `U(B)`**: a value wrapping a suspended computation of type B

**Computation types (B):**
- **Returner types `F(A)`**: a computation that may perform effects and return a value of type A
- Function types `A -> B`: computation accepting a value, producing a computation
- Product computation types `B1 & B2`: lazy pairs of computations

**The adjunction U -| F (thunk -| return):**
- `U` shifts computation to value: if B is a computation type, `U(B)` is a value type. Intro: `thunk M`. Elim: `force V`.
- `F` shifts value to computation: if A is a value type, `F(A)` is a computation type. Intro: `return V`. Elim: `M to x. N` (bind/sequencing).

**The comonad/monad decomposition:**
- **CBV = F . U composite**: CBV types are value types, CBV computations are wrapped in F(U(-)).
- **CBN = U . F composite**: CBN types are thunk types, CBN computations produce returns.
- Moggi's monadic metalanguage: the monad is `T = UF` on value types.

**Embedding translations:**
- CBV translation: `[A -> B]_v = U(F[A]_v -> F[B]_v)`, function values are thunked computations.
- CBN translation: `[A -> B]_n = U([A]_n -> [B]_n)`, everything is thunked.

### Core Algorithm

```typescript
// CBPV type checker:
type ValType =
  | { tag: 'Ground'; name: string }
  | { tag: 'Prod'; fst: ValType; snd: ValType }
  | { tag: 'Sum'; left: ValType; right: ValType }
  | { tag: 'Thunk'; comp: CompType };  // U(B)

type CompType =
  | { tag: 'Return'; val: ValType }     // F(A)
  | { tag: 'Arrow'; param: ValType; body: CompType }  // A -> B
  | { tag: 'CompProd'; fst: CompType; snd: CompType }; // B1 & B2

// Value typing: synthesizes a ValType
function checkVal(ctx: Context, v: ValTerm): ValType { /* ... */ }

// Computation typing: synthesizes a CompType
function checkComp(ctx: Context, m: CompTerm): CompType {
  switch (m.tag) {
    case 'Return': {
      const a = checkVal(ctx, m.value);
      return { tag: 'Return', val: a };
    }
    case 'Force': {
      const thunkTy = checkVal(ctx, m.thunk);
      if (thunkTy.tag !== 'Thunk') throw new Error('Expected thunk type');
      return thunkTy.comp;
    }
    case 'Bind': {
      // M to x. N : sequencing, eliminates F(A)
      const mTy = checkComp(ctx, m.comp);
      if (mTy.tag !== 'Return') throw new Error('Expected returner type F(A)');
      const extCtx = extend(ctx, m.var, mTy.val);
      return checkComp(extCtx, m.body);
    }
    case 'Lambda': {
      const bodyTy = checkComp(extend(ctx, m.param, m.paramType), m.body);
      return { tag: 'Arrow', param: m.paramType, body: bodyTy };
    }
    case 'App': {
      const fTy = checkComp(ctx, m.func);
      if (fTy.tag !== 'Arrow') throw new Error('Expected function computation');
      const aTy = checkVal(ctx, m.arg);
      assertEq(fTy.param, aTy);
      return fTy.body;
    }
  }
}
```

### Pragmatic Implementation

```typescript
// CBPV in TypeScript: values vs computations

// Thunk: U(B) -- a suspended computation
type Thunk<B> = { readonly force: () => B };
const thunk = <B>(comp: () => B): Thunk<B> => ({ force: comp });

// Return: F(A) -- a computation producing a value (possibly with effects)
type Comp<A> = { readonly run: () => A };
const ret = <A>(a: A): Comp<A> => ({ run: () => a });
const bind = <A, B>(m: Comp<A>, f: (a: A) => Comp<B>): Comp<B> =>
  ({ run: () => f(m.run()).run() });

// CBV embedding (F . U): function values are thunked computations
type CBVFun<A, B> = Thunk<Comp<(a: A) => Comp<B>>>;

// CBN embedding (U . F): everything is thunked
type CBNTerm<A> = Thunk<Comp<A>>;

// Effect tracking via computation types:
type IO<A> = Comp<A>;                    // side-effecting computation
type Pure<A> = A;                        // pure value (no effects)
type Effectful<A> = Thunk<IO<A>>;        // suspended effectful computation
```

### Common Pitfalls

1. **Forgetting to force thunks:** `Thunk<Comp<A>>` requires two layers of unwrapping: force, then run.
2. **Accidental eager evaluation:** In a strict language like TS, `thunk(() => expr)` is needed; plain `expr` evaluates immediately, defeating the purpose.
3. **F(A) vs U(B) confusion:** F goes value -> computation, U goes computation -> value. Getting the direction wrong breaks the polarity discipline.
4. **Breaking bind laws:** Especially associativity when implementing bind with error short-circuiting.
5. **Hiding effects:** CBPV's power comes from making effects visible in computation types. Hiding effects in value-returning functions defeats the purpose.
6. **Overusing thunks in strict languages:** In TypeScript (already CBV), only thunk computations that genuinely need deferral.

### Cross-References

- Generalizes: Moggi's monadic metalanguage (monad = UF), CBV lambda calculus (via F/return), CBN lambda calculus (via U/thunk).
- Specializes: Adjoint logic (CBPV is F -| U adjunction), Polarized lambda calculus (canonical example).
- Related: Monads & Kleisli Composition, Algebraic Effects & Handlers, Linear Logic, Continuations & CPS, Evaluation Strategy Interaction.

---

## 11. Totality, Termination Checking & Productivity

### Formal Foundations

**Totality** in type theory requires every function to be defined on all inputs and to produce a result. Two dual aspects:

**Termination** (for inductive data): every recursive call provably reaches a base case.

**Productivity** (for coinductive codata): every observation (destructor) produces the next piece of output in finite time.

**Three main termination-checking approaches:**

**1. Structural recursion (decreasing argument, guard condition):** Recursive calls must be on structurally smaller arguments. In Coq: `fix f (x : T) := ... f y ...` requires y to be a strict subterm of x. Enforced by Agda and Coq's pattern matcher.

**2. Size-change principle (Lee-Jones-Ben-Amram 2001, POPL):** Analyze all possible call sequences by building **size-change graphs**: directed graphs where nodes are function parameters and edges indicate "this parameter is strictly smaller" or "non-increasing." A program terminates if every infinite call sequence would force some parameter to decrease infinitely -- checked via a finite graph closure algorithm. Decidable. Sound but not complete.

**3. Sized types (Abel 2004-2012):** Annotate types with ordinal sizes. `Nat^{i}` means a natural number of size < i. Recursive calls require the size argument to decrease: `f : Nat^{i} -> Nat` can call `f : Nat^{j} -> Nat` for j < i. More expressive than structural recursion; handles nested and mutual recursion. Known edge-case unsoundness issues in Agda's sized types (issue #1201).

**Guardedness for corecursion:** Coinductive producers must have recursive calls guarded by a constructor. In Haskell: `ones = 1 : ones` is guarded (`:` wraps the recursive call). `bad = bad` is not productive. Coq's `CoFixpoint` enforces this syntactically.

**Copatterns (Abel-Pientka 2013):** Dual to pattern matching on constructors, copatterns define coinductive objects by observations. Define a stream by specifying what `head` and `tail` produce, with guardedness checked on the copattern structure.

**Key results:**
- Termination checking is undecidable in general (reduces to the halting problem).
- Size-change termination is PSPACE-complete (Lee-Jones-Ben-Amram 2001).
- Structural recursion checking is decidable and polynomial.
- Total languages (Agda, Coq without axioms) are not Turing-complete but cover all practically needed programs via ordinal recursion.
- **Filter on streams is not provably productive:** `filter p s` may diverge if the predicate is never satisfied.

### Core Algorithm

```typescript
// Size-change termination checker:
interface SizeChangeGraph {
  params: string[];
  edges: Array<{
    from: string;
    to: string;
    relation: 'strict' | 'nonstrict';  // < or <=
  }>;
}

// Build size-change graphs from call sites:
function buildSCG(callSites: CallSite[]): SizeChangeGraph[] { /* ... */ }

// Check termination: compute closure of graph compositions,
// verify every idempotent graph in the closure has a strict decrease on the diagonal.
function checkTermination(graphs: SizeChangeGraph[]): boolean {
  const closure = computeClosure(graphs); // fixed-point of graph composition
  for (const g of closure) {
    if (isIdempotent(g)) {
      // Every idempotent graph must have at least one
      // strict self-edge (param_i -->strict--> param_i)
      const hasStrictSelfEdge = g.edges.some(
        e => e.from === e.to && e.relation === 'strict'
      );
      if (!hasStrictSelfEdge) return false; // potential non-termination
    }
  }
  return true;
}

// Structural recursion check (simplified):
function isStructurallySmaller(arg: Term, param: Term): boolean {
  // arg must be a strict subterm of param (e.g., n in Succ(n))
  return isSubterm(arg, param) && arg !== param;
}

// Guardedness check for corecursion:
function isGuarded(body: CoTerm, corecVar: string): boolean {
  // Every occurrence of corecVar must be under a constructor
  return allOccurrencesGuardedByConstructor(body, corecVar);
}
```

### Pragmatic Implementation

```typescript
// Structural recursion in TS:
type Nat = { tag: 'Zero' } | { tag: 'Succ'; pred: Nat };

// Total: structurally decreasing on n
function add(m: Nat, n: Nat): Nat {
  switch (n.tag) {
    case 'Zero': return m;
    case 'Succ': return { tag: 'Succ', pred: add(m, n.pred) }; // n.pred < n
  }
}

// Corecursion with copatterns (stream):
interface Stream<A> { head: A; tail: Stream<A>; }

// Guarded: constructor wraps recursive call
function nats(n: number): Stream<number> {
  return { head: n, tail: nats(n + 1) }; // guarded by { head, tail } constructor
}

// Fuel-based bounded recursion (escape hatch for non-structural algorithms):
function collatz(n: number, fuel: number): number[] {
  if (fuel <= 0) return []; // bounded termination
  if (n === 1) return [1];
  return [n, ...collatz(n % 2 === 0 ? n / 2 : 3 * n + 1, fuel - 1)];
}

// Sized types approximation: track depth via generics
type Sized<N extends number, A> = N extends 0 ? never : A;
```

### Common Pitfalls

1. **Confusing termination and productivity:** Termination is for functions consuming inductive data; productivity is for functions producing coinductive codata. Wrong check = rejection of valid programs.
2. **Guardedness is fragile:** Abstracting a guarded corecursive call into a helper function breaks the syntactic guard condition (Coq's well-known "guardedness through functions" problem).
3. **Sized types with dependent types:** Size annotations interact with universe levels and definitional equality. Agda's sized types have known unsoundness in edge cases.
4. **Non-structural recursion:** Many natural algorithms (quicksort, Euclidean algorithm) are not structurally recursive. They require well-founded recursion proofs or accessibility predicates.
5. **Coinductive proofs require bisimulation, not induction:** Using induction on coinductive data is unsound.
6. **Filter on streams is not provably productive:** `filterStream` may diverge if the predicate is never satisfied -- this is fundamentally unprovable.

### Cross-References

- Generalizes: simple structural recursion (subsumed by size-change principle), syntactic guardedness (subsumed by sized types).
- Specializes: general recursion (totality restricts to terminating/productive subset), Turing completeness (total languages are not Turing-complete but cover all practically needed programs).
- Related: Inductive Types & W-Types, Coinductive Types & Copatterns, Dependent Types (MLTT), Well-Founded Recursion, Guarded Recursion & Clocks.

---

## 12. Two-Level Type Theory (2LTT) & Staged Compilation

### Formal Foundations

Two-Level Type Theory (Annenkov-Capriotti-Kraus-Sattler 2017; Kovacs 2022, 2024 ICFP) has two distinct levels: an **inner** (object/runtime) type theory and an **outer** (meta/compile-time) type theory, connected by a lifting operation.

**Two universe hierarchies:**
- Inner universes: `Set_0, Set_1, ...` (object types; may be HoTT with univalence)
- Outer universes: `SSet_0, SSet_1, ...` (strict sets, meta types; validate UIP)

**Judgement forms:**
```
Gamma |- A : Set_i      (inner type formation)
Gamma |- a : A           (inner term, A : Set_i)
Gamma |- B : SSet_j      (outer type formation)
Gamma |- b : B           (outer term, B : SSet_j)
```

**Key structural rules:**
1. **Lifting:** If `A : Set_i`, then `Lift(A) : SSet_i`. Internalizes inner type as outer type.
2. **Fibrancy:** An outer type `B : SSet` is fibrant if isomorphic to `Lift(A)` for some inner A.
3. **Outer theory validates UIP:** For all `p, q : Id_SSet(a, b)`, `p = q`.
4. **Inner theory may be extensional** (HoTT with univalence, HITs) or intensional.

**Staged compilation interpretation (Kovacs 2022):**
- **Meta level (outer/SSet):** Compile-time computation, types with stage annotation `Box(A)` (written `[]A`).
- **Object level (inner/Set):** Runtime types and terms.
- **Quote/splice:** `<t>` quotes an object term (lifting to meta), `~e` splices a meta expression (lowering to object code).

**Stage annotations:**
- `Box(A)` (or `[]A`) for meta-level (compile-time) types. A value of type `Box(A)` is a piece of *code* of type A, available at compile time.
- Object-level types are runtime types.

**Closure-free staging (Kovacs 2024):** 2LTT-based staging guarantees that generated code contains no closures (heap allocations for captured variables). All meta-level bindings are inlined or defunctionalized at staging time. This yields performance comparable to hand-written low-level code.

**Connection to MetaML:** MetaML (Taha-Sheard 2000) uses similar staging brackets `<e>` and splicing `~e`, but lacks the dependent type structure. 2LTT adds dependent types and a cleaner semantic foundation. MetaOCaml is the production implementation of MetaML-style staging.

**Connection to Agda 2LTT:** Agda experimentally supports two-level type theory via `--two-level` flag, with `SSet` as the strict outer universe.

### Core Algorithm

```typescript
// Two-level type checker: separate meta and object levels

type Level = 'meta' | 'object';

type MetaType =
  | { tag: 'SSet'; level: number }
  | { tag: 'Box'; inner: ObjectType }    // []A: code of type A
  | { tag: 'MetaArrow'; param: MetaType; ret: MetaType }
  | { tag: 'Lift'; inner: ObjectType };  // Lift(A)

type ObjectType =
  | { tag: 'Set'; level: number }
  | { tag: 'ObjArrow'; param: ObjectType; ret: ObjectType }
  | { tag: 'ObjPi'; param: ObjectType; body: ObjectType };

type StagedTerm =
  | { tag: 'MetaVar'; name: string }
  | { tag: 'ObjVar'; name: string }
  | { tag: 'Quote'; term: StagedTerm }      // <t> : Box(A)
  | { tag: 'Splice'; term: StagedTerm }     // ~e : A (from Box(A))
  | { tag: 'MetaLam'; param: string; body: StagedTerm }
  | { tag: 'ObjLam'; param: string; body: StagedTerm }
  | { tag: 'MetaApp'; func: StagedTerm; arg: StagedTerm }
  | { tag: 'ObjApp'; func: StagedTerm; arg: StagedTerm };

function checkStaged(ctx: StagedCtx, term: StagedTerm, level: Level): StagedType {
  switch (term.tag) {
    case 'Quote': {
      // <t> lifts object term to meta level
      if (level !== 'meta') throw new Error('Quote only at meta level');
      const innerTy = checkStaged(ctx, term.term, 'object');
      return { tag: 'Box', inner: innerTy as ObjectType };
    }
    case 'Splice': {
      // ~e lowers meta term to object level
      if (level !== 'object') throw new Error('Splice only at object level');
      const metaTy = checkStaged(ctx, term.term, 'meta');
      if (metaTy.tag !== 'Box') throw new Error('Splice requires Box type');
      return metaTy.inner;
    }
    // ... standard checking for lambdas, applications at each level ...
  }
}

// Staging evaluator: run meta-level, produce object code
function stage(env: MetaEnv, term: StagedTerm): ObjectCode {
  switch (term.tag) {
    case 'Quote': return { tag: 'Code', body: stage(env, term.term) };
    case 'Splice': {
      const code = evalMeta(env, term.term);
      if (code.tag !== 'Code') throw new Error('Splice: expected code');
      return code.body;
    }
    case 'MetaApp': {
      const f = evalMeta(env, term.func);
      const a = evalMeta(env, term.arg);
      return applyMeta(f, a);
    }
    case 'ObjLam': return { tag: 'ObjLam', param: term.param, body: stage(env, term.body) };
    case 'ObjApp': return { tag: 'ObjApp',
      func: stage(env, term.func), arg: stage(env, term.arg) };
    // Meta-level computation is executed; object-level code is preserved
  }
}
```

### Pragmatic Implementation

```typescript
// TypeScript approximation of 2LTT staging:
// TS compile-time = type level (meta), runtime = value level (object)

// Meta-level (compile-time) type computation:
type Power<B extends string, E extends number, Acc extends string = B> =
  E extends 1 ? Acc
  : Power<B, Decr<E>, `${Acc} * ${B}`>;
// Power<'x', 3> = 'x * x * x' (computed at compile time)

// Staged function generation (runtime code from compile-time decisions):
function makeAccessor<K extends string>(key: K) {
  // Meta-level: key is known at "compile time" (call site)
  // Object-level: returned function runs at runtime
  return <T extends Record<K, unknown>>(obj: T): T[K] => obj[key];
}
const getName = makeAccessor('name'); // meta-level specialization
getName({ name: 'Alice' });           // object-level execution: 'Alice'

// Template literal types as compile-time code generation:
type Route<P extends string> =
  P extends `${infer _}:${infer Param}/${infer Rest}`
    ? { [K in Param | keyof Route<`/${Rest}`>]: string }
    : P extends `${infer _}:${infer Param}`
      ? { [K in Param]: string }
      : {};

// SQL query builder with compile-time type safety:
function sql<T extends string>(
  query: T
): (params: ExtractParams<T>) => Promise<unknown> {
  // T is meta-level (known at type-check time)
  // The returned function is object-level (runs at runtime)
  return (params) => executeQuery(query, params);
}
```

### Common Pitfalls

1. **Accidental code duplication:** If splice `~e` appears under a meta-level lambda called multiple times, object code is duplicated. Use object-level let-bindings to share.
2. **Level confusion:** Mixing meta and object variables leads to staging errors. A meta-level variable cannot appear in generated object code (unbound at runtime).
3. **Scope extrusion:** A quoted variable `<x>` can only be spliced in a scope where x is bound. Escaping the scope produces ill-formed code.
4. **Non-terminating meta programs:** If meta-level computation diverges, staging never completes -- this hangs the compiler.
5. **Effects at the wrong level:** Side effects in meta-level code execute at compile time, not runtime. A meta-level `print()` fires during compilation.
6. **Closure capture in generated code:** Object-level lambdas capturing meta-level values require those values to be serializable into generated code. Complex meta-level structures may not be embeddable.

### Cross-References

- Generalizes: Multi-stage programming (MetaML/MetaOCaml -- 2LTT adds dependent types), Template Haskell (2LTT adds type safety), Partial evaluation (staging-by-evaluation subsumes binding-time analysis).
- Specializes: General dependent type theory (MLTT -- 2LTT adds two-level structure), Modal type theory (2LTT as a specific modal discipline with Lift as modality).
- Related: Normalization by Evaluation (NbE), Defunctionalization, Closure Conversion, Agda `--two-level`.
