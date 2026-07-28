# Type Inference & Checking Algorithms

*Sources: Hindley_Milner_Type_System.json, Bidirectional_Type_Checking.json, Constraint_Based_Type_Inference.json, Local_Type_Inference.json, Complete_Easy_Bidirectional_Higher_Rank.json, Algebraic_Subtyping.json, Algebraic_Subtyping_Extensions.json, Unification_Algorithms.json, Elaboration_Metavariable_Solving.json*

---

## 1. Hindley-Milner Type System & Algorithm W

### Formal Foundations

**Syntax.** Monotypes: `tau ::= alpha | tau -> tau | C tau_1 ... tau_n`. Type schemes: `sigma ::= tau | forall alpha. sigma`. A typing environment Gamma maps variables to type schemes. The key judgement form is `Gamma |- e : sigma`.

**Typing Rules.**

```
(Var)   (x : sigma) in Gamma    tau = inst(sigma)
        ───────────────────────────────────────────
        Gamma |- x : tau

(App)   Gamma |- e1 : tau1 -> tau2    Gamma |- e2 : tau1
        ─────────────────────────────────────────────────
        Gamma |- e1 e2 : tau2

(Abs)   Gamma, x:tau1 |- e : tau2
        ─────────────────────────────────
        Gamma |- lambda x. e : tau1 -> tau2

(Let)   Gamma |- e1 : sigma    Gamma, x:sigma |- e2 : tau
        ───────────────────────────────────────────────────
        Gamma |- let x = e1 in e2 : tau

(Inst)  Gamma |- e : forall alpha. sigma
        ─────────────────────────────────
        Gamma |- e : sigma[alpha := tau]

(Gen)   Gamma |- e : sigma    alpha not in FV(Gamma)
        ─────────────────────────────────────────────
        Gamma |- e : forall alpha. sigma
```

**Principal Type Theorem (Damas-Milner 1982).** Every typeable expression has a unique most general (principal) type scheme, and Algorithm W computes it. The system is predicative: quantifiers range only over monotypes.

**Complexity.** Type inference is DEXPTIME-complete in the worst case (Mairson 1990; Kfoury, Tiuryn & Urzyczyn 1990). The exponential blowup comes from let-polymorphism: each let-binding can double the size of inferred types through instantiation. In practice, Algorithm W runs in near-linear time O(n * alpha(n)) on realistic programs (where alpha is the inverse Ackermann function from union-find).

**Key metatheoretic properties.** Soundness (Damas 1985): if Algorithm W succeeds, the inferred type is valid in the declarative system. Completeness: if an expression is typeable, Algorithm W finds its principal type. Subject reduction: well-typed terms remain well-typed under reduction. The system is a restriction of System F to rank-1 polymorphism, making inference decidable.

### Core Algorithm

Algorithm W performs bottom-up type inference, producing a substitution and a type for each expression.

```typescript
// Algorithm W — Hindley-Milner type inference
// Types
type Ty = { tag: 'TVar'; name: string }
        | { tag: 'TFun'; a: Ty; b: Ty }
        | { tag: 'TCon'; c: string; args: Ty[] };
type Scheme = { forall: string[]; body: Ty };
type Sub = Map<string, Ty>;
type Env = Map<string, Scheme>;

let _n = 0;
const fresh = (): Ty => ({ tag: 'TVar', name: `t${_n++}` });

function apply(s: Sub, t: Ty): Ty {
  if (t.tag === 'TVar') return s.get(t.name) ?? t;
  if (t.tag === 'TFun') return { tag: 'TFun', a: apply(s, t.a), b: apply(s, t.b) };
  return { tag: 'TCon', c: t.c, args: t.args.map(a => apply(s, a)) };
}

function compose(s1: Sub, s2: Sub): Sub {
  // "apply s1 first, then s2"
  const r = new Map<string, Ty>();
  for (const [k, v] of s1) r.set(k, apply(s2, v));
  for (const [k, v] of s2) if (!r.has(k)) r.set(k, v);
  return r;
}

function fv(t: Ty): Set<string> {
  if (t.tag === 'TVar') return new Set([t.name]);
  if (t.tag === 'TFun') return new Set([...fv(t.a), ...fv(t.b)]);
  return t.args.reduce((s, a) => new Set([...s, ...fv(a)]), new Set<string>());
}

function unify(a: Ty, b: Ty): Sub {
  if (a.tag === 'TVar' && b.tag === 'TVar' && a.name === b.name) return new Map();
  if (a.tag === 'TVar') {
    if (fv(b).has(a.name)) throw Error(`occurs check: ${a.name} in ${JSON.stringify(b)}`);
    return new Map([[a.name, b]]);
  }
  if (b.tag === 'TVar') return unify(b, a);
  if (a.tag === 'TFun' && b.tag === 'TFun') {
    const s1 = unify(a.a, b.a);
    return compose(s1, unify(apply(s1, a.b), apply(s1, b.b)));
  }
  if (a.tag === 'TCon' && b.tag === 'TCon' && a.c === b.c && a.args.length === b.args.length)
    return a.args.reduce<Sub>((s, _, i) =>
      compose(s, unify(apply(s, a.args[i]), apply(s, b.args[i]))), new Map());
  throw Error(`cannot unify`);
}

function inst(sc: Scheme): Ty {
  const m = new Map<string, Ty>();
  sc.forall.forEach(v => m.set(v, fresh()));
  return apply(m, sc.body);
}

function gen(env: Env, t: Ty): Scheme {
  const envFV = new Set<string>();
  for (const sc of env.values()) for (const v of fv(sc.body)) if (!sc.forall.includes(v)) envFV.add(v);
  return { forall: [...fv(t)].filter(v => !envFV.has(v)), body: t };
}

function applyEnv(s: Sub, env: Env): Env {
  return new Map([...env].map(([k, sc]) => [k, { forall: sc.forall, body: apply(s, sc.body) }]));
}

type Expr = { tag: 'Var'; x: string }
          | { tag: 'App'; f: Expr; a: Expr }
          | { tag: 'Lam'; x: string; b: Expr }
          | { tag: 'Let'; x: string; v: Expr; b: Expr };

function W(env: Env, e: Expr): [Sub, Ty] {
  if (e.tag === 'Var')  return [new Map(), inst(env.get(e.x)!)];
  if (e.tag === 'Lam')  {
    const tv = fresh();
    const [s, t] = W(new Map([...env, [e.x, { forall: [], body: tv }]]), e.b);
    return [s, { tag: 'TFun', a: apply(s, tv), b: t }];
  }
  if (e.tag === 'App')  {
    const [s1, t1] = W(env, e.f);
    const [s2, t2] = W(applyEnv(s1, env), e.a);
    const tv = fresh();
    const s3 = unify(apply(s2, t1), { tag: 'TFun', a: t2, b: tv });
    return [compose(s1, compose(s2, s3)), apply(s3, tv)];
  }
  // Let
  const [s1, t1] = W(env, e.v);
  const env1 = applyEnv(s1, env);
  const sc = gen(env1, t1);
  const [s2, t2] = W(new Map([...env1, [e.x, sc]]), e.b);
  return [compose(s1, s2), t2];
}
```

**Algorithm J variant.** Uses mutable union-find instead of explicit substitution maps, yielding better practical performance. Each type variable is a node in a union-find structure; `unify` merges equivalence classes. This avoids repeated substitution application and achieves near-linear time via path compression and union-by-rank.

**Kiselyov levels trick.** Instead of computing `FV(Gamma)` at each generalization point (which is O(|Gamma|)), assign each type variable a *level* indicating the let-nesting depth at which it was created. Generalize all variables whose level exceeds the current let-depth. This reduces generalization to O(|FV(t)|), a substantial improvement for large environments.

### Pragmatic Implementation

- **Union-find (Algorithm J):** Replace `Sub` with a mutable union-find. `unify` becomes O(alpha(n)) per call. `apply` becomes `find` (path-compressed lookup). This is what production implementations (OCaml, GHC) use.
- **Level-based generalization:** Track a global `current_level` counter. Increment on entering a let-binding, decrement on exit. Fresh variables get the current level. At generalization, generalize all variables with `level > current_level`. Avoids the expensive `FV(Gamma)` traversal.
- **Persistent environments:** Use immutable/persistent maps for `Env` to avoid deep-copying on extension. Functional red-black trees or HAMTs work well.
- **Error reporting:** During unification, maintain a stack of "reasons" (which rule triggered the unification, which source locations) to produce human-readable error messages tracing the conflict back to source.
- **Incremental inference:** For IDE support, cache inference results per top-level binding and invalidate only when dependencies change.

### Common Pitfalls

1. **Wrong substitution composition order.** `compose(s1, s2)` must apply `s2` to the range of `s1`, then union. Swapping this produces silently wrong types.
2. **Missing occurs check.** Without it, `t ~ t -> t` produces an infinite type, causing non-termination in downstream processing.
3. **Missing value restriction.** In languages with mutation (ML), generalizing the type of `ref []` to `forall a. ref (list a)` is unsound. Only syntactic values should be generalized (Wright 1995).
4. **Variable capture during instantiation.** Fresh variables during `inst` must be globally unique. Reusing names across instantiations causes capture.
5. **Generalizing lambda-bound variables.** Only let-bound variables should be generalized; lambda-bound variables must remain monomorphic.
6. **Forgetting to apply substitution to the environment** between recursive W calls (especially in the App case).

### Cross-References

- Unification algorithm details: Section 7
- Extension to higher-rank polymorphism: Sections 2, 5
- Constraint-based reformulation: Section 3
- Extension with subtyping: Section 6
- Elaboration-based inference for dependent types: Section 8
- Theoretical foundations (System F, STLC): `01-theory-foundations.md` Sections 1-2

---

## 2. Bidirectional Type Checking

### Formal Foundations

**Core insight (Pierce-Turner 2000; Dunfield-Krishnaswami 2021 survey).** Split the typing judgement into two mutually recursive modes:

1. **Synthesis** (inference, "up" mode): `Gamma |- e => A` -- type A is an OUTPUT.
2. **Checking** ("down" mode): `Gamma |- e <= A` -- type A is an INPUT.

**Typing rules** for a simply-typed calculus with annotations:

```
(Var-Synth)   (x : A) in Gamma
              ─────────────────
              Gamma |- x => A

(Anno-Synth)  Gamma |- e <= A
              ─────────────────────
              Gamma |- (e : A) => A

(App-Synth)   Gamma |- e1 => A -> B    Gamma |- e2 <= A
              ──────────────────────────────────────────
              Gamma |- e1 e2 => B

(Lam-Check)   Gamma, x:A |- e <= B
              ──────────────────────────
              Gamma |- (lambda x. e) <= A -> B

(Sub)         Gamma |- e => A    A <: B
              ──────────────────────────
              Gamma |- e <= B
```

The classification principle: **introduction forms check** (lambdas receive type information from context), **elimination forms synthesize** (applications produce type information). Annotations bridge synthesis to checking.

**Subsumption rule (Sub).** The mode-switch rule allows any synthesizable term to be checked against a supertype. Without this rule, many well-typed terms are rejected. In systems without subtyping, `A <: B` is just `A = B`.

**Higher-rank extension (Dunfield-Krishnaswami 2013).** Additional rules for universal quantification:

```
(ForallI-Check)  Gamma, alpha |- e <= A
                 ──────────────────────────
                 Gamma |- e <= forall alpha. A

(ForallE-Synth)  Gamma |- e => forall alpha. A
                 ──────────────────────────────────
                 Gamma |- e => [alpha-hat/alpha]A    (alpha-hat fresh existential)
```

**Metatheory.** Soundness: the algorithmic system only derives typings valid in the declarative system. Completeness: every declaratively typeable term (with sufficient annotations) is typeable. For STLC, bidirectional checking is O(n) in term size. For higher-rank polymorphism, polynomial. The annotation burden is light: annotations needed only at top-level definitions, polymorphic function arguments, and GADT scrutinees (Pierce-Turner 2000).

### Core Algorithm

```typescript
type Type = { tag: 'Base'; name: string }
          | { tag: 'Arrow'; a: Type; b: Type }
          | { tag: 'Forall'; x: string; body: Type };
type Ctx = Map<string, Type>;

function synth(ctx: Ctx, e: Expr): Type {
  if (e.tag === 'Var')  return ctx.get(e.x) ?? (() => { throw Error(`unbound: ${e.x}`) })();
  if (e.tag === 'Ann')  { check(ctx, e.term, e.type); return e.type; }
  if (e.tag === 'App')  {
    const fn = synth(ctx, e.f);
    if (fn.tag !== 'Arrow') throw Error('expected function type');
    check(ctx, e.a, fn.a);
    return fn.b;
  }
  throw Error('cannot synthesize — add annotation');
}

function check(ctx: Ctx, e: Expr, t: Type): void {
  if (e.tag === 'Lam' && t.tag === 'Arrow') {
    check(new Map([...ctx, [e.x, t.a]]), e.b, t.b);
    return;
  }
  const inferred = synth(ctx, e);
  if (!typeEqual(inferred, t)) throw Error(`expected ${show(t)}, got ${show(inferred)}`);
}
```

**Key design decisions:**
- `synth` returns a `Type`; `check` returns `void` (accepts or throws).
- Lambdas in synthesis position are rejected unless annotated -- this is intentional, not a limitation.
- The fallback case in `check` synthesizes and compares -- this is the subsumption rule.

### Pragmatic Implementation

- **When to annotate:** Lambdas at rank >= 2 (e.g., passing `\x -> x` where `forall a. a -> a` is expected), let-bound polymorphic functions, GADT pattern match scrutinees.
- **Spine form optimization.** Convert `f e1 e2 e3` to `f [e1, e2, e3]` (application spine) and process all arguments against the function's parameter types in a single pass. Avoids repeated synthesis of the function type.
- **Zonking.** After type checking, perform a single pass to resolve all existential variables. Avoids repeated resolution during checking.
- **Error recovery.** When checking fails, continue with a "hole" type to report multiple errors in one pass. Essential for IDE support.
- **Contextual typing (Xie & Oliveira 2024).** Extend bidirectional typing with contextual information from surrounding expressions to further reduce annotation burden.
- **Incremental checking.** Reuse results from unchanged subterms for IDE responsiveness.

### Common Pitfalls

1. **Missing subsumption rule.** Without the Sub/mode-switch rule, synthesis and checking modes are disconnected. Many well-typed terms are rejected because synthesis produces a type not syntactically equal to the expected type.
2. **Synthesis failure without annotation.** Bare lambdas cannot synthesize a type. Either reject them (standard) or create existential variables (more complex, as in DK 2013).
3. **Subtyping direction in arrows.** Parameter types are CONTRAVARIANT: `(B1 -> A2) <: (A1 -> B2)` requires `A1 <: B1` and `A2 <: B2`. Getting this wrong (covariant parameters) is subtle and common.
4. **Incorrect scoping of existentials.** Solving an existential with a type referencing out-of-scope variables causes unsoundness. Track scoping via ordered contexts or levels.
5. **Eager vs. lazy existential resolution.** Too eager: prevents later constraints from being discovered. Too lazy: leaves ambiguous types. The right balance depends on the system.
6. **Not handling lambda in synthesis position.** Some implementations forget this case entirely and crash instead of producing a clear error message.

### Cross-References

- Higher-rank bidirectional checking: Section 5
- Local type inference (bidirectional + subtyping): Section 4
- Unification used within bidirectional systems: Section 7
- Elaboration uses bidirectional structure: Section 8
- Theoretical foundations: `01-theory-foundations.md` Sections 1-2
- Key references: Pierce & Turner 2000, Dunfield & Krishnaswami 2013, Dunfield & Krishnaswami 2021 (survey)

---

## 3. Constraint-Based Type Inference (HM(X))

### Formal Foundations

**Architecture (Pottier-Remy 2005).** Constraint-based inference decomposes type inference into two independent phases: (1) *constraint generation* traverses the program and emits typing constraints; (2) *constraint solving* solves the collected constraints. The system is parameterized over a constraint domain X, yielding the HM(X) framework (Odersky, Sulzmann, Wehr 1999).

**Constraint language.**

```
C ::= true                    -- trivially satisfied
    | false                   -- unsatisfiable
    | tau1 = tau2             -- type equality
    | C1 /\ C2               -- conjunction
    | exists alpha. C         -- existential quantification
    | def x : sigma in C      -- let binding (introduces polymorphic name)
    | x <= tau                -- instantiation (x used at type tau)
```

where `tau` ranges over monotypes and `sigma = forall alpha[C]. tau` are constrained type schemes.

**Constraint domain X.** Determines what atomic constraints beyond equality are permitted:
- HM(=): standard HM, equality only
- HM(<=): subtyping constraints
- HM(TC): type class membership predicates (Haskell)

**Constraint generation rules.** Judgement form: `Gamma |- e : tau ~> C` (expression e has type tau, generating constraint C).

```
[CG-Var]   Gamma |- x : tau ~> (x <= tau)

[CG-Abs]   Gamma, x:alpha |- e : tau ~> C    alpha fresh
           ───────────────────────────────────────────────
           Gamma |- \x.e : alpha -> tau ~> C

[CG-App]   Gamma |- e1 : tau1 ~> C1    Gamma |- e2 : tau2 ~> C2    alpha fresh
           ─────────────────────────────────────────────────────────────────────
           Gamma |- e1 e2 : alpha ~> C1 /\ C2 /\ (tau1 = tau2 -> alpha)

[CG-Let]   Gamma |- e1 : tau1 ~> C1
           alpha_bar = ftv(C1, tau1) \ ftv(Gamma)
           Gamma, x : forall alpha_bar[C1].tau1 |- e2 : tau2 ~> C2
           ────────────────────────────────────────────────────────
           Gamma |- let x = e1 in e2 : tau2 ~> C2
```

**Metatheory.** Type inference via constraint generation + solving is sound and complete with respect to Damas-Milner. For HM(=), constraint solving reduces to first-order unification, decidable and DEXPTIME-complete (same as Algorithm W). For HM(<=) with structural subtyping: decidable. For HM with bounded quantification (F-sub): subtyping is undecidable (Pierce 1992). Principal types preserved when the constraint domain X admits most general solutions.

**GHC's OutsideIn(X) (Vytiniotis et al. 2011).** A practical variant for Haskell with type classes, GADTs, and type families. Constraints are collected outside-in (top-level to nested), ensuring that local assumptions from GADT pattern matches do not escape their scope. Decidable under the condition that type family instances are confluent and terminating.

### Core Algorithm

```typescript
// Constraint-Based Type Inference (HM(X) architecture)

type Constraint =
  | { tag: 'CTrue' }
  | { tag: 'CFalse' }
  | { tag: 'CEq'; lhs: Ty; rhs: Ty }
  | { tag: 'CAnd'; c1: Constraint; c2: Constraint }
  | { tag: 'CExists'; v: string; body: Constraint }
  | { tag: 'CInst'; x: string; at: Ty };

// Phase 1: Constraint generation
function generate(env: Env, e: Expr): [Ty, Constraint] {
  if (e.tag === 'Var') {
    const tv = fresh();
    return [tv, { tag: 'CInst', x: e.x, at: tv }];
  }
  if (e.tag === 'Lam') {
    const a = fresh();
    const [t, c] = generate(new Map([...env, [e.x, mono(a)]]), e.b);
    return [{ tag: 'TFun', a, b: t }, c];
  }
  if (e.tag === 'App') {
    const [t1, c1] = generate(env, e.f);
    const [t2, c2] = generate(env, e.a);
    const tv = fresh();
    return [tv, { tag: 'CAnd', c1: { tag: 'CAnd', c1, c2 },
                  c2: { tag: 'CEq', lhs: t1, rhs: { tag: 'TFun', a: t2, b: tv } } }];
  }
  // Let: generate constraint for value, generalize, then body
  const [t1, c1] = generate(env, e.v);
  const sc = genScheme(env, t1, c1);
  const [t2, c2] = generate(new Map([...env, [e.x, sc]]), e.b);
  return [t2, c2];
}

// Phase 2: Constraint solving (for HM(=), reduces to unification)
function solve(c: Constraint, s: Sub): Sub {
  if (c.tag === 'CTrue') return s;
  if (c.tag === 'CFalse') throw Error('unsatisfiable');
  if (c.tag === 'CEq') return compose(s, unify(apply(s, c.lhs), apply(s, c.rhs)));
  if (c.tag === 'CAnd') { const s1 = solve(c.c1, s); return solve(c.c2, s1); }
  if (c.tag === 'CExists') return solve(c.body, s); // alpha already fresh
  if (c.tag === 'CInst') { /* resolve x's scheme, instantiate, unify with c.at */ }
  return s;
}
```

### Pragmatic Implementation

- **Interleaved generation/solving.** Solve constraints as they are generated rather than collecting all first. Catches errors earlier, reduces peak memory.
- **Union-find for substitution.** Use union-find instead of explicit `Map<Var, Type>`. Makes variable lookups amortized O(alpha(n)).
- **Level-based generalization (Remy).** Assign each type variable a level. Generalize variables whose level exceeds the current let-depth. Avoids the expensive `ftv(Gamma)` computation.
- **Constraint flattening.** Flatten nested `CAnd` into a list/queue of atomic constraints for iterative solving.
- **Rank-based quantification tracking.** Track the binding depth of type variables for efficient generalization decisions.

### Common Pitfalls

1. **Solving before generalizing.** Must solve constraints for a let-bound expression BEFORE generalizing, otherwise variables that should be constrained get generalized. The "collect all, solve at end" approach breaks let-polymorphism.
2. **Constraint escaping its scope.** Fresh existential variables introduced during generation must not leak into outer scopes. Track scoping levels carefully.
3. **Missing occurs check.** Without it, unification produces infinite types (e.g., `alpha = List<alpha>`).
4. **Constraint ordering sensitivity.** Although HM(=) solving is confluent in theory, implementation bugs can make it order-dependent. Test with shuffled constraint orderings.
5. **Incorrect generalization.** A type variable should only be generalized if it does NOT appear free in the typing environment.
6. **Coherence loss.** In HM with type classes, constraint solving must be coherent: different resolution paths must yield the same result. Loss of coherence produces nondeterministic program behavior.

### Cross-References

- Unification (the solving engine for HM(=)): Section 7
- Algorithm W as an alternative to generate-then-solve: Section 1
- OutsideIn(X) for GHC: Vytiniotis et al. 2011
- Algebraic subtyping as an alternative X domain: Section 6
- Key references: Pottier & Remy 2005 ("The Essence of ML Type Inference"), Odersky, Sulzmann & Wehr 1999

---

## 4. Local Type Inference (Pierce-Turner 2000)

### Formal Foundations

**Design philosophy.** Local type inference avoids global constraint solving. Instead, type argument synthesis for polymorphic function applications is performed *locally* -- using only type information from the immediate application site. This makes inference modular and predictable, at the cost of completeness: some programs typeable with full annotations require explicit type arguments that local inference cannot recover.

**Bidirectional structure.** The system uses bidirectional type checking (synthesis + checking) combined with local constraint solving for type argument inference in polymorphic applications.

**Typing rules.**

```
[Var-Synth]    (x : A) in Gamma
               ─────────────────────
               Gamma |- x => A

[Anno]         Gamma |- e <= A
               ─────────────────────
               Gamma |- (e : A) => A

[App-Synth]    Gamma |- e1 => A -> B    Gamma |- e2 <= A
               ─────────────────────────────────────────
               Gamma |- e1 e2 => B

[TApp-Synth]   Gamma |- e => forall alpha. A
               T = localSolve(alpha, arg, A, expectedReturnType)
               Gamma |- arg <= A[alpha := T]
               ────────────────────────────────────────────────
               Gamma |- e arg => B[alpha := T]

[Abs-Check]    Gamma, x:A |- e <= B
               ─────────────────────────
               Gamma |- (lambda x. e) <= A -> B

[Sub]          Gamma |- e => A    A <: B
               ─────────────────────────
               Gamma |- e <= B
```

**Local constraint solving** for `f[alpha](e)` where `f : forall alpha. A -> B`:
1. From `C <: A[alpha]` (argument type): collect upper bounds on alpha.
2. From `B[alpha] <: D` (expected return type, if checking mode provides D): collect lower bounds on alpha.
3. Solve: `alpha = join(lower bounds)` if it satisfies `meet(upper bounds)`.

Subtyping generates *bounds* (upper/lower) on type variables, not equality constraints. This is the key difference from HM's global unification.

**Metatheory.** Type checking is decidable (assuming decidable subtyping). Soundness: proven with respect to the fully-annotated declarative system. Completeness: *local* only -- for any single polymorphic application, the best instantiation is found if it exists. Global completeness does not hold. The system is designed for *prenex* polymorphism; impredicative instantiation must be explicit.

### Core Algorithm

```typescript
// Local Type Inference — type argument solving
function localSolve(
  typeParams: string[],
  argType: Type,         // actual argument type
  paramType: Type,       // formal parameter type (contains typeParams)
  expectedReturn?: Type  // expected return type from checking context
): Map<string, Type> {
  const bounds = new Map<string, { lower: Type[]; upper: Type[] }>();
  for (const p of typeParams) bounds.set(p, { lower: [], upper: [] });

  // Collect bounds from argument: argType <: paramType
  collectBounds(argType, paramType, 'upper', bounds);

  // Collect bounds from return type if available: returnType <: expectedReturn
  if (expectedReturn) collectBounds(expectedReturn, returnType, 'lower', bounds);

  // Solve: for each param, take join of lower bounds / meet of upper bounds
  const solution = new Map<string, Type>();
  for (const [p, b] of bounds) {
    if (b.lower.length > 0) solution.set(p, joinTypes(b.lower));
    else if (b.upper.length > 0) solution.set(p, meetTypes(b.upper));
    else throw Error(`cannot infer type argument ${p}`);
  }
  return solution;
}

function collectBounds(
  actual: Type, formal: Type, polarity: 'upper' | 'lower',
  bounds: Map<string, { lower: Type[]; upper: Type[] }>
): void {
  if (formal.tag === 'TVar' && bounds.has(formal.name)) {
    bounds.get(formal.name)![polarity].push(actual);
    return;
  }
  if (formal.tag === 'Arrow' && actual.tag === 'Arrow') {
    // Parameter position is contravariant: flip polarity
    collectBounds(actual.a, formal.a, polarity === 'upper' ? 'lower' : 'upper', bounds);
    // Return position is covariant: keep polarity
    collectBounds(actual.b, formal.b, polarity, bounds);
  }
  // Recurse into type constructor arguments respecting variance
}
```

### Pragmatic Implementation

- **TypeScript/Scala/Kotlin-style.** These languages use local type inference with left-to-right argument processing. TS infers generic type arguments from the first argument, then checks subsequent arguments against the partially-solved type.
- **Two-pass strategy.** First collect constraints from all arguments, then solve. Better results than strictly single-pass local solving.
- **Expected-type propagation.** If the application site has an expected type from an outer checking context, use it to solve return-position type variables. Aggressive propagation significantly reduces the need for explicit type arguments.
- **Colored local type inference (Odersky et al. 2001).** Mark type parameters as "determined" vs "undetermined" to avoid re-solving. Used in Scala.
- **Cache subtype decisions.** Structural subtype decisions are deterministic and can be memoized.

### Common Pitfalls

1. **Lambda without annotation in synthesis.** Attempting to synthesize an unannotated lambda is a common source of "cannot infer type" errors. Lambdas must be checked, not synthesized.
2. **Argument order sensitivity.** Pierce-Turner's system is sensitive to argument order. Over-eagerly solving from the first argument only can miss information from later arguments.
3. **Variance confusion.** Getting the variance wrong (covariant vs contravariant positions) when collecting bounds produces incorrect or unsound type argument inference.
4. **Missing expected-type propagation.** Not pushing checking-mode information through nested expressions (e.g., not pushing the expected return type through if-then-else) misses solving opportunities.
5. **Intentional incompleteness.** Trying to make local inference complete leads to global constraint solving, defeating its purpose. Accept the incompleteness.
6. **Subsumption as fallback.** The Sub rule (synthesize then subtype-check) must be the fallback, not the primary checking rule.

### Cross-References

- Bidirectional foundation: Section 2
- Complete-and-Easy for higher-rank: Section 5
- Unification used in local solving: Section 7
- Key references: Pierce & Turner 2000, Odersky et al. 2001 (colored local type inference)
- Industrial usage: TypeScript (TS Handbook: "Contextual Typing"), Scala, Kotlin, Swift

---

## 5. Complete and Easy Bidirectional Higher-Rank (Dunfield-Krishnaswami 2013)

### Formal Foundations

**Innovation.** Extends bidirectional type checking to handle higher-rank (impredicative) polymorphism *completely* without requiring type annotations beyond top-level bindings. The key mechanism is an **ordered algorithmic context** that tracks existential type variables (written `alpha-hat`) alongside universal variables and term variables.

**Types.** `A, B ::= 1 | alpha | alpha-hat | A -> B | forall alpha. A`

**Contexts.** `Gamma ::= . | Gamma, x:A | Gamma, alpha | Gamma, alpha-hat | Gamma, alpha-hat = tau | Gamma, marker`

The ordered context is essential: the position of existential variables in the context determines their scope. This prevents cyclic dependencies and scope escape.

**Algorithmic judgements** thread the context through as input/output:
- Synthesis: `Gamma |- e => A -| Delta` (outputs type A and updated context Delta)
- Checking: `Gamma |- e <= A -| Delta` (outputs updated context Delta)

**Key rules.**

```
(Var)          (x : A) in Gamma
               ──────────────────────
               Gamma |- x => A -| Gamma

(->E)          Gamma |- e1 => A -| Theta    Theta |- [Theta]A . e2 =>> C -| Delta
               ───────────────────────────────────────────────────────────────────
               Gamma |- e1 e2 => C -| Delta

(->I)          Gamma, x:A |- e <= B -| Delta, x:A, Theta
               ──────────────────────────────────────────
               Gamma |- (lambda x. e) <= A -> B -| Delta

(forall-I)     Gamma, alpha |- e <= A -| Delta, alpha, Theta
               ──────────────────────────────────────────────
               Gamma |- e <= forall alpha. A -| Delta

(Sub)          Gamma |- e => A -| Theta    Theta |- [Theta]A <: [Theta]B -| Delta
               ──────────────────────────────────────────────────────────────────
               Gamma |- e <= B -| Delta
```

**Subtyping with instantiation.** The algorithmic subtyping judgment solves existential variables:

```
(<:InstL)      Gamma |- alpha-hat :=< A -| Delta
               ────────────────────────────────────
               Gamma[alpha-hat] |- alpha-hat <: A -| Delta

(<:InstR)      Gamma |- A =<: alpha-hat -| Delta
               ────────────────────────────────────
               Gamma[alpha-hat] |- A <: alpha-hat -| Delta

(<:forallL)    Gamma, marker alpha-hat, alpha-hat |- [alpha-hat/alpha]A <: B -| Delta, marker, Theta
               ──────────────────────────────────────────────────────────────────────────────────────
               Gamma |- forall alpha. A <: B -| Delta

(<:forallR)    Gamma, alpha |- A <: B -| Delta, alpha, Theta
               ──────────────────────────────────────────────
               Gamma |- A <: forall alpha. B -| Delta
```

**Completeness theorem.** The algorithmic system is complete: every declaratively valid typing can be derived algorithmically. This is remarkable because higher-rank inference is generally considered to require annotations. Achieved by greedy instantiation through the ordered context.

**Decidability.** The algorithm terminates on all inputs. The ordered context provides a well-founded measure: the number of unsolved existential variables strictly decreases. Subtyping is decidable.

### Core Algorithm

```typescript
// Complete-and-Easy Bidirectional Higher-Rank Type Checking
// Ordered context as a list of entries

type CtxEntry =
  | { tag: 'CVar'; x: string; ty: Type }
  | { tag: 'CUniv'; alpha: string }
  | { tag: 'CExist'; alpha: string; solution?: Type }
  | { tag: 'CMarker'; alpha: string };

type Ctx = CtxEntry[];

function synthDK(ctx: Ctx, e: Expr): [Ctx, Type] {
  if (e.tag === 'Var') {
    const ty = lookupVar(ctx, e.x);
    return [ctx, ty];
  }
  if (e.tag === 'Ann') {
    const ctx1 = checkDK(ctx, e.term, e.type);
    return [ctx1, e.type];
  }
  if (e.tag === 'App') {
    const [ctx1, funTy] = synthDK(ctx, e.f);
    return applySpine(ctx1, applyCtx(ctx1, funTy), e.a);
  }
  throw Error('cannot synthesize');
}

function checkDK(ctx: Ctx, e: Expr, ty: Type): Ctx {
  // ForallI: check against forall alpha. A
  if (ty.tag === 'Forall') {
    const ctx1 = [...ctx, { tag: 'CUniv' as const, alpha: ty.x }];
    const ctx2 = checkDK(ctx1, e, ty.body);
    return dropAfter(ctx2, { tag: 'CUniv', alpha: ty.x });
  }
  // ->I: lambda checked against arrow
  if (e.tag === 'Lam' && ty.tag === 'Arrow') {
    const ctx1 = [...ctx, { tag: 'CVar' as const, x: e.x, ty: ty.a }];
    const ctx2 = checkDK(ctx1, e.b, ty.b);
    return dropAfter(ctx2, { tag: 'CVar', x: e.x, ty: ty.a });
  }
  // Sub: synthesize, then subtype
  const [ctx1, infTy] = synthDK(ctx, e);
  return subtype(ctx1, applyCtx(ctx1, infTy), applyCtx(ctx1, ty));
}

function subtype(ctx: Ctx, a: Type, b: Type): Ctx {
  // <:Var
  if (a.tag === 'TVar' && b.tag === 'TVar' && a.name === b.name) return ctx;
  // <:->
  if (a.tag === 'Arrow' && b.tag === 'Arrow') {
    const ctx1 = subtype(ctx, b.a, a.a);  // contravariant in param
    return subtype(ctx1, applyCtx(ctx1, a.b), applyCtx(ctx1, b.b));
  }
  // <:forallL
  if (a.tag === 'Forall') {
    const alpha_hat = freshExist();
    const ctx1 = [...ctx,
      { tag: 'CMarker' as const, alpha: alpha_hat },
      { tag: 'CExist' as const, alpha: alpha_hat }];
    const body = substType(a.body, a.x, { tag: 'TVar', name: alpha_hat });
    const ctx2 = subtype(ctx1, body, b);
    return dropAfter(ctx2, { tag: 'CMarker', alpha: alpha_hat });
  }
  // <:forallR
  if (b.tag === 'Forall') {
    const ctx1 = [...ctx, { tag: 'CUniv' as const, alpha: b.x }];
    const ctx2 = subtype(ctx1, a, b.body);
    return dropAfter(ctx2, { tag: 'CUniv', alpha: b.x });
  }
  // <:InstL / <:InstR
  if (a.tag === 'TVar' && isExistential(ctx, a.name)) return instantiateL(ctx, a.name, b);
  if (b.tag === 'TVar' && isExistential(ctx, b.name)) return instantiateR(ctx, a, b.name);
  throw Error(`cannot subtype ${show(a)} <: ${show(b)}`);
}

// Instantiation: solve alpha-hat to make alpha-hat <: A (InstL) or A <: alpha-hat (InstR)
function instantiateL(ctx: Ctx, alpha: string, ty: Type): Ctx {
  if (isMonotype(ty) && wellFormedInCtxBefore(ctx, ty, alpha)) {
    return solveExist(ctx, alpha, ty);
  }
  if (ty.tag === 'Arrow') {
    const [a1, a2] = [freshExist(), freshExist()];
    const ctx1 = insertBefore(ctx, alpha,
      [{ tag: 'CExist', alpha: a2 }, { tag: 'CExist', alpha: a1 }]);
    const ctx2 = solveExist(ctx1, alpha,
      { tag: 'Arrow', a: { tag: 'TVar', name: a1 }, b: { tag: 'TVar', name: a2 } });
    const ctx3 = instantiateR(ctx2, ty.a, a1);
    return instantiateL(ctx3, a2, applyCtx(ctx3, ty.b));
  }
  if (ty.tag === 'Forall') {
    const ctx1 = [...ctx, { tag: 'CUniv' as const, alpha: ty.x }];
    const ctx2 = instantiateL(ctx1, alpha, ty.body);
    return dropAfter(ctx2, { tag: 'CUniv', alpha: ty.x });
  }
  throw Error('instantiateL failed');
}
```

### Pragmatic Implementation

- **Context as zipper or finger tree.** O(log n) lookups and splits instead of O(n) list operations. Essential for performance on large programs.
- **Union-find for existential solutions.** Combine with the ordered context: the context provides scoping, union-find provides fast lookup.
- **Stack + side table.** Implement context as a stack with a hash table mapping existential names to their solutions. Combines ordered discipline with O(1) lookup.
- **De Bruijn indices for universals.** Avoids alpha-renaming overhead in the forall-I and forall-L rules.
- **Quick-look impredicativity (Serrano et al. 2020).** For GHC: a pragmatic optimization for common higher-rank patterns that avoids the full DK algorithm's overhead.

### Common Pitfalls

1. **Unordered context.** Implementing the context as an unordered map breaks termination and soundness. The ordering is essential for the well-founded measure.
2. **Forgetting to apply context as substitution.** The output context must be applied to types from earlier steps before use in subsequent judgments. Written `[Theta]A` in the rules.
3. **Marker scoping errors.** Failing to drop context entries after a marker leads to existential variable leakage (scope escape).
4. **InstL vs InstR confusion.** InstL solves `alpha-hat <: A`, InstR solves `A <: alpha-hat`. Swapping produces unsound results.
5. **Lambda checked against existential.** When a lambda is checked against an unsolved existential, the existential must be decomposed into `alpha1 -> alpha2` (function type). Missing this case rejects valid programs.
6. **Missing occurs check.** Allowing cyclic existential solutions produces infinite types.

### Cross-References

- Foundational bidirectional typing: Section 2
- Unification within instantiation: Section 7
- HM as a special case (rank-1): Section 1
- Algebraic subtyping as an alternative approach: Section 6
- Key references: Dunfield & Krishnaswami 2013, Serrano et al. 2020 ("A Quick Look at Impredicativity")

---

## 6. Algebraic Subtyping (MLsub, SimpleSub, MLstruct)

### Formal Foundations

**Dolan 2017: MLsub.** Extends HM type inference with subtyping while *preserving principal types*. The key idea: organize types into a distributive lattice with meet (intersection) and join (union).

**Type grammar.**

```
tau ::= alpha                       -- type variable
      | tau1 -> tau2                 -- function type
      | tau1 | tau2                  -- union (join / least upper bound)
      | tau1 & tau2                  -- intersection (meet / greatest lower bound)
      | top                          -- universal supertype
      | bot                          -- universal subtype
      | C(tau1, ..., tn)             -- type constructor application
```

**Subtyping lattice.**

```
tau <= top,   bot <= tau                             (bounds)
tau1 & tau2 <= tau1,   tau1 & tau2 <= tau2            (meet elimination)
tau1 <= tau1 | tau2,   tau2 <= tau1 | tau2            (join introduction)
(tau1 -> tau2) <= (tau3 -> tau4)                      (arrow)
    iff tau3 <= tau1 and tau2 <= tau4
tau1 & (tau2 | tau3) = (tau1 & tau2) | (tau1 & tau3)  (distributivity)
```

**Polar type variables.** The crucial innovation:
- A type variable alpha in a **positive** position (output/covariant) represents the join of all types it could be.
- A type variable alpha in a **negative** position (input/contravariant) represents the meet of all types it could be.
- Subtyping constraints `alpha <= tau` (positive) and `tau <= alpha` (negative) are accumulated as bounds on the variable.

**Biunification.** Dolan's algorithm solves subtype constraints by biunification: simultaneously tracking upper and lower bounds for each variable. A variable alpha has lower bound L (positive occurrences, `alpha >= L`) and upper bound U (negative occurrences, `alpha <= U`). The constraint `L <= alpha <= U` is satisfiable iff `L <= U`.

**Typing rules (MLsub/SimpleSub).**

```
[Var]   x : forall alpha_bar. tau in Gamma    beta_bar fresh
        ─────────────────────────────────────────────────────
        Gamma |- x : [beta_bar/alpha_bar]tau

[Abs]   Gamma, x : alpha |- e : tau    alpha fresh
        ───────────────────────────────────────────
        Gamma |- \x. e : alpha -> tau

[App]   Gamma |- e1 : tau1    Gamma |- e2 : tau2    alpha fresh
        constrain(tau1, tau2 -> alpha)
        ───────────────────────────────────────────
        Gamma |- e1 e2 : alpha

[Let]   level++    Gamma |- e1 : tau1    level--
        Gamma, x : Gen(tau1) |- e2 : tau2
        ───────────────────────────────────────────
        Gamma |- let x = e1 in e2 : tau2

[If]    constrain(tau1, Bool)
        Gamma |- e2 : tau2    Gamma |- e3 : tau3
        alpha fresh    constrain(tau2, alpha)    constrain(tau3, alpha)
        ───────────────────────────────────────────
        Gamma |- if e1 then e2 else e3 : alpha
        (result is the join tau2 | tau3, captured via fresh alpha)
```

Key difference from HM: the App rule uses *subtyping* (`<=`) via `constrain` rather than equality, and if-then-else returns a *union type* rather than requiring branches to have the same type.

**SimpleSub (Parreaux 2020).** Reformulates biunification as direct constraint propagation equivalent to Algorithm J extended with subtyping. Type variables are mutable cells with `lowerBounds` and `upperBounds` lists. Constraining `alpha <= tau` adds `tau` to `alpha.upperBounds` and propagates to all existing lower bounds. Much simpler to implement than Dolan's original polar-type/automata formulation.

**MLstruct (Parreaux 2022).** Extends SimpleSub with Boolean-algebraic subtyping: adds negation types (`~tau`), making types a Boolean algebra. Subtyping reduces to propositional satisfiability.

**Metatheory.** Inference is decidable with principal types (the central achievement). Complexity: DEXPTIME-complete worst case (same as HM), near-linear in practice. SimpleSub constraint solving is O(n^2) worst case, near-linear typical. MLstruct subtype checking: NP-complete in theory (SAT reduction), but instances from inference are tiny.

### Core Algorithm

```typescript
// SimpleSub — Algebraic subtyping with constraint propagation
// Type variables are mutable nodes with bounds

interface TypeVar {
  id: number;
  lowerBounds: SimpleType[];
  upperBounds: SimpleType[];
  level: number;
}

type SimpleType =
  | { tag: 'Var'; ref: TypeVar }
  | { tag: 'Fun'; param: SimpleType; ret: SimpleType }
  | { tag: 'Record'; fields: Map<string, SimpleType> }
  | { tag: 'Prim'; name: string }    // Int, Bool, String
  | { tag: 'Top' } | { tag: 'Bot' };

let currentLevel = 0;
let nextId = 0;
const freshVar = (): SimpleType => ({
  tag: 'Var',
  ref: { id: nextId++, lowerBounds: [], upperBounds: [], level: currentLevel }
});

// Core: constrain lhs <: rhs
function constrain(lhs: SimpleType, rhs: SimpleType): void {
  if (lhs === rhs) return;  // identity check (physical equality)
  if (lhs.tag === 'Top' || rhs.tag === 'Bot') throw Error('type mismatch');
  if (lhs.tag === 'Bot' || rhs.tag === 'Top') return;

  if (lhs.tag === 'Fun' && rhs.tag === 'Fun') {
    constrain(rhs.param, lhs.param);  // contravariant in param
    constrain(lhs.ret, rhs.ret);       // covariant in return
    return;
  }
  if (lhs.tag === 'Record' && rhs.tag === 'Record') {
    // Width subtyping: rhs fields must be subset of lhs fields
    for (const [label, rhsTy] of rhs.fields) {
      const lhsTy = lhs.fields.get(label);
      if (!lhsTy) throw Error(`missing field: ${label}`);
      constrain(lhsTy, rhsTy);
    }
    return;
  }
  if (lhs.tag === 'Var') {
    lhs.ref.upperBounds.push(rhs);
    // Propagate: for all existing lower bounds lb of lhs, constrain lb <: rhs
    for (const lb of lhs.ref.lowerBounds) constrain(lb, rhs);
    return;
  }
  if (rhs.tag === 'Var') {
    rhs.ref.lowerBounds.push(lhs);
    // Propagate: for all existing upper bounds ub of rhs, constrain lhs <: ub
    for (const ub of rhs.ref.upperBounds) constrain(lhs, ub);
    return;
  }
  if (lhs.tag === 'Prim' && rhs.tag === 'Prim' && lhs.name === rhs.name) return;
  throw Error(`type mismatch: ${showSimple(lhs)} </: ${showSimple(rhs)}`);
}

// Type extrusion: copy a type to a lower level (for generalization)
function extrude(ty: SimpleType, pol: boolean, targetLevel: number): SimpleType {
  if (ty.tag === 'Var') {
    if (ty.ref.level <= targetLevel) return ty;
    // Variable above target level: create fresh var at target, link
    const fresh = freshVarAt(targetLevel);
    if (pol) constrain(ty, fresh);    // positive: ty <: fresh
    else     constrain(fresh, ty);    // negative: fresh <: ty
    return fresh;
  }
  if (ty.tag === 'Fun') {
    return {
      tag: 'Fun',
      param: extrude(ty.param, !pol, targetLevel),  // flip polarity
      ret: extrude(ty.ret, pol, targetLevel)
    };
  }
  return ty;
}

// Generalization via levels
function generalize(ty: SimpleType): PolyType {
  // Variables with level > currentLevel become universally quantified
  const vars = collectVarsAboveLevel(ty, currentLevel);
  return { quantified: vars, body: ty };
}
```

### Pragmatic Implementation

- **Mutable type variables.** SimpleSub uses mutable state (bounds lists on variable nodes). For backtracking or parallel inference, snapshot-restore or copy-on-write is needed.
- **Level-based generalization.** Use Remy's level trick: increment `currentLevel` on entering a let, decrement on exit. Variables at level > currentLevel are generalizable. Avoids computing free variables.
- **Hash-consing type nodes.** Share identical type structures to reduce memory and speed up identity checks.
- **Cycle detection for recursive types.** Use tortoise-and-hare or DFS-based cycle detection during constraint propagation. SimpleSub does not handle equirecursive types by default; MLstruct adds them with a contractiveness check.
- **Union-find for variable equivalence.** When `alpha <= beta AND beta <= alpha`, merge via union-find to reduce the variable count.
- **Short-circuit for monomorphic bindings.** If a let-binding's type has no variables above current level, skip generalization entirely.

### Common Pitfalls

1. **Infinite loops in constraint propagation.** Constraining `alpha <= beta` and `beta <= alpha` (cyclic bounds) causes naive propagation to loop. Use memoization or physical-equality checks before propagating.
2. **Polarity confusion.** Function parameters are contravariant (negative), returns are covariant (positive). Mixing up polarity in `constrain` causes unsound types.
3. **Level management for generalization.** Forgetting to increment/decrement the level around let-bindings causes unsound generalization. Use RAII-style level management (try/finally).
4. **Width subtyping direction.** `{a: Int, b: String} <: {a: Int}` -- a record with MORE fields is a SUBTYPE. Getting this backwards is common.
5. **Simplification too early.** Simplifying types before all constraints are propagated produces wrong results. Run inference to completion first.
6. **Mutable aliasing on copy.** Copying a type scheme must deep-copy variable nodes (or use level-based instantiation). Shallow copying shares mutation, corrupting the original.
7. **SimpleSub unions vs TypeScript unions.** TS `A | B` has excess property checking and control-flow narrowing; SimpleSub unions do not.

### Cross-References

- HM (base system extended by algebraic subtyping): Section 1
- Constraint-based inference (HM(X) with X = <=): Section 3
- Unification vs biunification: Section 7
- Key references: Dolan 2017 ("Algebraic Subtyping"), Parreaux 2020 ("The Simple Essence of Algebraic Subtyping"), Parreaux 2022 ("MLstruct")

---

## 7. Unification Algorithms

### Formal Foundations

**The unification problem.** Given a signature Sigma of function symbols with arities, terms `T(Sigma, V)` over variables V are:

```
t ::= x                      (x in V)
    | f(t1, ..., tn)          (f in Sigma, arity(f) = n)
```

A substitution `sigma: V -> T(Sigma, V)` is extended homomorphically to terms. A *unifier* of equation `s =? t` is a substitution sigma such that `sigma(s) = sigma(t)` (syntactic identity).

**Most General Unifier (MGU).** A unifier sigma is most general if for every other unifier theta, there exists rho with `theta = rho . sigma`. The MGU is unique up to variable renaming. Robinson's key insight (1965): first-order syntactic unification always has an MGU if a unifier exists.

**Complexity.**
- Robinson 1965: exponential worst case O(2^n) due to eager substitution application.
- Martelli-Montanari 1982 (rule-based): near-linear O(n * alpha(n)) with union-find.
- Paterson-Wegman (DAG-based): O(n) time, but the MGU itself may be exponentially large.
- Space: O(n) for DAG representation; O(2^n) worst case for explicit MGU.

**Higher-order unification.** Undecidable in general (Huet 1973). Semi-decidable: if a unifier exists, a complete search will find it. Huet's pre-unification algorithm is used in practice (Coq, Lean, Agda) with heuristics.

**E-unification (modulo equational theories).** Decidability depends on the theory. AC-unification (associativity + commutativity): decidable but NP-complete. Unification modulo a general equational theory: undecidable.

**Nominal unification.** With name-binding: decidable, with MGU, in polynomial time (Urban, Pitts & Gabbay 2004).

### Core Algorithm

**Martelli-Montanari transformation rules (1982).** A unification problem is a set of equations `E = { s1 =? t1, ..., sn =? tn }`. The algorithm transforms E using four rules until solved or failed:

```
(Delete)     { t =? t } ∪ E  ==>  E
             -- identical terms: remove equation

(Decompose)  { f(s1,...,sn) =? f(t1,...,tn) } ∪ E
             ==>  { s1 =? t1, ..., sn =? tn } ∪ E
             -- same head symbol: decompose into subproblems

(Orient)     { t =? x } ∪ E  ==>  { x =? t } ∪ E    (where t is not a variable)
             -- move variable to LHS

(Eliminate)  { x =? t } ∪ E  ==>  { x =? t } ∪ [t/x]E
             where x not in FV(t)     -- OCCURS CHECK
             -- bind x to t, apply to remaining equations
```

Failure conditions:
- **Clash:** `f(s1,...,sm) =? g(t1,...,tn)` where `f != g` or `m != n`.
- **Occurs check:** `x =? t` where `x in FV(t)` and `t != x`.

```typescript
// Martelli-Montanari unification

type Term = { tag: 'Var'; name: string }
          | { tag: 'App'; head: string; args: Term[] };

type Equation = { lhs: Term; rhs: Term };

function unifyMM(equations: Equation[]): Map<string, Term> {
  const worklist = [...equations];
  const solution = new Map<string, Term>();

  while (worklist.length > 0) {
    const { lhs, rhs } = worklist.pop()!;
    const l = resolve(solution, lhs);
    const r = resolve(solution, rhs);

    // Delete: identical
    if (termEqual(l, r)) continue;

    // Orient: move variable to LHS
    if (l.tag === 'App' && r.tag === 'Var') {
      worklist.push({ lhs: r, rhs: l });
      continue;
    }

    // Eliminate: variable binding
    if (l.tag === 'Var') {
      if (occursIn(l.name, r)) throw Error(`occurs check: ${l.name} in ${showTerm(r)}`);
      solution.set(l.name, r);
      continue;
    }

    // Decompose: same head, decompose args
    if (l.tag === 'App' && r.tag === 'App') {
      if (l.head !== r.head || l.args.length !== r.args.length)
        throw Error(`clash: ${l.head} vs ${r.head}`);
      for (let i = 0; i < l.args.length; i++)
        worklist.push({ lhs: l.args[i], rhs: r.args[i] });
      continue;
    }

    throw Error('unification failed');
  }
  return solution;
}

function resolve(s: Map<string, Term>, t: Term): Term {
  if (t.tag === 'Var' && s.has(t.name)) return resolve(s, s.get(t.name)!);
  return t;
}

function occursIn(v: string, t: Term): boolean {
  if (t.tag === 'Var') return t.name === v;
  return t.args.some(a => occursIn(v, a));
}
```

**Union-find implementation** for near-linear unification:

```typescript
// Union-find based unification (Algorithm J style)

class UFind<T> {
  parent: Map<string, string> = new Map();
  rank: Map<string, number> = new Map();
  value: Map<string, T> = new Map();

  find(x: string): string {
    let r = x;
    while (this.parent.has(r)) r = this.parent.get(r)!;
    // Path compression
    let c = x;
    while (c !== r) { const next = this.parent.get(c)!; this.parent.set(c, r); c = next; }
    return r;
  }

  union(a: string, b: string): void {
    const ra = this.find(a), rb = this.find(b);
    if (ra === rb) return;
    const rka = this.rank.get(ra) ?? 0, rkb = this.rank.get(rb) ?? 0;
    if (rka < rkb) this.parent.set(ra, rb);
    else if (rka > rkb) this.parent.set(rb, ra);
    else { this.parent.set(rb, ra); this.rank.set(ra, rka + 1); }
  }
}
```

### Pragmatic Implementation

- **Union-find with path compression + union-by-rank.** Gives O(n * alpha(n)) amortized complexity. Path compression alone gives O(n * log(n)); both together yield the almost-linear bound. This is what production type inference engines use.
- **Hash-consing terms.** Intern all term nodes so structurally identical terms share the same pointer. Makes equality O(1).
- **Lazy occurs check.** Instead of checking at every binding, use a global pass after unification to detect cycles in the substitution graph. Amortizes the cost.
- **DAG representation (Paterson-Wegman).** Represent terms as DAGs rather than trees; shared subterms are represented once. Enables linear-time unification.
- **Explicit worklist.** Use an explicit worklist/stack instead of recursion to avoid stack overflow on deeply nested types (thousands of levels deep).
- **Incremental unification.** Process equations immediately as they arise during AST traversal rather than collecting all first.

### Common Pitfalls

1. **Omitting the occurs check.** The single most common unification bug. Without it, binding `x := List<x>` creates an infinite type, causing non-termination in downstream processing. In Prolog, the occurs check is traditionally omitted for performance (STO: "subject to occurs check"), but in type inference it MUST be present.
2. **Eager substitution application.** Robinson's original algorithm applies substitutions eagerly, leading to exponential blowup on pathological inputs. Use union-find or DAG representation.
3. **Variable-variable equations.** When unifying two variables, merge their equivalence classes (union), do not just bind one to the other as a term.
4. **Mutable state and backtracking.** Path compression mutates parent pointers. If you clone the union-find for backtracking (e.g., in Prolog or overloading resolution), you must deep-copy.
5. **Forgetting to resolve before comparing.** Always resolve both sides through the union-find before comparing. Comparing raw terms misses bindings.
6. **Stack overflow on deeply nested types.** Recursive unification on deeply nested types can overflow the call stack. Use an explicit worklist for production implementations.

### Cross-References

- Used by Algorithm W: Section 1
- Used within bidirectional checking: Section 2
- Constraint solving engine for HM(X): Section 3
- Biunification for algebraic subtyping: Section 6
- Higher-order pattern unification in elaboration: Section 8
- Key references: Robinson 1965, Martelli & Montanari 1982, Paterson & Wegman 1978, Huet 1973 (higher-order)

---

## 8. Elaboration & Metavariable Solving

### Formal Foundations

**Elaboration** is the translation from a high-level surface syntax (with implicit arguments, pattern matching, type class instances, do-notation) to a fully explicit core type theory (typically a dependently typed lambda calculus). Used in Agda (Norell 2007), Lean 4, Coq, Idris.

**Formal structure.**

```
elaborate : Surface.Expr -> Ctx -> Core.Expr x Core.Type
```

**Metavariable (hole).** A placeholder `?alpha` for an unknown term. The elaborator generates constraints:

```
Gamma |- ?alpha[sigma] == t : A
```

where sigma is a substitution (the metavariable's spine/context renaming).

**Core judgement with metavariables.**

```
Gamma ; Delta |- t : A
```

where Delta is the metavariable context mapping each `?alpha` to its type and local context.

**Typing rules.**

```
(Meta-Intro)    ?alpha : A in Delta    Gamma |- sigma : Gamma_alpha
                ──────────────────────────────────────────────────
                Gamma ; Delta |- ?alpha[sigma] : A[sigma]

(Meta-Solve)    Delta, ?alpha : A |- t : A    ?alpha not in FV(t)
                ──────────────────────────────────────────────────
                Delta[?alpha := t]    (substitute t for ?alpha everywhere)

(Implicit-Arg)  Gamma |- f : {x : A} -> B
                Gamma ; Delta, ?alpha : A |- f ?alpha : B[?alpha/x]
                ──────────────────────────────────────────────────
                elaborate(f) = f ?alpha    (fresh metavariable for implicit arg)

(Unification)   Gamma |- A == B : Type
                Triggers metavariable solving when A or B contains ?alpha
```

**Higher-order pattern unification (Miller 1991).** Restricts metavariable applications to patterns:

```
?alpha x1 x2 ... xn    where x1...xn are distinct bound variables
```

This fragment is decidable with unique most general unifiers. Solution by inversion:

```
?alpha x1...xn == t   ==>   ?alpha := lambda x1...xn. t   (if FV(t) subset {x1,...,xn})
```

The occurs check prevents cyclic solutions: `?alpha` cannot appear in its own solution.

**Metatheory.** Pattern unification is decidable in O(n) time (Miller 1991). Full higher-order unification is undecidable (Huet 1973). Practical elaborators use pattern unification as the core, with heuristics for non-pattern cases. Elaboration is generally incomplete: there exist surface programs with valid core translations that the elaborator cannot find. Soundness: maintained as an invariant that every solved metavariable context produces well-typed core terms.

### Core Algorithm

```typescript
// Elaboration with metavariable solving
// Based on Norell 2007 (Agda) / "Elaboration Zoo" (Kovacs)

type Meta = { id: number; type: Value; ctx: Ctx; solution?: Value };
const metas: Meta[] = [];

function freshMeta(ctx: Ctx, ty: Value): Term {
  const id = metas.length;
  metas.push({ id, type: ty, ctx, solution: undefined });
  // Apply meta to all bound variables in ctx (spine)
  const spine = ctx.boundVars.map(v => ({ tag: 'Var' as const, ix: v }));
  return { tag: 'Meta', id, spine };
}

// Force: resolve metavariable if solved
function force(v: Value): Value {
  if (v.tag === 'VMeta' && metas[v.id].solution !== undefined) {
    return force(applySpineVal(metas[v.id].solution!, v.spine));
  }
  return v;
}

// Unify two values, solving metavariables
function unify(ctx: Ctx, a: Value, b: Value): void {
  const a1 = force(a), b1 = force(b);

  if (a1.tag === 'VMeta') { solveMeta(ctx, a1.id, a1.spine, b1); return; }
  if (b1.tag === 'VMeta') { solveMeta(ctx, b1.id, b1.spine, a1); return; }

  if (a1.tag === 'VPi' && b1.tag === 'VPi') {
    unify(ctx, a1.domain, b1.domain);
    const x = freshVar(ctx);
    unify(extendCtx(ctx, x, a1.domain),
          applyVal(a1.codomain, x),
          applyVal(b1.codomain, x));
    return;
  }

  if (a1.tag === 'VLam' && b1.tag === 'VLam') {
    const x = freshVar(ctx);
    unify(extendCtx(ctx, x, a1.domain),
          applyVal(a1.body, x),
          applyVal(b1.body, x));
    return;
  }

  // Eta-expand if needed: f ~ \x -> f x
  if (a1.tag === 'VLam') {
    const x = freshVar(ctx);
    unify(extendCtx(ctx, x, a1.domain),
          applyVal(a1.body, x),
          applyVal(b1, x));
    return;
  }

  if (a1.tag === 'VApp' && b1.tag === 'VApp' && a1.head === b1.head) {
    for (let i = 0; i < a1.spine.length; i++) unify(ctx, a1.spine[i], b1.spine[i]);
    return;
  }

  throw Error(`cannot unify: ${quote(a1)} vs ${quote(b1)}`);
}

// Solve meta: ?alpha[spine] = rhs
function solveMeta(ctx: Ctx, id: number, spine: Value[], rhs: Value): void {
  // Pattern check: spine must be distinct bound variables
  const vars = spine.map(v => {
    const f = force(v);
    if (f.tag !== 'VVar') throw Error('non-pattern spine');
    return f.level;
  });
  if (new Set(vars).size !== vars.length) throw Error('non-linear pattern');

  // Occurs check
  if (occursMeta(id, rhs)) throw Error(`occurs check: ?${id}`);

  // Scope check: FV(rhs) must be subset of spine variables
  const freeVars = freeVarsOf(rhs);
  for (const v of freeVars) {
    if (!vars.includes(v)) throw Error(`scope escape: var ${v} not in meta spine`);
  }

  // Solution: ?alpha := \x1...xn. rhs  (with appropriate renaming)
  const solution = buildLambda(vars, rhs);
  metas[id].solution = solution;
}

// Bidirectional elaboration
function elabCheck(ctx: Ctx, surface: SurfaceExpr, expected: Value): Term {
  // Implicit argument insertion
  const exp = force(expected);
  if (exp.tag === 'VPi' && exp.implicit) {
    const meta = freshMeta(ctx, exp.domain);
    const body = elabCheck(ctx, surface, applyVal(exp.codomain, evalTerm(ctx, meta)));
    return { tag: 'App', fn: { tag: 'Lam', implicit: true, body }, arg: meta };
  }

  if (surface.tag === 'SLam' && exp.tag === 'VPi') {
    const x = freshVar(ctx);
    const body = elabCheck(
      extendCtx(ctx, x, exp.domain), surface.body,
      applyVal(exp.codomain, x));
    return { tag: 'Lam', name: surface.param, body };
  }

  // Fallback: infer and unify
  const [term, inferred] = elabInfer(ctx, surface);
  unify(ctx, inferred, expected);
  return term;
}

function elabInfer(ctx: Ctx, surface: SurfaceExpr): [Term, Value] {
  if (surface.tag === 'SVar') {
    const [term, ty] = lookupCtx(ctx, surface.name);
    return [term, ty];
  }
  if (surface.tag === 'SAnn') {
    const tyTerm = elabCheck(ctx, surface.type, VType);
    const tyVal = evalTerm(ctx, tyTerm);
    const term = elabCheck(ctx, surface.expr, tyVal);
    return [{ tag: 'Ann', term, type: tyTerm }, tyVal];
  }
  if (surface.tag === 'SApp') {
    const [fn, fnTy] = elabInfer(ctx, surface.fn);
    const fTy = force(fnTy);
    if (fTy.tag !== 'VPi') throw Error('expected function type');
    const arg = elabCheck(ctx, surface.arg, fTy.domain);
    return [{ tag: 'App', fn, arg }, applyVal(fTy.codomain, evalTerm(ctx, arg))];
  }
  if (surface.tag === 'SHole') {
    const ty = evalTerm(ctx, freshMeta(ctx, VType));
    return [freshMeta(ctx, ty), ty];
  }
  throw Error('cannot infer');
}
```

### Pragmatic Implementation

- **Normalization by Evaluation (NbE).** Use closures (environment + term body) instead of substitution for O(1) variable lookup during evaluation. Essential for performance in dependently typed elaboration.
- **Glued evaluation.** Maintain both a value (for computation) and a term (for error messages) simultaneously, avoiding re-quoting.
- **Zonking pass.** Do a single final pass to substitute all solved metas, rather than forcing repeatedly during elaboration. Produces clean core terms.
- **Path compression for metas.** When meta `?0` is solved to `?1` which is solved to `t`, short-circuit `?0` directly to `t`.
- **Spine representation.** Use a linked list or finger tree for spines to enable O(1) prepend.
- **Lazy forcing with memoization.** Cache the result of forcing a meta-applied spine to avoid re-traversal.
- **De Bruijn indices vs levels.** Indices count from the innermost binder (0 = closest), levels count from the outermost (0 = first binding). Levels are more convenient for metavariable solving because they are stable under context extension.

### Common Pitfalls

1. **Forgetting to force/zonk.** Always call `force()` before inspecting a Value. An unsolved meta may have been solved since the value was created. This is the most frequent elaboration bug.
2. **Scope escape.** A metavariable solution must only reference variables in the meta's declaration context, not the use-site context. Failing to check this causes unsound scope extrusion.
3. **Occurs check omission.** Without it, `?0 = List(?0)` produces cyclic terms, causing non-termination.
4. **Ordering sensitivity.** Elaboration order matters. Left-to-right vs right-to-left argument checking can lead to different meta-solving outcomes. Document the chosen order.
5. **Confusing de Bruijn indices and levels.** Indices count inward, levels count outward. Mixing them up causes subtle variable reference bugs.
6. **Eta-expansion neglect.** Failing to eta-expand during unification causes spurious failures (e.g., `f` should unify with `\x -> f x`).
7. **Non-termination with non-pattern spines.** Outside the pattern fragment, metavariable solving may not terminate. Use timeouts or fuel-based limits in practice.

### Cross-References

- Pattern unification as a specialization of first-order unification: Section 7
- Bidirectional structure used in elaboration: Section 2
- HM inference as a special case (no dependent types, no metas): Section 1
- Key references: Norell 2007 (Agda), Miller 1991 (pattern unification), Huet 1973 (higher-order undecidability), Kovacs ("Elaboration Zoo" tutorial)
- See also: `01-theory-foundations.md` Section 6 (Dependent Types / Martin-Lof Type Theory)
