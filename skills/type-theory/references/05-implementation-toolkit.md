# PL Implementation Toolkit

Builder's reference: maximum TypeScript pseudocode density, minimum pure theory. Every section has runnable or near-runnable code. Cross-references point to companion files in this directory.

---

## 1. Normalization by Evaluation (NbE)

### Formal Foundations

NbE computes normal forms of lambda-terms in two phases:
1. **Evaluation** (`eval`): interpret term into a semantic domain D where function types become meta-language functions
2. **Readback / Reification** (`quote`): read back the semantic value into a syntactic normal form

The semantic domain for STLC:
- `D(base)` = neutral terms (stuck applications, free variables)
- `D(A → B)` = meta-language functions `D(A) → D(B)`

This yields **η-long β-normal forms** without explicit η-reduction rules. Berger & Schwichtenberg 1991; extended to dependent types by Abel, Coquand, Dybjer.

### Core Algorithm

Complete de Bruijn level implementation (levels, not indices, in the semantic domain — avoids fresh name generation):

```typescript
type Val = { tag: 'VLam'; fn: (v: Val) => Val }
         | { tag: 'VNeutral'; neu: Neutral };
type Neutral = { tag: 'NVar'; lvl: number }
             | { tag: 'NApp'; fn: Neutral; arg: Val };
type Term = { tag: 'Var'; idx: number }   // de Bruijn index
          | { tag: 'Lam'; body: Term }
          | { tag: 'App'; fn: Term; arg: Term };

function eval_(env: Val[], t: Term): Val {
  if (t.tag === 'Var')  return env[env.length - 1 - t.idx];
  if (t.tag === 'Lam')  return { tag: 'VLam', fn: v => eval_([...env, v], t.body) };
  const fn = eval_(env, t.fn) as { tag: 'VLam'; fn: (v: Val) => Val };
  return fn.fn(eval_(env, t.arg));
}

function quote(lvl: number, v: Val): Term {
  if (v.tag === 'VLam')
    return { tag: 'Lam', body: quote(lvl + 1, v.fn({ tag: 'VNeutral', neu: { tag: 'NVar', lvl } })) };
  return quoteNeu(lvl, v.neu);
}
function quoteNeu(lvl: number, n: Neutral): Term {
  if (n.tag === 'NVar')  return { tag: 'Var', idx: lvl - n.lvl - 1 };
  return { tag: 'App', fn: quoteNeu(lvl, n.fn), arg: quote(lvl, n.arg) };
}
const normalize = (t: Term) => quote(0, eval_([], t));
// normalize(t) gives η-long β-normal form — no explicit η-reduction rules needed
```

For dependent type theories, extend `Val` with `VPi`, `VSigma`, `VU` etc. and extend `quote` with corresponding readback cases. The `eval_` function gets a `Type` parameter for type-directed η-expansion.

### Pragmatic Implementation

```typescript
// Conversion checking (equality) without full normalization
// Compare structurally, short-circuiting at first mismatch
function convVal(lvl: number, v1: Val, v2: Val): boolean {
  if (v1.tag === 'VLam' || v2.tag === 'VLam') {
    // η-expand: apply both to a fresh neutral variable
    const x: Val = { tag: 'VNeutral', neu: { tag: 'NVar', lvl } };
    const r1 = v1.tag === 'VLam' ? v1.fn(x) : { tag: 'VNeutral', neu: { tag: 'NApp', fn: (v1 as any).neu, arg: x } };
    const r2 = v2.tag === 'VLam' ? v2.fn(x) : { tag: 'VNeutral', neu: { tag: 'NApp', fn: (v2 as any).neu, arg: x } };
    return convVal(lvl + 1, r1 as Val, r2 as Val);
  }
  // Both neutral: compare structurally
  return convNeu(lvl, (v1 as any).neu, (v2 as any).neu);
}

function convNeu(lvl: number, n1: Neutral, n2: Neutral): boolean {
  if (n1.tag === 'NVar' && n2.tag === 'NVar') return n1.lvl === n2.lvl;
  if (n1.tag === 'NApp' && n2.tag === 'NApp')
    return convNeu(lvl, n1.fn, n2.fn) && convVal(lvl, n1.arg, n2.arg);
  return false;
}
```

**Glued evaluation** (Abel 2013) — maintain a semantic value *plus* an unfolded term for efficient definition unfolding in conversion checking:

```typescript
type Glued = { sem: Val; term: () => Term };  // lazy syntactic unfolding
```

### Common Pitfalls

1. **Missing η-expansion in readback**: `quote` at function type must always produce a `Lam`, even for neutrals. Omitting this gives β-normal but not η-long forms — two η-equivalent terms won't compare equal.
2. **Level/index confusion**: De Bruijn *levels* increment with the environment size (outside-in); de Bruijn *indices* count from the innermost binder (inside-out). Mixing them causes wrong variable capture. The `idx = lvl - n.lvl - 1` formula converts levels back to indices during readback.
3. **Non-termination with general recursion**: NbE only terminates for strongly normalizing systems. Adding unrestricted `fix` causes `eval_` to loop.
4. **Applying NbE to non-well-typed terms**: NbE assumes the term is well-typed. Applying it to ill-typed terms produces undefined behavior (pattern match failures on `fn.fn`).

### Cross-References

- Bidirectional checking using NbE for conversion: `02-inference-checking.md` §3
- Dependent type elaboration with NbE: `03-type-system-design.md` §5

---

## 2. Dependent Pattern Matching & Coverage Checking

### Formal Foundations

Dependent pattern matching extends standard matching: the types of later scrutinees may depend on values matched by earlier patterns. Coverage checking verifies:
1. **Exhaustiveness**: every possible constructor combination is covered
2. **Redundancy**: no clause is unreachable

The Maranget 2007 algorithm uses a *pattern matrix* where rows are clauses and columns are scrutinee positions. Specialization removes rows that cannot match a given constructor; the default matrix collects rows with wildcards/variables at the head column.

### Core Algorithm

Maranget 2007 specialization + exhaustiveness (simplified, non-dependent):

```typescript
type Pat = { tag: 'Con'; name: string; args: Pat[] } | { tag: 'Var' } | { tag: 'Wildcard' };
type PatMatrix = Pat[][];  // rows = clauses, cols = positions

function specialize(P: PatMatrix, ctor: string, arity: number): PatMatrix {
  return P.flatMap(row => {
    const [hd, ...tl] = row;
    if (hd.tag === 'Con' && hd.name === ctor) return [[ ...hd.args, ...tl ]];
    if (hd.tag === 'Var' || hd.tag === 'Wildcard') return [[ ...Array(arity).fill({ tag: 'Wildcard' }), ...tl ]];
    return [];  // different constructor — remove row
  });
}

function isExhaustive(P: PatMatrix, types: string[]): boolean {
  if (P.length === 0) return false;   // no clauses: not exhaustive
  if (types.length === 0) return true; // no scrutinee left: some clause matches everything
  const [headType, ...restTypes] = types;
  const ctors = constructorsOf(headType);  // all constructors of headType with their arities
  return ctors.every(({ name, arity }) =>
    isExhaustive(specialize(P, name, arity), [...Array(arity).fill('_'), ...restTypes]));
}
```

Redundancy checking — a clause at row `i` is redundant if it is *not useful* with respect to the prefix `P[0..i-1]`:

```typescript
function isUseful(P: PatMatrix, q: Pat[], types: string[]): boolean {
  // q is useful (not redundant) if there exists a value matched by q but not any row of P
  if (types.length === 0) return P.length === 0;
  const [hd, ...tl] = q;
  if (hd.tag === 'Con') {
    const { arity } = constructorsOf(types[0]).find(c => c.name === hd.name)!;
    return isUseful(specialize(P, hd.name, arity), [...hd.args, ...tl], [...Array(arity).fill('_'), ...types.slice(1)]);
  }
  // Variable/Wildcard: check all constructors
  const ctors = constructorsOf(types[0]);
  return ctors.some(({ name, arity }) =>
    isUseful(specialize(P, name, arity), [...Array(arity).fill({ tag: 'Wildcard' }), ...tl], [...Array(arity).fill('_'), ...types.slice(1)]));
}
```

### Pragmatic Implementation

TypeScript's discriminated unions give built-in coverage via `never`-checking:

```typescript
type Shape = { kind: 'circle'; r: number }
           | { kind: 'rect'; w: number; h: number };

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle': return Math.PI * s.r ** 2;
    case 'rect':   return s.w * s.h;
    // No default needed: TypeScript checks exhaustiveness via narrowing
  }
  // Explicit exhaustiveness assertion:
  const _: never = s;  // Error if Shape has uncovered variant
  return _;
}
```

For full coverage checking with dependent types (Agda-style), integrate type refinement per constructor:

```typescript
// After matching Con(C_i, args), add to context: scrutinee = C_i(args)
// Unify forced patterns (dot patterns) via the type-level substitution
// Detect absurd patterns by checking if the scrutinee type is uninhabited after unification
```

### Common Pitfalls

1. **GADT type refinement omission**: When a GADT constructor constrains type variables, the coverage checker must refine the type context per branch. Missing this causes false "missing pattern" warnings.
2. **Infinite unfolding of recursive types**: For `Nat`, do not unfold constructors recursively without a depth bound. Use wildcard generalization for recursive positions.
3. **Guard clauses**: Guards make exhaustiveness undecidable. Use a conservative approximation (ignore guards, warn that exhaustiveness is assumed).
4. **Or-pattern expansion**: Expand `(p1 | p2)` before building the pattern matrix to avoid unsoundness.
5. **Column selection heuristic**: Checking columns with the most distinct constructors first reduces recursive calls.

### Cross-References

- GADT pattern matching type refinement: `03-type-system-design.md` §4
- Dependent types (indexed families, `with`-abstraction): `01-theory-foundations.md` §6

---

## 3. Tagless Final / Finally Tagless

### Formal Foundations

The *tagless-final* approach (Carette, Kiselyov, Shan 2009) encodes a typed DSL not as an ADT (initial encoding) but as a parameterized interface (final encoding). Each expression `e : τ` in the object language is a value of type `R` in the metalanguage, where `R` is the interpretation type.

- **Initial encoding**: `type Expr = Lit of int | Add of Expr * Expr` — one ADT, many interpreters via structural recursion
- **Final encoding**: `interface ExprSym<R> { lit(n: number): R; add(l: R, r: R): R }` — one program, many interpreters via interface instantiation

The object language is the intersection of all models; a program `<R>(S: ExprSym<R>): R` is well-typed in every model simultaneously.

### Core Algorithm

```typescript
interface ExprSym<R> {
  lit(n: number): R;
  add(l: R, r: R): R;
  neg(e: R): R;
}
// Multiple interpreters — no sum type needed
const evalSym: ExprSym<number> = { lit: n => n, add: (l,r) => l+r, neg: e => -e };
const showSym: ExprSym<string> = { lit: n => `${n}`, add: (l,r) => `(${l}+${r})`, neg: e => `(-${e})` };
// DSL program: parameterized over representation
const prog = <R>(S: ExprSym<R>): R => S.add(S.lit(1), S.neg(S.lit(2)));
// prog(evalSym) = -1;  prog(showSym) = "(1+(-2))"
```

Extension without touching existing code — open DSL via interface merging:

```typescript
interface MulSym<R> extends ExprSym<R> {
  mul(l: R, r: R): R;
}
const evalMul: MulSym<number> = { ...evalSym, mul: (l,r) => l*r };
const prog2 = <R>(S: MulSym<R>): R => S.mul(S.lit(3), S.add(S.lit(1), S.lit(2)));
// prog2(evalMul) = 9
```

Tagless final with HOAS for variable binding:

```typescript
interface LambdaSym<R> extends ExprSym<R> {
  lam(f: (x: R) => R): R;
  app(fn: R, arg: R): R;
  letIn(v: R, f: (x: R) => R): R;
}
// prog: \x -> x + 1
const prog3 = <R>(S: LambdaSym<R>): R => S.lam(x => S.add(x, S.lit(1)));
```

### Pragmatic Implementation

```typescript
// CPS representation for control flow (exceptions, coroutines)
type CPS<A> = (k: (a: A) => void) => void;
const evalCPS: ExprSym<CPS<number>> = {
  lit: n => k => k(n),
  add: (l, r) => k => l(a => r(b => k(a + b))),
  neg: e => k => e(a => k(-a)),
};

// Product interpretation: run two interpreters in one pass
type Both<A, B> = [A, B];
function bothSym<A, B>(sa: ExprSym<A>, sb: ExprSym<B>): ExprSym<Both<A,B>> {
  return {
    lit: n => [sa.lit(n), sb.lit(n)],
    add: ([la,lb], [ra,rb]) => [sa.add(la,ra), sb.add(lb,rb)],
    neg: ([ea,eb]) => [sa.neg(ea), sb.neg(eb)],
  };
}
// prog(bothSym(evalSym, showSym)) = [-1, "(1+(-2))"]
```

### Common Pitfalls

1. **Eager branch evaluation**: In TypeScript (strict), both branches of `if_` evaluate eagerly. Use `() => R` thunks for conditional branches.
2. **HOAS serialization barrier**: Functions as binders cannot be serialized, compared, or pattern-matched. If you need those operations, use a first-order representation (de Bruijn or named variables).
3. **Non-compositional rewrites**: Optimizations like `x + 0 → x` require inspecting sub-expression structure — impossible with final encoding. Use a hybrid: initial encoding for optimization passes, final for interpretation.
4. **Type widening in product interpretation**: TypeScript may widen `Both<A,B>` tuple types; use `readonly [A, B]` or explicit type annotations.

### Cross-References

- Free monad vs. tagless final tradeoffs: §4 below
- aiqeung ReactiveExpr as Free Monad: aiqeung Worked Examples §1

---

## 4. Free Monads & Effect Systems

### Formal Foundations

The free monad over functor `F` is the least fixed point of `Free F A = A | F (Free F A)`. It is *free* in the categorical sense: it satisfies the monad laws by construction, and every F-algebra `F A → A` extends uniquely to a monad morphism `Free F A → A`.

The *Freer monad* (Kiselyov & Ishii 2015) relaxes the functor requirement:

```
Freer F A = Pure A | ∃X. F X × (X → Freer F A)
```

This allows effect operations `F` to be plain data types (no `fmap` needed), and makes composition of effects via coproducts trivial.

### Core Algorithm

```typescript
type Free<F, A> = { tag: 'Pure'; val: A }
               | { tag: 'Do'; op: F; cont: (r: unknown) => Free<F, A> };

const pure = <F, A>(val: A): Free<F, A> => ({ tag: 'Pure', val });
const liftF = <F, A>(op: F): Free<F, A> => ({ tag: 'Do', op, cont: r => pure(r as A) });
const chain = <F, A, B>(m: Free<F, A>, f: (a: A) => Free<F, B>): Free<F, B> =>
  m.tag === 'Pure' ? f(m.val) : { tag: 'Do', op: m.op, cont: r => chain(m.cont(r), f) };

function runFree<F, A, M>(
  handler: (op: F, k: (r: unknown) => M) => M,
  ret: (a: A) => M,
  m: Free<F, A>
): M {
  return m.tag === 'Pure' ? ret(m.val) : handler(m.op, r => runFree(handler, ret, m.cont(r)));
}
```

Effect coproduct — combining multiple effect types:

```typescript
type StateEff = { tag: 'Get' } | { tag: 'Put'; s: number };
type LogEff   = { tag: 'Log'; msg: string };
type AppEff   = StateEff | LogEff;

const get: Free<AppEff, number>   = liftF({ tag: 'Get' });
const put = (s: number): Free<AppEff, void> => liftF({ tag: 'Put', s });
const log = (msg: string): Free<AppEff, void> => liftF({ tag: 'Log', msg });

// Program: increment state and log it
const program: Free<AppEff, void> =
  chain(get, n => chain(put(n + 1), () => log(`state: ${n + 1}`)));

// Handler: State part
function runState<A>(m: Free<AppEff, A>, s0: number): [A, number] {
  if (m.tag === 'Pure') return [m.val, s0];
  const op = m.op as AppEff;
  if (op.tag === 'Get') return runState(m.cont(s0), s0);
  if (op.tag === 'Put') return runState(m.cont(undefined), op.s);
  throw new Error('unhandled effect: ' + op.tag);
}
```

### Pragmatic Implementation

Church-encoded free monad to eliminate left-recursion overhead (O(n) bind → O(1)):

```typescript
type FreeC<F, A> = <R>(ret: (a: A) => R, handler: (op: F, k: (r: unknown) => R) => R) => R;

const pureC = <F, A>(a: A): FreeC<F, A> => (ret, _) => ret(a);
const liftC = <F, A>(op: F): FreeC<F, A> => (ret, handler) => handler(op, r => ret(r as A));
const chainC = <F, A, B>(m: FreeC<F, A>, f: (a: A) => FreeC<F, B>): FreeC<F, B> =>
  (ret, handler) => m(a => f(a)(ret, handler), handler);
const runC = <F, A>(m: FreeC<F, A>, ret: (a: A) => A, handler: (op: F, k: (r: unknown) => A) => A): A =>
  m(ret, handler);
```

Iterative (trampoline) handler to prevent stack overflow on deep programs:

```typescript
function runFreeIter<F, A>(
  handler: (op: F) => [unknown, (r: unknown) => Free<F, A>] | ['done', A],
  m: Free<F, A>
): A {
  let current = m;
  while (current.tag === 'Do') {
    const op = current.op;
    const cont = current.cont;
    const result = (handler as any)(op);
    if (result[0] === 'done') return result[1];
    current = cont(result[0]);
  }
  return current.val;
}
```

### Common Pitfalls

1. **Left-recursive bind (O(n²))**: Naive `chain` builds right-skewed trees but left-associative bind (`chain(chain(m, f), g)`) adds nodes to the left, requiring full traversal. Use type-aligned sequences or Church encoding.
2. **Stack overflow**: Deep recursive `runFree` blows V8's call stack at ~10K operations. Use iterative handlers or trampolining.
3. **Handler ordering semantics**: `runState(runError(m))` vs `runError(runState(m))` differ on error: inner handler can see or lose state depending on order.
4. **Effect leakage**: Forgetting to handle an effect leaves a `Do` node in the result — fails at runtime not compile time without effect-level phantom types.

### Cross-References

- aiqeung ReactiveExpr as Free Monad: aiqeung Worked Examples §1
- Algebraic effects as a lower-level alternative: §5 below
- Tagless final comparison: §3 above

---

## 5. Algebraic Effects & Handlers

### Formal Foundations

An *algebraic effect theory* is a signature Σ of operations `op_i : A_i → B_i` (parameter type → result type). A *computation tree* (free model) for signature Σ is:

```
c ::= return v           -- pure value
    | op(a, k)           -- perform op with param a, continuation k : B → Comp
```

A *handler* `h` for effect E interpreting into F-computations:

```
h = { return : A → Comp_F B,
      op_i   : (a : A_i, k : B_i → Comp_F B) → Comp_F B }
```

Handlers are *delimited* (dynamic scope limited to the handled region) and *modular* (each handler processes only its own operations, forwarding others).

### Core Algorithm

Generator-based algebraic effects (single-shot, practical):

```typescript
// Effect tag interface
interface Eff<Tag extends string, P, R> {
  readonly _tag: Tag; readonly param: P; readonly _result: R;
}

// Perform an effect (yield to handler)
function* perform<Tag extends string, P, R>(
  eff: Eff<Tag, P, R>
): Generator<Eff<Tag, P, R>, R, R> {
  return (yield eff) as R;
}

// Handler: process effects and return a result
function handle<E extends Eff<string, unknown, unknown>, A>(
  comp: Generator<E, A, unknown>,
  handlers: Record<string, (param: unknown, resume: (r: unknown) => unknown) => unknown>,
  ret: (a: A) => unknown
): unknown {
  function step(result: IteratorResult<E, A>): unknown {
    if (result.done) return ret(result.value);
    const eff = result.value;
    const h = handlers[eff._tag];
    if (!h) throw new Error(`Unhandled effect: ${eff._tag}`);
    return h(eff.param, (r: unknown) => step(comp.next(r) as IteratorResult<E, A>));
  }
  return step(comp.next());
}
```

State effect example:

```typescript
interface GetEff extends Eff<'Get', void, number> {}
interface PutEff extends Eff<'Put', number, void> {}
type StateEffect = GetEff | PutEff;

function* counter(): Generator<StateEffect, number, number | void> {
  const n = yield* perform<'Get', void, number>({ _tag: 'Get', param: undefined, _result: 0 });
  yield* perform<'Put', number, void>({ _tag: 'Put', param: n + 1, _result: undefined });
  return n;
}

function runStateEff<A>(m: Generator<StateEffect, A, unknown>, s0: number): [A, number] {
  let state = s0;
  const result = handle(m, {
    Get: (_, resume) => resume(state),
    Put: (s, resume) => { state = s as number; return resume(undefined); },
  }, a => a);
  return [result as A, state];
}
```

### Pragmatic Implementation

```typescript
// Multi-handler composition: pipe effects through a stack
function withLog<A>(
  comp: Generator<StateEffect, A, unknown>,
  s0: number
): [A, number, string[]] {
  const logs: string[] = [];
  let state = s0;
  const result = handle(comp, {
    Get: (_, resume) => { logs.push(`get -> ${state}`); return resume(state); },
    Put: (s, resume) => { logs.push(`put ${s}`); state = s as number; return resume(undefined); },
  }, a => a);
  return [result as A, state, logs];
}
```

Evidence-passing style (avoids tree allocation, Koka-inspired):

```typescript
// Instead of building a tree and interpreting it, pass the handler as an implicit capability
type StateCapability = { get: () => number; put: (n: number) => void };
function withState<A>(s0: number, f: (cap: StateCapability) => A): [A, number] {
  let s = s0;
  const cap: StateCapability = { get: () => s, put: n => { s = n; } };
  return [f(cap), s];
}
```

### Common Pitfalls

1. **Multi-shot resumptions**: Generators only support single-shot `resume`. CPS-based implementations are needed for `choose` (backtracking) or `fork` (concurrency). Do not use generators for multi-shot effects.
2. **Effect interception collision**: Two handlers for the same tag in nested scopes — inner catches effects meant for outer. Use unique symbols as tags.
3. **Forgetting to resume**: A handler that doesn't call `resume` silently discards the continuation (like an uncaught exception with no rethrow).
4. **Stack overflow**: Without trampolining, deeply nested `handle` calls overflow. Use iterative stepping (while loop over `comp.next()`).

### Cross-References

- Free monads as an alternative encoding: §4 above
- aiqeung three-phase tick interpreter as handler: aiqeung Worked Examples §1

---

## 6. Phantom Types & Type-Level Programming

### Formal Foundations

A **phantom type** is a type parameter that does not appear in the runtime representation (right-hand side of the data definition). It exists solely at the type level for compile-time safety.

```
data Expr<T> = Expr { unExpr: unknown }
-- T is phantom: unused at runtime, but enforces type discipline statically
```

TypeScript phantom types use branded intersections:

```typescript
declare const __brand: unique symbol;
type Brand<T, B> = T & { readonly [__brand]: B };
// B is erased at runtime; only present in types
```

### Core Algorithm

Type-safe state machine using phantom types (states as type tags):

```typescript
type State = 'Open' | 'Locked' | 'Closed';
declare const __state: unique symbol;
type Handle<S extends State> = { readonly [__state]: S; readonly fd: number };

const open   = (path: string): Handle<'Open'>   => ({ [__state]: 'Open',   fd: 0 } as any);
const lock   = (h: Handle<'Open'>):   Handle<'Locked'> => ({ ...h, [__state]: 'Locked' }   as any);
const unlock = (h: Handle<'Locked'>): Handle<'Open'>   => ({ ...h, [__state]: 'Open' }     as any);
const close  = (h: Handle<'Open'>):   Handle<'Closed'> => ({ ...h, [__state]: 'Closed' }   as any);
// close(lock(open('f')))  ← Type error: expected Handle<'Open'>, got Handle<'Locked'>
```

Phantom types for units of measure:

```typescript
type Kg     = Brand<number, 'Kg'>;
type Lb     = Brand<number, 'Lb'>;
type Meters = Brand<number, 'Meters'>;
type Feet   = Brand<number, 'Feet'>;

const kg = (n: number): Kg => n as Kg;
const lb = (n: number): Lb => n as Lb;

// addKg : (Kg, Kg) → Kg  — cannot add Kg to Lb
const addKg = (a: Kg, b: Kg): Kg => (a + b) as Kg;
const toKg  = (n: Lb): Kg => (n * 0.453592) as Kg;

// addKg(kg(5), lb(10))   ← Type error: Lb is not assignable to Kg
```

### Pragmatic Implementation

Refined string types using template literals + phantom:

```typescript
type SqlSafe<S extends string> = Brand<S, 'SqlSafe'>;
const sanitize = (input: string): SqlSafe<string> => {
  // escape SQL injection characters
  return input.replace(/'/g, "''") as SqlSafe<string>;
};
function query(sql: SqlSafe<string>): unknown { /* ... */ return null; }
// query("DROP TABLE users")  ← Type error: string is not SqlSafe<string>
// query(sanitize(userInput)) ← OK
```

Type-safe builder pattern with phantom state accumulation:

```typescript
type QueryState = { selected: boolean; filtered: boolean; ordered: boolean };
type Query<S extends Partial<QueryState>, T> = { sql: string; __state: S; __table: T };

function select<T>(table: string): Query<{ selected: true }, T> {
  return { sql: `SELECT * FROM ${table}`, __state: { selected: true } } as any;
}
function where<S extends { selected: true }, T>(
  q: Query<S, T>, cond: string
): Query<S & { filtered: true }, T> {
  return { ...q, sql: q.sql + ` WHERE ${cond}` } as any;
}
function orderBy<S extends { selected: true }, T>(
  q: Query<S, T>, col: string
): Query<S & { ordered: true }, T> {
  return { ...q, sql: q.sql + ` ORDER BY ${col}` } as any;
}
// orderBy(select('users'), 'id')        → OK
// where(orderBy(select('users'), 'id'), 'age > 18')  ← Type error if using phantom constraint
```

### Common Pitfalls

1. **Structural typing escape**: Two branded types with the same brand string are identical in TypeScript. Use `unique symbol` (not string literals) for brands to prevent collisions.
2. **Forgetting `as const`**: Without `as const`, TypeScript widens literals (e.g., `'hello'` becomes `string`), losing precision for type-level computation.
3. **Unexpected distribution in conditional types**: `type IsString<T> = T extends string ? true : false` returns `true | false` for `T = string | number` because conditional types distribute over bare type parameters. Use `[T] extends [string]` to prevent.
4. **`__brand` erasure vs. runtime access**: The brand property is a type-only fiction. Accessing `obj[__brand]` at runtime always returns `undefined`. Never use it for runtime dispatch.

### Cross-References

- Phantom types as lightweight refinement types: §7 (Peano encoding extends this)
- Layer 6 vocabulary phantom types: aiqeung Worked Examples §2

---

## 7. Type-Level Arithmetic & Peano Encoding

### Formal Foundations

Peano numerals encode natural numbers inductively:
- `Zero = 0`
- `Succ(n) = n + 1`

In TypeScript, Peano numerals are encoded via *tuple length*:
- `type N = [unknown, unknown, unknown]` represents 3
- Arithmetic uses variadic tuple operations: `[...A, ...B]['length']` for addition

This is more efficient than recursive `Succ` wrapping because `[...A, ...B]` is O(1) to type-check vs O(n) recursive conditional type expansion.

### Core Algorithm

```typescript
// Convert numeric literal → tuple (the Peano representation)
type BuildTuple<N extends number, Acc extends unknown[] = []> =
  Acc['length'] extends N ? Acc : BuildTuple<N, [...Acc, unknown]>;

// Addition: concatenate tuples
type Add<A extends number, B extends number> =
  [...BuildTuple<A>, ...BuildTuple<B>]['length'] & number;

// Subtraction: peel elements off A using B as counter
type Sub<
  A extends number, B extends number,
  TA extends unknown[] = BuildTuple<A>,
  TB extends unknown[] = BuildTuple<B>
> = TB extends [unknown, ...infer RB]
  ? TA extends [unknown, ...infer RA] ? Sub<A, B, RA, RB> : 0
  : TA['length'] & number;

// Multiplication: repeated addition via recursion
type Mul<
  A extends number, B extends number,
  Acc extends unknown[] = []
> = B extends 0 ? Acc['length'] & number
  : Mul<A, Sub<B, 1>, [...Acc, ...BuildTuple<A>]>;

// Less-than comparison
type LT<A extends number, B extends number> =
  Sub<B, A> extends 0 ? false : true;

// Static assertion pattern
type Assert<T extends true> = T;
type _checks = [
  Assert<Add<3, 4> extends 7 ? true : false>,
  Assert<Sub<10, 3> extends 7 ? true : false>,
  Assert<Mul<3, 4> extends 12 ? true : false>,
];
```

Type-level vectors (fixed-length arrays):

```typescript
type Vec<N extends number, A, Acc extends A[] = []> =
  Acc['length'] extends N ? Acc : Vec<N, A, [...Acc, A]>;

type Vec3<A> = Vec<3, A>;          // [A, A, A]
type Vec5<A> = Vec<5, A>;          // [A, A, A, A, A]

// Safe head: only callable on non-empty vectors
type Head<V extends unknown[]> = V extends [infer H, ...unknown[]] ? H : never;
type Tail<V extends unknown[]> = V extends [unknown, ...infer T] ? T : never;

// Concatenation preserves lengths
type Concat<A extends unknown[], B extends unknown[]> = [...A, ...B];
type ConcatLen<A extends number, B extends number> = Add<A, B>;
```

### Pragmatic Implementation

Dimensional analysis (compile-time unit checking):

```typescript
// Dimension vector: [mass, length, time, ...]
type Dim = [number, number, number];  // but we want type-level numbers

type DimAdd<D1 extends number[], D2 extends number[]> =
  D1 extends [infer A extends number, ...infer RA extends number[]]
  ? D2 extends [infer B extends number, ...infer RB extends number[]]
    ? [Add<A, B>, ...DimAdd<RA, RB>]
    : D1
  : [];

// Quantity with phantom dimension
declare const __dim: unique symbol;
type Quantity<D extends number[]> = number & { readonly [__dim]: D };

type Meters    = Quantity<[0, 1, 0]>;  // [mass=0, length=1, time=0]
type Seconds   = Quantity<[0, 0, 1]>;
type MetersPerSec = Quantity<[0, 1, -1]>;  // but negative Peano is tricky — use signed encoding

const meters   = (n: number): Meters => n as Meters;
const seconds  = (n: number): Seconds => n as Seconds;
```

### Common Pitfalls

1. **Recursion depth explosion**: `Mul<30, 30>` creates 900 recursive steps. TypeScript's ~1000 conditional type limit is easily hit. Test with the maximum expected values.
2. **Missing `& number` intersection**: Without `& number`, `T['length']` returns `number` (not a literal) when the compiler cannot resolve statically. Always intersect.
3. **Non-tail recursion depth**: Non-tail-recursive conditional types hit ~50 depth limit. Tail-recursive forms hit ~1000. Rewrite to accumulator pattern (`Acc extends unknown[] = []`).
4. **Negative numbers**: Tuple length cannot represent negatives. Use tagged encoding `{ sign: '+' | '-'; mag: number }` at type level for signed arithmetic.

### Cross-References

- HKT encodings (extends Peano techniques): §8 below
- Phantom types for dimension: §6 above

---

## 8. HKT Encodings in TypeScript

### Formal Foundations

TypeScript lacks native higher-kinded types (kind `* → *` cannot be abstracted). The **defunctionalization** approach (Yallop & White 2014, implemented in fp-ts) encodes type constructors as URI strings and uses a global interface for type-level application:

```
Kind<'Array', A> = Array<A>
Kind<'Option', A> = Option<A>
```

Declaration merging fills the `URItoKind<A>` interface:

```typescript
interface URItoKind<A> { readonly 'Array': Array<A>; readonly 'Option': Option<A> }
```

Type classes (Functor, Monad etc.) are expressed as interfaces parameterized by `F extends URIS`.

### Core Algorithm

```typescript
// ─── HKT infrastructure ──────────────────────────────────────
interface URItoKind<A> {}
interface URItoKind2<E, A> {}
type URIS  = keyof URItoKind<unknown>;
type URIS2 = keyof URItoKind2<unknown, unknown>;

type Kind<F extends URIS, A>       = URItoKind<A>[F];
type Kind2<F extends URIS2, E, A>  = URItoKind2<E, A>[F];

// ─── Type class interfaces ────────────────────────────────────
interface Functor<F extends URIS> {
  readonly URI: F;
  map<A, B>(fa: Kind<F, A>, f: (a: A) => B): Kind<F, B>;
}
interface Applicative<F extends URIS> extends Functor<F> {
  of<A>(a: A): Kind<F, A>;
  ap<A, B>(fab: Kind<F, (a: A) => B>, fa: Kind<F, A>): Kind<F, B>;
}
interface Monad<F extends URIS> extends Applicative<F> {
  chain<A, B>(fa: Kind<F, A>, f: (a: A) => Kind<F, B>): Kind<F, B>;
}

// ─── Register Option ─────────────────────────────────────────
type Option<A> = { readonly _tag: 'Some'; readonly value: A } | { readonly _tag: 'None' };
const some = <A>(value: A): Option<A> => ({ _tag: 'Some', value });
const none: Option<never> = { _tag: 'None' };

declare module './hkt' {   // or wherever URItoKind is declared
  interface URItoKind<A> { readonly 'Option': Option<A>; }
}

const optionMonad: Monad<'Option'> = {
  URI: 'Option',
  map: (fa, f) => fa._tag === 'Some' ? some(f(fa.value)) : none,
  of: some,
  ap: (fab, fa) =>
    fab._tag === 'Some' && fa._tag === 'Some' ? some(fab.value(fa.value)) : none,
  chain: (fa, f) => fa._tag === 'Some' ? f(fa.value) : none,
};
```

Generic algorithms that work over any registered monad:

```typescript
function sequence<F extends URIS, A>(M: Monad<F>, fas: Kind<F, A>[]): Kind<F, A[]> {
  return fas.reduce(
    (acc, fa) => M.chain(acc, xs => M.map(fa, x => [...xs, x])),
    M.of<A[]>([])
  );
}

// sequence(optionMonad, [some(1), some(2), some(3)])  → Some([1, 2, 3])
// sequence(optionMonad, [some(1), none, some(3)])      → None
```

### Pragmatic Implementation

```typescript
// Pipe utility for readable HKT chains
const pipe = <A>(a: A, ...fns: Array<(x: any) => any>) =>
  fns.reduce((acc, fn) => fn(acc), a);

// Example: parse, validate, transform using HKT-polymorphic operations
const program = pipe(
  "42",
  s => optionMonad.of(parseInt(s, 10)),
  n => optionMonad.chain(n, v => isNaN(v) ? none : some(v)),
  n => optionMonad.map(n, v => v * 2),
);
// program: Option<number> = Some(84)
```

### Common Pitfalls

1. **URI collision**: Two type constructors with the same URI string silently merge. Use namespaced URIs (`'@mylib/Option'`) for libraries.
2. **Forgotten module import**: If the module that extends `URItoKind` is not imported, `Kind<F, A>` resolves to `never`, causing confusing downstream errors.
3. **Inference collapse in deep chains**: Deeply nested HKT expressions (`chain(chain(chain(...)))`) cause TypeScript to collapse to `unknown`/`any`. Use `pipe` to linearize.
4. **Build configuration issues**: Declaration merging may fail across separate compilation units in some `tsconfig` setups. Ensure `composite: true` and proper project references.

### Cross-References

- Free monads use HKT for functor-polymorphic programs: §4 above
- Recursion schemes use HKT for `Fix<F>`: §11 below

---

## 9. Type-Level Turing Completeness & Decidability in TypeScript

### Formal Foundations

TypeScript's type system is Turing complete. The key features:
1. **Conditional types** (`T extends U ? X : Y`): branching
2. **Recursive type aliases**: unbounded iteration (TS 3.7+)
3. **Mapped types** (`{ [K in keyof T]: F<T[K]> }`): iteration over structure
4. **Template literal types**: string-level computation
5. **Infer in conditional types**: pattern matching on types

Consequence: type checking TypeScript can be undecidable. The compiler imposes pragmatic limits:
- Non-tail-recursive conditional types: depth ~50
- Tail-recursive (last position): depth ~1000
- Template literal recursion: separate depth limit
- Instantiation limit: ~1M total type instantiations

### Core Algorithm

Type-level lambda calculus evaluator (demonstrates Turing completeness):

```typescript
// Church booleans at type level
type True_  = <A, B>(a: A) => (b: B) => A;
type False_ = <A, B>(a: A) => (b: B) => B;

// Using tuples for Peano + conditional types for computation
type If<Cond extends boolean, T, F> = Cond extends true ? T : F;

// Type-level Fibonacci (tail-recursive with accumulator)
type FibAcc<
  N extends number,
  A extends unknown[],   // fib(n-1) as tuple
  B extends unknown[],   // fib(n) as tuple
> = N extends 0
  ? A['length'] & number
  : FibAcc<Sub<N, 1>, B, [...A, ...B]>;

type Fib<N extends number> = FibAcc<N, [unknown], [unknown]>;
// Fib<10> = 55  (computed at compile time)
```

Type-level string parser (demonstrates template literal Turing completeness):

```typescript
// Parse a decimal number from a string at type level
type Digit = '0'|'1'|'2'|'3'|'4'|'5'|'6'|'7'|'8'|'9';
type IsDigit<S extends string> = S extends Digit ? true : false;

type ParseInt<S extends string, Acc extends unknown[] = []> =
  S extends `${infer D extends Digit}${infer Rest}`
    ? ParseInt<Rest, [...Acc, ...BuildTuple<D extends '0' ? 0 : D extends '1' ? 1 : D extends '2' ? 2 : D extends '3' ? 3 : D extends '4' ? 4 : D extends '5' ? 5 : D extends '6' ? 6 : D extends '7' ? 7 : D extends '8' ? 8 : 9>]>
    : Acc['length'] & number;

type _42 = ParseInt<'42'>;   // = 42
```

### Pragmatic Implementation

Practical type-level validation (not just academic exercises):

```typescript
// Validate tuple has unique elements at type level
type UnionToIntersection<U> = (U extends any ? (x: U) => void : never) extends (x: infer I) => void ? I : never;
type IsUnion<T> = [T] extends [UnionToIntersection<T>] ? false : true;

// String path access: ensure path exists in deeply nested object
type DeepGet<T, Path extends string> =
  Path extends `${infer K}.${infer Rest}`
    ? K extends keyof T ? DeepGet<T[K], Rest> : never
    : Path extends keyof T ? T[Path] : never;

type Config = { db: { host: string; port: number }; app: { name: string } };
type DBHost = DeepGet<Config, 'db.host'>;  // string
type Missing = DeepGet<Config, 'db.name'>; // never
```

### Common Pitfalls

1. **Accidental non-tail recursion**: Wrapping the recursive call (e.g., `Readonly<Recurse<T>>`) drops from ~1000 to ~50 depth limit. Keep the recursive call in the final `? X : Y` position.
2. **Union explosion**: Distributed conditional types over large unions: 20 elements × 3 levels = 8000 instantiations. Use `[T] extends [U]` to prevent distribution.
3. **Instantiation limit errors**: Complex type programs may hit `Type instantiation is excessively deep`. Cache results in named type aliases; avoid quadratic patterns.
4. **Template literal limits**: Template literal recursion has its own depth limit separate from conditional type limits. Do not compose both in the same recursive type.

### Cross-References

- Peano arithmetic foundations: §7 above
- HKT encodings use these techniques: §8 above

---

## 10. Theorems for Free (Parametricity)

### Formal Foundations

Parametricity (Reynolds 1983; Wadler 1989 "Theorems for Free!") states that every polymorphic function `f : ∀a. F(a)` is a *natural transformation*: for any types `A`, `B` and any function `g : A → B`,

```
F(g)(f_A) = f_B
```

where `F(g)` lifts `g` through the type constructor `F`. This gives *free theorems*: properties that hold for all implementations, derivable from the type signature alone.

Key examples:
- `f : ∀a. [a] → [a]` must return a permutation/subsequence of its input
- `f : ∀a. a → a` must be the identity (only parametric implementation)
- `f : ∀a. [a] → a` must be a selection function (head, last, etc.)
- `map(g) . f = f . map(g)` — naturality of list functions

### Core Algorithm

Free theorem derivation for `forall a. F(a) → G(a)`:

```typescript
// Free theorem: for any g: A → B and any relation R ⊆ A × B
// If (x, y) ∈ F(R) then (f(x), f(y)) ∈ G(R)
// This is the parametricity condition; for functions R = graph(g):
// G(g)(f(x)) = f(y) where F(g)(x) = y, i.e., naturality square

// Relation lifting rules:
// Lift(a)(R) = R                           if F(a) = a
// Lift(const T)(R) = identity on T         if F(a) = T (constant)
// Lift(A → B)(R)(f, g) = ∀(x,y) ∈ Lift(A)(R). (f(x), g(y)) ∈ Lift(B)(R)
// Lift([A])(R) = zip-wise: (xs, ys) ∈ Lift([A])(R) iff |xs|=|ys| and (xs_i, ys_i) ∈ Lift(A)(R)

// Worked example: derive free theorem for `reverse: ∀a. [a] → [a]`
// Theorem: map(g, reverse(xs)) = reverse(map(g, xs))
// Proof: apply parametricity with F = G = List, R = graph(g)
```

Naturality verification in TypeScript (runtime check for testing):

```typescript
function checkNaturality<A, B>(
  f: <T>(xs: T[]) => T[],
  xs: A[],
  g: (a: A) => B
): boolean {
  const lhs = f(xs).map(g);          // f then map
  const rhs = f(xs.map(g));          // map then f
  return JSON.stringify(lhs) === JSON.stringify(rhs);
}

// reverse is natural:
checkNaturality(xs => [...xs].reverse(), [1, 2, 3], (n: number) => n * 2);
// true: [6, 4, 2] === [6, 4, 2]
```

### Pragmatic Implementation

Free theorems enable **justified optimizations** (fusion rules that are provably correct):

```typescript
// map . map fusion (free theorem for map)
// map(g, map(f, xs)) = map(g . f, xs)  — eliminates intermediate array
const mapFuse = <A, B, C>(f: (a: A) => B, g: (b: B) => C, xs: A[]): C[] =>
  xs.map(x => g(f(x)));  // single pass; equivalent to xs.map(f).map(g)

// filterMap naturality: map(g, filterMap(f, xs)) = filterMap(mapOption(g) . f, xs)
function filterMap<A, B>(f: (a: A) => Option<B>, xs: A[]): B[] {
  const result: B[] = [];
  for (const x of xs) { const o = f(x); if (o._tag === 'Some') result.push(o.value); }
  return result;
}
// Free theorem allows fusing: map(g) . filterMap(f) = filterMap(x => mapOption(g, f(x)))
```

### Common Pitfalls

1. **TypeScript does NOT enforce parametricity**: A generic function can use `typeof`, `instanceof`, or JSON serialization to break it. Free theorems only hold for *truly parametric* implementations — verify the implementation does not inspect the type argument.
2. **Constrained polymorphism is not parametric**: `<A extends Comparable<A>>(x: A) => ...` gives access to comparison, breaking the free theorem. Free theorems require unconstrained type variables.
3. **Mutation invalidates naturality**: A function that mutates its input breaks `map(g) . f = f . map(g)` because f's side effect changes xs before the second application.
4. **Covariance/contravariance**: Free theorems for function types flip the relation direction for contravariant positions. Forgetting this gives incorrect fusion rules.

### Cross-References

- Tagless final interpreters are natural transformations: §3 above
- Recursion schemes (catamorphisms are natural transformations): §11 below

---

## 11. Recursion Schemes (Extended Family)

### Formal Foundations

A recursion scheme is structured (co)recursion factored through (co)algebras of an endofunctor `F`.

- **`Fix<F>`** = `μX. F(X)` — initial F-algebra carrier (finite inductive data)
- **`Nu<F>`** = `νX. F(X)` — final F-coalgebra carrier (potentially infinite coinductive data)
- **F-algebra**: `(A, α : F(A) → A)` — how to fold one layer into a value
- **F-coalgebra**: `(A, α : A → F(A))` — how to unfold a value into one layer

```typescript
// Fixed point (using a wrapper object)
interface Fix<F> { readonly unfix: HKTApply<F, Fix<F>> }
type Algebra<F, A>   = (layer: HKTApply<F, A>) => A;
type Coalgebra<F, A> = (seed: A) => HKTApply<F, A>;
```

### Core Algorithm

Complete morphism family (using concrete `NatF` for illustration):

```typescript
type NatF<R> = { tag: 'Zero' } | { tag: 'Succ'; pred: R };
const mapNat = <R, S>(f: (r: R) => S, n: NatF<R>): NatF<S> =>
  n.tag === 'Zero' ? { tag: 'Zero' } : { tag: 'Succ', pred: f(n.pred) };

interface FixNat { layer: NatF<FixNat> }
const wrap = (n: NatF<FixNat>): FixNat => ({ layer: n });
const unwrap = (n: FixNat): NatF<FixNat> => n.layer;

// Catamorphism (fold)
function cata<A>(alg: Algebra<'NatF', A>, n: FixNat): A {
  return alg(mapNat(m => cata(alg, m), unwrap(n)));
}

// Anamorphism (unfold)
function ana<A>(coalg: Coalgebra<'NatF', A>, seed: A): FixNat {
  return wrap(mapNat(s => ana(coalg, s), coalg(seed)));
}

// Hylomorphism (unfold then fold — no intermediate Fix needed)
function hylo<A, B>(alg: Algebra<'NatF', B>, coalg: Coalgebra<'NatF', A>, seed: A): B {
  return alg(mapNat(s => hylo(alg, coalg, s), coalg(seed)));
}

// Paramorphism (fold with access to original subterm)
function para<A>(alg: (layer: NatF<[FixNat, A]>) => A, n: FixNat): A {
  return alg(mapNat(m => [m, para(alg, m)], unwrap(n)));
}

// Histomorphism (fold with memoized previous results — for DP)
type Cofree<F, A> = { head: A; tail: HKTApply<F, Cofree<F, A>> };
function histo<A>(alg: (layer: NatF<Cofree<'NatF', A>>) => A, n: FixNat): A {
  function go(n: FixNat): Cofree<'NatF', A> {
    const layer = mapNat(go, unwrap(n));
    return { head: alg(layer), tail: layer };
  }
  return go(n).head;
}
```

### Quick-Reference Table

| Morphism | Direction | Pattern | Use case | TS type |
|---|---|---|---|---|
| `cata` | consume (fold down) | `(F A → A) → Fix F → A` | Evaluate, serialize, measure tree | `(alg: Alg<F,A>) => (t: Fix<F>) => A` |
| `ana` | produce (unfold up) | `(A → F A) → A → Fix F` | Generate, parse, corecursion | `(coalg: Coalg<F,A>) => (a: A) => Fix<F>` |
| `hylo` | produce then consume | `(F B → B) → (A → F A) → A → B` | Divide and conquer; parse + eval | composition of ana then cata |
| `para` | fold with original subtree | `(F (Fix F × A) → A) → Fix F → A` | Context-sensitive transformation | need both result and original |
| `histo` | fold with memoized history | `(F (Cofree F A) → A) → Fix F → A` | Dynamic programming | previous results cached |
| `futu` | unfold with lookahead | `(A → F (Free F A)) → A → Fix F` | Streaming, multi-step generation | can emit multiple levels at once |
| `apo` | unfold with early exit | `(A → F (Fix F ∨ A)) → A → Fix F` | Partial substitution | can short-circuit with an existing tree |

### Pragmatic Implementation

```typescript
// Shortcut fusion: replace cata . ana with hylo
// Instead of: cata(evalAlg, ana(parseCoalg, input))
// Use:        hylo(evalAlg, parseCoalg, input)  — no intermediate Fix allocation

// Banana split: fuse two catamorphisms into one pass
function splitCata<A, B>(
  algA: Algebra<'NatF', A>,
  algB: Algebra<'NatF', B>,
  n: FixNat
): [A, B] {
  return cata<[A, B]>(
    layer => [algA(mapNat(([a]) => a, layer)), algB(mapNat(([,b]) => b, layer))],
    n
  );
}
```

### Common Pitfalls

1. **Stack overflow on deep trees**: Direct recursive `cata` overflows V8 at ~10K nodes. Use an explicit stack with a while loop for production.
2. **Quadratic paramorphism**: Accessing the original subterm in `para` for size computation gives O(n²). Cache the size or use `zygo` (zygomorphism).
3. **Exponential hylomorphism for Fibonacci**: `hylo` with Fibonacci coalgebra produces an exponential call tree. Use `histo` for O(n) memoized access.
4. **HKT encoding fragility**: TypeScript URI-based HKT simulations require careful module import ordering. Missing import → `Kind<F, A>` resolves to `never`.

### Cross-References

- F-algebras in category theory context: `04-category-theory.md` §5
- Free monad as the free F-algebra: §4 above
- NbE uses a similar "initial algebra → semantic domain → readback" structure: §1 above

---

## 12. Denotational Semantics & Domain Theory

### Formal Foundations

Denotational semantics assigns a mathematical object `⟦e⟧` to each syntactic phrase `e` *compositionally*:

```
⟦C[e₁, ..., eₙ]⟧ = f(⟦e₁⟧, ..., ⟦eₙ⟧)
```

**Domain theory** provides the mathematical framework for handling recursion:
- **Partially ordered set (D, ⊑)**: `d ⊑ d'` means `d'` is more defined than `d`
- **Bottom (⊥)**: the least element; represents non-termination
- **Scott-continuous function**: monotone and preserves least upper bounds of chains
- **Least fixed point**: `fix(f) = ⊔{ f^n(⊥) | n ≥ 0 }` — Kleene's theorem

The semantic domains for IMP:
- `⟦Expr⟧ : State → ℤ⊥` — arithmetic expressions
- `⟦BExpr⟧ : State → 𝔹⊥` — boolean expressions
- `⟦Cmd⟧ : State⊥ → State⊥` — commands (state transformers)
- `⟦while b do c⟧ = fix(F)` where `F(φ)(σ) = if ⟦b⟧σ then φ(⟦c⟧σ) else σ`

### Core Algorithm

IMP denotational semantics with Kleene fixed-point iteration:

```typescript
type Value = number | boolean | undefined;  // undefined = ⊥
type Store = Map<string, Value>;
type Denotation = (s: Store) => Store | undefined;  // undefined = divergence

// Arithmetic expression denotation
type AE = { tag: 'num'; n: number } | { tag: 'var'; x: string }
        | { tag: 'plus'; l: AE; r: AE } | { tag: 'times'; l: AE; r: AE };

function denAE(e: AE, s: Store): number | undefined {
  switch (e.tag) {
    case 'num':   return e.n;
    case 'var':   return s.get(e.x) as number | undefined;
    case 'plus': {
      const l = denAE(e.l, s), r = denAE(e.r, s);
      return l === undefined || r === undefined ? undefined : l + r;
    }
    case 'times': {
      const l = denAE(e.l, s), r = denAE(e.r, s);
      return l === undefined || r === undefined ? undefined : l * r;
    }
  }
}

// Boolean expression denotation
type BE = { tag: 'true' } | { tag: 'false' }
        | { tag: 'leq'; l: AE; r: AE } | { tag: 'not'; b: BE };

function denBE(e: BE, s: Store): boolean | undefined {
  switch (e.tag) {
    case 'true':  return true;
    case 'false': return false;
    case 'leq': {
      const l = denAE(e.l, s), r = denAE(e.r, s);
      return l === undefined || r === undefined ? undefined : l <= r;
    }
    case 'not': { const b = denBE(e.b, s); return b === undefined ? undefined : !b; }
  }
}

// Command denotation
type Cmd = { tag: 'skip' }
         | { tag: 'assign'; x: string; e: AE }
         | { tag: 'seq'; c1: Cmd; c2: Cmd }
         | { tag: 'if'; b: BE; c1: Cmd; c2: Cmd }
         | { tag: 'while'; b: BE; c: Cmd };

function denCmd(cmd: Cmd): Denotation {
  switch (cmd.tag) {
    case 'skip':   return s => s;
    case 'assign': return s => {
      const v = denAE(cmd.e, s);
      if (v === undefined) return undefined;
      const s2 = new Map(s); s2.set(cmd.x, v); return s2;
    };
    case 'seq': {
      const d1 = denCmd(cmd.c1), d2 = denCmd(cmd.c2);
      return s => { const s1 = d1(s); return s1 === undefined ? undefined : d2(s1); };
    }
    case 'if': {
      const db = (s: Store) => denBE(cmd.b, s);
      const d1 = denCmd(cmd.c1), d2 = denCmd(cmd.c2);
      return s => { const b = db(s); return b === undefined ? undefined : b ? d1(s) : d2(s); };
    }
    case 'while': {
      // Kleene fixed point: iterate until convergence (or detect divergence)
      const body = denCmd(cmd.c);
      return fixWhile(cmd.b, body);
    }
  }
}

// Kleene iteration — approximate least fixed point with a step bound
function fixWhile(b: BE, body: Denotation): Denotation {
  return function step(s: Store | undefined): Store | undefined {
    if (s === undefined) return undefined;
    const bv = denBE(b, s);
    if (bv === undefined) return undefined;
    if (!bv) return s;
    return step(body(s));  // loop: relies on actual termination; use bounded iteration for safety
  };
}
```

### Pragmatic Implementation

Bounded Kleene iteration (safe for testing; detects likely divergence):

```typescript
function denCmdSafe(cmd: Cmd, maxSteps = 10_000): Denotation {
  if (cmd.tag !== 'while') return denCmd(cmd);
  const body = denCmdSafe(cmd.c, maxSteps);
  return function step(s: Store | undefined, steps = 0): Store | undefined {
    if (s === undefined) return undefined;
    if (steps >= maxSteps) throw new Error('Possible divergence: step limit reached');
    const bv = denBE(cmd.b, s);
    if (bv === undefined) return undefined;
    if (!bv) return s;
    return step(body(s), steps + 1);
  };
}
```

### Common Pitfalls

1. **Confusing ⊥ (bottom/non-termination) with error**: `undefined` models non-termination; use `Error` objects or a separate `Result<A, E>` type for runtime errors that are not divergence.
2. **Non-compositional semantics**: If `⟦C[e₁, e₂]⟧` depends on the syntactic structure of `e₁` (not just `⟦e₁⟧`), the semantics is not denotational. This breaks equational reasoning.
3. **Fixed-point non-monotonicity**: The semantic function `F` for `while` must be monotone for Kleene's theorem to apply. Adding operations that lower values in the partial order breaks this.
4. **Strict vs. lazy semantics**: The choice of when to evaluate `undefined` (strictness) affects what programs are semantically equivalent. Be explicit about strictness in each clause.

### Cross-References

- NbE uses a semantic domain with a similar "evaluate then reify" structure: §1 above
- Algebraic effects model computational effects in denotational style: §5 above
- Layer 3 synchronous reactive semantics: aiqeung Worked Examples

---

## aiqeung Worked Examples

### ReactiveExpr as Free Monad
aiqeung's `ReactiveExpr` in Layer 3 is the `Free<F, A>` pattern:
- Operations F = `{ tag: 'Emit'; signal: Signal; value: unknown } | { tag: 'Await'; signal: Signal } | { tag: 'Par'; left: ReactiveExpr; right: ReactiveExpr } | ...`
- The synchronous interpreter is `runFree` above with a handler that implements three-phase tick discipline
- Multiple interpreter strategies for the same AST = spec-execution duality from the SRS expert design

### Layer 6 Typed Vocabulary Terms
Layer 6 vocabulary terms use phantom types for domain-specific safety:
- `Term<'temporal/duration'>` vs `Term<'temporal/instant'>` — phantom type prevents mixing
- The vocabulary type system approximates a lightweight refinement type discipline
- Full refinement types (Liquid Types) would be the formal basis for a sound Layer 6 type checker

### Future Context-Parser Type Checker
A future aiqeung context-parser could use bidirectional type checking (from `02-inference-checking.md`):
- Natural language → untyped AST (synthesis mode fails without type annotation)
- Vocabulary declarations provide type annotations at vocabulary boundaries (checking mode)
- The `check(ctx, term, vocabType)` call validates that a parsed term has the expected vocabulary type
- Fallback to HM inference for terms that can be typed without vocabulary context
