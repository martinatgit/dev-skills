# Synchronous Reactive Systems — Foundational Languages

*Source: foundational_languages.json (2026-04-07), reactive-system-insights.md §1*

---

## 1. The Synchronous Hypothesis

The synchronous hypothesis (Berry & Gonthier 1992): **a reaction is instantaneous
relative to the environment**. In each logical instant (tick), the system:

1. **Samples all inputs** — reads the current values of all input signals
2. **Computes** — evaluates all equations/statements in the program
3. **Emits all outputs** — produces output signal values

No time passes during computation. The system observes input, computes, and responds
before the next input arrives. This is a **modelling abstraction**, not a physical
claim. It is valid when the worst-case execution time (WCET) of one reaction is
negligible compared to the minimum inter-arrival time of external events.

**Consequence:** the tick model defines a discrete sequence of deadlines. At each
tick boundary, every signal is committed as present or absent — not "maybe later."
This makes absence a **decidable, compositional property**.

---

## 2. Esterel

**Authors:** Gérard Berry and Georges Gonthier (1983–2000+)  
**Institution:** INRIA Sophia-Antipolis / École des Mines de Paris  
**Style:** Imperative synchronous reactive language

### 2.1 Formal Model

An Esterel program denotes a deterministic reactive finite-state machine. The semantic
domain is a set of reactions: given input signals at each instant, the program computes
output signals and transitions to a new internal state.

**Reaction relation:**
```
(p, E) → (p', E_out, k)
```
where:
- `p` = current program (set of paused program counters for parallel threads)
- `E` = signal environment: `S → {present, absent}` for all signal names
- `p'` = residual program (state after this tick)
- `E_out` = set of signals emitted this tick
- `k` = completion code: `0` = terminated, `1` = paused (resumes next tick), `k ≥ 2` = exited trap level `k−2`

**Signal coherence law:** A signal is present iff it is emitted by at least one thread
or is an input signal in E.

**Parallel completion:** `(p ∥ q)` has completion code `max(k_p, k_q)` and merged
emitted signal sets from both branches.

### 2.2 Key Constructs

| Construct | Semantics |
|---|---|
| `emit S` | Makes signal S present in the current instant. Terminates immediately (k=0). |
| `present S then p else q` | Branches on S's status. If S is ⊥ (not yet resolved), result is ⊥. |
| `pause` | Suspends until the next instant (yields k=1). Resumes at next tick. |
| `p ; q` | Sequential: execute q only if p terminates (k=0). |
| `p \|\| q` | Concurrent: both p and q execute in the same instant. Shared signal environment. |
| `signal S in p end` | Declares a local signal with scope p. S resolved by fixpoint within the instant. |
| `trap T in p end` | Structured exception handling. If p exits with matching trap, k becomes 0. |
| `exit T` | Raises trap T (completion code ≥ 2). Used for preemptive termination. |
| `suspend p when S` | If S is present, p does not execute this instant. |
| `loop p end` | Restarts p each time it terminates. **Body must not be instantaneous** (must contain `pause`). |
| `await S` | Suspends until the next instant where S is present. Sugar over `pause; present S ...`. |
| `emit S(expr)` | Valued signal emission. Last writer wins within an instant. |

### 2.3 Concurrency Model

Synchronous parallelism: `p ∥ q` runs both p and q in the same instant. Communication
is by **broadcast**: if any thread emits S, all threads immediately see S as present.
No race conditions — signal coherence is resolved by fixpoint within the instant.
Deterministic by construction.

### 2.4 Compilation

**Automata-based (v1–v3):** Each state = set of paused program counters. Transitions
labeled with input signal sets. Fast (one table lookup per tick) but **exponential** in
parallel thread count. State explosion made this impractical for large programs.

**Circuit-based (v5+):** Each signal becomes a wire; control flow encoded as boolean
gates. Circuit size is **O(n) in program size**. Acyclic under constructive semantics
(ternary simulation proves acyclicity). Compiles to C or VHDL. Enabled industrial
scale (Dassault avionics, STMicroelectronics).

**Sequential C output:** Both paths produce a function called once per tick:
read inputs → evaluate circuit/automaton → write outputs → update state registers.
Deterministic, bounded time, bounded memory — suitable for embedded/safety-critical.

### 2.5 Limitations

- **Mono-clock:** all threads share one global clock; no native multi-rate support
- **Fixed topology:** signal names and connections are static; no dynamic process creation
- **Bounded state:** programs compile to finite automata; no unbounded data structures
- **Schizophrenia problem:** instantaneous reincarnation of local signals in loops
  requires careful handling (see `07-pitfalls-risks.md §2`)
- **No true asynchrony:** cannot model components that run at truly independent speeds

---

## 3. Lustre

**Authors:** Nicolas Halbwachs, Paul Caspi, Pascal Raymond, Daniel Pilaud (1984–present)  
**Institution:** Verimag, Grenoble (IMAG/CNRS)  
**Style:** Declarative dataflow synchronous language

### 3.1 Dataflow Model: Streams and Nodes

Lustre programs are systems of equations over **infinite streams**. Each variable `x`
denotes a stream `(x₀, x₁, x₂, ...)` of values indexed by a logical clock. A Lustre
**node** is a stream transformer: it takes input streams and produces output streams
via a set of mutually recursive stream equations.

```lustre
node counter(reset: bool) returns (n: int);
let
  n = (0 -> pre(n) + 1) * (if reset then 0 else 1);
tel
-- Counts ticks. Resets to 0 when reset is true.
```

Key insight: programs are **declarative** — equations define relationships, the
compiler determines a valid evaluation order. Conceptually close to temporal logic:
Lustre expressions can be read as past-time LTL formulas.

### 3.2 Core Operators

| Operator | Formal semantics | Meaning |
|---|---|---|
| `pre(x)` | `(pre x)₀ = nil`, `(pre x)ₙ = xₙ₋₁` for n>0 | Previous value of stream x (unit delay) |
| `x -> y` | `(x → y)₀ = x₀`, `(x → y)ₙ = yₙ` for n>0 | Initialization: first value of x, then all of y |
| `x when c` | Defined only at instants where `cₙ = true` | Subsampling: stream x on clock c |
| `merge(c, x, y)` | `(merge c x y)ₙ = xₙ` if `cₙ=true`, else `yₙ` | Reconstruct from complementary substreams |
| `current(x)` | Latest value of x held until next tick where x is defined | Sample-and-hold for subsampled streams |
| `if c then x else y` | Pointwise conditional (same clock as c) | Synchronous conditional |

**Causality requirement:** No instantaneous circular dependency is allowed. If `x`
depends on `y` at the current tick (without `pre`), and `y` depends on `x` at the
current tick, the program is rejected. `pre` breaks the cycle by referring to the
previous tick. This is simpler than Esterel's three-valued fixpoint: Lustre uses a
**DAG check** instead.

**Kahn connection:** Lustre nodes are Kahn processes restricted to synchronous,
finite-memory execution. Kahn's theorem guarantees that continuous functions on stream
domains have least fixpoints. Lustre's restrictions ensure these fixpoints are
computable with bounded memory (see §5).

### 3.3 Clock Calculus

Clocks are types. Every stream expression has an associated clock — a boolean stream
that determines when the expression is active.

```
base                    -- base clock: always true
x when c                -- clock is (base when c): active when c is true
merge(c, x, y)          -- clock is base: reconstitutes to parent clock
```

**Clock rules:**
- `when`: if `x` is on clock `α` and `c` is boolean on clock `α`, then `(x when c)`
  is on clock `(α when c)` — a derived slower clock
- `merge`: if `x` is on clock `(α when c)` and `y` is on clock `(α when ¬c)`,
  then `merge(c, x, y)` is on clock `α` — reconstruction to parent clock
- `pre`, `->`: preserve the clock of their argument
- Arithmetic/logic: operands must be on the same clock
- Node application: parameter clocks must match

**Clock inference:** The compiler infers clocks for all expressions and checks
consistency. Clock errors indicate temporal mismatches — operations on streams not
simultaneously active. Clock types form a tree rooted at the base clock.

**Clock polymorphism:** Lustre v6 / SCADE support parameterizing nodes by clock,
enabling reuse at different clock rates. Analogous to ML parametric polymorphism.

### 3.4 Compilation

1. Parse and clock-type-check
2. Build intra-tick dependency graph (edges for current-tick dependencies, not through `pre`)
3. **Check acyclicity** — reject programs with instantaneous circular dependencies
4. Topologically sort equations
5. Generate sequential C code: one `step()` function per tick

Memory is bounded and statically determinable: one cell per `pre(x)` to store
the previous value. No dynamic allocation.

### 3.5 Industrial Deployment: SCADE and DO-178C

**SCADE Suite** (ANSYS/Esterel Technologies): Industrial tool based on Lustre.

- Qualified at **DO-178C TQL-1 (Level A)** — the highest assurance level for airborne
  software. Generated C code can be used in safety-critical avionics without additional
  verification of the code generator.
- **EN 50128 SIL 4** qualification for railway applications.
- Used in: **Airbus A380/A350 flight control** software, Dassault Falcon, nuclear power
  plant protection systems, railway signalling (Alstom, Thales).

**Astree** (Cousot et al., ENS): Abstract interpretation analyzer proved **zero runtime
errors** in the Airbus A340 flight control software (132,000 lines of C generated from
SCADE) with **zero false alarms**. This is the benchmark result for formal verification
of synchronous code.

---

## 4. Signal

**Authors:** Paul Le Guernic, Thierry Gautier (1986+)  
**Institution:** INRIA Rennes  
**Style:** Relational/polychronous synchronous language

### 4.1 Polychronous / Multi-Clock Model

Unlike Esterel and Lustre which assume a **single global clock**, Signal allows
**multiple clocks**. Processes are sets of equations over signals that may tick at
different rates. Two signals may be in different clock domains — one ticking every
millisecond, another every second.

This is the **polychronous** model: programs are sets of clock relations that constrain
when signals are active, without requiring a common base rate.

### 4.2 Constraint-Based Synchronization

Signal processes communicate by **sharing signals**. When two processes share a signal,
the Signal compiler checks that the clock constraints are consistent. If two processes
produce values for the same signal at different rates, the compiler detects the
inconsistency and rejects the program.

Key operators:
- `x := y` — signal assignment (y feeds into x at the same clock)
- `x default y` — x when x is active, y otherwise (clock merging)
- `when c` — subsampling on boolean clock c (same as Lustre)
- `x ^+ y` — clock union: signal active when either x or y is active

### 4.3 GALS Architectures

Signal's multi-clock model enables **GALS (Globally Asynchronous, Locally Synchronous)**
architectures: each component is synchronous internally (locally synchronous), but
components communicate asynchronously (globally asynchronous). Signal can model and
verify the interfaces between synchronous components running at independent rates.

**Comparison to Lustre:** Signal is more expressive for multi-rate systems but less
analyzable due to the multi-clock complexity. Lustre's single base clock with subsampling
via `when` is a restricted but more tractable multi-rate model.

**Tool: Sigali** — model checker for Signal programs. Performs controller synthesis from
safety specifications (precursor to Heptagon/BZR).

---

## 5. Kahn Process Networks

**Author:** Gilles Kahn (1974)  
**Key result:** Deterministic dataflow semantics

### 5.1 Deterministic Dataflow and Scott Domains

A **Kahn Process Network** (KPN) is a network of sequential processes communicating
via **unbounded FIFO channels**. Each process is a **continuous function** on streams
in the Scott domain-theoretic sense (preserves directed limits). Kahn's theorem:

> A KPN is **deterministic** (same inputs → same outputs) if and only if each process
> is a continuous function on streams, and channels are single-writer.

The determinism follows because continuous functions on Scott domains have unique
least fixpoints (Tarski/Kleene theorem). No matter how processes are scheduled,
the produced streams are identical.

### 5.2 Relationship to Lustre

Lustre can be understood as **finite-memory Kahn networks with synchronous scheduling**:

| KPN | Lustre |
|---|---|
| Unbounded FIFO channels | Bounded (at most 1 value per tick) — synchronous clock eliminates buffering |
| Sequential processes | Equations evaluated in topological order |
| Non-deterministic scheduling | Synchronous: all processes advance in lockstep |
| Continuous functions on streams | Stream equations with `pre` for state |

The synchronous hypothesis eliminates the need for unbounded buffers: each tick,
every channel carries exactly one value (or is absent via `when`). This makes
Lustre an efficient, implementable subset of KPN theory with static scheduling.

---

## 6. Modern Extensions

### 6.1 Lingua Franca (Lohstroh, Lee et al., 2019–2024)

A polyglot coordination language bridging synchronous and asynchronous worlds.
The **reactor model** uses **logical time tags** `(timestamp, microstep)` for
deterministic concurrency. Reactors communicate via ports with logical connections.
The runtime ensures reactions execute in tag order.

**Relevance to aiqeung:** The `Tag = { tick: number, microstep: number }` design
for Layer 3 superdense time is directly informed by Lingua Franca. The port-based
communication model aligns with HCPN port concepts.

### 6.2 ReactiveML (Mandel & Pouzet, 2005)

Extension of OCaml with Esterel-style reactive constructs: `process`, `signal`,
`emit`, `await`, `∥`. Demonstrates that synchronous reactive constructs compose
well with higher-order functions, algebraic data types, and pattern matching.

**Relevance to aiqeung:** Shows the synchronous model works within a general-purpose
host language. The `ReactiveExpr` free monad in Layer 3 is the TypeScript analog.

### 6.3 Heptagon/BZR (Delaval, Rutten, 2013)

Lustre dialect with behavioral contracts enabling **discrete controller synthesis**.
Given a plant model (synchronous program) and a contract (safety property), the
Sigali tool automatically synthesizes a controller ensuring the property holds.

**Relevance to aiqeung:** Contract-based approach aligns with Layer 2.5 `NetContract`.

### 6.4 Zelus (Bourke & Pouzet, 2013)

Hybrid synchronous language combining Lustre-style discrete computation with
continuous ODE-based dynamics. The `->` operator models instantaneous transitions
in a hybrid system.

---

## 7. Language Comparison

| Property | Esterel | Lustre | Signal |
|---|---|---|---|
| Style | Imperative control flow | Declarative dataflow | Relational / constraint |
| Clock model | Mono-clock (one global clock) | Mono + static subclocks | Polychronous (multi-rate) |
| Concurrency | Synchronous `∥` (shared signals, broadcast) | Implicit (parallel equations) | Constraint-based |
| Primary domain | Control-dominated (protocols, mode logic) | Data-dominated (signal processing, monitoring) | Multi-rate, GALS |
| Absence | Three-valued fixpoint (constructive) | DAG check (acyclicity) | Clock constraint analysis |
| Compiles to | Automata or circuits → C / hardware | Scheduled equations → C | Signals compiler → C |
| Verification tool | EC (Esterel compiler), constructive check | Lesar, Kind2 | Sigali |
| Industrial variant | N/A | SCADE (DO-178C Level A) | N/A |
| Aiqeung analog | `race`, `emit`, `present`, `suspend` | `ReactiveExpr` equations, stream nodes | Multi-rate extensions (future) |

---

## Bibliography

- Berry, G. & Gonthier, G. (1992). The Esterel synchronous programming language. *Science of Computer Programming*, 19(2):87-152.
- Berry, G. (2002). *The Constructive Semantics of Pure Esterel*, Draft Version 3.
- Halbwachs, N., Caspi, P., Raymond, P., Pilaud, D. (1991). The synchronous data flow programming language LUSTRE. *Proc. IEEE*, 79(9):1305-1320.
- Caspi, P., Pilaud, D., Halbwachs, N., Plaice, J. (1987). LUSTRE: A declarative language for real-time programming. *POPL 1987*.
- Le Guernic, P., Gautier, T. et al. (1991). Programming real-time applications with SIGNAL. *Proc. IEEE*, 79(9):1321-1336.
- Kahn, G. (1974). The semantics of a simple language for parallel programming. *IFIP Congress 1974*.
- Benveniste, A. et al. (2003). The synchronous languages 12 years later. *Proc. IEEE*, 91(1):64-83.
- Mandel, L. & Pouzet, M. (2005). ReactiveML, a reactive extension to ML. *PPDP 2005*.
- Lohstroh, M. et al. (2021). Toward a Lingua Franca for deterministic concurrent systems. *ACM TECS*, 20(4).
- Delaval, G., Rutten, E., Marchand, H. (2010). Contracts for modular discrete controller synthesis. *LCTES 2010*.
