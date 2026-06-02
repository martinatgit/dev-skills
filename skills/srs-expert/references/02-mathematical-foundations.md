# Mathematical Foundations of Synchronous Reactive Systems

*Sources: theoretical_foundations.json (2026-04-07), reactive-system-insights.md §2*

---

## 1. Constructive Semantics (Berry, 2002)

**Primary reference:** Berry, G. (2002). *The Constructive Semantics of Pure Esterel*, Draft Version 3.

The constructive semantics resolves the causality problem in synchronous formalisms by replacing classical Boolean logic with constructive (intuitionistic) Boolean logic. Classical reasoning allows proofs by contradiction — assume a signal is absent, derive a contradiction, conclude it must be present. Constructive semantics forbids this: a signal is present only if there is a direct proof of emission; a signal is absent only if there is a proof that no execution path can emit it.

### 1.1 Three-Valued Domain

The domain for signal status is the three-element flat lattice:

```
D = {⊥, 0, 1}

Information ordering: ⊥ ≤ 0, ⊥ ≤ 1, but 0 and 1 are incomparable
```

- `⊥` (bottom): unknown/undetermined — no information yet
- `0`: signal is definitively ABSENT in the current instant
- `1`: signal is definitively PRESENT in the current instant

`0` and `1` are incomparable: they represent different determinate information, not more/less information.

**Product lattice:** For n signals, the domain is D^n ordered componentwise. This is a complete lattice of height n with 3^n elements. The bottom element is `(⊥, ⊥, ..., ⊥)` — total ignorance.

**Scott domain connection:** D^n with the information ordering is a finite Scott domain (directed-complete partial order with least element). Every monotone function on a finite lattice is Scott-continuous, which ensures the existence of least fixpoints.

### 1.2 Must/Can Analysis

The Must/Can analysis is the core mechanism of constructive causality. Two predicates propagate through the program:

| Predicate | Meaning | How it resolves |
|---|---|---|
| **Must(S)** | S must be emitted — every execution path emits S | S is PRESENT (value 1) |
| **Can(S)** | S can be emitted — at least one path emits S | If Can(S)=false: S is ABSENT (value 0) |

**Resolution rule:**
- Signal S is PRESENT if `Must(S) = true`
- Signal S is ABSENT if `Can(S) = false`
- If `Must(S) = false` and `Can(S) = true`: signal status remains `⊥`

**Propagation rules (selected):**
```
emit(S)            ⇒  Must(S) = true
S ∥ T              ⇒  Must(S∥T terminates) = Must(S terminates) ∧ Must(T terminates)
S ; T              ⇒  Must(T executes) iff Must(S terminates)
present(S) then p  ⇒  Must(p executes) iff Must(S present)
```

The propagation is **monotone**: once a fact is established, it is never retracted. This is the formal counterpart of Berry's "adding information can only add information to other signals."

### 1.3 Constructive Fixpoint (Kleene Iteration)

Define the signal resolution function F: D^n → D^n where F takes the current signal environment σ and returns an updated environment by applying Must/Can analysis.

**F is monotone:** If σ ≤ σ' (componentwise), then F(σ) ≤ F(σ').

**Kleene ascending chain:**
```
σ₀ = (⊥, ⊥, ..., ⊥)          -- all signals unknown
σₖ₊₁ = F(σₖ)                   -- apply Must/Can propagation
```

**Convergence:** Since D^n is finite and F is monotone, the chain stabilizes by Kleene's fixpoint theorem:
> The least fixpoint lfp(F) = sup{F^n(⊥) | n ≥ 0} is reached in **at most n steps** (n = number of signals), because each step resolves at least one signal from ⊥ to 0 or 1.

**Causality criterion:** A program is constructive iff for every input assignment, the least fixpoint σ* satisfies: for all signals S, σ*(S) ∈ {0, 1} (no ⊥ remains). If some signal remains ⊥ at the fixpoint, the program has a **causality error**.

### 1.4 Causality Errors

A causality error occurs when circular signal dependencies cannot be resolved:

```esterel
-- Causality error: circular dependency A → B → A
present A then emit B end;
present B then emit A end;
```

Neither A nor B can be determined first. The fixpoint contains ⊥ for both. The Esterel compiler detects this statically by running the constructive fixpoint and checking for remaining ⊥ values.

**Detection complexity:** Polynomial time — run Kleene iteration (≤ n steps, each step O(n)), check for ⊥ in result.

### 1.5 Electrical Equivalence

Berry proved the equivalence of three views:

1. **Constructive behavioral semantics** — Must/Can analysis on program text
2. **Constructive operational semantics** — small-step SOS rules with ternary values
3. **Electrical semantics** — circuit ternary simulation

**Main theorem:** An Esterel program is constructive iff its compiled circuit reaches electrical stabilization under ternary simulation in bounded time.

**Ternary simulation:** Circuit gates operate on {⊥, 0, 1} with short-circuit rules:
```
AND(⊥, 0) = 0    -- short-circuit: one input definitively 0
AND(⊥, 1) = ⊥    -- unknown: need other input
OR(⊥, 1)  = 1    -- short-circuit: one input definitively 1
OR(⊥, 0)  = ⊥    -- unknown: need other input
NOT(⊥)    = ⊥    -- cannot determine negation of unknown
```

The ternary simulation of the circuit corresponds exactly to the constructive fixpoint on D^n.

### 1.6 Schizophrenia (Signal Reincarnation) Problem

The schizophrenia problem arises when a loop body completes and restarts within the same logical instant:

```esterel
loop
  emit S;      -- S emitted in first traversal
  -- if this terminates instantly (no pause), loop restarts in same tick
  -- S is 'born again' -- what is its status in the second traversal?
end loop
```

When the loop body exits and re-enters in the same tick, a signal has a "schizophrenic" behavior — it was emitted in the first traversal (present) but has an undefined status in the fresh incarnation.

**Constructive resolution:** Each incarnation of a signal is treated as a separate logical signal. The number of reincarnations is statically bounded. The **Berry-Tardieu transformation** handles signal reincarnation with linear complexity in program size.

**Fundamental constraint:** Loop bodies cannot be instantaneous. Every loop iteration must contain at least one `pause` statement. This prevents unbounded reincarnation in a single instant.

*For implementation impact in aiqeung, see `07-pitfalls-risks.md §2`.*

---

## 2. Clock Calculus (Colaço & Pouzet, 2003)

**Primary reference:** Colaço, J.-L. & Pouzet, M. (2003). Clocks as First Class Abstract Types. *EMSOFT 2003*, Philadelphia.

The clock calculus treats clocks as types in Lustre-style synchronous dataflow. Clocks define exactly when a stream is active (present) or absent. Clock inference — analogous to ML type inference — assigns clock types to all expressions at compile time.

### 2.1 Clocks as Types

```
Clock type syntax:
  ck ::= base          -- base clock: active at every tick
       | ck on c       -- subclock: active when boolean stream c is true
       | α             -- clock variable (for polymorphism)
```

A stream `x : τ on ck` has value type τ and is present only when clock `ck` is active. Absence is encoded in the type — not a runtime sentinel.

**Base clock:** `base` ticks at every tick. A stream on the base clock has a value at every instant.

**Derived clocks:** `ck on c` ticks only at those instants of `ck` where boolean stream `c` is true. This creates a strictly slower clock.

**Clock type system analogy:** Just as a data type specifies WHAT values a stream can take, a clock type specifies WHEN the stream is present. The clock calculus is a second independent type system layered on top of the data type system.

### 2.2 The `when` Operator (Subsampling)

`when` projects a stream onto a slower clock:

```
Formal semantics:
  If x : τ on ck  and  c : bool on ck
  then (x when c) : τ on (ck on c)

Pointwise:
  (x when c)_t = x_t   when c_t = true
  (x when c)_t = absent when c_t = false
```

**Clock typing rule:** The result lives on the strictly slower subclock `(ck on c)`.

**Example:**
```lustre
x : int on base          -- x has a value every tick
c : bool on base         -- c is a condition every tick  
y = x when c             -- y : int on (base on c)
                         -- y is present only when c is true
```

### 2.3 The `merge` Operator (Oversampling / Reconstruction)

`merge` is the dual of `when` — it reconstitutes a stream from complementary subclocks:

```
Formal semantics:
  If c : bool on ck
  If x : τ on (ck on c)        -- x active when c is true
  If y : τ on (ck on not c)    -- y active when c is false
  then merge(c, x, y) : τ on ck

Pointwise:
  merge(c, x, y)_t = x_t   when c_t = true
  merge(c, x, y)_t = y_t   when c_t = false
```

**Complementarity requirement:** `x` and `y` must be on exactly complementary subclocks — together they partition every tick of `ck`. This ensures no tick is missed or duplicated.

**Why this matters:** `when` and `merge` together enable multi-rate computations within a single synchronous framework. A fast sensor stream can be subsampled for slow processing, and the processed stream can be reconstructed at the full rate.

### 2.4 Clock Inference Algorithm

Clock inference generates constraints from the program structure, then solves them via unification:

1. Assign a fresh clock variable α to each expression
2. For each operator, generate clock constraints:
   - `x when c`: constrain clock(x) = clock(c), result clock = clock(x) on c
   - `merge(c, x, y)`: constrain clock(x) = clock(c) on c, clock(y) = clock(c) on not(c)
   - `pre(x)`, `x -> y`: result clock = clock(x) = clock(y)
   - Arithmetic/logic: all operands on same clock
3. Solve constraints by unification (Hindley-Milner style)
4. Generalize unresolved clock variables → clock-polymorphic node signatures

**Well-clockedness:** A program is well-clocked if clock inference succeeds. Ill-clocked programs — attempting to combine streams on incompatible clocks — are rejected at compile time with a meaningful clock error.

**Clock polymorphism:** Nodes can be parameterized by clock, enabling reuse at different clock rates (analogous to ML parametric polymorphism).

### 2.5 Absence as a First-Class Compile-Time Guarantee

The key insight: **absence is not a runtime concept in a well-clocked Lustre program — it is a type-level guarantee**.

A stream `x : τ on (base on c)` is definitively absent at all instants where `c = false`. The compiler knows this statically. Consequences:

- **No runtime tagging needed:** The generated code does not need option types or presence flags for synchronous computations — the clock condition becomes an if-guard in the C output.
- **No runtime detection needed:** The compiler can statically verify that no equation references an absent stream without a clock guard.
- **Compositionality:** If `x` is on `(base on c)` and `y = x when d`, then `y` is on `(base on c on d)`, absent at all instants where `c = false OR d = false`. Absence patterns compose under clock composition.
- **Contrast with asynchronous:** In asynchronous systems, absence is indistinguishable from delay. A timeout is required, which is non-compositional and introduces non-determinism.

---

## 3. Formal Reasoning About Absence

### 3.1 Why the Synchronous Clock is Required

**Asynchronous systems cannot formally reason about absence:** In an asynchronous model, at any observation point, the absence of a signal is indistinguishable from a signal that has not yet arrived. Formally, in a partial-order model of asynchronous events, there is no maximal element within a "tick" to serve as a deadline. Absence would require a timeout — inherently non-compositional, introducing non-determinism.

**The synchronous clock provides deadlines:** The synchronous hypothesis defines a discrete sequence of global ticks. At each tick boundary, every signal is committed as present or absent — no third possibility at the semantic level. The signal environment is a **total function** from signals to {present, absent} at each tick.

**Formal statement:** In the synchronous model, time is a sequence of discrete instants T = {t₀, t₁, t₂, ...}. At each instant tᵢ, every signal S has a determinate status: S(tᵢ) ∈ {present(v), absent}. This is guaranteed by the synchronous hypothesis: computation within a tick is logically instantaneous.

### 3.2 Implications for Compliance and Monitoring

The formal decidability of absence enables:

1. **Compliance gap detection:** If evidence signal E is expected at tick T but absent, that is a definitive compliance gap — not a "maybe it will arrive later." No timeout heuristic is needed.

2. **Deadline monitoring:** After N ticks without signal S, the deadline has definitively expired. `pre(counting) and not S` at tick N is a rigorous statement.

3. **Safety property verification:** "Signal S is never present when signal T is absent" is a well-defined, checkable property expressible in Lustre and verifiable by Kind2.

### 3.3 Esterel Absence Constructs

Esterel provides first-class constructs for acting on absence:

- **`present S then p else q`** — branches on S's status; requires S to be determined before execution proceeds
- **`abort p when not S`** — preempts p if S is absent in the current instant (reactive to absence)
- **`S default E`** — valued signal: yields value of S when present, E when absent

These constructs are only well-defined because absence is a precisely determined status, not a guess.

---

## 4. Tagged Signal Model (Lee & Sangiovanni-Vincentelli, 1998)

**Primary reference:** Lee, E.A. & Sangiovanni-Vincentelli, A. (1998). A Framework for Comparing Models of Computation. *IEEE Trans. CAD*, 17(12):1217-1229.

The Tagged Signal Model (TSM) is a denotational meta-framework that unifies synchronous, dataflow, discrete-event, and continuous-time models within a single mathematical formalism.

### 4.1 Fundamental Definitions

**Event:** An event e ∈ T × V associates a **tag** t ∈ T with a **value** v ∈ V.

**Signal:** A signal s is a partial function from T to V (for each tag, at most one value). The set of all signals: S = {s ∈ P(T × V) | s is a partial function}.

**Process:** A process P ∈ P(S₁ × S₂ × ... × Sₙ) defines the set of all acceptable behaviors — tuples of signals that satisfy all constraints. A process is a relation, not a function: it can represent nondeterministic behavior.

**Composition:** Composition is set intersection of behaviors: P₁ ∥ P₂ = P₁ ∩ P₂. The composed behavior is the set of signal tuples satisfying all constraints simultaneously.

### 4.2 Models of Computation as Tag Structures

| Model of Computation | Tag set T | Ordering | Absence encoding |
|---|---|---|---|
| **Synchronous** | ℕ (tick numbers) | Total order | Undefined at tag t |
| **Lustre clocks** | ℕ restricted to subclock | Inherited total | Absent at skipped tags |
| **Dataflow (KPN)** | ℕ per channel (token index) | Per-channel total, no global sync | N/A (FIFOs) |
| **Discrete event** | ℝ⁺ | Total order | Undefined at t |
| **Superdense time** | ℕ × ℕ (tick, microstep) | Lexicographic | Undefined at tag |
| **Continuous time** | ℝ⁺ | Total order | Undefined on interval |

**Synchronous model in TSM:** All signals share the same tag set T = ℕ. Synchronous events share the same tag — all signals "tick" simultaneously. A signal absent at tick t is modeled as undefined at tag t (partial function has no mapping for t).

**Superdense time:** The aiqeung `Tag = { tick: number, microstep: number }` design directly implements TSM superdense time with lexicographic ordering. This enables causally ordered intra-tick events without violating the synchronous hypothesis — see `06-algorithms.md §4`.

### 4.3 CPO Structure and Fixpoint Foundation

The set of all signals S with a partially ordered tag set forms a CPO under the subset ordering: s₁ ≤ s₂ iff s₁ ⊆ s₂ (s₁ has fewer events than s₂). The bottom element is the empty signal.

**Relevance:** This CPO structure enables fixpoint semantics for recursive process definitions (feedback loops). For deterministic process semantics, the process function must be monotone with respect to the information ordering, ensuring least fixpoints exist (Tarski/Kleene).

### 4.4 Position of Synchronous Programming in the Design Space

The TSM shows that synchronous reactive programming is one point in a design space, with precise tradeoffs:

| Property | Synchronous | Dataflow (KPN) | Discrete Event |
|---|---|---|---|
| Determinism | Guaranteed by construction | Guaranteed (Kahn 1974) | Depends on model |
| Absence reasoning | Formal, compile-time | Not applicable | Requires timeouts |
| Compositionality | Yes (synchronous product) | Yes (Kahn composition) | Limited (scheduling) |
| Buffering required | None (bounded, ≤1 per channel per tick) | Unbounded FIFO | Event queue |
| Analyzability | Polynomial (clock check, fixpoint) | Undecidable in general | Complex |

---

## 5. Mealy/Moore Machine Compilation

Synchronous reactive programs compile to finite state machines — specifically Mealy machines. This connects the fixpoint semantics to concrete executable code.

### 5.1 Mealy Machine Model

A Mealy machine M = (Q, Σ, Γ, δ, λ, q₀):
- Q: finite state set (encodes all `pause`/`pre` state)
- Σ: input alphabet (all input signal combinations)
- Γ: output alphabet (all output signal combinations)
- δ: Q × Σ → Q: transition function (next state)
- λ: Q × Σ → Γ: output function (emissions this tick)
- q₀: initial state

**Synchronous fit:** Outputs at tick t depend on both the accumulated state (from ticks 0..t-1) and the current input (tick t). The tick reaction IS the evaluation of δ and λ:
```
(next_state, outputs) = F(current_state, inputs)
```
where F is the constructive fixpoint. The within-tick fixpoint becomes the combinational logic; `pause`/`pre` state becomes the register state.

### 5.2 State Explosion Problem

When composing n concurrent modules each with kᵢ states, the product FSM has k₁ × k₂ × ... × kₙ states. Exponential blowup is the **state explosion problem**.

Example: 20 parallel threads with 2 states each → 2²⁰ ≈ 1 million states.

**Mitigations used in practice:**
- **BDD-based symbolic representation:** Represent the transition relation symbolically (not as enumerated states). BDD compression is often exponential in practice.
- **Circuit-based compilation (Esterel v5+):** Circuit size is O(n) in program size, avoiding explicit state enumeration.
- **Partial evaluation / unreachable state pruning.**
- **Compositional verification:** Verify modules independently (assume-guarantee), avoiding product construction.

### 5.3 Connection to the Fixpoint

The fixpoint computation within each tick defines the combinational logic of the compiled circuit. The transition function δ IS the constructive fixpoint computation: given state and inputs, run Kleene iteration to determine outputs and next state. This connection ensures:

- Constructive programs → constructive circuits (possibly cyclic, but stabilizing under ternary simulation)
- Circuit-based compilation avoids state enumeration while preserving constructive semantics

---

## 6. Formal Properties Summary

| Property | Statement | Formal basis |
|---|---|---|
| **Determinism** | Same inputs → same outputs at every tick | Synchronous hypothesis + unique least fixpoint |
| **Causality** | No circular signal deps within a tick | Constructive fixpoint contains no ⊥ |
| **Absence decidability** | Absence at a tick is a formal fact, not a guess | Total signal environment from sync. hypothesis |
| **Clock well-formedness** | All streams have compatible activation patterns | Clock inference succeeds (unification) |
| **Absence as type guarantee** | x on (base on c) is definitively absent when c=false | Clock calculus, compile-time |
| **Convergence bound** | Kleene iteration reaches fixpoint in ≤ n steps | Monotone function on finite lattice |
| **Causality detection** | Causality error detectable in polynomial time | ≤ n iterations, each O(n) |
| **Reactivity** | No deadlocks by construction | Synchronous model, always reacts |
| **Endochrony non-compositionality** | Parallel composition of two endochronous programs is NOT guaranteed endochronous | Benveniste et al. 2003 |
| **Isochrony** | Flow-preserving under desynchronization — the compositional alternative to endochrony | Benveniste et al. 2003 |

---

## Bibliography

- Berry, G. (2002). *The Constructive Semantics of Pure Esterel*, Draft Version 3.
- Berry, G. & Gonthier, G. (1992). The Esterel synchronous programming language. *Science of Computer Programming*, 19(2):87-152.
- Colaço, J.-L. & Pouzet, M. (2003). Clocks as First Class Abstract Types. *EMSOFT 2003*, Philadelphia.
- Lee, E.A. & Sangiovanni-Vincentelli, A. (1998). A Framework for Comparing Models of Computation. *IEEE Trans. CAD*, 17(12):1217-1229.
- Benveniste, A. et al. (2003). The Synchronous Languages 12 Years Later. *Proc. IEEE*, 91(1):64-83.
- Mendler, M., Shyamasundar, R.K., & Staber, S. (2015). A denotational fixed-point semantics for constructive scheduling of synchronous programs. *Formal Methods in System Design*, 48(1-2).
- Kahn, G. (1974). The semantics of a simple language for parallel programming. *IFIP Congress 1974*.
