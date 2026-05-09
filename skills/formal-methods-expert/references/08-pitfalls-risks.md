# Pitfalls, Risks, and Decidability Guide

*Synthesis across all sub-domains: SAT, SMT/Z3, CLP/CP, TLA+, theorem proving, model checking.*

---

## 1. Undecidability Landmines

These are the most dangerous failure modes — they cause solvers to hang indefinitely or produce
incorrect results without warning.

### 1.1 Adding Universal Quantifiers to SMT Formulas

The most common undecidability trap. Adding `∀x. P(x)` to a Z3 formula immediately exits the
decidable QF (quantifier-free) fragment. Z3 handles quantifiers heuristically via **E-matching**
(pattern-based instantiation) — which is **incomplete**: Z3 may return `sat` when the formula is
actually `unsat` (missing instantiation), or fail to terminate.

```
⚠ LANDMINE:
(assert (forall ((x Int)) (>= x 0)))   ; ← INCORRECT fragment; Z3 uses E-matching
                                         ; may not terminate; may give wrong answer
```

**Fix**: Use quantifier-free encoding. If universally quantifying over a finite range is needed,
enumerate explicitly. If the quantification is over an infinite domain, restructure the problem.

**Rule**: Never introduce `∀` or `∃` in Z3 formulas unless you have verified the resulting logic
fragment is decidable (e.g., Presburger arithmetic allows bounded quantifiers).

### 1.2 QF_NIA — Non-Linear Integer Arithmetic

Multiplying two symbolic integer variables (`x * y` where both are free) places the formula in
QF_NIA. Z3's QF_NIA handling is heuristic (not complete). Z3 may return `unknown` or time out.

```
⚠ LANDMINE:
(assert (= (* x y) 12))  ; x and y are both free integers → QF_NIA
```

**Fix**: Multiply by a concrete constant (`(* 3 x)` is fine — QF_LIA). Reformulate non-linear
constraints as linear ones by introducing case splits or bounded enumeration.

### 1.3 Inhibitor Arcs in Petri Nets + SMT Encoding

Petri nets with inhibitor arcs (transition enabled iff place is **empty**) enable zero-testing.
Zero-testing in counter machines makes reachability **undecidable** (Minsky 1961).

The state equation encoding works only for pure Petri nets (no inhibitor arcs, no reset arcs).
Encoding inhibitor arcs as `x[p] = 0` in the state equation is **incorrect** — it conflates the
structural equation with the control condition.

**Fix**: Use pure Petri nets for SMT-based verification. For nets with inhibitor arcs, use
bounded model checking (explicit enumeration up to a token bound).

### 1.4 Petri Net Reachability — Ackermann-Complete

General Petri net reachability (no inhibitor arcs, pure nets) is now known to be
**Ackermann-complete** (Czerwinski et al. 2021) — not just EXPSPACE. This means:
- No practical algorithm can solve all instances.
- SMPT and other tools handle many practical cases but not all.
- TLC/Apalache can only handle **bounded** nets (finite token bounds).

**Fix**: For unbounded Petri nets with many tokens: use conservative over-approximations (state
equation gives necessary conditions; trap invariants sharpen). Accept that completeness is
impossible for this problem class.

### 1.5 First-Order Logic with Equality

Full first-order logic (with equality, function symbols, quantifiers) is **semi-decidable**:
complete but not terminating for unsatisfiable formulas. Z3's behavior on first-order logic
inputs is heuristic and non-terminating in the worst case.

**Fix**: Identify the decidable fragment (QF_LIA, QF_UF, QF_BV) and stay within it.

---

## 2. Performance Cliffs

These are scenarios where performance drops precipitously — from milliseconds to minutes or hours.

### 2.1 State Space Explosion

Explicit-state model checking is fundamentally limited by state space size:
- 10 Boolean variables: 2^10 = 1,024 states (trivial)
- 30 Boolean variables: 2^30 ≈ 10^9 states (challenging)
- 50 Boolean variables: 2^50 ≈ 10^15 states (infeasible)

**Practical limit**: TLC handles ~10^8 states in memory on a 16GB machine.

**Fix**: Use symbolic model checking (Apalache), state space reduction (symmetry — but not for
liveness), compositional verification, or abstract interpretation.

### 2.2 TLC Symmetry Reduction Unsafe for Liveness

TLC's symmetry reduction is **unsound for liveness properties** (LTL formulas, fairness). The
reduction may eliminate states needed for the Büchi automaton SCC search, producing false "property
holds" verdicts.

TLC does warn about this, but the warning is easy to miss in output.

**Fix**: **Always disable symmetry reduction when checking any temporal (liveness) property**.
Use symmetry only for safety (invariant) checking.

### 2.3 Z3 WASM Overhead

| Scenario | Overhead |
|---|---|
| WASM vs native Z3 | 2–5× slower |
| First `init()` call | 1–3 second WASM load |
| Uncached Context creation | ~100ms per creation |
| `unknown` return (timeout) | Blocking — need explicit timeout |

**Fix**:
1. Cache `Context('main')` globally — create once at startup.
2. Set explicit timeout: `solver.set('timeout', 5000)`.
3. Always handle `'unknown'` return in production code.

### 2.4 TypeScript Propagator Performance

TypeScript is 10–100× slower than C++ (Gecode) for raw propagation inner loops.

**Acceptable for**: Compliance-scale problems (<1000 variables, few thousand constraint evaluations
per second needed). Within TypeScript's budget.

**Not acceptable for**: Hard scheduling problems (>10,000 variables, many backtracks). Use OR-Tools.

**Key TypeScript optimizations**:
- `Int32Array` for domain storage (avoid GC pressure from `number[]`)
- Pre-allocated result buffers (no allocation in propagation hot loop)
- `|`, `&` bitwise operations for bit-set domains (32-bit JavaScript)
- Monomorphic propagator classes (V8 inline cache works on single shape)

### 2.5 OR-Tools CP-SAT Overhead on Micro-Problems

OR-Tools has significant per-call overhead for the portfolio initialization (~5ms).
For problems solved in <1ms, OR-Tools overhead dominates.

**Fix**: Use OR-Tools for problems with >1000 variables or >1 second native solve time. Use Z3 or
a custom propagator for micro-problems.

### 2.6 TLAPS Proof Obligation Timeouts

TLAPS sends proof obligations to external backends (Isabelle, Zenon, Z3). Each backend has a
default timeout (Isabelle: 60s, Z3: 10s). Long-running arithmetic obligations may time out.

**Fix**: Increase timeouts explicitly:
```tla
BY DEF ... WITH Zenon, Z3 TIMEOUT 120
```
Or break the obligation into smaller lemmas that each fit within the timeout.

---

## 3. Completeness Gaps

These are situations where the algorithm is sound but **incomplete** — it may fail to find a
proof even when one exists.

### 3.1 Arc Consistency Without LCG

Pure propagation to fixpoint (arc consistency) is complete for finding all solutions in a given
search tree, but **does not backjump**. Without lazy clause generation (LCG), each failed subtree
is discovered by chronological backtracking — exponential on hard instances.

**Example**: N-Queens for N=25 may take hours with pure propagation + chronological backtracking,
but milliseconds with LCG (Chuffed/OR-Tools CP-SAT).

**Fix**: Use LCG-based solver (OR-Tools, Chuffed) for hard combinatorial instances.

### 3.2 BMC Without k-Induction

BMC finding UNSAT up to k=100 **does not prove the property holds**. There may be counterexamples
of length 101 or larger. BMC is only a bug-finding technique.

**Fix**: Use k-Induction (extends BMC to a proof attempt) or IC3/PDR (learns inductive clauses).

### 3.3 SMPT SAT Result

The state equation for a Petri net giving SAT means the **linear algebraic necessary condition
is satisfied**. It does NOT mean the target marking is reachable. Firing order constraints may
prevent the reachability.

**Fix**: Only UNSAT is a proof (of unreachability). SAT requires additional verification. Add trap
constraints (Section 5.3 of `06-model-checking-algorithms.md`) for sharper necessary conditions.

### 3.4 Apalache Bounded Model Checking

Apalache checks TLA+ specs up to a bounded number of steps (k). Finding no counterexample up to k
does not prove correctness beyond k.

**Fix**: Use Apalache for counterexample finding and debugging. Use TLAPS for complete proofs.

### 3.5 Z3 E-Matching for Quantified Formulas

When Z3 handles quantified formulas, it uses E-matching (pattern-based instantiation). E-matching
is a heuristic — it may miss some instantiations, causing incorrect `sat` results.

**Fix**: For quantified formulas, test with multiple patterns and trigger annotations. Prefer
quantifier-free encodings whenever possible.

---

## 4. Theory Combination Failures

These arise when using multiple theories together (Nelson-Oppen combination).

### 4.1 Skipping Purification

When constructing mixed-theory formulas manually (EUF + LIA + Arrays), each theory solver
expects formulas entirely in its own signature. An "alien subterm" (a term from another theory's
signature) causes incorrect behavior.

```
⚠ WRONG: assert f(x + 1) = g(y) directly to EUF solver
✓ RIGHT: introduce z = x + 1 (fresh var); assert f(z) = g(y) to EUF; assert z = x + 1 to LIA
```

Z3 handles purification automatically when using the standard API. Manual API users constructing
formulas directly are at risk.

### 4.2 Non-Convex Theory Case-Split Explosion

When combining non-convex theories (LIA, BV), equality sharing requires case splits. Each case
split doubles the search space. Five non-convex theory atoms → 2^5 = 32 case splits in the worst case.

**Fix**: Minimize mixing of non-convex theories. QF_LIA alone is convex (no case splits needed).
The cost is paid when combining LIA with BV or with arrays involving integer indices.

### 4.3 Mixing Quantified and Quantifier-Free Constraints

If even one assertion in a formula is quantified (`∀` or `∃`), the entire formula becomes
harder for Z3 to handle. The solver must switch from a complete procedure to a heuristic.

**Fix**: Isolate quantified assertions. If a quantified assertion is necessary (e.g., an
axiom), use trigger annotations to help E-matching: `(forall ((x Int)) (! P(x) :pattern (f x)))`.

### 4.4 Array Extensionality with Large Models

The extensionality axiom `(∀i. a[i] = b[i]) → a = b` is universally quantified. In large models
with many array operations, lazy instantiation may miss needed cases.

**Fix**: Use `(get-value (a i))` to check specific array accesses in the model. Add explicit
equality assertions for specific indices if needed.

---

## 5. Decidable Fragment Quick Reference

| Logic / Fragment | Decidable? | Complexity | Primary use |
|---|---|---|---|
| QF_PROP (propositional SAT) | Yes | NP-complete | Hardware verification, planning |
| QF_LIA (linear integer arithmetic) | Yes | NP-complete | Compliance constraints, PN state equations |
| QF_LRA (linear real arithmetic) | Yes | Polynomial (LP/simplex) | Continuous thresholds |
| QF_NRA (non-linear real) | Yes | 2-EXP (CAD) | Polynomial real constraints — use sparingly |
| QF_NIA (non-linear integer) | Incomplete | — | Avoid; heuristic only; set timeout |
| QF_BV (bit-vectors) | Yes | NP-complete | Hardware, byte-level protocol verification |
| QF_UF / EUF | Yes | NP-complete | Symbolic equality, uninterpreted functions |
| QF_AX (arrays, quantifier-free) | Yes | NP-complete | Quantifier-free array reasoning |
| QF_AUFLIA | Yes | NP-complete | Arrays + integer arithmetic |
| LIA (Presburger arithmetic) | Yes | 2-EXP | Quantified integer arithmetic |
| Full first-order logic | Semi-decidable | — | Cannot guarantee termination |
| General PN reachability | Ackermann-complete | — | Beyond any fixed exponential tower |
| Inhibitor arc PN reachability | Undecidable | — | Minsky counter machine reduction |

---

## 6. Trailing Implementation Bugs

Trailing is the backtracking mechanism for CLP solvers. These bugs are subtle and hard to detect
because they cause **silent incorrect results** (not crashes).

### 6.1 Missing Magic-Number Optimization

Without the magic-number check (`trail_level[attr] < current_level`), a propagator that modifies
the same domain attribute k times in one propagation step creates k trail entries. On backtrack,
all k entries are replayed — but only the last value matters. This creates O(modifications) trail
entries per choice point.

On deep backtracking with many domain modifications: exponential trail growth → memory exhaustion.

**Fix**: Always check `trail_level[attr] < current_level` before adding a trail entry.

### 6.2 Backtrack Scope Error

Off-by-one in trail marks: when a choice point is pushed, the trail mark `m` is stored. On
backtrack, entries are popped until `trail.length == m`. If the mark is recorded one entry too
late, the backtrack misses the last modification at the previous level.

**Fix**: Record the trail mark **before** any modifications at the new level; restore to mark value
**inclusively** (pop until trail.length == mark).

### 6.3 Over-Trailing After Fixpoint

If code trails entries during propagation loops (rather than before domain modifications), the
same entry may be trailed multiple times before propagation completes. Magic-number check prevents
this within a level, but if the level counter is not updated correctly between propagation calls,
the same level is trailed multiple times.

### 6.4 Not Snapshotting at Choice Points

If trail marks are not saved at each choice point (branching in search), there is no way to
distinguish "modifications at level k" from "modifications at level k+1." The entire trail since
the last backtrack becomes the undo target.

---

## 7. TypeScript-Specific Traps

### 7.1 Object Allocation in Propagation Hot Loops

Creating `new PropagationResult(...)` or `new Array(...)` inside tight propagation loops triggers
the garbage collector. V8 GC pauses are unpredictable (1–100ms). For compliance-scale problems,
this may be acceptable; for performance-sensitive applications, it causes latency spikes.

**Fix**: Pre-allocate result buffers; reuse objects; use `Int32Array` for domain storage.

### 7.2 32-Bit Bitwise Operations

JavaScript uses **32-bit signed integers** for bitwise operations (`|`, `&`, `~`, `^`, `<<`, `>>`).
A bit-set domain representation is limited to 32 values without multi-word handling.

```typescript
// This silently truncates to 32 bits:
const mask = 1 << 33;   // = 2, not 2^33

// Correct multi-word approach:
const mask = new Uint32Array(Math.ceil(maxValue / 32));
```

### 7.3 V8 Inline Cache vs C++ Monomorphization

TypeScript generic classes (like `LessEq<V0 extends IntView, V1 extends IntView>`) are erased at
runtime — V8 sees `LessEq<Object>`. Without monomorphization, the code-reduction benefit of views
is preserved but the performance benefit is smaller than in Gecode's C++ templates.

**Fix**: For performance-critical propagators, use concrete (non-generic) implementations of the
hot path. Use views for correctness and code organization; specialize by inlining the hot loop.

### 7.4 Async Z3 API

All Z3 WASM operations are asynchronous (`Promise`-based). Every call to `solver.check()` needs
`await`. Mixing sync/async (calling `solver.check()` without `await`) returns a `Promise<'sat'>`,
not `'sat'` — the equality check `result === 'sat'` silently returns `false`.

**Fix**: Always `await` Z3 calls. Use TypeScript's strict type checking to catch missing `await`.

---

## 8. Top-3 Mistakes Per Sub-Domain (Quick Reference)

### SAT
1. Watches not maintained on backtrack (invariant: each clause always has 2 non-false watched literals)
2. Activity bump misses literals — only 1-UIP bumped instead of all learned clause literals
3. Clause deletion removes "reason" clauses currently used in trail — dangling reason pointers

### SMT/Z3
1. QF_NIA used when QF_LIA suffices — 100–1000× performance drop
2. Purification step skipped in Nelson-Oppen combination — incorrect theory interaction
3. UserPropagator missing push()/pop() — state leaks across backtracks → wrong results

### CLP/CP
1. Magic-number trailing optimization missing — exponential trail growth
2. Affected propagators not rescheduled on domain change — incomplete propagation → wrong results
3. No termination guarantee on unbounded CLP(Z) domains — infinite propagation loop

### TLA+/TLC
1. Symmetry reduction enabled for liveness properties — unsound; may report "holds" when it doesn't
2. Stuttering steps missing in refinement proof — refinement proof fails in non-obvious ways
3. Liveness checking on large state space — nested DFS requires full state graph in memory

### Theorem Proving
1. Isabelle: apply-style proofs break between versions — use Isar structured proofs
2. Dafny: loop invariant too weak — doesn't capture what the loop establishes → postcondition unprovable
3. Lean4: universe level errors — add `Type*` or explicit universe annotations

### Model Checking
1. BMC result declared "verified" when it is only bounded bug-finding — no proof of correctness
2. k-Induction UNKNOWN misinterpreted as "property might fail" — it means "inductive step failed at k"
3. SMPT SAT result used as reachability proof — it is only a necessary condition

---

## 9. Common Beginner Misconceptions

**(a) "SMT solvers are always complete"**
False. Z3 is complete only for decidable QF fragments. Quantified formulas, QF_NIA, string theory:
Z3 uses heuristics. The `'unknown'` result is not an error — it is the correct answer when Z3
cannot determine satisfiability.

**(b) "Propagation to fixpoint proves correctness"**
False. Arc consistency / bounds consistency is a local property: after fixpoint, no single constraint
has a domain value that is provably inconsistent with the constraint in isolation. But global
satisfiability is not implied — there may be no consistent assignment even though each constraint
individually is consistent with each domain value.

**(c) "UNSAT means the system is safe"**
Only if the encoding is faithful. UNSAT means "the negation of the property is unreachable in the
encoded model." If the encoding over-approximates (misses behaviors) or under-approximates (adds
spurious behaviors), UNSAT may not correspond to real safety. Always verify that the encoding
faithfully captures the system.

**(d) "More learned clauses = better solver"**
Not necessarily. Learned clause databases require memory and slow unit propagation (more clauses to
scan per BCP step). Clause deletion is essential: keep only the highest-quality clauses (LBD ≤ 2 =
"glue clauses"). Aggressive deletion may lose useful clauses; conservative deletion → memory exhaustion.

**(e) "IC3/PDR is always better than k-Induction"**
IC3/PDR is more powerful but also more complex and resource-intensive. For simple invariants that are
1-inductive (no auxiliary invariants needed), k-Induction solves them instantly while IC3 initializes
its frame structure. Use k-Induction first; escalate to IC3 only when k-Induction fails to converge.

---

## 10. Key References

- Czerwinski, W. et al. (2021). The reachability problem for Petri nets is not elementary. *JACM*, 68(1). [Ackermann-complete]
- Feydy, T. & Stuckey, P.J. (2009). Lazy clause generation reengineered. *CP 2009*. [LCG completeness]
- de Moura, L. & Bjørner, N. (2008). Z3: An efficient SMT solver. *TACAS 2008*. [QF fragment decidability]
- Schulte, C. & Stuckey, P.J. (2008). Efficient constraint propagation engines. *TOPLAS*, 31(1). [Trailing]
- Biere, A. et al. (1999). Symbolic model checking without BDDs. *TACAS 1999*. [BMC completeness gap]
- Bradley, A.R. (2011). SAT-based model checking without unrolling. *VMCAI 2011*. [IC3]
- Minsky, M.L. (1961). Recursive unsolvability of Post's problem of tag and other topics in theory of Turing machines. *Annals of Mathematics*, 74(3). [Inhibitor arc undecidability]
