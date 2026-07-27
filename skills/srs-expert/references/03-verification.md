# Verification of Synchronous Reactive Systems

*Sources: verification_and_properties.json (2026-04-07), reactive-system-insights.md §3*

---

## 1. The Synchronous Observer Pattern

**Primary reference:** Halbwachs et al. (1993); Raymond (1994); Champion et al. (2016).

The central verification technique for synchronous systems. A **safety property** is expressed as a **synchronous observer** — a Lustre node that runs in parallel with the system under verification. The observer takes the same inputs/outputs as the system and emits a `violation` signal when the property is breached.

### 1.1 Structure and Semantics

```lustre
-- Observer for: "alarm must never be active while door is open"
node SafetyObserver(alarm: bool; door_open: bool) returns (violation: bool);
let
  violation = alarm and door_open;
tel
```

**Verification reduction:** Checking a safety property P reduces to:
> Can the `violation` signal ever become true? (reachability on `(system ∥ observer)`)

This is a reachability question on the composed automaton (system combined with observer), solvable by model checking.

### 1.2 Why the Observer Pattern Works

| Advantage | Explanation |
|---|---|
| **Same language** | Observers are Lustre nodes — executable and testable, not a separate spec language |
| **Runtime deployable** | Observers can run in the deployed system for runtime monitoring and autotest |
| **Compositional** | Multiple observers compose in parallel with the same system without interference |
| **Formally verifiable** | The observer composition is exactly the input for model checkers (Lesar, Kind2) |
| **Environment assumptions** | A second observer can encode input assumptions, enabling assume-guarantee reasoning |

### 1.3 Observer Pattern Correctness (Halbwachs et al. 1992)

**Formal statement:** A safety property P holds iff a synchronous observer watching for P violations never emits `violation = true`. Verification reduces to reachability on `(system ∥ observer)`.

The correctness argument follows from the synchronous parallel composition semantics: the observer sees exactly the same signal values as the system at every tick, because they share the frozen signal environment. There is no race condition between observation and execution.

### 1.4 Observer Pattern for Compliance

Every regulatory obligation is a safety property. Direct mapping:

| Compliance requirement | Observer structure |
|---|---|
| Notification within deadline | Counter node: `hours_elapsed ≤ 72` |
| Evidence must be present | `violation = expected_signal and (evidence_signal = absent)` |
| Concurrent obligations | Parallel composition of observer nodes |
| Cross-article dependency | Shared signal between observer nodes |
| Exception condition | Environment assumption observer |

*See `05-compliance-modeling.md` for full GDPR experiments.*

### 1.5 Correctness by Construction Spectrum

Synchronous systems offer a spectrum of correctness guarantees:

| Level | Properties guaranteed | Mechanism |
|---|---|---|
| By language design | Determinism, no race conditions | Synchrony hypothesis, functional stream semantics |
| By static analysis (compile-time) | Causality, clock consistency, type safety | Compiler checks |
| By synthesis | Enforced behavioral constraints | Discrete controller synthesis (Heptagon/BZR + Sigali) |
| By formal verification | Safety properties (observer-specified), no runtime errors | Model checking (Kind2, Lesar), abstract interpretation (Astree) |
| By qualified code generation | Implementation faithfulness | SCADE KCG at DO-178C/DO-330 TQL-1 |

---

## 2. Lesar (BDD-Based Model Checker)

**Authors:** Halbwachs, Raymond, Ratel (Verimag, ~1993)

Lesar is a symbolic, BDD-based model checker specifically designed for Lustre programs. It verifies safety properties expressed as synchronous observers.

### 2.1 Algorithm

1. Extract the Boolean part of the Lustre program
2. Transform into logical functions represented as Binary Decision Diagrams (BDDs)
3. Build an **implicit (symbolic) representation** of the state space — no explicit state enumeration
4. Use BDD operations to check reachability of the alarm state

**Strengths:** Tight integration with Lustre and the observer pattern; pioneered synchronous program verification.

**Limitations:**
- Only handles Boolean abstraction of programs; numerical properties must be abstracted
- BDD size can explode for large state spaces (BDD variable ordering problem)
- Superseded by SMT-based approaches (Kind2) for programs with integer/real variables

---

## 3. Kind2 (SMT-Based Model Checker)

**Authors:** Champion, Mebsout, Sticksel, Tinelli — University of Iowa (2016)  
**Primary reference:** Champion et al. (2016). The Kind 2 Model Checker. *CAV 2016*.

Kind2 is an open-source, multi-engine, SMT-based automatic model checker for safety properties of synchronous reactive systems expressed in Lustre (with extensions). It runs multiple verification engines in parallel.

### 3.1 Verification Engines

| Engine | Algorithm | Use case |
|---|---|---|
| **BMC** (Bounded Model Checking) | Unroll transition relation up to bound k; check via SAT/SMT | Find counterexamples within k steps |
| **k-induction** | Prove property holds for k steps; then prove k-step to (k+1)-step | Prove invariants in bounded depth |
| **IC3/PDR** (Property Directed Reachability) | Incrementally build inductive invariants using SAT frames | Infinite-state invariant proving |
| **IC3QE** | IC3 with quantifier elimination | Programs with quantified properties |
| **IC3IA** | IC3 with implicit abstraction | Large programs, abstraction refinement |
| **Invariant generation** | Multiple processes generate candidate invariants | Strengthen induction hypotheses |

All engines run **in parallel** on all properties simultaneously. The first engine to prove or disprove a property wins.

### 3.2 SMT Backends

Kind2 supports: Bitwuzla, cvc5, MathSAT5, SMTInterpol, Yices 2, Z3.

**Key advantage over Lesar:** Kind2 handles **infinite-state systems** (integer and real variables), not just Boolean programs. Directly applicable to compliance models with numeric counters and thresholds (e.g., `hours_elapsed ≤ 72`, `counter ≥ 0`).

### 3.3 Contract-Based Compositional Verification

```lustre
node component(x: int) returns (y: int);
(*@contract
  assume x >= 0;       -- environment must satisfy this
  guarantee y > x;     -- component guarantees this
*)
```

**Compositional rule (assume-guarantee):** If all components verify their contracts AND all calls satisfy the caller's assumptions, then the overall system is safe — without building the explicit product state space.

**Kind2 algorithm:**
1. Verify each component against its contract (bottom-up in the subsystem hierarchy)
2. Abstract each verified component by its contract at call sites in larger systems
3. If compositional verification fails, refine contracts to strengthen abstractions
4. Report counterexamples as concrete input traces

**Output when property fails:** Kind2 produces an input sequence (counterexample) showing exactly how the violation occurs — directly actionable for debugging.

### 3.4 Applicability to aiqeung

Kind2-style properties can be stated about the aiqeung synchronous runtime:

```lustre
-- aiqeung compliance property (pseudo-Lustre)
property: G (breach_known and risk_to_rights => F[0..72] authority_notified)
```

The `ObligationObserver` in aiqeung corresponds exactly to a Kind2-verifiable Lustre observer node. If the runtime is formalized as a Lustre model, Kind2 can verify that compliance properties hold for ALL possible input sequences.

---

## 4. Astree (Abstract Interpretation)

**Authors:** Cousot, Cousot, Feret, Mauborgne, Miné, Monniaux, Rival (ENS) — 2003+  
**Primary reference:** Cousot et al. (2005). The ASTREE Analyzer. *ESOP 2005*.

### 4.1 Abstract Interpretation Foundation

Abstract interpretation (Cousot & Cousot, 1977) computes a **sound overapproximation** of all possible program behaviors without enumerating concrete states. Key properties:

- **Soundness:** If the analysis proves property P, then P holds for ALL concrete executions (no false negatives for proven properties)
- **Potential false alarms:** Overapproximation may report violations that cannot occur concretely — but specialized domains minimize this
- **No state explosion:** Works on abstract domains, not the concrete state space

**Applicability to synchronous code:** Synchronous programs have bounded state and no dynamic allocation, making them especially well-suited to abstract interpretation. The analysis can exploit the tick structure to do local analysis between ticks.

### 4.2 The Astree Result

> Astree proved the **complete absence of any runtime error** in the primary flight control software of the **Airbus A340** fly-by-wire system — **132,000 lines of C** generated from SCADE — in 1h20 on a 2.8 GHz PC using 300 MB, with **zero false alarms**.

This is the benchmark result for formal verification of synchronous code. It demonstrates:
1. Abstract interpretation scales to industrial-size code
2. Zero false alarms is achievable with carefully designed abstract domains for synchronous code patterns
3. SCADE's code generation is structured enough that abstract analysis succeeds without false alarms

**Astree is now commercialized** by AbsInt GmbH and is part of the certification workflow for safety-critical embedded software.

---

## 5. Velus (Verified Compilation)

**Authors:** Bourke, Brun, Dagand, Leroy, Pouzet, Rieg (INRIA) — 2017  
**Primary reference:** Bourke et al. (2017). A Formally Verified Compiler for Lustre. *PLDI 2017*.

### 5.1 Purpose and Achievement

Velus is a formally verified Lustre compiler implemented in **Coq**, extending **CompCert** (the verified C compiler by Leroy). It creates an **end-to-end trust chain**:

```
Lustre specification
       ↓ [Velus: Coq-certified]
Normalized Lustre
       ↓ [Velus: Coq-certified]
CompCert C
       ↓ [CompCert: Coq-certified]
Executable assembly
```

Every step is formally verified in Coq. The generated assembly is **provably faithful** to the synchronous specification.

### 5.2 What Velus Proves

The correctness theorem (informally):
> For every Lustre program P and every input trace I, the assembly produced by Velus on input P, when run on input I, produces the same output trace as the Lustre operational semantics of P on I.

This is an **end-to-end correctness theorem** — no trusted components between spec and code.

### 5.3 Significance

| Property | Status before Velus | Status with Velus |
|---|---|---|
| Compiler correctness | Trusted (tested but not proved) | Formally proved in Coq |
| Trust chain | Broken at code generation | Unbroken: spec → assembly |
| DO-178C qualification | Testing-based | Can potentially replace testing with proof |

**Practical impact:** In safety-critical domains, this eliminates the need to separately verify the code generator output. The code generator IS the proof.

---

## 6. LOLA (Runtime Monitoring)

**Authors:** D'Angelo, Sankaranarayanan, Sánchez, Robinson, Finkbeiner, Sipma, Naldurg, Manna — 2005  
**Primary reference:** D'Angelo et al. (2005). LOLA: Runtime Monitoring of Synchronous Systems. *TIME 2005*.

### 6.1 Purpose

LOLA is a specification language and runtime monitor for synchronous systems. Unlike model checking (which verifies all possible executions), LOLA monitors a **specific execution trace** as it happens.

### 6.2 Bounded Memory Theorem

> Runtime monitors for synchronous systems can be implemented in **constant space per tick** — memory independent of trace length.

Formally: a LOLA specification with past-only operators (no future operators) requires O(1) memory per tick, because once a tick's data is processed and the property checked, it can be discarded. The monitor only needs to remember the state necessary for computing the next output.

**Implication for aiqeung:** The `ObligationObserver` pattern implements exactly LOLA-style bounded monitoring. Each observer's state is finite (bounded by the specification), and memory does not grow with the length of the compliance trace.

### 6.3 Past and Future Operators

LOLA supports both:
- **Past operators** (`pre`, `since`): bounded memory — monitor discards old data
- **Future operators** (`next`, `until`): unbounded memory in general (must buffer future data); bounded for bounded lookahead

For compliance monitoring, past operators suffice: "was the obligation satisfied within the deadline?" requires only backward-looking computation.

### 6.4 LOLA vs. Model Checking

| Dimension | Kind2 (model checking) | LOLA (runtime monitoring) |
|---|---|---|
| Target | All possible executions | Specific execution trace |
| Memory | State space (can be large) | Bounded (constant per tick) |
| Timing | Offline (pre-deployment) | Online (during execution) |
| Coverage | Complete for finite models | Single trace |
| Output | Proof or counterexample | Per-tick violation signal |

Both are needed: Kind2 for pre-deployment guarantees, LOLA-style monitors for runtime enforcement.

---

## 7. Heptagon/BZR (Controller Synthesis)

**Authors:** Delaval, Marchand, Rutten (INRIA Ctrl-A) — 2010+  
**Primary reference:** Delaval, Marchand, Rutten (2010). Contracts for Modular Discrete Controller Synthesis. *LCTES 2010*.

### 7.1 Key Idea: Correctness by Controller Synthesis

Rather than verifying a property after designing the program, Heptagon/BZR **automatically synthesizes a controller** that enforces the property. The programmer specifies:
- **Assumptions:** what the environment is expected to do
- **Enforce property:** what must always hold (compiler enforces this)
- **Controllable variables:** which variables the synthesized controller can set

The Sigali tool performs **discrete controller synthesis** (DCS): given a plant model (the synchronous program) and a safety property, it synthesizes the most permissive controller that guarantees the property.

### 7.2 Connection to aiqeung

The Layer 2.5 `NetContract` mechanism in aiqeung aligns with the Heptagon/BZR contract-based approach:

| Heptagon/BZR | aiqeung analog |
|---|---|
| `enforce` property | `NetContract.obligation` |
| `controllable` variable | Output signal of the reactive runtime |
| Synthesized controller | `ObligationObserver` (manual synthesis) |
| Contract composition | Multiple `ObligationObserver` nodes in `par` |

Heptagon/BZR provides the theoretical backing for why contract-based obligation modeling is sound: it is a known, well-studied approach to correctness by construction in synchronous systems.

---

## 8. Verification Stack for aiqeung Compliance

Full stack from specification to runtime:

```
Level 0 (Design): Observer pattern
    Compliance requirement → Lustre observer node
    → ObligationObserver in ReactiveExpr

Level 1 (Pre-deployment): Kind2 model checking
    (system ∥ observer) → verify violation is unreachable
    → Formal proof that compliant input traces stay compliant

Level 2 (Code generation): SCADE/Velus qualification
    Lustre → C, with certified correctness
    → aiqeung interpreter IS the runtime (spec-execution duality)

Level 3 (Runtime): LOLA-style bounded monitoring
    ObligationObserver runs per-tick with bounded memory
    → Runtime enforcement and evidence collection

Level 4 (Synthesis): Heptagon/BZR contracts
    Behavioral contracts with controllable variables
    → Strongest possible soundness: property enforced by construction
```

---

## Bibliography

- Halbwachs, N., Raymond, P., & Ratel, C. (1993). Generating efficient code from data-flow programs. *Programming Language Implementation and Logic Programming* (Springer).
- Champion, A., Mebsout, A., Sticksel, C., & Tinelli, C. (2016). The Kind 2 Model Checker. *CAV 2016*. Lecture Notes in Computer Science, vol. 9780.
- Cousot, P., Cousot, R., Feret, J., Mauborgne, L., Miné, A., Monniaux, D., & Rival, X. (2005). The ASTREE Analyzer. *ESOP 2005*.
- Bourke, T., Brun, L., Dagand, P.-E., Leroy, X., Pouzet, M., & Rieg, L. (2017). A Formally Verified Compiler for Lustre. *PLDI 2017*.
- D'Angelo, B., Sankaranarayanan, S., Sánchez, C., Robinson, W., Finkbeiner, B., Sipma, H.B., Naldurg, P., & Manna, Z. (2005). LOLA: Runtime Monitoring of Synchronous Systems. *TIME 2005*.
- Delaval, G., Marchand, H., & Rutten, E. (2010). Contracts for Modular Discrete Controller Synthesis. *LCTES 2010*.
- Benveniste, A. et al. (2003). The Synchronous Languages 12 Years Later. *Proc. IEEE*, 91(1):64-83.
- Leroy, X. (2009). Formal verification of a realistic compiler. *Communications of the ACM*, 52(7):107-115.
