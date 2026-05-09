# TLA+ and Temporal Logics

*Source: TLA_Language_and_Logic.json, TLC_Model_Checker.json, Apalache_Symbolic_Model_Checker.json,
TLAPS_Proof_System.json, PlusCal_Algorithm_Language.json, Quint_Specification_Language.json,
Temporal_Logic_LTL_CTL.json, AWS_TLA_Plus_Usage.json, Protocol_Verification_Paxos_Raft.json,
tla-z3-insights.md.*

---

## 1. Temporal Logics Overview

Temporal logics express properties about sequences of states (system behaviors over time).

### 1.1 LTL — Linear Temporal Logic

LTL formulas are interpreted over **infinite linear paths** (sequences of states).

**Operators**:
| Operator | Notation | Meaning |
|---|---|---|
| Globally | `G φ` (or `□φ`) | φ holds in all future states |
| Eventually | `F φ` (or `◇φ`) | φ holds in some future state |
| Until | `φ U ψ` | φ holds until ψ becomes true |
| Next | `X φ` (or `○φ`) | φ holds in the next state |
| Release | `φ R ψ` | ψ holds until and including when φ holds |

**Key LTL properties for verification**:
- Safety: `G (¬bad_state)` — nothing bad ever happens
- Liveness: `G (request → F response)` — every request is eventually served
- Fairness: `G F (process_enabled) → G F (process_executed)` — enabled processes run infinitely often

**Model checking LTL** (Büchi automaton approach):
1. Negate the property: check if the system can violate φ
2. Convert ¬φ to a Büchi automaton B_¬φ (accepts counterexample traces)
3. Form product: system M ⊗ B_¬φ
4. Search for accepting cycle (reachable SCC with accepting state)
5. If accepting cycle found: counterexample exists. If no accepting cycle: property holds.

Complexity: PSPACE-complete in formula size; linear in state space.

### 1.2 CTL — Computation Tree Logic

CTL interprets over **computation trees** — all possible futures from each state.

**Path quantifiers**: `A` (for All paths), `E` (there Exists a path)
**State operators**: `G`, `F`, `U`, `X` (same as LTL but scoped by path quantifier)

**CTL operators** (always paired path + state quantifier):
| | Meaning |
|---|---|
| `AG φ` | On all paths, globally φ |
| `EF φ` | There exists a path where eventually φ |
| `AX φ` | In all next states, φ |
| `EX φ` | In some next state, φ |
| `A[φ U ψ]` | On all paths, φ until ψ |
| `E[φ U ψ]` | On some path, φ until ψ |

**Model checking CTL** (BDD/fixpoint approach):
CTL properties are computed as **fixpoints** over sets of states. Key equations:
```
EF φ  = μX. φ ∨ EX(X)         // least fixpoint: smallest set reachable from φ
AG φ  = νX. φ ∧ AX(X)         // greatest fixpoint: largest set where φ always holds
E[φ U ψ] = μX. ψ ∨ (φ ∧ EX(X))
```
Binary Decision Diagrams (BDDs) represent state sets symbolically. Operations are polynomial in BDD size.
Complexity: P-time in state space.

### 1.3 CTL* — Common Generalization

CTL* allows arbitrary combinations of path quantifiers and temporal operators.
LTL ⊂ CTL* and CTL ⊂ CTL*, but **LTL and CTL are incomparable** (neither subsumes the other).

| Logic | Path structure | Properties | Tools |
|---|---|---|---|
| LTL | Linear paths | Safety, liveness, fairness | SPIN, nuXmv, TLC (liveness) |
| CTL | Tree (all paths) | Reachability, unavoidability | NuSMV, BDD-based tools |
| CTL* | Tree + linear | Both | nuXmv, academic tools |

**Expressiveness note**: `AF AG φ` is a CTL property (not LTL). `F G φ` is LTL (not CTL).
TLA+ properties are expressed in a stuttering-invariant fragment of LTL (TLA).

---

## 2. TLA+ Language

TLA+ (Temporal Logic of Actions, Lamport 1994/2002) specifies concurrent systems as **behaviors**:
infinite sequences of states, where a state is an assignment of values to variables.

### 2.1 Canonical Spec Form

```tla
VARIABLES x, y, ...

Init == x = 0 /\ y = InitValue /\ ...   (* initial condition predicate *)

Next == Action1 \/ Action2 \/ ...        (* transition relation: "some enabled action fires" *)

Spec == Init /\ [][Next]_vars /\ Fairness   (* complete specification *)
```

- `Init`: Predicate over unprimed variables specifying initial states.
- `[][Next]_vars`: Always, either `Next` transitions hold or the tuple of variables is unchanged
  (stuttering step). This is the TLA **box-action** operator.
- `Fairness`: Weak/strong fairness conditions (WF, SF).
- `vars`: Usually `<<x, y, ...>>` — the tuple of all specification variables.

### 2.2 Actions — Primed/Unprimed Variables

An **action** is a predicate over pairs of consecutive states. Unprimed variables refer to the
current state; primed variables refer to the next state.

```tla
Increment == x' = x + 1 /\ UNCHANGED y    (* x increases by 1; y unchanged *)
Reset     == x' = 0 /\ y' = 0            (* both reset *)
```

`UNCHANGED y` ≡ `y' = y`. Always specify all variables in each action (what changes AND what stays).

### 2.3 Temporal Operators in TLA+

| Operator | Notation | Meaning |
|---|---|---|
| Always | `[]P` | P holds in all states of all behaviors |
| Eventually | `<>P` | P holds in some state of all behaviors |
| Leads-to | `P ~> Q` | Whenever P holds, Q eventually holds |
| Infinitely often | `[]<>P` | P holds infinitely often |
| Weak fairness | `WF_vars(A)` | If A is enabled forever, it eventually fires |
| Strong fairness | `SF_vars(A)` | If A is enabled infinitely often, it fires infinitely often |

### 2.4 Stuttering Invariance — The Central Property

A TLA+ formula is **stuttering-invariant**: appending/removing finite stretches of identical states
("stuttering steps") does not change whether the formula holds.

**Why**: This enables **refinement** between specs at different abstraction levels. If a concrete
spec refines an abstract spec, every behavior of the concrete spec (possibly with implementation-level
stuttering) must be a behavior of the abstract spec when stuttering is abstracted away.

**Consequence**: TLA+ has no `X` (Next) operator in the temporal layer — `X P` is not
stuttering-invariant. This is a deliberate design choice, not a limitation.

**Refinement definition**: Concrete spec CSpec **refines** abstract spec ASpec iff every behavior
of CSpec is (after abstracting stuttering) also a behavior of ASpec.

```tla
THEOREM CSpec => ASpec     (* refinement statement *)
```

### 2.5 Fairness

**Weak Fairness** `WF_vars(A)`: If action A is continuously enabled from some point onward,
then A must eventually fire.
Use for: actions that should eventually run if they never become disabled.

**Strong Fairness** `SF_vars(A)`: If action A is enabled infinitely often, then A must fire infinitely often.
Use for: actions that may become enabled and disabled repeatedly but must still make progress.

Example for a producer-consumer system:
```tla
Fairness == WF_vars(Produce) /\ WF_vars(Consume)
```

---

## 3. TLC Model Checker

TLC is the standard model checker for TLA+. It performs **explicit-state BFS**.

### 3.1 State Exploration

```
function TLC_BFS(Spec):
    initial_states = {s : Init(s)}          // enumerate all initial states
    queue = FIFO(initial_states)
    seen = {}

    while queue is not empty:
        s = queue.dequeue()
        if s in seen: continue
        seen.add(s)

        check_invariants(s)                  // check safety properties
        check_type_invariant(s)              // user-defined type checking

        successors = {s' : Next(s, s')}      // enumerate all next states
        for s' in successors:
            if s' not in seen:
                queue.enqueue(s')

    check_liveness(seen_graph)               // offline: Büchi product + SCC search
```

### 3.2 State Fingerprinting

TLC represents each state as a 64-bit Rabin fingerprint (polynomial hash).
- **In-memory table**: Stores fingerprints in a hash set. Each fingerprint: 8 bytes.
- **Disk-backed seen set**: For large state spaces, fingerprints sorted in disk blocks. Binary search
  for membership test. Slower but handles billions of states.
- Collision probability: ~1/2^64 per pair — negligible for practical state spaces.

State fingerprinting enables TLC to handle >100M states on a modern machine (in-memory).

### 3.3 Symmetry Reduction

If the state space has symmetry (e.g., processes are interchangeable), TLC can reduce exploration:
```tla
SYMMETRY Permutations({p1, p2, p3})   (* treat all permutations of p1/p2/p3 as equivalent *)
```

**Performance gain**: Up to n! factor reduction for n symmetric components.

**CRITICAL WARNING**: Symmetry reduction is **unsound for liveness properties** (LTL properties,
fairness). TLC will warn about this but may not prevent incorrect results. Use symmetry reduction
only for safety properties (invariants). This is one of the most common TLC mistakes.

### 3.4 Invariant and Liveness Checking

**Invariants** (safety): Checked immediately on each newly explored state. Violation → counterexample
trace printed. Fast: no post-processing needed.

**Liveness** (`Spec => []<>P` or `Spec => P ~> Q`): TLC uses the Büchi product construction:
1. Translate liveness formula to a Büchi automaton.
2. Form product of system states × automaton states.
3. Search for a reachable accepting SCC using **nested DFS** (Tarjan's algorithm or multi-SCC search).
4. If found: liveness violation counterexample (a cycle exhibiting the violation).

**Performance**: Liveness checking via nested DFS requires storing the full state graph in memory.
For large state spaces, liveness checking is prohibitively expensive — use compositional reasoning.

### 3.5 Performance

TLC throughput: 1M–10M states/second/core on typical hardware.
TLC is multi-threaded: multiple worker threads explore the state space in parallel with work-stealing.

---

## 4. Apalache Symbolic Model Checker

Apalache (Konnov et al. 2019) is a symbolic model checker for TLA+ specifications that handles
**infinite-domain** specs via SMT encoding.

### 4.1 Architecture

```
TLA+ spec
    ↓ parsing + type inference
KerA+ (intermediate representation)
    ↓ arena-based set encoding
SMT formula (Z3)
    ↓ bounded model checking
counterexample | no counterexample (up to bound k)
```

**KerA+**: A subset of TLA+ with explicit typing. Apalache's type system infers types for all
expressions. Type errors are caught before encoding.

### 4.2 Arena-Based Set Encoding

TLA+ sets are encoded via an **arena** (a collection of cells with containment predicates):
- Each set expression `S` is mapped to an arena cell `c_S`.
- Containment: `elem ∈ S` becomes a Boolean predicate `in(elem, c_S)`.
- Set comprehension `{x ∈ S : P(x)}` encoded by constraining `in(elem, c_new)` to `in(elem, c_S) ∧ P(elem)`.

This avoids the need for extensional set axioms (which would make the encoding undecidable) while
faithfully representing set semantics over bounded domains.

### 4.3 When to Use Apalache vs TLC

| | TLC | Apalache |
|---|---|---|
| State space | Finite, enumerable | Infinite or large finite |
| Domain types | Finite sets of model values | Integer, string, arbitrary sets |
| Method | Explicit BFS | Symbolic BMC (Z3) |
| Counterexample | Exact state trace | Symbolic trace |
| Liveness | Yes (nested DFS) | Limited (temporal BMC) |
| Setup | Simpler | Requires type annotations |

**Use Apalache when**: Variables range over unbounded integers or real numbers; state space too large
for TLC; need to check properties for all possible initial states; have a spec with parametric bounds.

---

## 5. TLAPS Proof System

TLAPS (TLA+ Proof System) enables **machine-verified, interactive proofs** of TLA+ theorems.

### 5.1 Proof Structure

```tla
THEOREM Spec => []Invariant
<1>1. Init => Invariant
    <2>1. CASE x = 0                (* base case: show Invariant holds initially *)
          BY DEF Init, Invariant
    <2>2. QED BY <2>1 DEF Init
<1>2. Invariant /\ [Next]_vars => Invariant'
    <2>1. CASE Action1              (* inductive step: each action preserves invariant *)
          BY <2>1 DEF Action1, Invariant
    <2>2. CASE Action2
          <3>1. ...
          <3>QED BY <3>1
    <2>QED BY <2>1, <2>2 DEF Next
<1>QED BY <1>1, <1>2, PTL     (* PTL: propositional temporal logic — axiom instance *)
```

### 5.2 Backend Dispatching

TLAPS dispatches proof obligations to multiple backends:
- **Isabelle/HOL**: Structural and inductive reasoning; higher-order logic.
- **Zenon**: Classical first-order reasoning (tableau-based).
- **Z3**: Arithmetic facts, linear arithmetic obligations.
- **CVC5**: Additional SMT support.

Each `BY` clause specifies what the backend should use:
```tla
BY DEF Invariant, Action1   (* use these definitions; let backend figure it out *)
BY ONLY <2>1, <2>2          (* use only these labeled facts *)
BY Zenon DEF ...            (* explicitly route to Zenon *)
BY IsabelleM("sledgehammer") DEF ...  (* invoke Sledgehammer *)
```

### 5.3 Common Proof Patterns

**Safety proof** (invariant):
1. `Init => Inv` (base case): unfold Init and Inv definitions; arithmetic/set reasoning.
2. `Inv /\ [Next]_vars => Inv'` (inductive step): case-split on each disjunct of Next; for each
   action, show primed Inv holds; UNCHANGED cases trivial.

**Liveness proof** (leads-to, P ~> Q):
Typically requires WF_vars(A) fairness assumption. Proof: show P enables A, A establishes Q.

**MongoDB case study** (Schultz et al. 2022): ~400 proof obligations, ~3500 lines of TLAPS proofs,
4 backends invoked. Validates MongoDB's Raft-based replication protocol correctness.

---

## 6. PlusCal

PlusCal is an algorithm language that compiles to TLA+. It provides a more familiar imperative or
Pascal-style syntax for engineers unfamiliar with TLA+.

### 6.1 Label Semantics

**Every label marks the boundary of an atomic action**:
```
labels:
  lbl1: action1; action2; action3;   (* action1/2/3 execute atomically — no interleaving *)
  lbl2: action4;
```
Each label corresponds to one disjunct in the TLA+ Next predicate. The label name becomes the action name.

**Critical rule**: Choose label granularity carefully. Too few labels → atomicity too coarse
(misses real concurrency bugs). Too many labels → exponential state space.

### 6.2 C-Like Syntax Example

```pluscal
--algorithm MutualExclusion {
  variables flag = [p \in {"p1","p2"} |-> FALSE], turn = "p1";

  fair process (p \in {"p1","p2"})
  variables other = IF self = "p1" THEN "p2" ELSE "p1";
  {
    ncs: while (TRUE) {   (* non-critical section *)
      lbl1: flag[self] := TRUE;
      lbl2: turn := other;
      lbl3: while (flag[other] /\ turn = other) { skip };  (* wait *)
            (* critical section *)
      cs:   skip;
      lbl4: flag[self] := FALSE;
    }
  }
}
```

### 6.3 Translation to TLA+

The PlusCal compiler generates a TLA+ specification from the algorithm. The generated TLA+ includes:
- Variable definitions for all algorithm variables + pc (program counter) per process
- `Init` predicate
- One `Next` disjunct per label
- Fairness conditions from `fair process` declarations

Engineers write PlusCal; TLC and TLAPS operate on the generated TLA+. The TLA+ is not meant to be edited.

---

## 7. Quint

Quint (Informal Systems) is a modern TypeScript-native specification language that compiles to TLA+.

### 7.1 Type System

Quint has **row polymorphism** for record types (like Elm or OCaml):
```quint
type Process = { id: str, state: str, clock: int }
// Row polymorphism: functions can operate on any record that has at least these fields
```

### 7.2 Effect System

Quint's effect system tracks whether a definition is:
- **Pure**: No state reads or writes (deterministic function)
- **Stateful**: Reads/writes state variables
- **Temporal**: Contains temporal operators (`always`, `eventually`)

This enables static checking of incorrect temporal formula composition.

### 7.3 Test Framework

Quint includes a built-in test framework for simulation:
```quint
test MyTest {
    var x: int = 0
    action init = { x' = 0 }
    action step = { x' = x + 1 }
    invariant xPositive = x >= 0
}
```
Simulator runs the spec for N steps, checking invariants at each step.

### 7.4 Integration with Apalache

Quint compiles to TLA+ and integrates directly with Apalache:
```bash
quint verify --main=MySpec --invariant=Safety myspec.qnt
```
This invokes Apalache on the compiled TLA+. Best choice for TypeScript-native projects that need
TLA+-style verification.

### 7.5 Why Quint vs TLA+

| | TLA+ | Quint |
|---|---|---|
| Syntax familiarity | Mathematical (LaTeX-like) | TypeScript-like |
| Type system | Weakly typed | Statically typed with row polymorphism |
| Effect system | Manual | Built-in |
| Test framework | No | Yes (simulation) |
| Toolchain | TLC + Apalache + TLAPS | Quint CLI → Apalache |
| Best for | TLA+ experts, existing TLA+ specs | TypeScript teams, new specs |

---

## 8. Industry Adoption Patterns

**AWS** (Newcombe et al. 2015 CACM): 10 systems verified with TLA+ (DynamoDB, S3, EBS, etc.).
7 had **previously unknown bugs** discovered. Key findings:
- Bugs found had 35+ step failure sequences — impossible to find by testing or code review.
- Engineers learned TLA+ in 2–3 weeks.
- Framing as "exhaustive design testing" (not "formal methods") improved adoption.
- PlusCal used for engineers; TLA+ for experts.
- AWS style: write spec → run TLC → fix model → implement → spec becomes documentation.

**MongoDB** (Schultz et al. 2022 VLDB): Used TLAPS to prove correctness of Raft-based replication.
~400 proof obligations, 3500+ lines of proof. Discovered subtle edge case in leader lease logic.

**Lesson for adoption**: Formal methods value is concentrated at the **design phase** — before any code
is written. The spec catches design bugs that are extremely expensive to fix post-implementation.
TLA+ should be used to validate distributed protocol designs, not to verify running code.

---

## 9. Specification Patterns

### 9.1 Safety vs. Liveness Separation

Always separate safety and liveness into distinct invariants:
```tla
SafetyInvariant == (* state predicates that must always hold *)
    /\ x >= 0
    /\ mutualExclusion

LivenessProperty == (* temporal: eventually something happens *)
    /\ WF_vars(Process1)
    /\ [](request => <>response)
```

Type check separately: `TypeInvariant` (structural validity) and `SafetyInvariant` (behavioral safety).

### 9.2 What to Specify vs. Not Specify

**Specify**:
- The abstract algorithm (distributed protocol, state machine)
- Safety invariants: mutual exclusion, data integrity, consistency
- Liveness: eventual progress, termination
- Refinement: that the concrete spec refines the abstract spec

**Do not specify** (too much detail kills tractability):
- Exact timing (unless using Real-Time TLA+)
- Low-level implementation details (buffer management, network framing)
- Properties that follow trivially from the type system

---

## 10. Implementation Strategies

**When to use TLA+** (highest ROI):
- Distributed systems with complex concurrency (consensus, replication, coordination)
- Before writing a single line of implementation code
- When the protocol has subtle invariants that could fail after millions of steps

**Tool selection**:
- **Finite, small state space**: TLC (direct, no setup overhead, exact counterexamples)
- **Infinite integer domains or very large state space**: Apalache (symbolic BMC)
- **Need machine-verified proof**: TLAPS (interactive proof assistant backend)
- **TypeScript-native project**: Quint → Apalache
- **New engineers learning**: PlusCal as entry point

**Spec strategy**:
1. Start with a simplified abstract model (5–10 variables, 3–5 actions).
2. Check safety invariants first — run TLC for a few minutes.
3. Add liveness and fairness once safety is established.
4. Gradually add detail — refine abstract model toward implementation.

---

## 11. Common Pitfalls

**Pitfall 1: Symmetry reduction enabled for liveness properties.**
TLC's symmetry reduction partitions the state space by permutation equivalence. For safety (invariants),
this is sound. For liveness (Büchi automaton, SCC search), the partition may eliminate states needed
for the SCC analysis — leading to incorrect "property holds" verdicts. TLC warns when symmetry is
combined with liveness, but the warning is easy to miss. Fix: always disable symmetry when checking
any temporal (liveness) property.

**Pitfall 2: Liveness checking on large state spaces.**
Nested DFS for SCC detection requires storing the entire product state graph in memory. For systems
with millions of states, liveness checking can exhaust memory or run indefinitely. Fix: use
compositional liveness reasoning (prove liveness module-by-module using assume-guarantee), or
restrict liveness checks to small model instances.

**Pitfall 3: Forgetting stuttering steps in refinement proofs.**
When proving `ConcreteSpec => AbstractSpec`, the concrete spec may take multiple steps for each abstract
step. The abstract spec must be **stuttering-invariant** (already guaranteed by TLA+ semantics), but the
mapping must correctly identify which concrete actions correspond to which abstract actions and which
are "stutter-only" (UNCHANGED all abstract variables). Missing a stutter identification causes the
refinement proof to fail in non-obvious ways.

---

## 12. Key References

- Lamport, L. (1994). The temporal logic of actions. *TOPLAS*, 16(3).
- Lamport, L. (2002). *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers*. Addison-Wesley.
- Newcombe, C. et al. (2015). How Amazon Web Services uses formal methods. *CACM*, 58(4).
- Schultz, W. et al. (2022). TLA+ model checking of a distributed protocol in a database. *VLDB*.
- Konnov, I. et al. (2019). TLA+ model checking with Apalache. *OOPSLA 2019*.
- Informal Systems (2023). Quint specification language. https://github.com/informalsystems/quint
- Chaudhuri, K. et al. (2010). The TLAPS proof system. *TACAS 2010*.
