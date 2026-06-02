# Algorithms for Synchronous Reactive Systems

*Sources: theoretical_foundations.json (2026-04-07), reactive-system-insights.md §2*

---

## 1. Constructive Fixpoint Algorithm (Berry, 2002)

**Purpose:** Determine the status (present/absent) of all signals in a single synchronous tick. Detects causality errors.

### 1.1 Inputs and Outputs

**Input:** A synchronous program P with n signals S = {S₁, ..., Sₙ} and a set of input signal values (from the environment).

**Output:** Either:
- A fully determined environment σ* ∈ {0, 1}^n — all signals resolved (program is constructive)
- A partial environment with some σ*(Sᵢ) = ⊥ — causality error (signal Sᵢ undetermined)

### 1.2 Algorithm

```
ConstructiveFixpoint(program P, input values I):

  1. Initialize:
     σ ← (⊥, ⊥, ..., ⊥)   -- all signals unknown
     for each input signal Sᵢ ∈ I:
       σ(Sᵢ) ← I(Sᵢ)        -- set known input values

  2. Repeat until stable:
     σ' ← F_P(σ)             -- apply Must/Can propagation
     if σ' = σ then break    -- fixpoint reached
     σ ← σ'

  3. Check result:
     if ∀i. σ(Sᵢ) ≠ ⊥ then
       return σ              -- constructive: fully determined
     else
       report CausalityError({Sᵢ | σ(Sᵢ) = ⊥})
```

### 1.3 The Signal Resolution Function F

F: D^n → D^n is defined by Must/Can analysis over the program text:

```
For each signal S in the program:

  Must(S) = true   iff   every execution path through the current tick emits S

  Can(S) = false   iff   no execution path through the current tick emits S

  F(σ)(S) = σ(S) ∨ resolution_update(S, σ) where:

    resolution_update(S, σ) =
      | 1  if Must_P(S, σ) = true      -- S must be present
      | 0  if Can_P(S, σ) = false      -- S cannot be present
      | ⊥  otherwise                   -- still unknown
```

**Must propagation rules (selected):**
```
emit(S)                   → Must(S) = true
p ∥ q:   Must(S via p) or Must(S via q)   → Must(S)
p ; q:   Must(q executes) iff Must(p terminates)
present(S) then p:        Must(p) iff σ(S) = 1
present(S) else q:        Must(q) iff σ(S) = 0
```

**Can propagation rules (selected):**
```
emit(S) reachable:        Can(S) = true
no path emits S:          Can(S) = false
present(S) then p:        Can(emit via p) requires Can(S=1)
```

### 1.4 Convergence Guarantee

**Theorem (Kleene):** The algorithm terminates in at most n iterations, where n is the number of signals.

**Proof sketch:**
1. D^n = {⊥, 0, 1}^n is a finite lattice with 3^n elements
2. F is monotone (information ordering): σ ≤ σ' implies F(σ) ≤ F(σ')
3. The Kleene ascending chain σ₀ ≤ σ₁ ≤ ... is strictly increasing until fixpoint
4. Each step resolves at least one signal from ⊥ to 0 or 1 (in the worst case)
5. With n signals, at most n steps before all are resolved

**In practice:** Well-designed programs converge in 2-3 iterations. The n-step worst case requires a long chain of signal dependencies.

### 1.5 Causality Error Detection

A program has a causality error iff the fixpoint contains ⊥:
```
σ*(Sᵢ) = ⊥ for some i
```

**Example causality error:**
```esterel
-- Circular dependency: A depends on B, B depends on A
present A then emit B;
present B then emit A;
-- F cannot resolve either A or B without knowing the other
-- Fixpoint: σ*(A) = ⊥, σ*(B) = ⊥ → causality error
```

**Example correct (Berry's "beneficial" cycle):**
```esterel
-- This IS constructive despite apparent cycle:
present A then emit B;
present B else emit A;
-- F(⊥,⊥): Must(A) = false, Can(A) = false → A = 0
-- F(0,⊥): Must(B) = false, Can(B) = false (present A with A=0 takes else branch) → B = 0
-- Fixpoint: (A=0, B=0) — constructive
```

---

## 2. Must/Can Analysis — Detailed Propagation

Must/Can analysis is the key engine of the constructive fixpoint. This section provides the complete structural rules.

### 2.1 Sequential Composition (p ; q)

```
Must-terminates(p;q, σ) = Must-terminates(p, σ) AND Must-terminates(q, σ_after_p)
Can-terminates(p;q, σ)  = Can-terminates(p, σ) AND Can-terminates(q, σ_after_p)

Must-emits(S, p;q, σ) =
  Must-emits(S, p, σ)
  OR (Must-terminates(p, σ) AND Must-emits(S, q, σ_after_p))

Can-emits(S, p;q, σ) =
  Can-emits(S, p, σ)
  OR (Can-terminates(p, σ) AND Can-emits(S, q, σ_after_p))
```

### 2.2 Parallel Composition (p ∥ q)

```
Must-emits(S, p∥q, σ) = Must-emits(S, p, σ) OR Must-emits(S, q, σ)
Can-emits(S, p∥q, σ)  = Can-emits(S, p, σ) OR Can-emits(S, q, σ)

-- Both branches contribute to Must; either branch suffices for Can
-- Joint fixpoint: σ_merged includes emissions from both branches
```

### 2.3 Conditional (present S then p else q)

```
If σ(S) = 1 (present):
  Must-emits(X, present S then p else q) = Must-emits(X, p, σ)
  Can-emits(X, present S then p else q)  = Can-emits(X, p, σ)

If σ(S) = 0 (absent):
  Must-emits(X, present S then p else q) = Must-emits(X, q, σ)
  Can-emits(X, present S then p else q)  = Can-emits(X, q, σ)

If σ(S) = ⊥ (unknown):
  Must-emits(X, ...) = Must-emits(X, p, σ) AND Must-emits(X, q, σ)
  Can-emits(X, ...)  = Can-emits(X, p, σ) OR Can-emits(X, q, σ)

-- Key: if S unknown, both branches might execute — conservative approximation
```

### 2.4 Completion Codes

Esterel uses completion codes to encode the outcome of a reaction:
- `k = 0`: statement terminated (no `pause` in the path)
- `k = 1`: paused (hit a `pause` statement, will resume next tick)
- `k ≥ 2`: exited at trap level `k-2`

Must/Can propagation tracks these codes alongside signal emissions, enabling precise analysis of sequencing and preemption.

---

## 3. Clock Inference Algorithm (Colaço & Pouzet, 2003)

**Purpose:** Assign clock types to all stream expressions in a Lustre program. Detect clock mismatches (temporal errors). Generate the static schedule.

### 3.1 Algorithm

```
ClockInference(Lustre program P):

  1. Assign a fresh clock variable αᵢ to each stream expression eᵢ

  2. For each operator occurrence, generate clock constraints:
     - e₁ when c:     clock(e₁) = clock(c) = α;   result clock = α on c
     - merge(c,e₁,e₂): clock(e₁) = α on c;         clock(e₂) = α on ¬c;   result = α
     - pre(e₁):       clock(result) = clock(e₁)
     - e₁ -> e₂:      clock(e₁) = clock(e₂) = clock(result)
     - f(e₁,...,eₙ):  match parameter clocks of f's signature
     - if c then e₁ else e₂:  clock(c) = clock(e₁) = clock(e₂) = clock(result)

  3. Solve constraints by unification (Hindley-Milner style):
     - Substitute clock variables for clock expressions
     - Detect occurs-check failures (cyclic clock dependencies)
     - Detect incompatible clock unifications (clock mismatch = type error)

  4. Generalize unresolved variables → clock-polymorphic node signature

  5. Build the activation schedule:
     - Each expression's clock condition becomes an if-guard in generated code
     - Absent streams (clock condition false) produce no code for that tick
```

### 3.2 Clock Unification Examples

```lustre
-- Simple subsampling: well-clocked
x : int on base
c : bool on base
y = x when c       -- y : int on (base on c) ✓

-- merge reconstruction: well-clocked
y = x when c       -- y : int on (base on c)
z = x when not c   -- z : int on (base on not c)
w = merge(c, y, z) -- w : int on base ✓ (complementary subclocks)

-- Clock mismatch: ill-clocked (REJECTED)
x : int on (base on c1)
y : int on (base on c2)
bad = x + y        -- clock(x) ≠ clock(y) → unification fails → compile error
```

### 3.3 Well-Clockedness as Well-Typedness

The key insight from Colaço & Pouzet (2003):

> Clock inference uses the SAME algorithms as ML type inference (Hindley-Milner). Well-clockedness is the temporal analog of well-typedness. Clock polymorphism is the analog of parametric polymorphism.

This means:
- Clock inference is decidable and efficient (same complexity as type inference)
- Error messages are precise: clock mismatch = "these streams are not simultaneously active"
- Clock polymorphism enables reuse at different rates (same node used on `base`, `base on fast`, etc.)

### 3.4 Static Schedule Generation

After clock inference:

```
For each stream equation `x = expr`:
  guard = activation_condition(clock(x))

  Generated code:
    if (guard) {
      x_current = evaluate(expr, current_values);
    }
    // else: x is absent at this tick — no computation needed
```

The topological sort of the dependency DAG gives the execution order. Each `pre(e)` breaks a potential cycle: `pre(e)` at tick N reads the value of `e` from tick N-1, stored in a register.

---

## 4. Topological Sort for Node Scheduling

In aiqeung, `inferClocks` in clock.ts computes a topological sort of the `SyncNode` dependency graph.

### 4.1 Algorithm

```
NodeSchedule(nodes: SyncNode[]):

  1. Build signal producer map: signal name → node name
     (from node.outputs and emit_signal equations)

  2. Build dependency graph:
     For each node N:
       For each input stream I of N:
         If producer(I) = M (some other node):
           Add edge M → N (N depends on M's output)

  3. Topological sort of dependency graph:
     - Kahn's algorithm (BFS-based):
       enqueue nodes with no incoming edges
       repeat: dequeue N, add to order, remove edges from N
     - If queue empties before all nodes processed: CYCLE → inter_node_cycle error

  4. Return nodeOrder (the valid evaluation sequence)
```

**Connection to constructive fixpoint:** The `inter_node_cycle` error is the node-level analog of the signal-level causality error. A cycle in the node dependency graph means two nodes depend on each other's current-tick outputs — the constructive fixpoint on signals cannot resolve this.

### 4.2 aiqeung Clock Errors (types.ts)

```typescript
// From src/aiqeung-core/reactive/types.ts
export type ClockError =
  | { kind: "clock_mismatch";   // two streams on incompatible clocks
      node: string; stream: string; expected: ClockType; actual: ClockType }
  | { kind: "unguarded_pre";    // pre(x) without initialization → undefined at tick 0
      node: string; stream: string }
  | { kind: "inter_node_cycle"; // circular node dependency = aiqeung causality error
      nodes: readonly string[] }
  | { kind: "duplicate_fire";   // two nodes fire the same net = conflict
      node: string; net: string }
```

---

## 5. Superdense Time — Tag Computation

**Purpose:** Order causally dependent events within a single synchronous tick without violating the synchronous hypothesis.

### 5.1 Tag Definition

```typescript
// Design recommendation (DR-2)
interface Tag {
  readonly tick: number;      // global tick counter (advances once per step())
  readonly microstep: number; // intra-tick ordering (0, 1, 2, ...)
}

// Ordering: lexicographic
// (t1, m1) < (t2, m2)  iff  t1 < t2  OR  (t1 = t2 AND m1 < m2)
```

**Formal basis:** Tagged Signal Model (Lee & Sangiovanni-Vincentelli 1998): T = ℕ × ℕ with lexicographic ordering. Superdense time extends discrete time by adding a second dimension for instantaneous causality.

### 5.2 Tag Assignment Rules

```
Rule 1: Normal (tick) advance
  Before step(): tag = (N, 0) for all signals
  After step():  tag = (N+1, 0) for all signals

Rule 2: Sequential bind — microstep advance
  bind(fire(net, T1), _ => fire(net, T2)):
    T1 fires at (N, 0), produces marking M1
    T2 fires at (N, 1), reads M1, produces marking M2
    Both within the same tick N

Rule 3: Parallel par — no microstep advance
  par(fire(net1, T1), fire(net2, T2)):
    T1 fires at (N, 0), reads snapshot markings
    T2 fires at (N, 0), reads SAME snapshot markings
    Both at same tag; neither sees the other's result
```

### 5.3 When to Use Microsteps

| Operation | Use microsteps? | Reason |
|---|---|---|
| Sequential `bind` chain firing same net | YES | T2 needs to see T1's marking update |
| Parallel `par` with different nets | NO | Independent; snapshot sufficient |
| Parallel `par` with same net | Design smell; use `bind` instead | Conflicting writes to same net |
| `until` body per tick | NO | Each iteration is a full tick; body sees tick-N snapshot |

**Design rule (DR-4):** Use microstep-based visibility for sequential `bind` chains. Use frozen snapshot for `par` branches. This follows the Lingua Franca principle: "A triggered reaction shall not execute before all observable events with the same tag that might affect it have been produced."

### 5.4 Microstep vs. Tick: What Changes

| Property | Tick advance (N → N+1) | Microstep advance (N,m → N,m+1) |
|---|---|---|
| Signal values committed | YES (current ← pending) | Partial (only in sequential chain) |
| DB assertions committed | YES | Only for the preceding `bind` step |
| Subscribers notified | YES | NO |
| `pre(x)` updated | YES | NO (`pre` still reads tick N-1) |
| Tick counter advanced | YES | NO |

---

## 6. Absence Algorithm — Closed-World SLD

In aiqeung, absence is determined by the SLD resolver under the closed-world assumption (CWA):

```
AbsenceAlgorithm(query: Term, db: ClauseDB):

  1. Run SLD resolution: findSolutions(query, db)

  2. If solutions = []:
     → query definitively fails
     → signal absent (CWA: not provable = false)

  3. If solutions ≠ []:
     → query succeeds
     → signal present
```

**Connection to constructive semantics:** SLD's CWA is the logic programming analog of the synchronous closed-world assumption. In Esterel, "Can(S) = false" is derived by showing no path emits S. In SLD, "query fails" is derived by showing no clause resolves the query. Both are constructive negation.

**`until` termination semantics:**
```
until(body, cond):
  while true:
    execute body
    if AbsenceAlgorithm(cond, db) = present:
      return              -- condition met
    else:
      advance tick        -- condition absent = definitively failed = continue
```

The `else` branch is not "maybe later" — it is a definitive "cond is not provable from the current DB."

---

## 7. Complexity Summary

| Algorithm | Complexity | Notes |
|---|---|---|
| Constructive fixpoint | O(n²) | n = number of signals; n iterations × O(n) per step |
| Must/Can analysis (one step) | O(n) | Linear scan of program structure |
| Causality error detection | O(n²) | Included in fixpoint algorithm |
| Clock inference | O(m · α(m)) | m = expressions; α = inverse Ackermann (near-linear) |
| Topological sort (node schedule) | O(V + E) | Standard Kahn's algorithm |
| Ternary circuit simulation | O(n · g) | n = signals; g = gates (circuit-based compilation only) |
| SLD resolution (one query) | O(b^d) in worst case | b = branching factor; d = depth; bounded in practice |

All static analysis algorithms (constructive fixpoint, clock inference, topological sort) run at compile time, not at tick time. Per-tick runtime cost is O(number of nodes × average equation count) — bounded by program size.

---

## Bibliography

- Berry, G. (2002). *The Constructive Semantics of Pure Esterel*, Draft Version 3.
- Colaço, J.-L. & Pouzet, M. (2003). Clocks as First Class Abstract Types. *EMSOFT 2003*, Philadelphia.
- Lee, E.A. & Sangiovanni-Vincentelli, A. (1998). A Framework for Comparing Models of Computation. *IEEE Trans. CAD*, 17(12).
- Lohstroh, M. et al. (2021). Toward a Lingua Franca for Deterministic Concurrent Systems. *ACM TECS*, 20(4).
- Kahn, G. (1974). The semantics of a simple language for parallel programming. *IFIP Congress 1974*.
- Tarski, A. (1955). A lattice-theoretical fixpoint theorem and its applications. *Pacific J. Math.*, 5(2).
