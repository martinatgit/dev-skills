# Category Theory for Type Theory & Programming Languages

This reference covers category theory as it applies to type theory and PL design. Maximize
cross-referencing with adjacent files: 01-theory-foundations.md (CCC/STLC correspondence),
02-inference-checking.md (monadic elaboration), 03-type-system-design.md (effect systems).

---

## CT–Type Theory Connection Table

| CT concept | Type theory connection | PL consequence |
|---|---|---|
| CCC | Model of STLC (Lambek correspondence) | Products = tuples; exponentials = functions; currying = curry adjunction |
| Locally CCC | Model of dependent type theory | Π-types = dependent products; context extension = base change |
| Monads | Computational effects (Moggi 1989) | bind/return; sequencing; do-notation; Promise ≈ monad |
| Applicative | Independent effects (McBride-Paterson 2008) | `<*>` parallel composition; validation pattern |
| Adjunctions | Free constructions everywhere | Free monad = left adjoint to forgetful; Free category; Free algebra |
| Yoneda | Representation theorem | Yoneda/CoYoneda for functor fusion; NTs as ends |
| Profunctors | Generalised relations contra×covariant | Optics = profunctor transformers: Lens s t a b = ∀p. Strong p ⇒ p a b → p s t |
| F-algebras | Initial algebra = inductive type | Fix F = μF; cata = fold; ana = unfold |
| Ends | Categorical ∀ | Natural transformations as ends: [F,G] = ∫_a F(a) → G(a) |
| Coends | Categorical ∃ | Existential types as coends: ∃a.F(a) = ∫^a F(a) |
| Enriched categories | Quantitative type systems | Graded monads; metric spaces as enriched categories (Lawvere 1973) |
| SMC | Resource-sensitive computation | Linear logic as SMC; monoidal = tensor product for parallel composition |

---

## 1. Categories, Functors, Natural Transformations

### 1.1 Formal Foundations

A **category** C consists of: a collection Ob(C) of objects; for each pair A, B a collection
Hom(A,B) of morphisms; identity id_A : A → A; and composition g∘f : A → C for f : A → B,
g : B → C. Laws: associativity (h∘g)∘f = h∘(g∘f); identity f∘id_A = f = id_B∘f.

A **functor** F : C → D maps objects to objects and morphisms to morphisms, preserving identities
(F(id_A) = id_{F(A)}) and composition (F(g∘f) = F(g)∘F(f)).

A **natural transformation** α : F ⇒ G between functors F,G : C → D assigns to each object A
in C a component α_A : F(A) → G(A) in D, satisfying the naturality square:
`α_B ∘ F(f) = G(f) ∘ α_A` for all f : A → B.

### 1.2 Core Algorithm

HKT defunctionalization (fp-ts pattern) encodes higher-kinded types in TypeScript:

```typescript
declare module 'HKT' {
  interface URItoKind<A> {
    'Option': Option<A>;
    'Either': Either<never, A>;   // simplified
    'IO':     IO<A>;
  }
}
type URIS = keyof URItoKind<unknown>;
type Kind<F extends URIS, A> = URItoKind<A>[F];
// Usage: map: <F extends URIS>(F: Functor<F>) => <A, B>(fa: Kind<F,A>, f: (a:A)=>B) => Kind<F,B>
```

Functor and natural transformation interfaces:

```typescript
interface Functor<F extends URIS> {
  readonly URI: F;
  readonly map: <A, B>(fa: Kind<F, A>, f: (a: A) => B) => Kind<F, B>;
}

type NaturalTransformation<F extends URIS, G extends URIS> =
  <A>(fa: Kind<F, A>) => Kind<G, A>;
```

### 1.3 Pragmatic Implementation

- Functor laws hold by construction if `map` is pure and referentially transparent.
- `Array`, `Option`, `Either<E, _>`, `Promise` (approximately) are all functors.
- Natural transformations in TypeScript: functions polymorphic in A (no runtime A).
- Free theorems: any NT between `List` and `Option` must be either `head`, `last`, or constant `None`.

### 1.4 Common Pitfalls

- **Promise is not a lawful functor**: `Promise` auto-flattens `Promise<Promise<A>>` to
  `Promise<A>`, violating identity. Use `Task` (lazy `() => Promise<A>`) instead.
- **Array.map index leaking**: `['1','2','3'].map(parseInt)` gives `[1, NaN, NaN]` because
  `parseInt` receives `(value, index, array)`. Always use arrow wrappers: `arr.map(x => parseInt(x))`.
- **Covariant vs contravariant**: `Functor` maps covariantly. For predicate types use `Contravariant`.
- **Functor != Applicative**: `Functor` cannot sequence, only transform.

### 1.5 Cross-References

- §13 (CCC) — categories that model STLC
- §3 (Monads) — functors plus monadic structure
- §8 (Profunctors) — bifunctors contra×covariant
- §15 (Ends/Coends) — natural transformations as ends

---

## 2. Monoids & Semigroups

### 2.1 Formal Foundations

A **semigroup** is (S, ⊕) where ⊕ : S × S → S satisfies associativity: (a⊕b)⊕c = a⊕(b⊕c).

A **monoid** is (M, ⊕, e) where (M, ⊕) is a semigroup and e is an identity:
e⊕a = a = a⊕e for all a.

Categorically: a monoid is a single-object category where morphisms are elements, composition
is ⊕, and the identity morphism is e. A monoid homomorphism h : M → N preserves operation
(h(a⊕b) = h(a)⊕h(b)) and identity (h(e_M) = e_N).

Key variants: free monoid on A = A* (finite sequences, concat); commutative monoid (⊕ symmetric);
groups (every element has an inverse).

### 2.2 Core Algorithm

```typescript
interface Semigroup<A> {
  readonly concat: (x: A, y: A) => A;
  // Law: concat(concat(a, b), c) === concat(a, concat(b, c))
}

interface Monoid<A> extends Semigroup<A> {
  readonly empty: A;
  // Laws: concat(empty, a) === a, concat(a, empty) === a
}

// fold: reduce a list using a monoid (fundamental elimination)
function fold<A>(M: Monoid<A>, as: A[]): A {
  return as.reduce(M.concat, M.empty);
}

// foldMap: map then fold (requires Functor + Monoid)
function foldMap<A, B>(M: Monoid<B>, f: (a: A) => B, as: A[]): B {
  return fold(M, as.map(f));
}

// mconcat: list of monoid values -> single value
function mconcat<A>(M: Monoid<A>, as: A[]): A {
  return fold(M, as);
}
```

### 2.3 Pragmatic Implementation

Common monoid instances: `(number, +, 0)`, `(number, *, 1)`, `(string, concat, '')`,
`(boolean, &&, true)`, `(boolean, ||, false)`, `(Array<A>, concat, [])`,
`(A → A, compose, id)` (endomorphism monoid). For parallel computation, fold over a
balanced tree using the monoid structure.

### 2.4 Common Pitfalls

- **Subtraction is not associative**: `(10-5)-3 ≠ 10-(5-3)`. Never use subtraction as concat.
- **Non-lawful "monoids"**: `Math.max` with `0` is not a monoid for negative numbers
  (`Math.max(Math.max(-1, 0), -2) = 0 ≠ Math.max(-1, Math.max(0, -2)) = 0`—actually fine
  here, but `Math.max` with `Infinity` as identity, not `0`).
- **Order-dependent folds**: when ⊕ is not commutative (e.g., `string concat`), `foldLeft` and
  `foldRight` give different results. Be explicit about order.
- **Writer monad requires Monoid**: `Writer<W, A>` needs `Monoid<W>` for `chain`.

### 2.5 Cross-References

- §3 (Monads) — Writer monad uses monoid for logging
- §12 (SMC) — monoidal categories generalize monoids
- §9 (F-algebras) — folding as initial-algebra morphism

---

## 3. Monads (Moggi/Wadler)

### 3.1 Formal Foundations

A **monad** on category C is a triple (T, η, μ) where:
- T : C → C is an endofunctor
- η : Id_C ⇒ T is the unit (return/pure)
- μ : T² ⇒ T is the multiplication (join)

satisfying: μ∘T(μ) = μ∘μ_T (associativity) and μ∘T(η) = μ∘η_T = id_T (unit laws).

**Kleisli triple** equivalent: T on objects, η_A : A → T(A), and Kleisli extension
(−)* : (A → T(B)) → T(A) → T(B). Laws: η* = id, f*∘η = f, (g*∘f)* = g*∘f*.

Moggi (1989): a monad models a *notion of computation*. The value type A is separated from
the computational context T(A). Wadler (1992): monads structure functional programs.

### 3.2 Core Algorithm

```typescript
interface Monad<M extends URIS> extends Functor<M> {
  of<A>(a: A): Kind<M, A>;                           // return / pure
  chain<A, B>(fa: Kind<M, A>, f: (a: A) => Kind<M, B>): Kind<M, B>; // bind / flatMap
}
// Laws:
// Left identity:  chain(of(a), f)      ≡ f(a)
// Right identity: chain(fa, of)        ≡ fa
// Associativity:  chain(chain(fa,f),g) ≡ chain(fa, x => chain(f(x), g))
```

Derived operations:

```typescript
// join: M(M(A)) → M(A)
const join = <M extends URIS, A>(M: Monad<M>, mma: Kind<M, Kind<M, A>>): Kind<M, A> =>
  M.chain(mma, ma => ma);

// Kleisli composition (fish operator >=>)
const composeK =
  <M extends URIS, A, B, C>(M: Monad<M>, f: (a: A) => Kind<M, B>, g: (b: B) => Kind<M, C>) =>
  (a: A): Kind<M, C> => M.chain(f(a), g);
```

### 3.3 Pragmatic Implementation

Canonical instances: `Option` (partiality), `Either<E,_>` (failure), `Array` (nondeterminism),
`IO<_>` (side effects), `State<S,_>` (mutable state), `Reader<R,_>` (environment),
`Writer<W,_>` (logging), `Cont<R,_>` (continuations).

Do-notation desugaring (conceptual):
```
do { x <- ma; y <- f(x); return g(x, y) }
≡ chain(ma, x => chain(f(x), y => of(g(x, y))))
```

### 3.4 Common Pitfalls

- **Promise is not lawful**: `Promise.resolve(Promise.resolve(42))` auto-flattens. Use `Task`.
- **map vs chain confusion**: using `map` when `chain` is needed produces `M(M(A))`.
- **Left-associated bind chains**: `((m >>= f) >>= g) >>= h` is O(n²) in Free monads.
  Use Codensity/Church encoding (see §7).
- **Error swallowing**: `chain` propagates `Left` silently—use `fold/match` to recover.
- **Monad ≠ Applicative when effects interact**: `ap` derived from `chain` may not match
  a more efficient direct `ap` (e.g., `Validation` cannot be a lawful monad).

### 3.5 Cross-References

- §5 (Adjunctions) — every monad arises from an adjunction
- §11 (Kleisli/EM) — two canonical categories from a monad
- §17 (Distributive Laws) — composing two monads
- §4 (Applicative) — strictly weaker; use when effects are independent

---

## 4. Applicative Functors (McBride-Paterson)

### 4.1 Formal Foundations

An **applicative functor** (McBride-Paterson 2008) is a functor F with:
- `pure` : A → F(A)
- `<*>` : F(A→B) → F(A) → F(B)

Laws: identity (`pure id <*> v = v`), composition
(`pure (∘) <*> u <*> v <*> w = u <*> (v <*> w)`), homomorphism
(`pure f <*> pure x = pure (f x)`), interchange
(`u <*> pure y = pure ($ y) <*> u`).

Equivalent monoidal form (lax monoidal functor):
- `unit` : F(1) and `mult` : F(A)×F(B) → F(A×B)

satisfying pentagon and triangle identities. Applicative is strictly between Functor and Monad:
every monad is applicative but not vice versa.

### 4.2 Core Algorithm

```typescript
interface Applicative<F extends URIS> extends Functor<F> {
  readonly of: <A>(a: A) => Kind<F, A>;
  readonly ap: <A, B>(fab: Kind<F, (a: A) => B>, fa: Kind<F, A>) => Kind<F, B>;
}

// liftA2: lift binary function (parallel, not sequential)
function liftA2<F extends URIS, A, B, C>(
  F: Applicative<F>,
  f: (a: A) => (b: B) => C,
  fa: Kind<F, A>,
  fb: Kind<F, B>
): Kind<F, C> {
  return F.ap(F.map(fa, f), fb);
}

// sequenceA: [F<A>] → F<[A]>
function sequenceA<F extends URIS, A>(
  F: Applicative<F>,
  fas: Kind<F, A>[]
): Kind<F, A[]> {
  return fas.reduce(
    (acc, fa) => F.ap(F.map(acc, as => (a: A) => [...as, a]), fa),
    F.of([] as A[])
  );
}
```

### 4.3 Pragmatic Implementation

Key use case: **Validation** (error accumulation). Unlike `Either`, `Validation`'s `ap` collects
all errors (uses `Semigroup<E>`) rather than stopping at the first. Form validation,
JSON parsing, CSV row validation all benefit.

`traverse` = `foldMap` + applicative: `traverse(f, xs) = sequenceA(xs.map(f))`.

### 4.4 Common Pitfalls

- **Use Applicative, not Monad, when effects are independent**: `Applicative` allows
  parallelism; `Monad`'s `chain` forces sequential dependency.
- **Non-curried functions**: TypeScript functions are not curried by default. Must curry
  before using `ap`: `ap(map(fa, a => b => f(a,b)), fb)`.
- **Validation is not a monad**: `Validation`'s `ap` accumulates errors, but a lawful
  `chain` would require stopping on first error (contradicting accumulation).
- **`ap` argument order**: fp-ts uses `ap(fab, fa)` (function first). Haskell uses `<*>` infix.

### 4.5 Cross-References

- §3 (Monads) — superset; derive `ap` from `chain` if needed
- §15 (Ends) — `traverse` expressed via ends
- §23 (Optics/Traversals) — `Traversal` uses `Applicative`

---

## 5. Adjunctions

### 5.1 Formal Foundations

An **adjunction** L ⊣ R consists of functors L : C → D (left adjoint) and R : D → C
(right adjoint) with a natural isomorphism:
`Hom_D(L(A), B) ≅ Hom_C(A, R(B))` for all A ∈ C, B ∈ D.

**Unit/counit form**: natural transformations η : Id_C ⇒ R∘L (unit) and ε : L∘R ⇒ Id_D
(counit) satisfying triangle identities:
- (ε_L)∘(L_η) = id_L
- (R_ε)∘(η_R) = id_R

Key examples: Free ⊣ Forgetful (monoids, groups, modules); (−×A) ⊣ (A⇒−) in CCC (currying);
∃_f ⊣ f* ⊣ ∀_f in dependent type theory (quantifiers); Free monad ⊣ forgetful.

Every adjunction generates a monad: T = R∘L, η = unit, μ = R(ε_L).

### 5.2 Core Algorithm

```typescript
interface Adjunction<L extends string, R extends string> {
  readonly L: Functor1<L>;
  readonly R: Functor1<R>;
  // unit: A → R(L(A))
  unit: <A>(a: A) => HKT<R, HKT<L, A>>;
  // counit: L(R(B)) → B
  counit: <B>(lrb: HKT<L, HKT<R, B>>) => B;
  // leftAdjunct: (L(A) → B) → (A → R(B))
  leftAdjunct: <A, B>(f: (la: HKT<L, A>) => B) => (a: A) => HKT<R, B>;
  // rightAdjunct: (A → R(B)) → (L(A) → B)
  rightAdjunct: <A, B>(g: (a: A) => HKT<R, B>) => (la: HKT<L, A>) => B;
}

// Derived monad from an adjunction
function adjunctionToMonad<L extends string, R extends string>(
  adj: Adjunction<L, R>
): Monad<'RL'> {
  return {
    of: adj.unit,
    chain: (rla, f) => adj.R.map(rla, adj.rightAdjunct(f))
  } as any;
}
```

### 5.3 Pragmatic Implementation

The **State monad** arises from the adjunction `(−×S) ⊣ (S⇒−)`:
- Left adjoint: `(−×S)` (pair with state)
- Right adjoint: `(S⇒−)` (function from state)
- Induced monad: `State<S, A> = S → (A × S)`

The **free monad** `Free(F)` is the left adjoint to the forgetful functor from monads to
endofunctors. The **continuation monad** `Cont<R, A> = (A→R)→R` arises from
the self-adjunction of `(−^R)`.

### 5.4 Common Pitfalls

- **Forgetting triangle identities**: hand-implemented adjunctions without verifying triangles
  produce invalid monads (monad laws fail).
- **L⊣R direction confusion**: L is LEFT adjoint (appears on left of ⊣). Mnemonic:
  `Hom(L−, −) ≅ Hom(−, R−)`.
- **State monad variance**: the naive `State` encoding `S → A × S` is not a proper HKT
  without wrapping. Use `newtype`-style wrappers.

### 5.5 Cross-References

- §3 (Monads) — every monad arises from an adjunction
- §11 (Kleisli/EM) — two adjunctions for each monad
- §13 (CCC) — (−×A) ⊣ (A⇒−) is the defining adjunction of exponentials

---

## 6. Yoneda Lemma & Yoneda Embedding

### 6.1 Formal Foundations

**Yoneda Lemma**: For a locally small category C, functor F : C^op → Set, and object A:
```
Nat(Hom(−, A), F) ≅ F(A)
```
The isomorphism: forward evaluates at id_A; backward extends by applying F to morphisms.

**Covariant form**: `Nat(Hom(A, −), F) ≅ F(A)`.

**Yoneda Embedding**: `yo : C → [C^op, Set]`, `yo(A) = Hom(−, A)`, is fully faithful.

**CoYoneda Lemma** (computational form):
`F(A) ≅ ∃B. (B→A) × F(B)` — existential encoding enabling functor fusion.

### 6.2 Core Algorithm

```typescript
// Yoneda<F, A> = ∀B. (A→B) → F<B>  (CPS-transformed F<A>)
interface Yoneda<F extends URIS, A> {
  run: <B>(f: (a: A) => B) => Kind<F, B>;
}

// Lift F<A> into Yoneda (requires Functor)
const yonedaLift = <F extends URIS, A>(
  F: Functor<F>, fa: Kind<F, A>
): Yoneda<F, A> => ({ run: f => F.map(fa, f) });

// Lower Yoneda back to F<A>
const yonedaLower = <F extends URIS, A>(y: Yoneda<F, A>): Kind<F, A> =>
  y.run(a => a);  // run(id)

// Map on Yoneda is O(1) — compose functions, no Functor needed!
const yonedaMap = <F extends URIS, A, B>(
  y: Yoneda<F, A>, f: (a: A) => B
): Yoneda<F, B> => ({ run: g => y.run(a => g(f(a))) });

// CoYoneda: existential encoding for fusion
class CoYoneda<A> {
  private constructor(
    private readonly _map: (b: any) => A,
    private readonly _value: any
  ) {}
  static lift<A>(fa: A[]): CoYoneda<A> {
    return new CoYoneda(a => a, fa);
  }
  map<B>(f: (a: A) => B): CoYoneda<B> {
    return new CoYoneda((x: any) => f(this._map(x)), this._value);
  }
  lower(F: Functor<any>): any {
    return F.map(this._value, this._map);
  }
}
```

### 6.3 Pragmatic Implementation

Use **CoYoneda** to batch multiple `map` calls into one: wrap with `lift`, chain `map` calls
(each O(1)), then `lower` once at the end. Particularly effective for arrays and data streams
with 3+ chained transforms.

### 6.4 Common Pitfalls

- **Forgetting to lower**: CoYoneda accumulates closures but executes nothing until `lower`.
- **Type erasure**: internal `any` in CoYoneda means type errors surface at runtime.
- **Over-fusion**: for 1–2 maps, CoYoneda overhead (closure allocation) exceeds benefit.
- **Side effects in maps**: fusion reorders when side effects execute.

### 6.5 Cross-References

- §15 (Ends/Coends) — natural transformations expressed as ends
- §8 (Profunctors) — profunctor optics use Yoneda embedding
- §7 (Kan Extensions) — Yoneda is a special case: `Ran_yo(F) = F`

---

## 7. Kan Extensions

### 7.1 Formal Foundations

Given functors F : C → D and K : C → E, the **right Kan extension** `Ran_K(F) : E → D`
comes with ε : Ran_K(F)∘K ⇒ F (counit), universal among all G : E → D with G∘K ⇒ F.

**Left Kan extension** `Lan_K(F) : E → D` comes with η : F ⇒ Lan_K(F)∘K (unit).

Pointwise formulas:
- `(Ran_K F)(e) = lim_{c, K(c)→e} F(c)`
- `(Lan_K F)(e) = colim_{c, e→K(c)} F(c)`

Special cases: if K has left adjoint L, then `Ran_K(F) = F∘L`. The **Codensity monad**
`Ran_G(G)(A) = ∀R. (A→G(R))→G(R)` is the right Kan extension of G along itself.

### 7.2 Core Algorithm

```typescript
// Right Kan extension: Ran_K(F)(e) = ∀c. (K(c)→e) → F(c)
type Ran<K, F, E> = <C>(k: (kc: K_of<C>) => E) => F_of<C>;

// Codensity monad: Ran_G(G)(A) = ∀R. (A→G<R>)→G<R>
interface Codensity<A> {
  run: <R>(k: (a: A) => R[]) => R[];
}

const codensityPure = <A>(a: A): Codensity<A> =>
  ({ run: k => k(a) });

const codensityBind = <A, B>(ca: Codensity<A>, f: (a: A) => Codensity<B>): Codensity<B> =>
  ({ run: k => ca.run(a => f(a).run(k)) });

// Lower: Codensity<A> back to G<A> (for G = Array)
const codensityLower = <A>(ca: Codensity<A>): A[] =>
  ca.run(a => [a]);
```

### 7.3 Pragmatic Implementation

The **Codensity monad** reassociates left-nested binds to the right, eliminating the O(n²)
problem in naive Free monad chains. Workflow: wrap computation in Codensity, perform all
binds (each O(1)), then lower once. This is the `toCodensity / fromCodensity` pattern in
`free`/`kan-extensions` libraries.

Left Kan extensions appear as **density comonads** and in the construction of Lan-based
free constructions (free functors, free applicatives).

### 7.4 Common Pitfalls

- **Stack overflow**: deep Codensity chains build nested closures; trampoline for >10k binds.
- **Debugging opacity**: Codensity values are opaque functions; intermediate states invisible.
- **Premature lowering**: lowering inside a loop defeats the optimization.
- **Wrong direction**: Codensity helps left-associated binds; right-associated chains need
  a different optimization (e.g., difference lists for Writer).

### 7.5 Cross-References

- §6 (Yoneda) — Yoneda lemma = Ran along yo; CoYoneda = Lan along yo
- §3 (Monads) — Free monad performance; Codensity improves it
- §5 (Adjunctions) — Kan extensions generalize adjunctions

---

## 8. Profunctors

### 8.1 Formal Foundations

A **profunctor** P : C^op × D → Set is contravariant in the first argument, covariant in the
second. In programming terms: `dimap : (a₁→a₀) → (b₀→b₁) → P<a₀,b₀> → P<a₁,b₁>`.

Laws: `dimap id id = id`; `dimap (f∘g) (h∘k) = dimap g h ∘ dimap f k`.

**Tambara modules**: A `Strong` profunctor has `first : P<A,B> → P<(A,C),(B,C)>` (products);
a `Choice` profunctor has `left : P<A,B> → P<Either<A,C>, Either<B,C>>` (coproducts);
`Wander` captures traversals.

**Profunctor optics**: `Optic S T A B = ∀p. Constraints p ⇒ p A B → p S T`.
- Lens: `Strong p`
- Prism: `Choice p`
- Traversal: `Wander p`
- Iso: `Profunctor p`

### 8.2 Core Algorithm

```typescript
interface Profunctor<F> {
  dimap<A, B, C, D>(
    f: (c: C) => A,   // contravariant: map input
    g: (b: B) => D,   // covariant: map output
    pab: P_of<F, A, B>
  ): P_of<F, C, D>;
}

interface Strong<F> extends Profunctor<F> {
  first<A, B, C>(pab: P_of<F, A, B>): P_of<F, [A, C], [B, C]>;
  second<A, B, C>(pab: P_of<F, A, B>): P_of<F, [C, A], [C, B]>;
}

interface Choice<F> extends Profunctor<F> {
  left<A, B, C>(pab: P_of<F, A, B>): P_of<F, Either<A,C>, Either<B,C>>;
  right<A, B, C>(pab: P_of<F, A, B>): P_of<F, Either<C,A>, Either<C,B>>;
}

// Function is the canonical profunctor (→)
const FnProfunctor: Strong<'Fn'> = {
  dimap: (f, g) => pab => b => g(pab(f(b))),
  first: pab => ([a, c]) => [pab(a), c],
  second: pab => ([c, a]) => [c, pab(a)]
};
```

### 8.3 Pragmatic Implementation

Profunctor optics compose simply as function composition. The `(→)` function type and
the `Star<F,A,B> = A → F(B)` type are the workhorse profunctors. For the Van Laarhoven
encoding of Lens, `Star<Identity, A, B>` recovers `over`; `Star<Const<A>, A, B>` recovers
`view`. See §23 for optic implementations.

### 8.4 Common Pitfalls

- **Forgetting contravariance**: the first argument maps *backward*. `dimap(f, g)` applies
  `f` *before* the profunctor, `g` *after*.
- **Optic law violations**: writing a "lens" without verifying PutGet/GetPut/PutPut.
- **Inference failures**: deeply composed profunctor optics exhaust TypeScript's type
  inference; add explicit type annotations at boundaries.
- **Closure overhead**: each optic application allocates closures; avoid in hot loops.

### 8.5 Cross-References

- §23 (Optics) — profunctor encoding of Lens/Prism/Traversal
- §15 (Ends/Coends) — natural transformations between profunctors
- §6 (Yoneda) — profunctor Yoneda: P(A,B) ≅ ∀C. Hom(B,C) → Hom(C,A) → P(C,C)

---

## 9. F-Algebras & Catamorphisms

### 9.1 Formal Foundations

An **F-algebra** for endofunctor F : C → C is a pair (A, α : F(A)→A) where A is the carrier
and α is the structure map. F-algebra homomorphisms h : (A,α)→(B,β) satisfy h∘α = β∘F(h).

The **initial F-algebra** (μF, in) is initial in Alg(F). By **Lambek's Lemma**, `in` is an
isomorphism, so μF ≅ F(μF) — the fixed point.

A **catamorphism** (fold) `cata(φ) : μF → A` is the unique homomorphism from the initial
algebra to any F-algebra (A, φ): `cata(φ) ∘ in = φ ∘ F(cata(φ))`.

Banana bracket notation: `(|φ|) = cata(φ)`.

### 9.2 Core Algorithm

```typescript
type Fix<F> = { unfix: F };  // F is a type with Fix<F> as recursive positions
function cata<F, A>(alg: (f: F) => A, fmap: <X,Y>(f: (x:X)=>Y) => (fx: F_with_X) => F_with_Y): (t: Fix<F>) => A {
  return t => alg(fmap(cata(alg, fmap))(t.unfix as any));
}
// Concrete: ExprF<R> = Num(n) | Add(l: R, r: R)
// evalAlg: ExprF<number> → number = e => e.tag==='Num' ? e.n : e.l + e.r
// cata(evalAlg, fmapExpr): Fix<ExprF> → number
```

Additional recursion schemes:

```typescript
// Anamorphism (unfold): A → νF
type Coalgebra<F extends URIS, A> = (a: A) => Kind<F, A>;
function ana<F extends URIS, A>(
  F: Functor<F>, coalg: Coalgebra<F, A>
): (a: A) => Fix<F> {
  return a => ({ unfix: F.map(coalg(a), ana(F, coalg)) as any });
}

// Hylomorphism: unfold then fold (no intermediate Fix)
function hylo<F extends URIS, A, B>(
  F: Functor<F>, alg: (fb: Kind<F, B>) => B, coalg: (a: A) => Kind<F, A>
): (a: A) => B {
  return a => alg(F.map(coalg(a), hylo(F, alg, coalg)) as any);
}
```

### 9.3 Pragmatic Implementation

Pattern functor recipe: replace all recursive occurrences of type `T` with type parameter `R`
to get `TF<R>`. Then `Fix<TF> ≅ T`. Example: `ListF<R> = Nil | Cons(head: A, tail: R)`.
`cata` over `ListF` gives `foldr`.

### 9.4 Common Pitfalls

- **Stack overflow**: deep `Fix` structures blow the call stack. Use trampolining in production.
- **Forgetting Lambek**: `in`/`out` must be mutual inverses. Extra fields break this.
- **Non-functorial fmap**: if `fmap` violates functor laws, all recursion schemes break silently.
- **Anamorphism non-termination**: infinite coalgebras need coinductive types (see §10).

### 9.5 Cross-References

- §10 (Initial/Terminal) — categorical foundation of Fix and νF
- §16 (Polynomial Functors) — ListF, TreeF as polynomial functors
- §11 (Kleisli/EM) — T-algebras in EM category correspond to F-algebras

---

## 10. Initial Algebras & Terminal Coalgebras

### 10.1 Formal Foundations

Given endofunctor F : C → C:

**Initial F-algebra** (μF, in_F): initial in Alg(F). For every F-algebra (A, φ),
∃! F-algebra homomorphism h : μF → A. By Lambek: μF ≅ F(μF) — *least fixed point*.

**Terminal F-coalgebra** (νF, out_F): terminal in CoAlg(F). For every F-coalgebra (A, ψ),
∃! h : A → νF. By Lambek: νF ≅ F(νF) — *greatest fixed point*.

In Set: μF gives **inductive** (finite, well-founded) types; νF gives **coinductive**
(potentially infinite, productive) types.

Adámek's theorem: if C has initial object 0 and F preserves colimits, then
`μF = colim(0 → F(0) → F²(0) → ...)`.

### 10.2 Core Algorithm

```typescript
// Inductive type: Fix<F> as least fixed point
interface Fix<F extends URIS> {
  readonly tag: 'Fix';
  readonly unFix: Kind<F, Fix<F>>;
}
const mkFix = <F extends URIS>(layer: Kind<F, Fix<F>>): Fix<F> =>
  ({ tag: 'Fix', unFix: layer });

// Coinductive type: thunked greatest fixed point
interface Cofix<F extends URIS> {
  readonly force: () => Kind<F, Cofix<F>>;  // thunk prevents eager expansion
}
const mkCofix = <F extends URIS>(th: () => Kind<F, Cofix<F>>): Cofix<F> =>
  ({ force: th });

// Anamorphism: seed → νF
function coana<F extends URIS, A>(
  F: Functor<F>, coalg: (a: A) => Kind<F, A>
): (a: A) => Cofix<F> {
  return a => mkCofix(() => F.map(coalg(a), coana(F, coalg)) as any);
}
```

### 10.3 Pragmatic Implementation

Use `Fix<F>` (eager) for finite data (ASTs, trees, lists). Use `Cofix<F>` (lazy/thunked)
for streams, state machines, reactive values. In TypeScript, all recursion is inductive;
model coinductive types with explicit thunks `() => ...` at every self-reference.

### 10.4 Common Pitfalls

- **Confusing μ and ν**: `Fix<F>` (eager) used for coinductive data causes infinite loops.
- **Missing thunks**: coinductive definitions without `() => ...` at each self-reference
  cause immediate infinite recursion in a strict language.
- **Non-productive corecursion**: a coinductive definition that doesn't produce a constructor
  before recursing is non-productive and will diverge.
- **Strictness vs. laziness**: TypeScript is strict; Haskell is lazy. Algorithms from Haskell
  need explicit lazification for TypeScript coinductive types.

### 10.5 Cross-References

- §9 (F-Algebras) — catamorphisms over initial algebras
- §16 (Polynomial Functors) — polynomial functors have well-behaved μ and ν
- §22 (Comonads) — cofree comonad = terminal coalgebra for a polynomial

---

## 11. Kleisli & Eilenberg-Moore Categories

### 11.1 Formal Foundations

Given monad (T, η, μ) on C:

**Kleisli category** C_T:
- Objects: same as C
- Morphisms A →_T B = A → T(B) in C (Kleisli arrows)
- Identity: η_A : A → T(A)
- Composition: g ∘_T f = μ_B ∘ T(g) ∘ f

Kleisli adjunction: F_T ⊣ U_T where F_T(A) = A, U_T(A) = T(A). U_T∘F_T = T.

**Eilenberg-Moore category** C^T:
- Objects: T-algebras (A, h : T(A)→A) with h∘η_A = id and h∘μ_A = h∘T(h)
- Morphisms: T-algebra homomorphisms (f∘h_A = h_B∘T(f))

EM adjunction: F^T ⊣ U^T, U^T∘F^T = T. The EM category is the *terminal* resolution
of the monad; the Kleisli category is the *initial* resolution.

### 11.2 Core Algorithm

```typescript
// Kleisli arrow: a morphism in the Kleisli category C_T
type KleisliArrow<M extends URIS, A, B> = (a: A) => Kind<M, B>;

// Kleisli composition (fish operator >=>)
const kleisliCompose =
  <M extends URIS, A, B, C>(M: Monad<M>) =>
  (f: KleisliArrow<M, A, B>, g: KleisliArrow<M, B, C>): KleisliArrow<M, A, C> =>
  a => M.chain(f(a), g);

// T-algebra: a structure map h : T(A) → A
interface TAlgebra<M extends URIS, A> {
  carrier: A;  // phantom; actual type is A
  structure: (ta: Kind<M, A>) => A;
  // Laws: structure(M.of(a)) = a  and  structure(join(tta)) = structure(M.map(tta, structure))
}

// Free T-algebra (in C^T): (T(A), μ_A : T(T(A)) → T(A))
const freeAlgebra = <M extends URIS, A>(M: Monad<M>): TAlgebra<M, Kind<M, A>> =>
  ({ carrier: undefined as any, structure: (tta) => M.chain(tta, ta => ta) });
```

### 11.3 Pragmatic Implementation

The **Kleisli category** is what you work in when you write effectful programs in `do`-notation
or `chain` pipelines. Every `chain` step is Kleisli composition. The **EM category** is what
you need when studying universal properties of the monad (e.g., constructing the monad from
its algebras).

### 11.4 Common Pitfalls

- **Monad law violations break Kleisli composition**: if the monad doesn't satisfy the laws,
  Kleisli composition is not associative—the category axioms fail.
- **Confusing Kleisli and EM perspectives**: Kleisli = effectful functions; EM = algebraic
  structure. Don't mix without the comparison functor K : C_T → C^T.
- **Forgetting strength**: in a CCC, every monad is strong, meaning Kleisli arrows can capture
  free variables from the context. In other categories this may fail.

### 11.5 Cross-References

- §3 (Monads) — Kleisli triples are exactly monads
- §5 (Adjunctions) — Kleisli and EM adjunctions for the monad
- §9 (F-Algebras) — T-algebras in EM are F-algebras for F = T

---

## 12. Monoidal & Symmetric Monoidal Categories

### 12.1 Formal Foundations

A **monoidal category** (C, ⊗, I, α, λ, ρ):
- Bifunctor ⊗ : C×C → C
- Unit object I
- Associator α_{A,B,C} : (A⊗B)⊗C → A⊗(B⊗C) (natural iso)
- Left unitor λ_A : I⊗A → A; right unitor ρ_A : A⊗I → A
- Pentagon identity (for α) and triangle identity (for λ, ρ, α)

A **symmetric monoidal category** (SMC) adds braiding σ_{A,B} : A⊗B → B⊗A with
σ_{B,A}∘σ_{A,B} = id and hexagon identities.

Mac Lane's coherence theorem: every monoidal category is equivalent to a *strict* one
(where α, λ, ρ are identities). Justify working with strict SMCs in practice.

Connection to type theory: **linear type systems** are modeled by SMCs where ⊗ is the
tensor and the missing diagonal/terminal prevents copying/discarding.

### 12.2 Core Algorithm

```typescript
// Type-level tensor and unit
type Tensor<A, B> = readonly [A, B];
type Unit = void;

// Coherence isomorphisms
const assoc  = <A,B,C>([[a,b],c]: Tensor<Tensor<A,B>,C>): Tensor<A,Tensor<B,C>> => [a,[b,c]];
const assocI = <A,B,C>([a,[b,c]]: Tensor<A,Tensor<B,C>>): Tensor<Tensor<A,B>,C> => [[a,b],c];
const lunit  = <A>([,a]: Tensor<Unit,A>): A => a;
const runit  = <A>([a,]: Tensor<A,Unit>): A => a;
const swap   = <A,B>([a,b]: Tensor<A,B>): Tensor<B,A> => [b,a];

// Verify pentagon (a*(b*c))*d = a*((b*c)*d) = a*(b*(c*d)) = (a*b)*(c*d) etc.
// In strict setting all associators are identity — work in strict by default.
```

### 12.3 Pragmatic Implementation

In the strict SMC modeling TypeScript: `Tensor<A,B> = [A,B]`, `Unit = void`. The swap
(braiding) is `swap`. Linear-style APIs enforce single-use via phantom types or type-state
patterns. For parallel computation, ⊗ models independent threads; sequential composition
is function composition.

### 12.4 Common Pitfalls

- **Cartesian ≠ monoidal**: in a CCC, products have diagonal Δ : A→A×A and !:A→1;
  in a general SMC these are absent (no copy, no discard → linearity).
- **Forgetting coherence**: pentagon and triangle must hold. Skipping verification leads to
  bugs where different reassociation paths give different results.
- **Strictification pitfalls**: the equivalence to a strict SMC involves non-trivial
  natural transformations; don't conflate the equivalence with equality.

### 12.5 Cross-References

- §13 (CCC) — cartesian monoidal with exponentials
- §18 (Enriched Categories) — enriching in a closed SMC
- §20 (String Diagrams) — graphical calculus for SMC morphisms

---

## 13. Cartesian Closed Categories (CCCs)

### 13.1 Formal Foundations

A **CCC** C has:
1. Terminal object 1 with !_A : A → 1 unique.
2. Binary products A×B with projections π₁, π₂ and universal pairing ⟨f,g⟩.
3. Exponentials B^A (internal hom) with eval : B^A×A → B, universal: for every
   f : C×A → B there exists unique curry(f) : C → B^A such that eval∘(curry(f)×id) = f.

**Curry-Howard-Lambek correspondence**:
- CCC ↔ STLC (simply typed λ-calculus)
- Products ↔ conjunction / tuple types
- Exponentials ↔ implication / function types
- Terminal ↔ unit type

The defining adjunction: `Hom(C×A, B) ≅ Hom(C, B^A)` (currying).

### 13.2 Core Algorithm

```typescript
// TypeScript is the internal language of a CCC (approximately)
type Unit = void;
type Product<A, B> = readonly [A, B];

const fst  = <A,B>([a,_]: Product<A,B>): A => a;
const snd  = <A,B>([_,b]: Product<A,B>): B => b;
const pair = <C,A,B>(f: (c:C)=>A, g: (c:C)=>B) => (c: C): Product<A,B> => [f(c), g(c)];
const curry   = <C,A,B>(f: (ca: Product<C,A>)=>B) => (c: C) => (a: A): B => f([c,a]);
const uncurry = <C,A,B>(f: (c:C)=>(a:A)=>B) => ([c,a]: Product<C,A>): B => f(c)(a);
const eval_   = <A,B>([f,a]: Product<(a:A)=>B, A>): B => f(a);

// CCC interface for abstract reasoning
interface CCC<Obj, Mor> {
  terminal: Obj; toTerminal(a: Obj): Mor;
  product(a: Obj, b: Obj): Obj; fst(a: Obj, b: Obj): Mor; snd(a: Obj, b: Obj): Mor;
  pair(f: Mor, g: Mor): Mor;
  exponential(a: Obj, b: Obj): Obj; eval(a: Obj, b: Obj): Mor;
  curry(f: Mor): Mor; uncurry(f: Mor): Mor;
}
```

### 13.3 Pragmatic Implementation

TypeScript (modulo recursive types and `any`) is a CCC:
- Terminal = `void`; Products = tuples/interfaces; Exponentials = function types.
- `curry` and `uncurry` are the adjunction witnesses.
- Dependent types require a **locally CCC** (indexed family of CCCs).

### 13.4 Common Pitfalls

- **Cartesian ≠ tensor product**: CCC products allow copy (Δ) and discard (!). Linear types
  break this by forbidding Δ and !, requiring a non-cartesian SMC.
- **η-equality**: beta-normal terms may not be equal without eta-expansion. Normalize with
  η for correct equality checking in CCC-based type checkers.
- **Recursive types break the CCC model**: `type F = (x: F) => F` has no CCC interpretation.
  Require a domain-theoretic/cocompleteness extension (CPOs).

### 13.5 Cross-References

- §5 (Adjunctions) — currying = the product-exponential adjunction
- §14 (Toposes) — a topos is a CCC with subobject classifier
- §12 (SMC) — CCC is the cartesian case of SMC

---

## 14. Toposes & Subobject Classifiers

### 14.1 Formal Foundations

An **elementary topos** E has:
1. All finite limits
2. Exponentials (internal hom)
3. Subobject classifier: an object Ω with `true : 1 → Ω` such that for every mono
   m : U ↣ X there exists unique χ_m : X → Ω making the square a pullback:
   ```
   U ──!──→ 1
   |         |
   m       true
   |         |
   v         v
   X ─χ_m→ Ω
   ```

In **Set**: Ω = {false, true}, χ_m = characteristic function of U ⊆ X.
In a general topos, Ω may have more truth values (intuitionistic logic).

Ω forms a **Heyting algebra** (intuitionistic logic); classical logic requires Ω = 2.
The **internal language** of a topos is intuitionistic higher-order logic.

### 14.2 Core Algorithm

```typescript
interface HeytingAlgebra<T> {
  top: T; bottom: T;
  meet: (a: T, b: T) => T;   // AND
  join: (a: T, b: T) => T;   // OR
  implies: (a: T, b: T) => T; // a ⊃ b = largest c with a∧c ≤ b
  not: (a: T) => T;           // ¬a = a ⊃ ⊥
  leq: (a: T, b: T) => boolean;
}

// Boolean (classical) topos: Ω = {true, false}
const BoolHA: HeytingAlgebra<boolean> = {
  top: true, bottom: false,
  meet: (a,b) => a && b, join: (a,b) => a || b,
  implies: (a,b) => !a || b, not: a => !a,
  leq: (a,b) => !a || b
};

// Subobject: U ⊆ X represented as characteristic function
type Subobject<X> = (x: X) => boolean; // for Set-topos

// Classification: given mono m:U→X, derive χ_m
const classify = <X>(m: (u: any) => X, us: any[]): Subobject<X> =>
  x => us.some(u => m(u) === x);
```

### 14.3 Pragmatic Implementation

Presheaf categories `[C^op, Set]` are toposes. The subobject classifier is the functor
of sieves: `Ω(c) = { sieves on c }`. Useful for domain-specific logics: a site (C, J)
has a sheaf subtopos with its own Ω (Lawvere-Tierney topology).

For type theory: Ω corresponds to the **propositions-as-types** universe at level -1 (proof-
irrelevant propositions); distinguishable from the type universe U.

### 14.4 Common Pitfalls

- **Boolean vs Heyting**: in general toposes Ω is Heyting (double-negation ≠ identity).
  Don't assume classical logic.
- **Subobject classifier ≠ universe**: Ω classifies monos, not all maps. Universe U in HoTT
  is an *object classifier* (classifies all maps).
- **Internal vs external**: the internal logic is intuitionistic even if the metatheory is
  classical. Use internal language carefully.
- **Presheaf vs sheaf**: not every presheaf topos is a sheaf topos; sheaf conditions are
  extra data (Grothendieck topology).

### 14.5 Cross-References

- §13 (CCC) — every topos is a CCC
- §19 (Double Categories) — stack of toposes and geometric morphisms
- §18 (Enriched Categories) — enriched presheaves and quantale-valued logic

---

## 15. Ends & Coends

### 15.1 Formal Foundations

Given P : C^op × C → D (a profunctor/bifunctor):

**End** `∫_c P(c,c)`: object with projections π_c : E → P(c,c) satisfying the wedge condition
`P(id,f)∘π_c = P(f,id)∘π_{c'}` for all f : c→c', and universal among all wedges.

Equivalently: `∫_c P(c,c) = equalizer(∏_c P(c,c) ⇉ ∏_{f:c→c'} P(c,c'))`.

**Coend** `∫^c P(c,c)`: dual, with injections ι_c : P(c,c) → E and cowedge condition.

Key identities:
- Natural transformations: `Nat(F,G) = ∫_c Hom(F(c), G(c))`
- Hom-tensor: `(∫^c F(c) ⊗ G(c)) ≅ ∫_c Hom(F(c), G(c))` (Yoneda-style)
- Coends as existentials: `∫^c F(c) ≅ ∃c. F(c)`

### 15.2 Core Algorithm

```typescript
// End as universal quantification (TypeScript: polymorphic function)
// ∫_c P(c,c) = <C>(c: C) => P<C,C>
type End<P> = <C>(c: C) => P_of<C, C>;

// Coend as existential (packed existential)
interface Coend<P> {
  readonly witness: unknown;          // existential c (type-erased)
  readonly value: P_of<unknown, unknown>; // P(c, c) at erased type
}
const packCoend = <C, P>(c: C, pcc: P_of<C,C>): Coend<P> =>
  ({ witness: c, value: pcc as any });

// Natural transformation as end: Nat(F,G) = forall A. F<A> → G<A>
type Nat<F extends URIS, G extends URIS> = <A>(fa: Kind<F,A>) => Kind<G,A>;

// Dinaturality check (for a dinatural transformation)
// alpha_c : P(c,c) → Q(c,c) is dinatural if alpha_{c'} . P(f,id) = Q(id,f) . alpha_c
```

### 15.3 Pragmatic Implementation

In Haskell/TypeScript, parametricity enforces the wedge condition automatically (free
theorems). Ends appear as: `∫_a Hom(F(a),G(a))` = type of natural transformations;
`∫_a F(a)→G(a)` = universal property of functor composition. Coends appear as:
existential types, type-indexed data, heterogeneous containers.

### 15.4 Common Pitfalls

- **Forgetting wedge condition**: families of morphisms that don't satisfy naturality
  don't form an end. Parametricity ensures this for System F types.
- **Coend quotient**: computing a coend requires quotienting by the cowedge relation;
  forgetting gives a coproduct, not a coend.
- **Size issues**: ends over large categories may not exist. Use density theorems.
- **Variance confusion**: profunctors are contravariant in first arg, covariant in second.

### 15.5 Cross-References

- §8 (Profunctors) — profunctors are precisely bifunctors used in end/coend formulas
- §6 (Yoneda) — Yoneda lemma expressed as an end isomorphism
- §4 (Applicative) — `traverse` and `sequenceA` expressed as ends/coends

---

## 16. Polynomial Functors

### 16.1 Formal Foundations

A **polynomial functor** p : Set → Set has the form:
`p(Y) = Σ_{i∈I} Y^{B_i}`
where I is the set of positions/shapes and B_i is the set of directions/ports at position i.

In dependent type notation: `p(Y) = Σ(i:I). (B(i)→Y)`.

The **category Poly**:
- Objects: polynomial functors p = (I, B : I→Set)
- Morphisms (I,B) → (J,C): a lens (f : I→J, f# : (i:I)→C(f(i))→B(i))

This is precisely a dependent lens. Composition in Poly = lens composition.

Key polynomials: identity `y` (I=1, B(*)=1); constant `c` (I=c, B=∅); linear `n·y` (I=n, B=1);
sum `p+q`; product `p·q`; power `p^q`; free monad `T_p = μ(y·p)`.

### 16.2 Core Algorithm

```typescript
interface Polynomial<I extends string, B extends Record<I, string[]>> {
  positions: I[];
  directions: (i: I) => string[];
}

// Element of p(Y)
interface PolyElem<I, Y> {
  position: I;
  filling: Map<string, Y>;  // B(position) → Y
}

// Functorial action (map)
const polyMap = <I extends string, Y, Z>(
  p: Polynomial<I, any>,
  e: PolyElem<I, Y>,
  f: (y: Y) => Z
): PolyElem<I, Z> => ({
  position: e.position,
  filling: new Map([...e.filling].map(([k,v]) => [k, f(v)]))
});

// Lens morphism between polynomials
interface PolyMorphism<I, J> {
  onPosition: (i: I) => J;
  onDirection: (i: I, d: string) => string;  // backwards: C(f(i)) → B(i)
}
```

### 16.3 Pragmatic Implementation

Polynomial functors give the **pattern functors** for recursion schemes (§9). `ListF<R> = 1 + R`
is the polynomial with I={Nil,Cons}, B(Nil)=∅, B(Cons)={head, tail}. The **free monad** of
a polynomial functor p is `T_p(A) = μR. A + p(R)`, modeling interaction protocols (Ports and
Protocols). W-types in dependent type theory are initial algebras of polynomial functors.

### 16.4 Common Pitfalls

- **Confusing polynomial functors with ring polynomials**: p(Y)=Y²+Y is a functor Set→Set,
  not a polynomial in a ring.
- **Strict positivity**: only strictly positive type operators have initial algebras.
  TypeScript allows `type F<A> = (a:A) => A` (negative occurrence) which breaks W-type.
- **Non-termination**: without positivity checks, recursive polynomial types diverge.
- **Composition explosion**: `p ∘ q` has |positions(q)|^|directions(p)| elements; can
  blow up combinatorially.

### 16.5 Cross-References

- §9 (F-Algebras) — catamorphisms for polynomial functor algebras
- §10 (Initial/Terminal) — W-types = initial algebras of polynomials
- §22 (Comonads) — cofree comonad of a polynomial

---

## 17. Distributive Laws

### 17.1 Formal Foundations

A **distributive law** of monad S over monad T is a natural transformation
λ : T∘S ⇒ S∘T satisfying four axioms:
- (DL1) λ∘(η^T · S) = S · η^T (T's unit distributes)
- (DL2) λ∘(μ^T · S) = (S · μ^T)∘(λ · T)∘(T · λ) (T's multiplication distributes)
- (DL3) λ∘(T · η^S) = η^S · T (S's unit distributes)
- (DL4) λ∘(T · μ^S) = (μ^S · T)∘(S · λ)∘(λ · S) (S's multiplication distributes)

Given λ, the composite ST = S∘T acquires a monad structure:
`η^{ST} = η^S ∘ η^T`, `μ^{ST} = μ^S ∘ S∘μ^T ∘ S∘λ∘T`.

This is how **monad transformers** (MaybeT, StateT, etc.) work: they embed a distributive law.

### 17.2 Core Algorithm

```typescript
// Distributive law: T(S(A)) → S(T(A))
interface DistributiveLaw<S extends URIS, T extends URIS> {
  distribute: <A>(tsa: Kind<T, Kind<S, A>>) => Kind<S, Kind<T, A>>;
}

// Compose two monads via a distributive law
function composeMonads<S extends URIS, T extends URIS>(
  S: Monad<S>, T: Monad<T>,
  law: DistributiveLaw<S, T>
): Monad<'ST'> {
  return {
    of: a => S.of(T.of(a)) as any,
    chain: (sta, f) => S.chain(sta as any, ta =>
      law.distribute(T.chain(ta, a => S.of((f(a) as any))))
    ) as any
  };
}

// Example: Maybe ⊗ List via distribute([Just(x)] → Just([x]))
const maybeTListLaw: DistributiveLaw<'Maybe', 'Array'> = {
  distribute: (arr) => arr.every(m => m.tag === 'Some')
    ? some(arr.map(m => (m as any).value))
    : none
};
```

### 17.3 Pragmatic Implementation

Not all monad pairs compose. Known working pairs: State+Any, Writer+Any, Reader+Any (these
are additive). Known failures: List∘List, Powerset∘Powerset, Exception∘Continuation.
When in doubt, use **monad transformers** (StateT, ReaderT, WriterT) which encode the
distributive law implicitly.

### 17.4 Common Pitfalls

- **Not all monads compose**: the most common mistake. Check known results before attempting.
- **Direction confusion**: λ : TS ⇒ ST, not ST ⇒ TS. Getting it backwards gives a different
  (possibly invalid) composition.
- **Monad transformer order matters**: `StateT<S, Maybe<A>>` vs `MaybeT<State<S, A>>` have
  different semantics (outer monad controls failure behavior).
- **Forgetting four axioms**: implementing only DL1/DL3 (unit laws) and ignoring DL2/DL4
  (multiplication laws) gives an invalid distributive law.

### 17.5 Cross-References

- §3 (Monads) — the monads being composed
- §11 (Kleisli/EM) — Kleisli composition and monad structure
- §12 (SMC) — some distributive laws arise from strength in SMC

---

## 18. Enriched Categories

### 18.1 Formal Foundations

Given monoidal category (V, ⊗, I), a **V-enriched category** C has:
- Objects Ob(C)
- Hom-objects C(A,B) ∈ V (not a set of morphisms, but an object of V)
- Identity j_A : I → C(A,A) in V
- Composition M_{A,B,C} : C(B,C)⊗C(A,B) → C(A,C) in V

satisfying associativity and unit coherence in V.

Key examples:
- V = Set: ordinary categories
- V = Cat: strict 2-categories
- V = ([0,∞], ≥, +, 0): Lawvere metric spaces (`C(a,b)` = distance, composition = triangle ineq)
- V = (Vect, ⊗, k): linear categories
- V = (Graded types, ⊗, I): graded/coeffect type systems

**Enriched functors** and **enriched natural transformations** generalize their ordinary
counterparts with hom-maps in V.

### 18.2 Core Algorithm

```typescript
interface MonoidalBase<V> {
  readonly unit: V;
  tensor: (a: V, b: V) => V;
  eq: (a: V, b: V) => boolean;
}

interface VCategory<Obj, V> {
  readonly base: MonoidalBase<V>;
  hom: (a: Obj, b: Obj) => V;
  id: (a: Obj) => V;
  compose: (a: Obj, b: Obj, c: Obj, f: V, g: V) => V;
}

// Lawvere metric space: [0,∞]-enriched category
const RealsBase: MonoidalBase<number> = {
  unit: 0, tensor: (a,b) => a+b, eq: (a,b) => Math.abs(a-b) < 1e-10
};
const makeMetric = <P>(pts: P[], dist: (a:P,b:P) => number): VCategory<P,number> => ({
  base: RealsBase,
  hom: dist,
  id: _ => 0,
  compose: (_a,_b,_c,f,g) => f+g  // triangle inequality holds by assumption
});

// Graded monad: V = (Grades, *, 1) enriched type system
interface GradedMonad<G> {
  of: <A>(a: A) => Graded<G, A>;   // grade = 1 (identity)
  chain: <A, B, r extends G, s extends G>(
    ga: Graded<r, A>, f: (a: A) => Graded<s, B>
  ) => Graded<Multiply<r,s>, B>;  // grades multiply
}
```

### 18.3 Pragmatic Implementation

Graded monads model **bounded resource use**: a computation of grade `n` uses a resource
at most `n` times. Implement as `Graded<n, A>` where `n` is a type-level natural number
(Peano encoding). Graded bind multiplies grades; graded return has grade 1.
`Sensitivity<r, A>` (differential privacy) is a graded monad with Lipschitz constant `r`.

### 18.4 Common Pitfalls

- **Forgetting coherence**: associativity and unitality of composition in V must hold.
  A "metric space" without triangle inequality is not a valid [0,∞]-enriched category.
- **Hom-object ≠ set of morphisms**: C(A,B) is a V-object. Treating it as a function type
  is a category error in non-Set-enriched contexts.
- **Graded monad grade drift**: forgetting to compose grades in `bind` loses effect information.
- **Semiring choice**: grades form a semiring; choosing the wrong semiring (ℕ vs {0,1,ω})
  changes the expressiveness dramatically.

### 18.5 Cross-References

- §12 (SMC) — the enriching base must be (at least) monoidal
- §3 (Monads) — graded monads generalize monads with resource tracking
- §13 (CCC) — closed monoidal = V-enriched where V = itself (self-enrichment)

---

## 19. Double Categories & Multicategories

### 19.1 Formal Foundations

A **double category** D has: 0-cells (objects); horizontal 1-cells A→B; vertical 1-cells
A↓C; and 2-cells (squares) filling configurations of horizontal and vertical cells.
Horizontal and vertical compositions both form categories; they satisfy the interchange law:
`(β∘α) * (δ∘γ) = (β*δ) ∘ (α*γ)` where ∘ = vertical, * = horizontal composition.

Formally: an internal category in Cat. Examples: spans (horizontal = spans, vertical = maps);
profunctors (horizontal = profunctors, vertical = functors).

A **multicategory** (colored operad) has: objects; multimorphisms with multiple inputs and
one output `f : (A₁,...,Aₙ) → B`; and substitution composition satisfying associativity
and unitality. A representable multicategory = monoidal category.

### 19.2 Core Algorithm

```typescript
// Multicategory
interface Multimorphism<T> {
  readonly sources: readonly T[];  // ordered inputs
  readonly target: T;
  readonly label: string;
}

class Multicategory<T> {
  addMorphism(sources: T[], target: T, label: string): Multimorphism<T>;
  identity(a: T): Multimorphism<T>;  // id : (A) → A
  // Substitution: f(g_1,...,g_n) where dom(f) matches cod(g_i)
  compose(f: Multimorphism<T>, gs: Multimorphism<T>[]): Multimorphism<T>;
}

// Double cell
interface DoubleCell<H, V> {
  top: H; bottom: H;   // horizontal source/target
  left: V; right: V;  // vertical source/target
}
// Horizontal composition: paste left-right
// Vertical composition: paste top-bottom
// Interchange: both give same result
```

### 19.3 Pragmatic Implementation

Multicategories model **typed term rewriting systems** and **non-symmetric monoidal categories**.
They appear in string diagram calculi, operadic composition in algebra, and type theories with
multi-argument type constructors. In PL: function types are binary multimorphisms; n-ary
functions are n-input multimorphisms.

Double categories model systems where morphisms have two independent directions of composition,
e.g., programs (vertical = computation, horizontal = resource flow).

### 19.4 Common Pitfalls

- **Interchange law violations**: forgetting to verify the interchange law gives inconsistent
  2-cells.
- **Boundary mismatch**: composing cells with mismatched source/target is the most common bug.
  Enforce strict runtime boundary checks.
- **Multicategory ≠ monoidal category**: multicategories need not be representable (have
  tensor products). Don't assume representability.
- **Arity tracking**: losing track of arities in substitution composition causes subtle bugs.

### 19.5 Cross-References

- §12 (SMC) — representable multicategory = SMC
- §20 (String Diagrams) — string diagrams give syntax for double categories
- §8 (Profunctors) — profunctors are horizontal morphisms in a double category

---

## 20. String Diagrams

### 20.1 Formal Foundations

A **string diagram** for a (strict) monoidal category C: objects = labeled wires (strings);
morphisms f : A → B = boxes with A-input wires at top, B-output wires at bottom; composition
= vertical stacking; tensor product = horizontal juxtaposition; identity = bare wire; unit I =
empty space.

Formally a typed directed acyclic graph (DAG) with boundary. **Correctness theorem** (Joyal-
Street): two diagrams represent the same morphism if and only if they are isotopic as
planar graphs. Pivotal categories allow wire bending (cups and caps).

For SMCs: wire crossings represent the braiding σ_{A,B}. For CCCs: lambda boxes represent
currying. For Frobenius algebras: copy and discard nodes are added.

### 20.2 Core Algorithm

```typescript
type WireId = number & { readonly __brand: 'WireId' };
type NodeId = number & { readonly __brand: 'NodeId' };

interface GeneratorSpec {
  readonly domain: readonly string[];    // input wire types
  readonly codomain: readonly string[];  // output wire types
}
interface MonoidalSignature {
  readonly objects: ReadonlySet<string>;
  readonly generators: ReadonlyMap<string, GeneratorSpec>;
}
interface DiagramNode {
  readonly generator: string;
  readonly inputs: readonly WireId[];   // one wire per domain type
  readonly outputs: readonly WireId[];  // one wire per codomain type
}
interface StringDiagram {
  readonly wires: Map<WireId, string>;       // wireId → type label
  readonly nodes: Map<NodeId, DiagramNode>;
  readonly inputs: readonly WireId[];         // diagram's external inputs
  readonly outputs: readonly WireId[];        // diagram's external outputs
}

// Compose diagrams: connect outputs of d1 to inputs of d2
function compose(d1: StringDiagram, d2: StringDiagram): StringDiagram;
// Tensor diagrams: place side by side
function tensor(d1: StringDiagram, d2: StringDiagram): StringDiagram;
```

### 20.3 Pragmatic Implementation

String diagrams are the **equational language** for monoidal categories: instead of manipulating
long chains of natural isomorphisms, draw and isotope diagrams. Implementations: `catlab`
(Julia), `DisCoPy` (Python), `Globular` (web). In TypeScript, wire up a DAG interpreter
to evaluate diagrams compositionally.

Useful for circuit design, quantum computation (ZX-calculus), proof nets (linear logic),
and visual documentation of monad laws.

### 20.4 Common Pitfalls

- **Forgetting strictification**: real SMCs have associators; string diagrams assume strict
  (by Mac Lane coherence). Implement in strict setting to avoid tracking parenthesization.
- **Wire identity confusion**: when composing, boundary wires must be properly identified.
  Each internal wire needs exactly one producer and one consumer.
- **Ignoring symmetry**: in SMCs, wire crossings are semantically meaningful. In a cartesian
  category they can be removed but must be consistently tracked.
- **Planarity**: for braided (non-symmetric) categories, over/under crossings differ.

### 20.5 Cross-References

- §12 (SMC) — string diagrams are the graphical calculus for SMCs
- §21 (Arrows) — arrows have a natural string diagram calculus (circuits)
- §22 (Comonads) — comonadic diagrams: extract = termination node; duplicate = copy

---

## 21. Arrows (Hughes)

### 21.1 Formal Foundations

An **Arrow** (Hughes 2000) is a type constructor `A :: * → * → *` with:
- `arr : (b→c) → A b c` — lift pure function
- `(>>>) : A b c → A c d → A b d` — sequential composition
- `first : A b c → A (b,d) (c,d)` — process first component of pair

Nine laws (identity, associativity, arr functor, first/arr, first/(>>>), exchange, cancel,
assoc, left). Generalization: `ArrowChoice` (left/right for sums), `ArrowLoop` (feedback),
`ArrowApply` (≅ monad).

Categorical interpretation: arrows are **strong profunctors** in a monoidal category; `arr` is
the identity profunctor map; `(>>>)` is horizontal composition; `first` is the `Strong` instance.

### 21.2 Core Algorithm

```typescript
interface Arrow<F> {
  arr<B, C>(f: (b: B) => C): ArrowVal<F, B, C>;
  compose<B, C, D>(f: ArrowVal<F, B, C>, g: ArrowVal<F, C, D>): ArrowVal<F, B, D>;
  first<B, C, D>(f: ArrowVal<F, B, C>): ArrowVal<F, [B, D], [C, D]>;
}

// Derived operations
const second = <F,B,C,D>(A: Arrow<F>, f: ArrowVal<F,B,C>): ArrowVal<F,[D,B],[D,C]> => {
  const swap = A.arr(<X,Y>([x,y]: [X,Y]): [Y,X] => [y,x]);
  return A.compose(A.compose(swap as any, A.first(f) as any), swap as any) as any;
};

const split = <F,B,C,D,E>(A: Arrow<F>, f: ArrowVal<F,B,C>, g: ArrowVal<F,D,E>) =>
  A.compose(A.first(f), second(A, g) as any);  // f *** g

const fanout = <F,B,C,D>(A: Arrow<F>, f: ArrowVal<F,B,C>, g: ArrowVal<F,B,D>) =>
  A.compose(A.arr((b: B): [B,B] => [b,b]), split(A, f, g));  // f &&& g
```

### 21.3 Pragmatic Implementation

Use arrows when: (1) you need static analysis of the computation graph (Kleisli arrows hide
structure behind closures; arrow `arr` exposes it); (2) you have signal/reactive computations
with both input and output; (3) you need `ArrowLoop` for feedback without monadic `fix`.

`Kleisli<M, A, B> = A → M(B)` with Kleisli composition is an arrow when M is a monad.
FRP (Functional Reactive Programming) uses `SF<A,B>` (signal function) as an arrow.

### 21.4 Common Pitfalls

- **Arrow vs Monad**: not every arrow is a Kleisli arrow. `ArrowApply` ≅ Monad; use arrows
  only when you *cannot* use a monad (static analysis, signal functions).
- **Tuple nesting**: deep arrow pipelines produce `((((a,b),c),d),e)` nested pairs.
  Use record types at pipeline boundaries.
- **ArrowLoop unsoundness**: feedback loops require productivity; non-productive loops diverge.
- **Law 4 (arr functor)**: `arr (g∘f) = arr f >>> arr g`. Getting the composition order wrong
  (directional confusion) violates this law.

### 21.5 Cross-References

- §3 (Monads) — `ArrowApply` ≅ monad; monad is stronger
- §8 (Profunctors) — arrows are strong profunctors
- §20 (String Diagrams) — circuit diagrams for arrow computations

---

## 22. Comonads

### 22.1 Formal Foundations

A **comonad** (W, ε, δ) on C:
- W : C → C endofunctor
- ε : W ⇒ Id (counit / extract)
- δ : W ⇒ W∘W (comultiplication / duplicate)

Laws (dual to monad): ε_W∘δ = id, W(ε)∘δ = id (counit), δ_W∘δ = W(δ)∘δ (coassociativity).

**CoKleisli extension**: `extend : (W(A)→B) → W(A) → W(B)`, satisfying:
`extend(extract) = id`, `extract∘extend(f) = f`, `extend(g)∘extend(f) = extend(g∘extend(f))`.

Key examples: `Store<S,A> = (S→A)×S` (focused store); `Env<E,A> = E×A` (read-only env);
`NonEmpty<A>` (list with focus); `Zipper<A>` (list with current position);
`Traced<M,A> = M→A` (for monoid M — dual to Writer).

### 22.2 Core Algorithm

```typescript
interface Comonad<W extends URIS> extends Functor<W> {
  extract:   <A>(wa: Kind<W, A>) => A;
  duplicate: <A>(wa: Kind<W, A>) => Kind<W, Kind<W, A>>;
  extend:    <A, B>(f: (wa: Kind<W, A>) => B, wa: Kind<W, A>) => Kind<W, B>;
}

// Store comonad: W(A) = (S→A) × S
interface Store<S, A> { peek: (s: S) => A; pos: S; }
const storeComonad = <S>(): Comonad<'Store'> => ({
  extract:   ({ peek, pos }) => peek(pos),
  duplicate: ({ peek, pos }) => ({ peek: s => ({ peek, pos: s }), pos }),
  extend:    (f, wa) => ({ peek: s => f({ peek: wa.peek, pos: s }), pos: wa.pos }),
  map:       (f, { peek, pos }) => ({ peek: s => f(peek(s)), pos })
} as any);

// CoKleisli composition: f =>> g = extend(g) . f
const cokleisli = <W extends URIS, A, B, C>(
  W: Comonad<W>, f: (wa: Kind<W,A>)=>B, g: (wb: Kind<W,B>)=>C
) => (wa: Kind<W,A>): C => g(W.extend(f, wa));
```

### 22.3 Pragmatic Implementation

Comonads model **context-dependent computation**: `extract` reads the current focus;
`extend` applies a context-consuming function everywhere simultaneously. Cellular automata:
`Zipper<Bool>` is the state; `extend(rule)` applies `rule` to every cell in context.
UI spreadsheets: `Store<Cell, Value>` with `extend` recomputing all dependent cells.

### 22.4 Common Pitfalls

- **Boundary conditions**: for Zipper-based comonads, decide what happens at edges
  (dead cells, wrapping, infinite).
- **Eager duplicate**: for large grids, `duplicate` creates O(n²) data. Use lazy evaluation.
- **Comonad law violations**: easy to write `extend` that doesn't satisfy coassociativity.
  Test all three laws.
- **Confusion with monads**: comonad operations go the *opposite* direction—`extract` pulls
  A *out of* context (vs `return` which puts A *into* context).

### 22.5 Cross-References

- §3 (Monads) — dual; monadic `join` ↔ comonadic `duplicate`
- §11 (Kleisli/EM) — CoKleisli category; comonad EM = coalgebras
- §16 (Polynomial Functors) — cofree comonad of polynomial p = ν(p)

---

## 23. Optics (Lenses, Prisms, Traversals)

### 23.1 Formal Foundations

An **optic** is a composable bidirectional accessor. The optic hierarchy:

| Optic | Constraint | Focuses on |
|---|---|---|
| Iso | `Profunctor p` | Exactly one; lossless |
| Lens | `Strong p` | Exactly one part of product |
| Prism | `Choice p` | One case of sum (0 or 1) |
| Optional | `Strong + Choice` | Zero or one |
| Traversal | `Wander p` | Zero or more |
| Fold | `Forget r` | Read-only, zero or more |
| Setter | `Mapping p` | Write-only |

**Van Laarhoven encoding** (for Lens):
`Lens S T A B = ∀F. Functor F ⇒ (A→F(B)) → S→F(T)`

**Profunctor encoding** (unified):
`Lens S T A B = ∀p. Strong p ⇒ p A B → p S T`
`Prism S T A B = ∀p. Choice p ⇒ p A B → p S T`

Optic laws (Lens):
- GetSet: `set(s, get(s)) = s`
- SetGet: `get(set(s, b)) = b`
- SetSet: `set(set(s, b), c) = set(s, c)`

### 23.2 Core Algorithm

**Van Laarhoven lens** (canonical):
```typescript
// Lens s t a b = ∀F. Functor F ⇒ (a → F b) → (s → F t)
// view: Const a functor;  over: Identity functor
type Lens<S, T, A, B> = <F extends URIS>(F: Functor<F>, f: (a: A) => Kind<F, B>, s: S) => Kind<F, T>;
const view = <S, A>(lens: Lens<S, S, A, A>, s: S): A =>
  lens(constFunctor, a => constOf(a), s).getConst;
const over = <S, T, A, B>(lens: Lens<S, T, A, B>, f: (a: A) => B, s: S): T =>
  lens(identityFunctor, a => identityOf(f(a)), s).runIdentity;
```

Concrete (getter/setter) encoding:

```typescript
interface Lens<S, A> {
  readonly get: (s: S) => A;
  readonly set: (a: A) => (s: S) => S;
  readonly modify: (f: (a: A) => A) => (s: S) => S;
  readonly compose: <B>(inner: Lens<A, B>) => Lens<S, B>;
}

const mkLens = <S, A>(get: (s: S) => A, set: (a: A) => (s: S) => S): Lens<S, A> => ({
  get, set,
  modify: f => s => set(f(get(s)))(s),
  compose: inner => mkLens(s => inner.get(get(s)), b => s => set(inner.set(b)(get(s)))(s))
});

interface Prism<S, A> {
  readonly getOption: (s: S) => A | undefined;
  readonly reverseGet: (a: A) => S;
}

// Traversal uses Applicative
interface Traversal<S, A> {
  readonly modifyF: <F extends URIS>(F: Applicative<F>) =>
    (f: (a: A) => Kind<F, A>) => (s: S) => Kind<F, S>;
}
```

### 23.3 Pragmatic Implementation

Composition order: lens composition is function composition in profunctor encoding, or
getter/setter threading in concrete encoding. `lensA.compose(lensB)` focuses into `lensA`
then `lensB`. Libraries: `monocle-ts` (fp-ts ecosystem), `optics-ts` (standalone TypeScript).

Traversals generalize `map` over arbitrary data structures: `modifyF` with `Identity` functor
= `modify`; with `Const` functor = `fold`; with `Array` applicative = collecting all foci.

### 23.4 Common Pitfalls

- **Lens law violations**: any normalization in the setter (trimming, clamping) violates
  GetSet or SetGet. Laws must hold literally.
- **Forgetting immutability**: optics assume immutable data. Mutating the source after
  `set`/`modify` breaks referential transparency.
- **Deep composition performance**: each lens composition level adds a closure. >10 levels
  may be measurable.
- **Type-changing optics**: `Lens<S,T,A,B>` with S≠T is valid (type-changing update) but
  complicates inference. Start with monomorphic `Lens<S,S,A,A>`.
- **Optional vs undefined**: confusing `undefined` (absent) with `null` (present-but-null)
  breaks Prism/Optional behavior.

### 23.5 Cross-References

- §8 (Profunctors) — profunctor encoding is the theoretical foundation of optics
- §4 (Applicative) — Traversal uses Applicative for `modifyF`
- §15 (Ends/Coends) — `Traversal S T A B = ∀p. Wander p ⇒ p A B → p S T` as an end
