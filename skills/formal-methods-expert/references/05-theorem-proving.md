# Theorem Proving and Proof Assistants

*Sources: TLAPS_Proof_System.json, Dafny_Verification_Language.json, web research (Isabelle/HOL,
Lean4, PAT).*

---

## 1. Taxonomy: Proof Assistants vs. Automated Provers vs. Model Checkers

| Category | Tools | Approach | Automation | Expressiveness |
|---|---|---|---|---|
| Interactive proof assistants | Isabelle/HOL, Lean4, Coq | User-guided proof construction | Low (user drives) | Full higher-order logic |
| Automated provers (SAT/SMT) | Z3, CVC5, Vampire | Search-based | High (fully automatic) | Decidable fragments only |
| Deductive verifiers | Dafny, Why3, Frama-C | WP calculus + SMT backend | Medium (annotations needed) | Typed programs + contracts |
| Model checkers | TLC, Apalache, PAT | State space exploration | High | Finite/bounded state spaces |

**Selection guide** (decision flowchart):
1. **Finite state, no proof needed** → model checker (TLC, PAT, Apalache)
2. **Infinite state, arithmetic constraints, code-level verification** → deductive verifier (Dafny)
3. **Need full machine-checked proof of algorithm** → interactive proof assistant (Isabelle/HOL or Lean4)
4. **Need verified compiler/certified program** → Coq (CompCert ecosystem)
5. **Need TLA+ proof of distributed protocol** → TLAPS (Isabelle/Zenon/Z3 backends)
6. **CSP protocol safety with refinement checking** → PAT

---

## 2. Isabelle/HOL

Isabelle/HOL is an interactive theorem prover for Higher-Order Logic. It is among the most widely
used proof assistants and has the largest archive of verified mathematics (AFP — Archive of Formal Proofs).

### 2.1 Type System

HOL type system with **polymorphic types** and **type classes**:
```
Types: τ ::= α (type variable) | base_type | τ₁ → τ₂ | τ list | τ set | ...
Type classes: class ring α where ... (* requires + and * for type α *)
Instances: instance int :: ring where ... (* int is a ring *)
```

Type inference: ML-style Hindley-Milner. Schematic type variables `'a`, `'b` are implicit universals.

### 2.2 Isar — Structured Proof Language

Isar (Wenzel 1999) is Isabelle's declarative proof language, inspired by informal mathematical prose.

**Core keywords**:
```isabelle
proof                   (* begin a proof block *)
  have "subgoal" by ... (* prove an intermediate step *)
  show "goal" by ...    (* prove the current goal *)
  obtain x where "P x" by ... (* introduce witnesses *)
  assume "hypothesis"   (* introduce an assumption *)
  fix x                 (* introduce arbitrary element *)
  from this             (* use previous result *)
  using hyp1 hyp2       (* make hypotheses available *)
  with assm1            (* use assm1 with other facts *)
  qed                   (* end proof block *)
```

**Isar proof example** (induction on natural numbers):
```isabelle
lemma sum_formula: "2 * (\<Sum>i\<le>n. i) = n * (n + 1)"
proof (induction n)
  case 0
  show ?case by simp                          (* base case: trivial by simplification *)
next
  case (Suc k)
  have ih: "2 * (\<Sum>i\<le>k. i) = k * (k + 1)" by (rule Suc.IH)
  have "2 * (\<Sum>i\<le>Suc k. i) = 2 * (\<Sum>i\<le>k. i) + 2 * (Suc k)" by simp
  also have "... = k * (k + 1) + 2 * (Suc k)" by (simp add: ih)
  also have "... = (Suc k) * (Suc k + 1)" by ring
  finally show ?case .
qed
```

**Apply-style proofs** (avoid — brittle across Isabelle versions):
```isabelle
lemma "P" apply (rule xyz) apply (simp) apply (auto) done
```
Apply-style proofs use a tactic list without explicit intermediate goals. They are fragile: automation
changes across Isabelle releases can silently break them. Use Isar instead.

### 2.3 Key Tactics

| Tactic | What it does |
|---|---|
| `simp` | Rewrite using simp rules; normalize terms; good for arithmetic and basic algebra |
| `auto` | Combination of simp + classical reasoning; usually sufficient for "obvious" goals |
| `blast` | Classical tableau prover; good for first-order logic with quantifiers |
| `clarsimp` | simp + clarify; good for reducing goals to simpler form |
| `force` | More aggressive than auto; tries harder |
| `metis` | Resolution-based; calls external prover Metis directly |
| `linarith` | Linear arithmetic over ordered fields/rings |
| `omega` | Presburger arithmetic (linear integer arithmetic with quantifiers) |
| `algebra` | Ring/field algebra; handles polynomial equalities |
| `decide` | Propositional tautology checker |

### 2.4 Sledgehammer

Sledgehammer is Isabelle's automation bridge to external provers.

**How to invoke**: Type `sledgehammer` in a proof state — Isabelle sends the goal and relevant lemmas
to external ATPs and SMT solvers:
- **Vampire** (resolution-based ATP)
- **E-prover** (resolution-based ATP)
- **CVC5** (SMT)
- **Z3** (SMT)

Sledgehammer runs them in parallel (timeout: 30s default). If any prover succeeds, Sledgehammer
returns an Isabelle proof method (e.g., `by (metis lemma1 lemma2)`) that can be inserted into the proof.

**When Sledgehammer fails**:
1. Simplify the goal first: `apply simp` or `apply (intro ...)` to reduce to a simpler subgoal.
2. Provide a lemma hint: `sledgehammer [add: my_lemma]`.
3. Increase timeout: `sledgehammer [timeout=60]`.
4. Break the goal into intermediate steps and prove each separately.
5. If truly stuck: weaken the statement (prove a simpler variant first) or seek a different proof strategy.

### 2.5 Archive of Formal Proofs (AFP)

The AFP is a peer-reviewed collection of formalized proofs in Isabelle/HOL. As of 2024: 750+ entries
covering algebra, number theory, analysis, algorithms, cryptographic protocols, compiler verification, etc.

**Using AFP**: Any AFP entry can be imported as a Isabelle session:
```isabelle
imports "AFP/Formal_Power_Series/FPS_Convergence"
```

AFP entries are maintained for the current Isabelle release. Key entries relevant to formal systems:
- `Native_Word`: Efficient machine-word arithmetic
- `Regular_Algebras`: Kleene algebra with applications to automata
- `Separation_Algebra`: Basis for concurrent separation logic

### 2.6 Common Pitfalls

1. **Apply-style proofs brittle across Isabelle versions**: Auto/simp behavior changes between
   releases. Isar proofs with explicit intermediate goals are robust.
2. **Schematic vs. fixed variables**: `?x` (schematic) vs. `x` (fixed by `fix x`). Incorrect mixing
   causes "type mismatch" errors that appear unrelated to the actual issue.
3. **Missing `THEN` / `OF` patterns**: `rule foo [OF bar]` applies rule `foo` with `bar` as premise.
   Forgetting `OF` causes the goal to not unify with the rule.

---

## 3. Dafny / Boogie — Deductive Program Verification

Dafny (Leino 2010) is a programming language with built-in verification conditions. It is the
primary deductive verifier for real programs (as opposed to abstract mathematical proofs).

### 3.1 Architecture

```
Dafny program (with annotations)
    ↓ Weakest Precondition calculus
Boogie intermediate verification language (IVL)
    ↓ Verification conditions (VCs)
Z3 SMT solver
    ↓ SAT / UNSAT
Verified | Counterexample
```

### 3.2 Method Annotations

```dafny
method BinarySearch(a: array<int>, key: int) returns (index: int)
    requires a != null && a.Length > 0
    requires forall i, j :: 0 <= i < j < a.Length ==> a[i] <= a[j]  (* sorted *)
    ensures 0 <= index < a.Length ==> a[index] == key
    ensures index == -1 ==> forall i :: 0 <= i < a.Length ==> a[i] != key
{
    var lo := 0; var hi := a.Length - 1;
    while lo <= hi
        invariant 0 <= lo <= a.Length && -1 <= hi < a.Length
        invariant forall i :: 0 <= i < lo ==> a[i] < key  (* key not in left portion *)
        invariant forall i :: hi < i < a.Length ==> a[i] > key  (* key not in right portion *)
        decreases hi - lo + 1
    {
        var mid := (lo + hi) / 2;
        if a[mid] == key { return mid; }
        else if a[mid] < key { lo := mid + 1; }
        else { hi := mid - 1; }
    }
    return -1;
}
```

### 3.3 Weakest Precondition Calculus

`wp(S, Q)` = the weakest predicate P such that if P holds before S executes, Q holds after.

Key rules:
```
wp(x := e, Q)           = Q[e/x]              (* substitution *)
wp(S₁; S₂, Q)           = wp(S₁, wp(S₂, Q))  (* sequential composition *)
wp(if B then S₁ else S₂, Q) = (B → wp(S₁,Q)) ∧ (¬B → wp(S₂,Q))
wp(assert P, Q)          = P ∧ Q
wp(assume P, Q)          = P → Q
wp(while B invariant I decreases t, Q) = I ∧ (I ∧ B → wp(body, I)) ∧ (I ∧ ¬B → Q)
```

Loop invariant checklist — the invariant must:
1. **Hold on entry**: `precondition → invariant` must be provable.
2. **Be preserved by the loop body**: `invariant ∧ guard → wp(body, invariant)`.
3. **Imply the postcondition on exit**: `invariant ∧ ¬guard → postcondition`.
4. **Express what the loop achieves**: not just `true` — must capture the loop's semantic content.

### 3.4 Ghost Variables and Lemmas

```dafny
ghost var history: seq<int>        (* verification-only variable; erased from compiled code *)

lemma SortedSubarrayLemma(a: array<int>, lo: int, hi: int)
    requires 0 <= lo <= hi <= a.Length
    requires sorted(a, lo, hi)
    ensures forall i, j :: lo <= i < j < hi ==> a[i] <= a[j]
{ /* proof body */ }
```

Ghost code and lemmas exist only during verification. Lemmas are proved by Dafny/Z3 and can be
called in method bodies to provide intermediate proof steps.

### 3.5 Common Pitfalls

1. **Loop invariant too weak**: The most common Dafny error. If Dafny cannot prove a postcondition,
   the loop invariant almost always needs strengthening. Add terms that capture "what the loop has
   established about array[lo..i-1]" or similar.
2. **Termination argument too coarse**: `decreases hi - lo` for a loop that modifies hi and lo in
   complex ways; Dafny may not be able to prove the measure decreases. Use multiple components:
   `decreases hi - lo, hi` for lexicographic ordering.
3. **Heap aliasing**: Dafny tracks heap modifications via `modifies` clauses. Missing a heap
   location in `modifies` causes failures that look unrelated to the actual issue.

---

## 4. Lean4

Lean4 (de Moura et al. 2021) is a modern, high-performance proof assistant and programming language.
It has rapidly grown in adoption due to Mathlib4 and excellent meta-programming support.

### 4.1 Type-Theoretic Foundation

Lean4 is based on the **Calculus of Inductive Constructions (CIC)**, a dependent type theory.

**Propositions as types** (Curry-Howard isomorphism):
- Propositions are types: `P : Prop`
- Proofs are terms: `h : P` (h is a proof of P)
- `P → Q` is both the function type and logical implication
- `∀ x : α, P x` is both dependent function type and universal quantification
- Proving a theorem = constructing a term of the right type

```lean4
-- Prove: ∀ n : Nat, 0 + n = n
theorem zero_add (n : Nat) : 0 + n = n := by
    induction n with
    | zero => rfl              (* 0 + 0 = 0: reflexivity *)
    | succ k ih => simp [Nat.add_succ, ih]  (* inductive step *)
```

### 4.2 Tactic Mode

Lean4 tactics manipulate proof goals interactively:

| Tactic | What it does |
|---|---|
| `intro h` | Introduce hypothesis h from `∀` or `→` |
| `apply f` | Apply function/lemma f (backward reasoning) |
| `exact h` | Close goal with term h (exact match) |
| `rw [h]` | Rewrite goal using equation h (left to right) |
| `rw [← h]` | Rewrite goal using equation h (right to left) |
| `simp [h]` | Simplification using h and simp lemmas |
| `simp_all` | Simplification including all hypotheses |
| `omega` | Linear arithmetic over Int/Nat (complete decision procedure) |
| `ring` | Commutative ring equalities (polynomial identities) |
| `linarith` | Linear arithmetic with given hypotheses |
| `norm_num` | Numerical computations (evaluate concrete expressions) |
| `decide` | Finite decidable propositions (propositional tautology, small bounded search) |
| `tauto` | Propositional tautology checker |
| `contradiction` | Derive False from contradictory hypotheses |
| `constructor` | Prove `And`, `Iff`, inductive types by providing components |
| `cases h` | Case-split on hypothesis h (pattern matching) |
| `induction n` | Structural induction on n |
| `use x` | Provide witness for `∃ x, P x` |

### 4.3 The `omega` Tactic

`omega` is Lean4's complete decision procedure for **linear arithmetic over integers and naturals**.
It handles: `+`, `-`, `*c` (multiplication by constants), `≤`, `<`, `=`, `≠`, quantifier-free.

```lean4
example (x y : Int) (h1 : x + 2 * y ≤ 10) (h2 : x ≥ 3) : y ≤ 3 := by omega
example (n : Nat) : n + 1 > n := by omega
example (a b : Nat) (h : a < b) : a + 1 ≤ b := by omega
```

`omega` is analogous to Z3's QF_LIA fragment — complete for linear integer arithmetic,
runs in polynomial time.

### 4.4 Mathlib

Mathlib4 is the community mathematical library for Lean4. As of April 2026: 220,000+ theorems
and 110,000+ definitions covering:
- **Algebra**: Groups, rings, fields, modules, linear algebra, category theory
- **Analysis**: Real analysis, complex analysis, measure theory, topology
- **Number theory**: Primes, modular arithmetic, algebraic number theory
- **Combinatorics**: Graph theory, finite sets, permutations
- **Logic**: Set theory, model theory basics

**Importing Mathlib**: `import Mathlib` (or specific modules). Compilation takes several minutes.

### 4.5 Meta-programming

Lean4's macro system enables custom syntax and tactics:

```lean4
-- Custom syntax:
macro "myTactic" : tactic => `(tactic| simp; omega; ring)

-- Custom notation:
notation:50 a " ≡ " b " (mod " n ")" => Nat.ModEq n a b

-- Elaborator for custom tactics:
elab "mySearch" : tactic => do
    let goal ← Lean.Elab.Tactic.getMainTarget
    -- inspect goal, dispatch to appropriate proof strategy
```

### 4.6 Common Pitfalls

1. **Universe level errors**: Lean4 has a universe hierarchy (Type 0, Type 1, ...) to prevent
   paradoxes. Error messages like "type mismatch: Type 1 ≠ Type" indicate universe issues.
   Fix: use `Type*` (universe-polymorphic) or explicitly annotate universe levels with `universe u`.
2. **Instance synthesis failures**: When a type class instance is not found for a concrete type,
   Lean4 produces an "unknown instance" error. Fix: add `deriving` or explicitly `instance` the
   required type class.
3. **`simp` looping**: `simp` with a lemma that rewrites left-to-right and another that rewrites
   right-to-left (or a reflexive rewrite) loops forever. Fix: use `simp only [h1, h2]` to control
   which simp lemmas are active; add `[↓ reduceRecursor]` or `[norm_cast]` as appropriate.
4. **`decide` timeout on large types**: `decide` compiles a decision procedure for finite types.
   For types with millions of elements, it times out. Fix: use `norm_num` or `omega` for arithmetic;
   use `native_decide` (compile to native code, but unsound under unverified native execution).

---

## 5. Coq

Coq is a mature proof assistant based on CIC, similar to Lean4 but with a different ecosystem.

**Key characteristics**:
- Proof terms extracted to OCaml or Haskell (extraction)
- CompCert: verified C compiler implemented in Coq — the gold standard of verified compilers
- Mature, stable, large industrial proof library
- `Proof. intro. apply. Qed.` proof structure
- Ssreflect library (mathematical components) for cleaner proofs

**When to use Coq over Lean4**:
- Existing Coq proofs (large legacy base)
- Need CompCert-style verified compilation (C → assembly, with correctness proof)
- Team already knows Coq

**When to use Lean4 over Coq**:
- New project with no legacy
- TypeScript/ML familiarity (Lean4 syntax is more accessible)
- Need Mathlib (much larger than Coq's math library)
- Need metaprogramming (Lean4's macro system is more ergonomic)

---

## 6. PAT — Process Analysis Toolkit

PAT (Process Analysis Toolkit, Sun, Liu et al. 2009, NUS) is a CSP-based model checker for
concurrent and real-time systems.

### 6.1 What PAT Is

PAT is a model checker and simulator for event-based systems specified in CSP (Communicating
Sequential Processes). It verifies safety and liveness properties and checks CSP refinement.

**Eleven modules**: CSP, Real-Time Systems, Probability CSP, Probability RTS, LTS, Timed Automata,
NesC, ORC, Stateflow, Security, Web Service.

### 6.2 CSP Operators

```csp
-- Prefix (sequencing): event → process
a -> P                      (* perform event a, then behave as P *)

-- External choice: environment chooses
P [] Q                      (* environment selects which branch to engage *)

-- Internal choice: process chooses nondeterministically
P |~| Q                     (* process internally selects branch — env cannot control *)

-- Parallel composition: synchronize on shared events
P || Q                      (* fully synchronized: all events must synchronize *)
P [|A|] Q                   (* synchronize on set A; other events free *)
P ||| Q                     (* interleaving: no synchronization *)

-- Sequential composition
P; Q                        (* P runs, then Q runs *)

-- Hiding: internalize events
P \ A                       (* events in A become τ (internal) *)

-- Recursion
X = a -> b -> X             (* infinite process *)
```

### 6.3 Verification Properties

| Property | PAT syntax | Meaning |
|---|---|---|
| Deadlock freedom | `#deadlock-free` | System can always make progress |
| Livelock freedom | `#livelock-free` | System never enters τ-loop |
| Reachability | `#reach {state}` | State is reachable from initial |
| LTL | `#assert Spec |= G(a -> F b)` | LTL formula holds on all traces |
| Trace refinement | `#assert Spec [T= Spec2` | Every trace of Spec is a trace of Spec2 |
| Failures refinement | `#assert Spec [F= Spec2` | Trace + refusal set refinement |
| FD refinement | `#assert Spec [FD= Spec2` | Failures-divergences refinement |

### 6.4 Refinement Checking

**Trace refinement** `P [T= Q` (P is trace-refined by Q):
Every trace of P is also a trace of Q. P has no behaviors that Q prohibits.

**Failures refinement** `P [F= Q`:
Every (trace, refusal-set) pair of P is also in Q. Stronger: also captures what the process refuses.

**Failures-divergences refinement** `P [FD= Q`:
FD refinement is the standard CSP notion of refinement, capturing both refusal behavior and
absence of livelock (divergence).

```csp
-- Example: mutual exclusion protocol verification
P1 = enter1 -> cs1 -> exit1 -> P1
P2 = enter2 -> cs2 -> exit2 -> P2
Lock = acquire -> release -> Lock
System = (P1 [|{enter1, exit1}|] Lock) ||| P2
Spec = (cs1 -> STOP) [> (cs2 -> STOP)   -- never both in critical section

-- Check that System satisfies Spec (safety: no simultaneous CS access)
#assert System [T= Spec
```

### 6.5 State Space Exploration

PAT uses BFS with **anti-chain optimization** for refinement checking (substantial speedup over
naive BFS). Anti-chains represent sets of "dominated" states; dominated states are pruned.

### 6.6 Common Pitfalls

1. **State explosion in large parallel compositions**: Every `||` doubles (approximately) the state
   space. 10 parallel processes can produce 2^10 = 1024× more states. Fix: abstract unimportant
   processes; use hiding (`\`) to remove irrelevant events before composition.
2. **Internal choice `|~|` vs external choice `[]`**: `P |~| Q` means the process decides;
   `P [] Q` means the environment decides. Confusing them produces wrong verification results.
   In CSP safety proofs, internal choice is typically more conservative (harder to satisfy safety).
3. **Interleaving explosion**: `P ||| Q ||| R` generates all interleavings — O(n! / (n₁! n₂! n₃!))
   states for lengths n₁, n₂, n₃. Use synchronization (`[|A|]`) to constrain interleaving where possible.

---

## 7. Proof Strategy Selection Guide

```
Question: What do I need to verify?
    ↓
Is the state space finite and enumerable?
    YES → Use model checker:
         Protocol (CSP, concurrent): PAT
         TLA+ spec: TLC
         Infinite domain spec: Apalache
    NO (unbounded state / programs) →
         Is the question about program code with pre/postconditions?
             YES → Dafny (automated, SMT-backed)
             NO → Need a full machine-checked proof:
                  Is the project using CompCert ecosystem?
                      YES → Coq
                      NO → Lean4 (larger math library, better metaprogramming)
                           Isabelle/HOL (larger AFP, more proof tactics)
         Is it a TLA+ spec that needs a proof (not just model checking)?
             YES → TLAPS
```

---

## 8. Automation Limits

**When automation suffices**:
- Bounded properties (up to k steps)
- QF_LIA / QF_LRA arithmetic facts
- Decidable datatype properties (pattern matching, constructor injectivity)
- Simple inductions with obvious measure

**When interactive proof is needed**:
- Inductive invariants with complex invariant structure
- Unbounded programs with non-trivial loop invariants
- Protocol correctness (safety + liveness both, full proof)
- Foundational results (soundness/completeness of a logic)

**Sledgehammer/decide as automation within interactive provers**: In Isabelle/HOL, `sledgehammer`
often closes subgoals automatically. In Lean4, `omega`/`ring`/`decide` cover large fragments.
Use interactive proof only for the residual goals that automation cannot handle.

---

## 9. Implementation Strategies

**For verification-by-design in a software project**:
1. **Model check first** (cheapest): TLC or PAT on the protocol design — 2–3 hours investment,
   finds design bugs.
2. **Add SMT-backed verification** (for code): Dafny for critical algorithms (binary search,
   sorting, data structure operations). Moderate annotation effort.
3. **Add interactive proofs sparingly**: Only for absolute core invariants (e.g., "the consensus
   algorithm always terminates" or "the encryption scheme is correct"). Reserve for 5–10% of
   verification effort at most.

---

## 10. Common Pitfalls Summary

**Isabelle/HOL**: Apply-style proofs break between versions — use Isar.

**Dafny**: Loop invariant too weak (most common cause of verification failure) — the invariant must
capture what the loop has established, not just what is true at the start.

**Lean4**: Universe level errors — add `Type*` or explicit universe annotations; `simp` loops —
use `simp only` with explicit lemma list.

**Coq**: Proof irrelevance issues — in Coq, proofs of `Prop` are interchangeable but `Set`/`Type`
proofs are not; confusing them causes type errors.

**PAT**: State explosion from unconstrained interleaving — always synchronize or hide events when
possible; use anti-chain refinement algorithms.

---

## 11. Key References

- Nipkow, T., Paulson, L.C. & Wenzel, M. (2002). *Isabelle/HOL: A Proof Assistant for Higher-Order Logic*. LNCS 2283.
- de Moura, L., Ullrich, S. et al. (2021). The Lean 4 theorem prover and programming language. *CADE 2021*.
- Leino, K.R.M. (2010). Dafny: An automatic program verifier for functional correctness. *LPAR 2010*.
- Bertot, Y. & Castéran, P. (2004). *Interactive Theorem Proving and Program Development: Coq'Art*. Springer.
- Sun, J., Liu, Y. et al. (2009). PAT: Towards flexible verification under fairness. *CAV 2009*.
- Frühwirth, T. (1998). Theory and practice of constraint handling rules. *JLP*, 37(1-3).
