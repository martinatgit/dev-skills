# Model Checking Algorithms

*Source: Kind2_Lustre_Model_Checker.json, SMPT_Petri_Net_Verification.json, CDCL_T_Framework.json,
Synchronous_Observer_Methodology.json, Apalache_Symbolic_Model_Checker.json, tla-z3-insights.md.*

---

## 1. Overview — Explicit vs. Symbolic vs. Bounded

Three fundamental approaches to model checking:

| Approach | State representation | Completeness | Tools | Best for |
|---|---|---|---|---|
| **Explicit-state** | Enumerate states individually | Complete for finite models | TLC, SPIN, PAT | Small/medium finite systems |
| **Symbolic** (BDD) | State sets as BDDs | Complete for finite domains | NuSMV, Cadence SMV | Boolean/enum state spaces |
| **Symbolic** (SMT) | State predicates as formulas | Complete for decidable theories | Apalache, Kind2 | Infinite/large domains |
| **Bounded** (BMC) | Unrolled transition relation | Sound but **incomplete** | Kind2, nuXmv | Bug finding up to bound k |

**Completeness-vs-automation trade-off**:
- Explicit-state BFS is complete but memory-limited (state explosion).
- Symbolic BDD handles larger spaces but BDD size can explode.
- SMT-based BMC handles infinite domains but only finds bugs of bounded length.
- k-Induction extends BMC to prove properties (if inductive step succeeds).
- IC3/PDR learns inductive clauses — most powerful finite-state property prover.

---

## 2. Bounded Model Checking (BMC)

BMC encodes "is there a counterexample of length ≤ k?" as an SMT formula.

**Full pseudocode**:
```
function BMC(Init, Trans, Prop, k_max):
    for k = 0 to k_max:
        // Unroll: INIT ∧ TRANS^k ∧ ¬PROP_at_some_step
        formula = INIT(s₀)
        for i = 0 to k-1:
            formula ∧= TRANS(sᵢ, sᵢ₊₁)     // transition: state i → state i+1
        neg_prop = OR(¬PROP(sᵢ) for i = 0 to k)  // property violated at some step
        formula ∧= neg_prop

        result = Z3.check(formula)

        if result == SAT:
            model = Z3.get_model()
            return Counterexample(reconstruct_trace(model))  // bug found!
        // UNSAT means: no counterexample of length k exists
    return NoBugFoundUpTo(k_max)
```

**Interpretation**:
- **SAT**: A counterexample of length ≤ k was found. The model gives concrete state values.
- **UNSAT**: No counterexample exists of length ≤ k. Does **not** mean the property holds for all k.

**Critical limitation**: BMC is a bug-finding technique. UNSAT only means "no bug of this length."
**BMC is NOT a proof of correctness.** This is the #1 misuse of BMC — claiming that BMC passing
means the property holds. It does not.

**What makes BMC fast**: The SMT formula is highly structured (repeated TRANS blocks). Modern SMT
solvers (Z3) exploit this structure via incremental solving: add TRANS(sₖ₋₁, sₖ) incrementally,
push ¬PROP on each step, pop and continue.

---

## 3. k-Induction

k-Induction extends BMC to produce proofs. Two parts:

**Base case** (= BMC up to k):
```
∀ i < k: no counterexample of length i exists
```

**Inductive step**: Assume k consecutive states all satisfy PROP. Does the (k+1)-th?
```
function k_Inductive_Step(Trans, Prop, k):
    // Assume: k states s₀, ..., sₖ₋₁ all satisfy Prop
    formula = AND(PROP(sᵢ) for i = 0 to k-1)
    for i = 0 to k-2:
        formula ∧= TRANS(sᵢ, sᵢ₊₁)
    formula ∧= TRANS(sₖ₋₁, sₖ)
    formula ∧= ¬PROP(sₖ)           // can the property fail on step k?

    result = Z3.check(formula)
    if result == UNSAT: return Proved    // inductive: property holds for all k
    else: return Unknown(k)             // inductive step fails at k — try k+1 or strengthen
```

**Full k-Induction algorithm**:
```
function k_Induction(Init, Trans, Prop, k_max):
    for k = 1 to k_max:
        // Try to prove
        if k_Inductive_Step(Trans, Prop, k) == Proved:
            return Proved
        // Look for bugs simultaneously (BMC)
        if BMC_has_counterexample(Init, Trans, Prop, k):
            return Counterexample

    return Unknown(k_max)
```

**Interpretation**:
- **Proved**: PROP is a k-inductive invariant — it holds for all reachable states.
- **Counterexample**: Actual bug found (from BMC sub-check).
- **Unknown(k)**: Inductive step failed at k. Does NOT mean the property is wrong.
  **Common mistake**: treating Unknown as "property might fail." Correct interpretation:
  k-induction is not strong enough at this k. Try: (1) increase k; (2) add auxiliary invariants.

**Auxiliary invariant strengthening**: The inductive step may fail because the invariant I is not
strong enough — i.e., I does not rule out all spurious preimage states. Adding auxiliary invariants
`I ∧ Aux` can make the inductive step succeed:
```
Augmented_Prop = Prop ∧ Aux1 ∧ Aux2 ∧ ...   (* stronger invariant, still holds *)
```
Kind2 learns auxiliary invariants automatically via IC3/PDR (see Section 4).

---

## 4. IC3/PDR — Property-Directed Reachability

IC3 (Bradley 2011) / PDR (Property-Directed Reachability, Eén et al. 2011) is the state-of-the-art
property prover for finite transition systems. It learns inductive clauses that "block" the
backward-reachable bad states.

**Key data structure**: Frame array `F[0], F[1], ..., F[n]` where each F[i] is a set of clauses.
`F[0] = Init`. `F[i]` represents an over-approximation of states reachable in ≤ i steps that
are not yet known to be bad.

**IC3 main loop pseudocode**:
```
function IC3(Init, Trans, Prop):
    F = [Init]              // F[0] = Init; F[1..] = {True} initially

    while True:
        // Phase 1: Find a counterexample-to-induction (CTI)
        // Look for a state in F[n] that is one step from ¬Prop
        cti = find_CTI(F, Trans, Prop)

        if cti is None:
            // Phase 2: Forward propagation — push clauses forward
            for i = 0 to len(F)-2:
                for clause c in F[i]:
                    if c is inductive relative to F[i+1]:
                        F[i+1].add(c)   // clause can be pushed forward
                if F[i] == F[i+1]:     // fixpoint: no new states reachable
                    return Proved       // F[i] is an inductive invariant

            // Add new frame
            F.append({True})
        else:
            // Phase 3: Cube blocking (generalize and push backward)
            obligations = [cti]
            while obligations is not empty:
                (state, level) = obligations.pop()
                if state is reachable from Init: return Counterexample
                
                // Generalize: find a minimal cube (conjunction of literals)
                // that blocks this class of bad states
                cube = generalize(state, F[level], Trans)
                
                // Block cube at level and all prior levels
                for j = 0 to level:
                    F[j].add(¬cube)    // add learned clause: this cube is unreachable
                
                // Push obligation backward
                predecessor = find_predecessor(cube, F[level-1], Trans)
                if predecessor is not None:
                    obligations.push((predecessor, level-1))
```

**What makes IC3 powerful**:
IC3 does not just check "is the invariant preserved?" It learns **inductive clauses** that block
specific bad states. These clauses are not property-based — they are discovered by analyzing why
bad states are unreachable. The forward propagation phase pushes these clauses toward a fixpoint.

**Comparison to k-induction**:
- k-Induction asks: "Does k steps of the transition preserve Prop?" A failure means the invariant
  needs strengthening (no direction provided).
- IC3 asks: "Which specific states lead to ¬Prop?" A failure produces a cube that is blocked,
  and the blocked cube becomes a learned clause. The direction is always productive.

---

## 5. SMPT — State Equation Reachability for Petri Nets

SMPT (State Marking Problem via Transition firing) uses the **Petri net state equation** to encode
reachability as a Z3 LIA query.

### 5.1 State Equation

For a Petri net with places P = {p₁,...,pₙ}, transitions T = {t₁,...,tₘ}:
- `m₀`: Initial marking vector (|P|-dimensional)
- `m*`: Target marking to check reachability
- `C`: Incidence matrix (|P|×|T|); `C[p][t] = Post[p][t] - Pre[p][t]`
- `x`: Firing count vector — x[t] = how many times transition t fires

**State equation**: `m* = m₀ + C · x`

If there exists a non-negative integer vector `x` satisfying this equation, then `m*` is a
necessary condition for reachability (but not sufficient — firing order matters).

### 5.2 Z3 LIA Encoding

```
function SMPT_Reachability(net, m0, m_target):
    Z3 = new Solver(QF_LIA)

    // Variables: x[t] for each transition t (firing count)
    x = {t: Z3.Int.const(f"x_{t}") for t in net.transitions}

    // Non-negativity
    for t in net.transitions:
        Z3.add(x[t] >= 0)

    // State equation: for each place p
    for p in net.places:
        sum_terms = m0[p]  +  sum(C[p][t] * x[t] for t in net.transitions)
        Z3.add(sum_terms == m_target[p])

    result = Z3.check()

    if result == UNSAT:
        return Unreachable  // LINEAR ALGEBRAIC CERTIFICATE: target is provably unreachable
    else:
        return PotentiallyReachable  // NOT a witness to reachability (spurious)
```

**Critical interpretation**:
- **UNSAT**: The target marking is **provably unreachable** via any firing sequence. This is a
  genuine formal certificate. No firing sequence (regardless of order) can reach `m*`.
- **SAT**: The state equation has a non-negative integer solution. This does NOT mean `m*` is
  reachable — it only means the linear algebraic necessary condition is satisfied. The actual
  firing order may make `m*` unreachable. **SAT is not a reachability proof.**

### 5.3 Trap Refinement

When the state equation gives SAT (spurious), add **trap constraints** to sharpen the approximation:

A **trap** is a set of places S such that if any place in S is marked, S always has a marked place
(tokens never leave S collectively). If m*[p] = 0 for all p ∈ S but m₀[p] > 0 for some p ∈ S,
then m* is unreachable.

```
function add_trap_constraints(Z3, net, m0, m_target):
    // Find a trap that witnesses unreachability
    // Trap S: for each transition t, if Pre[S] ∩ {t's input places} ≠ ∅ then Post[S] ∩ {t's output places} ≠ ∅
    // Encode trap membership as Boolean variables
    S = {p: Z3.Bool.const(f"trap_{p}") for p in net.places}

    // Trap constraint: for each transition t
    for t in net.transitions:
        // if t removes tokens from S (consumes from some p in S)
        // then t must also add tokens to S (produces to some p' in S)
        Z3.add(
            Or(Not(S[p]) for p in Pre(t)) |  // t doesn't remove from S
            Or(S[q] for q in Post(t))         // or t adds to S
        )

    // Witness: trap S has a token in m₀ but not in m*
    Z3.add(Or(S[p] for p in net.places if m0[p] > 0))   // initially marked
    Z3.add(And(Not(S[p]) for p in net.places if m_target[p] > 0))  // not in target

    return Z3.check()  // if UNSAT: no trap witnesses unreachability; if SAT: trap found
```

**Iterative refinement**: Add trap constraints, check again. Repeat until UNSAT (proved) or
the trap search itself returns UNSAT (no trap exists — stronger techniques needed).

### 5.4 Polyhedral Reductions

SMPT also applies structural reductions before encoding:
- **Pre/post-agglomeration**: Merge sequences of places/transitions with no branching.
- **Redundant place elimination**: Remove places that are always implied by other places.
- **Invariant detection**: Find P-invariants (place invariants: `λ^T · C = 0`) as additional constraints.

P-invariant: If `λ^T · m = λ^T · m₀` for all reachable m, then `λ^T · m* = λ^T · m₀` is required
for reachability. This is a linear equality constraint, strengthening the QF_LIA encoding.

---

## 6. Synchronous Observer Methodology

A **synchronous observer** expresses a safety property P as a synchronous stream computation with
a Boolean output `ok`. The property holds iff `ok` is always true.

**Key theorem** (Halbwachs et al. 1992): Safety property P holds iff the observer for P never
emits `ok = false`. Model checking reduces to reachability of `{ok = false}` in the composed system.

```
// Observer for "x never exceeds 100 while active":
node SafetyObserver(x: int, active: bool) returns (ok: bool)
let
    ok = if active then (x <= 100) else true;
tel

// Composed system:
SystemWithObserver = System ||| SafetyObserver

// Verification query:
// Can SystemWithObserver reach a state where ok = false?
// Encoded as BMC / k-Induction / IC3 query
```

**Integration with Kind2** (Champion et al. 2016 CAV):
Kind2 is a model checker for Lustre synchronous programs. Node contracts in Kind2 follow the
observer pattern:
```lustre
(*@contract
    assume x >= 0;     (* system assumption *)
    guarantee y >= x;  (* property to check = observer output *)
*)
node MyNode(x: int) returns (y: int) ...
```

Kind2 internally converts these to synchronous observer nodes and applies BMC + k-Induction + IC3/PDR
concurrently. Multiple engines share discovered auxiliary invariants.

**Connection to aiqeung-style compliance monitoring**: Each `ObligationObserver` in the reactive
runtime follows this exact pattern. The obligation check is a stream computation; compliance =
"observer always outputs satisfied." Model checking the compliance observer reduces to checking
reachability of the "violated" output state.

---

## 7. Algorithm Comparison Table

| Algorithm | Soundness | Completeness | Proves property | Finds CEX | Infinite state | Tools |
|---|---|---|---|---|---|---|
| Explicit BFS | Sound | Complete (finite) | Yes | Yes | No | TLC, SPIN, PAT |
| BMC | Sound | **Incomplete** | No | Yes (bounded) | Yes (w/ SMT) | Kind2, nuXmv |
| k-Induction | Sound | Complete if k-inductive | Yes | Yes (via BMC) | Yes (w/ SMT) | Kind2, ABC |
| IC3/PDR | Sound | Complete (finite) | Yes | Yes | No (needs bounded) | IC3, Kind2 |
| SMPT (state eq.) | Sound | Incomplete (UNSAT only) | UNSAT proves unreachability | SAT is spurious | Via LIA | SMPT |
| Symbolic BDD | Sound | Complete (finite) | Yes | Yes | No | NuSMV |
| Apalache (BMC) | Sound | Incomplete | No | Yes (bounded) | Yes | Apalache |

---

## 8. Implementation Strategies

**For a TypeScript project using Z3 WASM**:

**BMC** (easiest to implement — start here):
```typescript
async function BMC(
    init: (s: State) => z3.BoolExpr,
    trans: (s: State, s_next: State) => z3.BoolExpr,
    prop: (s: State) => z3.BoolExpr,
    k_max: number
): Promise<'safe_up_to_k' | CounterExample> {
    const solver = new Z3.Solver();
    const states = [freshState(0)];
    solver.add(init(states[0]));

    for (let k = 0; k < k_max; k++) {
        const s_next = freshState(k + 1);
        solver.add(trans(states[k], s_next));
        states.push(s_next);

        // Check: can any state so far violate prop?
        solver.push();
        const neg_prop = Z3.Or(...states.map(s => Z3.Not(prop(s))));
        solver.add(neg_prop);
        const result = await solver.check();
        solver.pop();

        if (result === 'sat') {
            return extractCounterExample(solver.model(), states, k);
        }
    }
    return 'safe_up_to_k';
}
```

**k-Induction** (adds ~30% code on top of BMC): Add inductive step check after each BMC step.
If both BMC (UNSAT) and inductive step (UNSAT) hold, return Proved.

**IC3/PDR**: Significant implementation complexity (~500 LOC). Only implement if k-Induction
UNKNOWN occurs frequently. For most compliance-scale problems, k-Induction suffices.

**SMPT state equation** (simplest formal certificate, just a Z3 LIA query):
Implement as a standalone function: encode state equation + non-negativity → Z3 check.
Add P-invariants and trap refinement loop for stronger results.

---

## 9. Common Pitfalls

**Pitfall 1: BMC declared "verification" when it is only bounded bug-finding.**
BMC finding UNSAT up to k=10 does not mean the property holds for k=11 or any larger k.
Always label BMC results as "no counterexample found up to bound k" — not "property verified."
Use k-Induction or IC3/PDR for actual proofs.

**Pitfall 2: k-Induction UNKNOWN treated as "property might fail."**
UNKNOWN means the inductive step failed at this k — not that the property is false. The property
may still be true, but k-Induction could not prove it with this k and without auxiliary invariants.
Response: increase k, add auxiliary invariants, or switch to IC3/PDR.

**Pitfall 3: SMPT SAT result treated as a witness to reachability.**
The state equation gives a necessary condition, not sufficient. A satisfying assignment to the firing
count vector `x` does not correspond to a valid firing sequence in general (ordering constraints may
prevent it). The only meaningful SMPT result for verification is UNSAT (proves unreachability).
Add trap constraints to reduce spurious SAT results.

---

## 10. Key References

- Biere, A. et al. (1999). Symbolic model checking without BDDs. *TACAS 1999*. [BMC]
- Sheeran, M., Singh, S. & Stålmarck, G. (2000). Checking safety properties using induction and a SAT-solver. *FMCAD 2000*. [k-Induction]
- Bradley, A.R. (2011). SAT-based model checking without unrolling. *VMCAI 2011*. [IC3]
- Champion, A. et al. (2016). The Kind 2 model checker. *CAV 2016*.
- Amat, N. et al. (2023). SMPT: A testbed for reachability methods in Petri nets. *TACAS 2023*.
- Halbwachs, N. et al. (1992). Verification of linear hybrid systems using a property-based loop detection. *CHARME 1992*.
- de Moura, L. & Bjørner, N. (2008). Z3: An efficient SMT solver. *TACAS 2008*.
