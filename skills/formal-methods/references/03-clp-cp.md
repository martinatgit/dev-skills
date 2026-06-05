# Constraint Logic Programming and Constraint Programming

*Source: Jaffar_Lassez_CLP_Scheme.json, Triska_SWI_CLP_FD.json, Triska_CLPZ_Metalevel.json,
Schulte_Stuckey_Propagation_Engines.json, Schulte_Trailing_vs_Copying.json,
View_Based_Propagator_Derivation.json, MiniCP_Teaching_Solver.json,
Gecode_Constraint_Propagation_Book.json, Lazy_Clause_Generation.json, CHR_Constraint_Handling_Rules.json,
OR_Tools_CP_SAT_Architecture.json, clpfd-clpz-insights.md.*

---

## 1. CLP(X) Framework — Jaffar & Lassez 1987

**CLP(X)** (Constraint Logic Programming over domain X) is a generalization of Prolog where the
Herbrand domain H is replaced by an arbitrary constraint domain X. Prolog itself = CLP(H).

**Core idea**: Goals are either atoms (resolved by SLD) or **constraints** (sent to the constraint
store). A query succeeds if the constraint store is satisfiable at every step.

**CLP derivation step** (two cases):

```
Given: goal G, store CS, substitution σ

Case 1: G is a constraint c
    new_CS = CS ∪ {c·σ}
    if SATISFIABLE(new_CS):
        continue with remaining goals, store = new_CS
    else:
        FAIL (backtrack)

Case 2: G is an atom p(args)
    // SLD resolution: pick clause head p(params) :- body
    σ' = mgu(p(args), p(params))      // unification
    new_goals = body·σ'               // instantiate body
    new_CS = CS ∪ θ(σ')              // θ extracts constraint part from unifier
    if SATISFIABLE(new_CS):
        continue with new_goals, store = new_CS
    else:
        FAIL (backtrack)
```

**Residual constraint answers**: Instead of a single ground answer, CLP programs return a **residual
constraint**: the conjunction of constraints that characterizes the solution set.
Example: Query `X + Y #= 10` with no grounding returns `X + Y = 10` as the answer — all pairs
satisfying the equation are described.

**CLP(Z) vs CLP(FD)**:
- CLP(FD): Variables range over finite domains (integer intervals, e.g., 1..100). Standard SWI-Prolog library.
- CLP(Z): Variables range over all integers (unbounded). Metalevel reasoning possible. Triska 2013 PhD.

**Key insight**: CLP separates the search strategy (Prolog-style SLD resolution + backtracking)
from the constraint-solving algorithm (theory-specific). The solver handles arithmetic; Prolog handles
combinatorial search.

---

## 2. Propagator-Based Architecture

The core pattern of a modern CP solver:

```
┌────────────────────────────────────────────────────────┐
│  Search (labeling/branching)                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Propagation Engine (fixpoint loop)              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │  │
│  │  │ Propagator │  │ Propagator │  │ Propagator │ │  │
│  │  │  (all_diff) │  │ (element)  │  │  (sum)    │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘ │  │
│  │            shared domain store                   │  │
│  └──────────────────────────────────────────────────┘  │
│  Trailing / Copying (backtracking)                     │
└────────────────────────────────────────────────────────┘
```

**Propagator interface**:
```typescript
interface Propagator {
    propagate(): PropagationResult;  // SUBSUMED | ENTAILED | FAILED | SCHEDULED
    priority(): number;              // lower = higher priority; schedule cheap first
    subscribe(var: IntVar): void;    // receive events when domain changes
}
```

**Fixpoint engine** (Schulte & Stuckey 2008):
```
function propagation_fixpoint(queue: PriorityQueue<Propagator>):
    while queue is not empty:
        p = queue.dequeue_highest_priority()
        result = p.propagate()
        match result:
            FAILED:    return FAILURE          // domain wipe-out or unsatisfiability
            ENTAILED:  remove p from propagator set   // p is forever satisfied
            SCHEDULED: queue.enqueue(affected_propagators)
            SUBSUMED:  continue                // domain unchanged; no reschedule
    return CONSISTENT                          // fixpoint reached
```

**Event levels** (three tiers, coarsest to finest):
1. **GROUND** (val): Variable became ground (domain = {v}). Cheapest to trigger on; fewest events.
2. **BOUNDS** (bd): Lower or upper bound changed. Moderate frequency.
3. **DOMAIN** (dom): Any domain value removed. Finest; most events; most expensive propagators use selectively.

**Priority queue rationale**: Cheap propagators (e.g., `X > 0`) have lower cost and higher priority;
expensive propagators (e.g., `all_different` domain consistency) run only after bounds propagation
has narrowed domains.

---

## 3. Trailing — Backtracking Integration

Trailing is the standard backtracking mechanism for Prolog-based CLP solvers. When a domain modification
is made, the **previous value** is saved on a **trail** (undo stack). On backtrack, the trail is
rewound to the previous choice point.

```
Trail entry: { object, attribute, old_value }

function trail_push(trail, mark, obj, attr):
    old_value = obj[attr]
    trail.append({ obj, attr, old_value })
    // obj[attr] can now be modified freely

function backtrack_to(trail, mark):
    while trail.length > mark:
        entry = trail.pop()
        entry.obj[entry.attr] = entry.old_value   // undo modification
```

**Magic-number optimization** (Schulte empirical finding):
Naive trailing trails every domain modification individually, even multiple modifications per propagation
step. The magic-number optimization: associate each domain slot with a `last_trail_level`. If the
current level equals `last_trail_level`, the value is already trailed at this level — skip trailing.

```
function trail_if_new(trail, mark, obj, attr):
    if obj.trail_level[attr] < current_level:
        trail.append({ obj, attr, obj[attr] })
        obj.trail_level[attr] = current_level
    // Now safe to modify obj[attr]
```

Without this: if a propagator modifies `x.lower_bound` 3 times in one propagation step, it trails 3
entries. With magic-number: only 1 entry per choice-point-level. Exponential savings on busy propagation.

**Trailing vs. Copying**:
| | Trailing | Copying |
|---|---|---|
| Backtrack cost | O(trail entries since last CP) | O(heap size) |
| Forward propagation | O(actual modifications) | O(full state snapshot) |
| Memory | Small (just delta) | Large (full state per CP) |
| Best for | Prolog-style CLP, depth-first search | Parallel search, restarts |

Schulte's empirical finding: Trailing dominates on sequential depth-first search with shallow backtracks.
Copying is beneficial when restarts occur frequently or when parallelism requires independent states.

---

## 4. Domain Representations

**Selection guide table**:
| Representation | Storage | Removal | Best for |
|---|---|---|---|
| Interval tree (Triska) | O(n) nodes | O(log n) | Unbounded integer domains, CLP(Z/FD) |
| Sparse set (MiniCP) | O(max) | O(1) | Small finite domains, teaching implementations |
| Bit-set (32-bit) | 1 word | O(1) bitwise | Domains ≤ 32 values |
| Bounds-only | O(1) | O(1) | Pure bounds propagation; loses inner structure |

**Interval tree** (Triska SWI CLP(FD) representation):
Each domain is an interval tree with symbolic endpoints `inf`/`sup`:
```prolog
%% Internal domain representation:
from_to(From, To)        % single interval [From, To]
split(N, Left, Right)    % N is excluded; Left covers below N, Right covers above
```
Operations: `domain_remove_smaller_than(D, N, D')`, `domain_remove_larger_than(D, N, D')`,
`domain_subtract(D, N, D')` — all O(log n) in number of interval nodes.

Symbolic `inf`/`sup` represent ±∞. CLP(Z) uses these for open-ended integer domains — no bound forced.

**Termination guarantee** (Triska's flags): Without special care, propagation on unbounded domains can
loop forever (e.g., `X #> X - 1` is always satisfiable but creates infinitely narrowing bounds).
Triska uses three monotonicity flags on each constraint:
- **Left flag**: Constraint can only tighten lower bound of X (monotone from below)
- **Right flag**: Constraint can only tighten upper bound of X (monotone from above)
- **Spread flag**: Constraint's influence on X's bounds is bounded

When all flags are set, the propagator terminates even on unbounded domains. Without flags,
propagation on CLP(Z) may not terminate.

**Sparse set** (MiniCP):
```
values[0..size-1]  : the current domain values (active elements)
indices[v]         : position of v in values[] (for O(1) membership test)
size               : current number of domain values
```
Remove value v: swap `values[indices[v]]` with `values[size-1]`, update indices, decrement size.
Only `size` is trailed (not the arrays themselves — removal is O(1) undo by incrementing size).

---

## 5. Attributed Variables

Attributed variables are the mechanism by which CLP(FD) constraints attach to Prolog variables.

```prolog
%% SWI-Prolog attributed variable API:
put_attr(Var, Module, Value)  % attach attribute Value to Var under Module
get_attr(Var, Module, Value)  % retrieve attribute
del_attr(Var, Module)         % remove attribute

%% Called automatically when Var is unified with another term:
attr_unify_hook(Attr, Other)  % user-defined: check consistency after unification
```

**clpfd_attr structure** (Triska implementation):
Each CLP(FD) variable carries an attribute record containing:
- `dom`: The current domain (interval tree)
- `att`: Attached propagators (constraint list)
- `trail_level`: Magic-number trail level
- `flags`: Left/Right/Spread termination flags

**How unification interacts with CLP**:
When a CLP(FD) variable X is unified with a concrete integer N, `attr_unify_hook` is called.
The hook checks that N ∈ dom(X) and fires all propagators watching X for GROUND events.

---

## 6. Global Constraints

### 6.1 all_different — Hall Interval Bounds Consistency

Naive implementation: O(n²) pairwise ≠ constraints.
Efficient implementation: Hall's theorem + interval sorting (Régin 1994 / Leconte 1996).

**Hall's theorem**: A set S of values is "Hall-critical" if exactly |S| variables have domains
⊆ S. In that case, no variable outside the Hall set can take any value in S.

**Bounds consistency algorithm** (O(n log n)):
```
Sort variables by lower bound, by upper bound.
Identify Hall intervals [a, b] where |{vars: dom ⊆ [a,b]}| == b - a + 1.
For each Hall interval: remove [a,b] from domains of all other variables.
```
This achieves bounds consistency in O(n log n) per propagation call, vs O(n²) for pairwise.

### 6.2 element(Index, List, Value)

Bidirectional propagation (no single direction dominates):
- If Index is ground: dom(Value) = dom(List[Index])
- If Value domain is known: narrow Index to only indices i where List[i] ∩ dom(Value) ≠ ∅
- If some List[i] is fully eliminated from Value's domain: remove i from Index

Implement via subscription: propagate on Index GROUND event and Value DOMAIN event.

### 6.3 sum / scalar_product — Bounds Propagation

```
sum([X1, ..., Xn], Result)
bounds propagation:
  lb(Result) ≥ Σ lb(Xi)
  ub(Result) ≤ Σ ub(Xi)
  lb(Xi) ≥ lb(Result) - Σ_{j≠i} ub(Xj)   // propagate back to each Xi
  ub(Xi) ≤ ub(Result) - Σ_{j≠i} lb(Xj)
```

Recompute all bounds from scratch on each propagation call: O(n). Cache the sum/diff for O(1) updates.

### 6.4 table Constraint — Compact Table (CT) Algorithm

The `table` constraint restricts a tuple of variables to a set of allowed tuples.
Naive: O(|T| × n) per propagation. Compact Table (CT): O(|T| / word_size × n) using bit-sets.

**CT Algorithm — Two phases** (Demeulenaere et al. 2016):
```
Phase 1: Compute valid table T' = {t ∈ T : t[i] ∈ dom(Xi) for all i}
    // T' = set of tuples still compatible with current domains

Phase 2: Update domains from T'
    for each variable Xi:
        dom(Xi) = {v : ∃t ∈ T' with t[i] = v}  // keep only values in some valid tuple
```

**Compact Table uses reversible sparse bit-sets**:
- Each tuple t ∈ T is stored as a bit in a word array.
- `valid_tuples` bit-set: bit j = 1 iff tuple j is still valid.
- Phase 1: `valid_tuples &= domain_mask[i][v]` for each assigned variable.
  `domain_mask[i][v]` = bit-set of tuples where position i has value v (precomputed).
- Phase 2: `dom(Xi) = {v : (domain_mask[i][v] & valid_tuples) ≠ 0}`.

**Word-level parallelism**: 64 tuples processed per bit-AND operation. On dense tables, this is
the fastest known table propagation algorithm. Reversible bit-sets: only `valid_tuples.size` is trailed.

---

## 7. Views — Zero-Cost Propagator Derivation

**Problem**: `X + 3 ≤ Y` requires a different propagator from `X ≤ Y`. Without views, this means
writing separate propagator code for every linear transformation.

**Solution**: A **view** is a lightweight adapter that makes variable X appear as `X + offset`,
`-X`, `c × X`, etc. to a propagator. The propagator is written once for a generic `V` and used
for all view types.

**View interface**:
```typescript
interface IntView {
    min(): number;
    max(): number;
    removeBelow(v: number): void;   // remove values < v
    removeAbove(v: number): void;   // remove values > v
    subscribe(event: EventType, propagator: Propagator): void;
}

class IntVar implements IntView { /* direct access to domain */ }

class OffsetView implements IntView {
    constructor(private x: IntVar, private offset: number) {}
    min(): number { return this.x.min() + this.offset; }
    max(): number { return this.x.max() + this.offset; }
    removeBelow(v: number): void { this.x.removeBelow(v - this.offset); }
    removeAbove(v: number): void { this.x.removeAbove(v - this.offset); }
    subscribe(e, p) { this.x.subscribe(e, p); }
}

class MinusView implements IntView {
    constructor(private x: IntVar) {}
    min(): number { return -this.x.max(); }
    max(): number { return -this.x.min(); }
    removeBelow(v: number): void { this.x.removeAbove(-v); }
    removeAbove(v: number): void { this.x.removeBelow(-v); }
    subscribe(e, p) { this.x.subscribe(e, p); }
}

class ScaleView implements IntView {
    constructor(private x: IntVar, private scale: number) {}
    min(): number { return this.x.min() * this.scale; }
    max(): number { return this.x.max() * this.scale; }
    removeBelow(v: number): void { this.x.removeBelow(Math.ceil(v / this.scale)); }
    removeAbove(v: number): void { this.x.removeAbove(Math.floor(v / this.scale)); }
    subscribe(e, p) { this.x.subscribe(e, p); }
}
```

**Result**: A single `LessEqualPropagator<V0 extends IntView, V1 extends IntView>` handles all of:
`X ≤ Y`, `X + 3 ≤ Y`, `-X ≤ Y`, `2X ≤ Y + 1`, etc. **4.5× code reduction** in Gecode.

**TypeScript note**: V8 does not specialize generic types like C++ templates. Runtime type erasure
means the code-reduction benefit is preserved but the performance benefit is smaller. Use concrete
implementations when inner loops are performance-critical; use views for correctness first.

---

## 8. Lazy Clause Generation (LCG)

LCG (Ohrimenko, Stuckey & Codish, 2009) embeds a CDCL SAT engine inside a CLP(FD) solver.
Implemented in Chuffed (MiniZinc competition winner). Key insight: FD propagation ≈ theory
propagation in CDCL(T); domain prunings can generate clausal explanations.

**Order encoding**:
For variable x with domain {1..n}: introduce Boolean literals `[[x ≤ d]]` for d = 1..n-1.
- `[[x ≤ d]] → [[x ≤ d+1]]` (structural implication chains — added once at setup)
- `[[x ≤ d]] = false` means `x ≥ d+1` (lower bound raised above d)
- `[[x ≤ d]] = true` means `x ≤ d` (upper bound at most d)

**Core LCG loop**:
```
function LCG_propagation_fixpoint():
    loop:
        // SAT unit propagation
        sat_result = BCP(order_encoding_clauses, trail)
        if sat_result is Conflict(c): return Conflict(c)

        // FD propagation
        for each propagator p in queue:
            dom_changes = p.propagate()
            for each (var, old_bound, new_bound) in dom_changes:
                explanation = p.explain(var, old_bound)
                // explanation = clause over order literals
                add_clause(explanation, trail)
                trail.push(unit from explanation)
        if queue is empty: return CONSISTENT
```

**Propagator explain() method**:
When propagator p prunes x's lower bound to d+1 (asserts `[[x ≤ d]] = false`), it must produce:
```
explain(x, d) → {[[y ≤ ky]], [[z ≤ kz]], ...}   // order literals that caused the pruning
```
The resulting clause is: `[[x ≤ d]] ∨ ¬[[y ≤ ky]] ∨ ¬[[z ≤ kz]] ∨ ...`
This becomes a clause in the SAT engine — if the RHS literals are all true, then x's bound must be raised.

**Why LCG works**: Non-chronological backjumping in the SAT layer skips irrelevant subtrees.
Clause learning prevents re-deriving the same bound prunings. Result: 1–2 orders of magnitude faster
than pure propagation on hard combinatorial problems (scheduling, planning, bin packing).

**When to use LCG vs pure propagation**:
- LCG: Hard problems with many backtracks, where nogood learning provides significant pruning.
- Pure propagation: Simple problems where search tree is shallow; LCG overhead not justified.
- OR-Tools CP-SAT always uses LCG internally — just use it for hard problems.

---

## 9. Constraint Handling Rules (CHR)

CHR (Frühwirth, 1998) is a declarative rule language for writing constraint solvers. CHR rules
transform constraint stores — they are an excellent tool for implementing custom CP propagators
or rewrite-based reasoning.

**Three rule types**:

```prolog
% Simplification: remove lhs constraints, add rhs
X ≤ Y, Y ≤ X <=> X = Y.          % anti-symmetry: X≤Y ∧ Y≤X simplifies to X=Y

% Simpagation: keep head₁, remove head₂, add body
X ≤ Y \ X ≤ Y <=> true.          % remove duplicate constraints (first ≤ kept)

% Propagation: keep all constraints, add new ones
X ≤ Y, Y ≤ Z ==> X ≤ Z.         % transitivity: add X≤Z (without removing X≤Y, Y≤Z)
```

**Operational semantics (ω_r)**:
1. Wake all rules with matching head
2. Apply first matching rule (check guard if present)
3. Commit (no backtracking over rule choice — deterministic)
4. Recurse until no rule applies (fixpoint)

**Confluence analysis**: A CHR program is confluent if all rule orderings produce the same result.
Joinability: for any pair of rules that both apply to the same store, applying either order leads to
the same final store. Confluence is decidable for restricted CHR (no guards); undecidable in general.

**Propagation history**: To prevent infinite derivation loops in propagation rules
(`X ≤ Y, Y ≤ Z ==> X ≤ Z` applied to the new `X ≤ Z` would add it again), each propagation rule
application is recorded in a history set. A rule application `(c1, c2) → c3` is only performed if
`(c1, c2) ∉ history`.

**CHR in TypeScript (CHR.js)**:
```javascript
const chr = new CHR();
chr.rule('leq-reflexivity').simplification()
    .head('leq', (X, X) => true)    // X ≤ X
    .body(() => []);                 // → true (remove)

chr.rule('leq-antisymmetry').simplification()
    .head('leq', (X, Y) => true, 'leq', (Y, X) => true)  // X≤Y ∧ Y≤X
    .body(() => [['eq', X, Y]]);                            // → X=Y
```

**Implementation estimate**: ~1000–2000 LOC for a basic CHR runtime in TypeScript (without JIT
optimization). Suitable for compliance rules where expressibility > raw performance.

---

## 10. OR-Tools CP-SAT Architecture

CP-SAT (Google, 2018+) is the state-of-the-art open-source CP solver. It is the dominant force in
the MiniZinc Challenge. Architecture: portfolio of workers sharing a common propagation core.

**Core**: LCG (Section 8) with an embedded SAT solver (see Section 8 for LCG details).

**Portfolio workers**:
- **Core worker**: LCG with VSIDS-style heuristics + restarts.
- **LP worker**: Continuous relaxation (LP via GLOP). LP bound strengthens SAT assignment via cuts.
- **LNS workers**: Large Neighborhood Search — fix most variables, re-solve sub-problem. Multiple
  LNS workers with different fixing strategies run in parallel.
- **Full BFS worker**: Breadth-first search for proving infeasibility quickly.

**Presolve**:
Before search, CP-SAT applies aggressive preprocessing:
- Bound tightening via constraint propagation to fixpoint
- Variable elimination (substitute out variables appearing in only one constraint)
- Symmetry breaking
- Constraint simplification (merge overlapping constraints)

**When to use OR-Tools instead of building**:
- Problem has >1000 variables or >10,000 constraints: use OR-Tools.
- Need parallelism: OR-Tools portfolio is production-grade.
- Need optimization (minimize/maximize): OR-Tools has excellent branch-and-bound.
- Build your own for: learning, custom constraint types requiring non-standard propagation, integration
  with a language runtime where FFI overhead matters.

**Integration (TypeScript)**:
OR-Tools has no official TypeScript/WASM binding. Options:
- `@google-or-tools/or-tools`: Unofficial WASM binding.
- REST microservice: Run OR-Tools in Python/C++ subprocess, communicate via JSON.
- Z3 with nuZ: For optimization with compliance-scale problems (<1000 variables), Z3 Optimize is adequate.

---

## 11. Labeling Heuristics

Labeling is the search strategy — which variable to branch on next, and in what order.

| Strategy | Variable selection | Value order | When to use |
|---|---|---|---|
| leftmost | First variable in list | Min first | Testing; baseline |
| ff (first-fail) | Smallest domain | Min first | General-purpose; usually best default |
| ffc | Smallest domain / most constraints | Min first | Heavily constrained problems |
| bisect | Smallest domain | Split at midpoint | Large numeric domains |
| impact | By historical impact on domain reduction | Historical | Large scheduling problems |
| random | Random | Random | Diversification; complement to LNS |

**First-fail principle**: Branch on the variable most likely to fail (smallest domain). Fail early,
backtrack early, discover infeasibility fast.

**Value ordering**: For satisfiability, try the value most likely to be consistent (e.g., median of
domain). For optimization, try the value moving the objective in the right direction.

---

## 12. Reification

Reification creates a Boolean bridge between a constraint and a Boolean variable:

```prolog
X #> 5 #<==> B.   % B = 1 iff X > 5 holds; B = 0 iff X ≤ 5 holds
```

**Essential for**: Conditional constraints (if-then rules), counting constraints
(`at_most(N, [C1, C2, ...])` where each Ci is a reified constraint), disjunctive constraints.

**Half-reification**: Propagate only one direction — either enforce constraint from B=1, or set B=0
from constraint failure. Full reification is bidirectional. Half-reification is cheaper and sufficient
for many compliance modeling patterns.

**TypeScript implementation**:
```typescript
class Reification implements Propagator {
    constructor(
        private b: BoolVar,
        private inner: Propagator,
        private mode: 'full' | 'half-forward' | 'half-backward'
    ) {}

    propagate(): PropagationResult {
        if (this.b.isTrue()) {
            return this.inner.propagate();              // forward: enforce inner
        } else if (this.b.isFalse()) {
            return this.inner.propagateNegation();      // backward: enforce ¬inner
        } else {
            // Check if inner is entailed → B must be 1
            if (this.inner.isEntailed()) this.b.setTrue();
            // Check if inner fails → B must be 0
            if (this.inner.isFailed()) this.b.setFalse();
        }
        return CONSISTENT;
    }
}
```

---

## 13. Proof Logging (VeriPB)

CP solvers can generate independently checkable proofs of unsatisfiability or optimality.

**VeriPB proof system** (Gocht et al. 2020): Based on pseudo-Boolean reasoning. An order encoding
of FD domains maps naturally to pseudo-Boolean constraints. Proof steps include:
- `pol`: Polarity (derive from existing constraints by linear combination)
- `rup`: Reverse Unit Propagation (verify by unit propagation in negated form)
- `del`: Delete a constraint (with justification)

**Certifying solvers**: Pumpkin (Pon Dries 2023) generates VeriPB proofs for all propagation steps.
The proof is checked by VeriPB, providing a mathematical certificate that the answer is correct.

**Why this matters**: For compliance applications, a proof certificate means the "UNSAT" answer
(no valid assignment exists for these regulations) is independently auditable — essential for legal defensibility.

---

## 14. TypeScript Performance Reality

Raw propagation performance in TypeScript:
- **10–100× slower** than C++ (Gecode) for tight propagation loops.
- **Why acceptable**: Compliance-scale problems (< 1000 variables, < 10,000 constraint evaluations
  per second required) stay within TypeScript's budget. Hard scheduling problems (>10,000 variables)
  belong on C++/OR-Tools.

**Key optimizations for TypeScript**:
- **Avoid allocation in propagation loops**: Pre-allocate domain arrays; reuse buffers.
  Use `Int32Array` instead of `number[]` for domain storage.
- **32-bit bitwise operations**: JavaScript uses 32-bit signed integers for bitwise ops (`|`, `&`, `~`).
  Bit-set domains limited to 32 values without multi-word handling.
- **V8 inline caches**: Keep propagator classes monomorphic (same object shapes). Avoid prototype chain
  polymorphism in hot loops.
- **Sparse set over interval tree**: For small fixed domains (<100 values), sparse set gives O(1)
  removal with less overhead than interval tree operations.

---

## 15. Implementation Strategies (Priority-Ordered)

**P0 — Core engine** (must have for a functional CLP solver):
- Interval-based domain representation with `removeBelow`/`removeAbove`
- Trailing with magic-number optimization
- Fixpoint propagation engine with priority queue
- `all_different` (bounds) + `element` + `sum`/`scalar_product` (bounds)
- Basic labeling (first-fail)

**P1 — Essential global constraints**:
- Reification (enables conditional constraints)
- `table` constraint (CT algorithm for efficient extensional constraints)
- Views (OffsetView, MinusView, ScaleView)

**P2 — Advanced features** (if needed):
- CHR runtime (if rule-based constraint specification is required)
- LCG integration (if hard combinatorial instances with many backtracks appear)

**P3 — Production scale** (if required):
- OR-Tools integration (for problems exceeding TypeScript's performance budget)
- Proof logging (for auditable compliance verdicts)

---

## 16. Common Pitfalls

**Pitfall 1: Missing magic-number optimization in trailing.**
Without it, multiple modifications to the same domain attribute in one propagation step each add a
trail entry. On backtrack, all entries are replayed, but only the last value matters. This creates
an exponential explosion on problems with many domain modifications per choice-point level. Fix:
implement magic-number check (`trail_level[attr] < current_level`) before every trail push.

**Pitfall 2: Not rescheduling affected propagators after domain change.**
If a propagator modifies variable X's domain but does not schedule all propagators subscribed to X,
those propagators miss the event. The propagation becomes incomplete — the solver may return a
"satisfying" assignment that actually violates constraints. Fix: every domain modification must
trigger the event system, which enqueues all subscribed propagators.

**Pitfall 3: No termination guarantee on unbounded CLP(Z) domains.**
A propagator that repeatedly narrows X's lower bound without a floor (e.g., `X #> X - 1`)
will loop forever on an unbounded domain. Fix: Triska's Left/Right/Spread monotonicity flags.
Before posting a propagator, prove it satisfies at least one flag. If a custom propagator cannot
be shown to satisfy any flag, add explicit bound guards or limit the domain to a finite range.

---

## 17. Key References

- Jaffar, J. & Lassez, J.-L. (1987). Constraint logic programming. *POPL 1987*.
- Schulte, C. & Stuckey, P.J. (2008). Efficient constraint propagation engines. *TOPLAS*, 31(1).
- Triska, M. (2012). The finite domain constraint solver of SWI-Prolog. *FLOPS 2012*.
- Triska, M. (2013). *The Power of Prolog: Metalevel Information in Constraint Logic Programming*. PhD thesis.
- Michel, L. et al. (2021). MiniCP: A lightweight solver for constraint programming. *ORIJ*.
- Feydy, T. & Stuckey, P.J. (2009). Lazy clause generation reengineered. *CP 2009*.
- Frühwirth, T. (1998). Theory and practice of constraint handling rules. *JLP*, 37(1-3).
- Demeulenaere, J. et al. (2016). Compact-table: Efficiently filtering table constraints with reversible sparse bit-sets. *CP 2016*.
- OR-Tools CP-SAT: https://developers.google.com/optimization/reference/python/sat/python/cp_model
