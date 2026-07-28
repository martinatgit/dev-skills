# SMT Solving and Z3

*Source: Z3_SMT_Solver_Architecture.json, Z3_Theory_Solvers.json, Nelson_Oppen_Theory_Combination.json,
Z3_UserPropagator_API.json, Z3_Optimization_nuZ.json, Z3_TypeScript_WASM_Bindings.json,
SMT_LIB_Standard.json, Programming_Z3_Tutorial.json, CDCL_T_Framework.json.*

---

## 1. What is SMT?

**Satisfiability Modulo Theories (SMT)** extends SAT to handle formulas containing:
- Integer and real arithmetic (e.g., `x + 2*y ≤ 15`)
- Arrays (`a[i] = b[j]`)
- Uninterpreted functions (`f(x) = f(y) → x = y`)
- Bit-vectors, strings, algebraic datatypes, and more

An SMT formula is satisfiable iff there exists an interpretation of theory variables that makes it
true under the theory axioms (e.g., the standard axioms of linear arithmetic).

**Architecture**: Two-level system:
- **SAT core**: Handles Boolean structure, clause learning, non-chronological backtracking (CDCL)
- **Theory solvers**: Plug-in modules that check consistency of theory-level atoms

The SAT core treats theory atoms (like `x + y ≤ 5`) as opaque Boolean variables. Theory solvers only
need to answer: "Is this conjunction of theory literals consistent with the theory?"

---

## 2. CDCL(T) Architecture — Full Main Loop

```
function CDCL_T(formula):
    (bool_formula, atom_map) = abstract(formula)
    // atom_map: Boolean var bₙ ↔ theory atom (e.g., x+y≤5)
    trail = []; level = 0; clauses = bool_formula
    for each T_solver: T_solver.init()

    loop:
        // Phase 1: Boolean Constraint Propagation (BCP)
        conflict = BCP(clauses, trail)
        if conflict != NULL:
            if level == 0: return UNSAT
            (learned, bt_level) = analyze_1UIP(conflict, trail)
            add_clause(clauses, learned)
            backtrack_to(trail, bt_level)
            for each T_solver: T_solver.pop_to(bt_level)
            level = bt_level
            continue

        // Phase 2: Theory Propagation (T-propagation)
        for each T_solver:
            new_lits = T_solver.propagate()          // cheap, incomplete
            for (lit, reason) in new_lits:
                trail.push(Propagated(lit, level, reason))

        // Phase 3: Theory Consistency Check (T-check)
        for each T_solver:
            result = T_solver.check()                // complete consistency
            if result is Conflict(explanation):
                theory_clause = clausify(explanation) // theory lemma
                add_clause(clauses, theory_clause)
                continue outer_loop  // BCP will see conflict

        // Phase 4: Decision
        if all_assigned(trail): return SAT
        level += 1
        lit = VSIDS_pick(trail)
        trail.push(Decision(lit, level))
        for each T_solver:
            T_solver.push()
            T_solver.assert_atom(atom_map[lit])
```

**Theory solver interface**:
```
interface TheorySolver:
    init()
    assert_atom(literal)                        // fast, may detect conflict
    check() → SAT | Conflict(explanation)       // full consistency check
    propagate() → [(literal, explanation)]      // T-deduce new literals
    explain_propagation(literal) → clause       // lazy: only called in conflict analysis
    push()                                      // save state at decision level
    pop()                                       // restore state on backtrack
    get_model() → assignment                    // extract model after SAT
```

**Explanation clauses are critical**: When a theory solver reports a conflict, it must return a
minimal subset of currently-asserted theory literals whose conjunction is T-inconsistent. These
become propositional learned clauses — the bridge between theory reasoning and CDCL learning.

---

## 3. EUF Congruence Closure — The Blackboard

**Equality and Uninterpreted Functions (EUF)** is the central theory in Z3 because all other theory
solvers communicate through equality. The EUF solver implements **congruence closure** via an
**E-graph** (union-find + signature table).

**Data structures**:
- `uf`: Union-Find (disjoint sets). `uf.find(a)` = representative of a's equivalence class.
- `sig`: Signature table: maps `(f, rep(arg₁), ..., rep(argₙ))` → node.

```
function merge(a, b, reason):
    ra = uf.find(a); rb = uf.find(b)
    if ra == rb: return            // already in same class

    // Union the two classes
    uf.union(ra, rb)               // merge smaller into larger (union by rank)
    pending_merges = []

    // Check for newly congruent function applications
    for each function application f(args) in class of ra:
        sig_key = (f, map(uf.find, args))
        if sig_key in sig_table:
            other = sig_table[sig_key]
            pending_merges.append((f(args), other))  // congruence: same sig → same value
        else:
            sig_table[sig_key] = f(args)

    for (x, y) in pending_merges:
        merge(x, y, "congruence")  // recursive: new equalities may cause further merges
```

**When `a = b` is asserted**: `merge(a, b, reason)` is called.
**Congruence closure**: If `a = b` holds and we have `f(a)` and `f(b)`, the signature table finds
that both map to the same key after union, and `f(a) = f(b)` is derived automatically.

**Backtracking**: Union-find with path compression is not naturally backtrackable. Z3 uses an
explain-based approach: on backtrack, undo unions by recording the merge history in a stack.

---

## 4. Theory Solvers — Per-Domain Details

### 4.1 Linear Integer Arithmetic (QF_LIA) — DECIDABLE

**Algorithm**: Dual simplex for the real relaxation (QF_LRA). For integer case: Gomory cuts +
branch-and-bound. Omega test for Presburger arithmetic (quantified integer arithmetic).

**Decidability**: QF_LIA: NP-complete. QF_LRA: Polynomial (LP / simplex).

**Domain**: Linear inequalities over integers: `a₁x₁ + ... + aₙxₙ ≤ b`, `a₁x₁ + ... = b`.

**Primary use for formal verification**: Compliance constraints (deadline counting, threshold checks),
Petri net state equations (`m = m₀ + C·x`), loop invariant arithmetic.

**Dual simplex for incremental solving**: Theory solver maintains simplex tableau. On assert of new
constraint: add row to tableau, pivot to maintain feasibility. T-propagation: detect implied bounds
on variables from the tableau. Backtrack: undo pivots (expensive — use Z3's push/pop carefully).

### 4.2 Non-Linear Arithmetic (QF_NIA / QF_NRA)

**QF_NRA** (non-linear real arithmetic): nlsat algorithm (cylindrical algebraic decomposition — CAD).
**Decidable**. Complexity: doubly exponential (2-EXP) in number of variables.

**QF_NIA** (non-linear integer arithmetic): **Undecidable** in general. Z3 uses heuristics
(linearization, bit-blasting, model-based quantifier elimination) — **not complete**. May return
`unknown`.

**WARNING: QF_NIA is a performance cliff.** If your formula involves multiplication of two
non-constant variables (`x * y` where both are symbolic), you have QF_NIA. Avoid it: restructure
the problem to QF_LIA if at all possible.

### 4.3 Arrays (QF_AX)

**Theory axioms**:
- `select(store(a, i, v), i) = v` (read from written index returns written value)
- `i ≠ j → select(store(a, i, v), j) = select(a, j)` (read from other index unchanged)
- Extensionality: `(∀i. a[i] = b[i]) → a = b`

**Algorithm**: Lazy axiom instantiation — only instantiate array axioms when a conflict requires it.
**Decidable** for quantifier-free fragment.

**Warning**: Quantified array axioms (`∀i. a[i] ≥ 0`) make the formula semi-decidable — Z3 uses
E-matching heuristics which are incomplete.

### 4.4 Bit-Vectors (QF_BV)

**Algorithm**: Bit-blasting — encode each bit-vector operation as a Boolean circuit, then solve with
the SAT core. Word-level reasoning for simpler cases.

**Decidable**. Complexity: NP-complete (in number of bits). Exponential in bit-width for some
operations (e.g., multiplication, division).

**Use for**: Hardware verification, low-level protocol modeling, overflow checking.

### 4.5 Strings and Sequences (QF_S)

**Algorithm**: Word equations (Liang-Reger-Tinelli), length abstraction, regular expression
derivatives. Nielsen transformation for simple equations.

**Decidability**: Fragment covering word equations is decidable (Makanin 1977, DEXPTIME). Full
string theory with length and regex is **semi-decidable** — complete algorithms are not yet practical.
Z3 handles many practical cases but can return `unknown`.

### 4.6 Algebraic Datatypes (QF_DT)

**Axioms**: Constructor injectivity (`cons(h₁, t₁) = cons(h₂, t₂) → h₁ = h₂ ∧ t₁ = t₂`),
constructor disjointness (`cons(h, t) ≠ nil`), acyclicity (no circular values possible).

**Algorithm**: Congruence closure (via EUF) + acyclicity (occurs check).
**Decidable**. Useful for term-structure reasoning: ASTs, parse trees, rule terms.

---

## 5. Nelson-Oppen Theory Combination

When a formula mixes multiple theories (e.g., LIA + EUF + Arrays), each theory solver operates
on its own signature. The **Nelson-Oppen framework** (1979) allows them to cooperate.

**Step 1 — Purification**: Introduce fresh variables for "alien" subterms.
```
Formula: f(x + 1) = g(y)  ∧  x + 1 ≥ 5
                                ↓ purification
LIA atoms: z = x + 1, z ≥ 5     (z is fresh)
EUF atoms: f(z) = g(y)
```
After purification: each theory solver sees only atoms from its own signature.

**Step 2 — Equality sharing**: Run to fixpoint.
```
repeat:
    for each theory T:
        equalities_T = T.deduced_equalities_between_shared_vars()
        for each (a = b) in equalities_T:
            if not already shared:
                assert (a = b) to all other theories
until no new equalities
```

**Step 3 — Non-convex theories**: For theories where equality propagation is not complete
(LIA, BV — non-convex: knowing x ≠ y doesn't determine which of x < y or x > y holds without
case splitting), CDCL provides the case split via the Boolean layer.

**Convex theories** (EUF, LRA, QF_AX): Deterministic equality sharing, polynomial overhead.
**Non-convex theories** (LIA, BV): Require case splits via CDCL — exponential worst case.

**Critical pitfall**: If purification is skipped, theory solvers receive malformed input — alien
subterms cause incorrect results. Always purify before theory dispatch.

---

## 6. UserPropagator API — Custom Theory Plugins

Z3 exposes `UserPropagator` to let you extend CDCL(T) with custom constraint logic.

**Callbacks** (Python API — TypeScript via WASM follows same pattern):
```python
class MyPropagator(z3.UserPropagatorBase):

    def push(self):
        # Save state: called when Z3 makes a new decision (increases decision level)
        self.state_stack.append(copy(self.current_state))

    def pop(self, num_scopes):
        # Restore state: called on backtrack, pop num_scopes levels
        for _ in range(num_scopes):
            self.current_state = self.state_stack.pop()

    def fixed(self, x, val):
        # Z3 assigned variable x = val (a concrete value)
        # Run custom propagation logic here
        consequence = self.custom_propagate(x, val)
        if consequence is None:
            return  # no new information
        # Report a propagated consequence with justification
        self.propagate(consequence, [x], [])

    def final(self):
        # Called when all Boolean variables are assigned, no conflict yet
        # Completeness check: if a constraint is violated, report conflict here
        if self.has_violation():
            self.conflict([self.violating_var], [])
```

**Conflict reporting**:
```python
self.conflict([x, y], [])  # x and y's current values lead to conflict
# Z3 adds the negation of these assignments as a learned clause
```

**Propagation**:
```python
self.propagate(consequence_expr, [justifying_var1, justifying_var2], [])
# Z3 adds consequence as an implied literal with the given antecedents
```

**Use case**: Implement constraints that don't fit Z3's built-in theories — e.g., Petri net firing
semantics (token conservation), custom temporal constraints, domain-specific rules.

**Requirements**:
- `push()` / `pop()` must correctly save/restore ALL custom state. Missing this causes state to
  leak across backtracks → **incorrect results** (not just performance degradation).
- `fixed()` must be **idempotent**: may be called multiple times for the same assignment.
- `final()` is the completeness checkpoint: if your custom constraint can only be fully checked when
  all variables are assigned, check here.

---

## 7. nuZ — Optimization (MaxSMT)

Z3's `Optimize` class (not `Solver`) for weighted MaxSMT and lexicographic/Pareto optimization.

```python
from z3 import *
o = Optimize()

x = Int('x'); y = Int('y')

# Hard constraints: must be satisfied
o.add(x >= 0, y >= 0, x + y <= 10)

# Soft constraints: maximize sum of satisfied weights
o.add_soft(x >= 5, weight=3, id="c1")   # prefer x >= 5, weight 3
o.add_soft(y >= 4, weight=2, id="c2")   # prefer y >= 4, weight 2

# Optimization objective
h = o.maximize(x + y)                    # or minimize(...)

if o.check() == sat:
    print(o.model())                      # optimal model
    print(o.lower(h), o.upper(h))        # bounds on objective
```

**Modes**:
- **MaxSMT**: Maximize the total weight of satisfied soft constraints. Useful for "find the
  minimum-violation assignment" (e.g., which rules can we satisfy given conflicting facts?).
- **Lexicographic**: Prioritized objective list — optimize first objective, then second subject to
  first being optimal, etc.
- **Pareto**: Enumerate Pareto-optimal solutions (no solution is strictly better on all objectives).

**Compliance use case**: Assert regulations as hard constraints; assert facts as soft constraints with
`weight = cost_of_violation`. `o.check()` produces the assignment with minimal total violation cost.
`o.unsat_core()` (on the hard constraints) identifies which rules are mutually contradictory.

---

## 8. SMT-LIB2 Syntax Reference

Standard interface for all SMT solvers (Z3, CVC5, Yices, MathSAT):

```smt2
; Setup
(set-logic QF_LIA)                        ; declare background theory FIRST
(set-option :produce-models true)
(set-option :produce-unsat-cores true)

; Variable declarations
(declare-const x Int)
(declare-const y Int)
(declare-fun f (Int Int) Int)             ; uninterpreted function

; Assertions
(assert (>= x 0))
(assert (>= y 0))
(assert (! (<= (+ x y) 10) :named c1))   ; named assertion for unsat core

; Incremental solving
(push 1)                                  ; save state
(assert (>= x 6))
(check-sat)                               ; check augmented formula
(pop 1)                                   ; restore state

; Results
(check-sat)                               ; sat | unsat | unknown
(get-model)                               ; model satisfying assignment
(get-unsat-core)                          ; minimal unsat subset (named assertions)
(get-value ((+ x y)))                     ; evaluate expression in model
```

**Critical rule**: Always call `(set-logic ...)` before any `declare-*` or `assert`. This enables
solver-specific optimizations and theory-specific preprocessing. Common mistake: omitting set-logic
causes Z3 to use the most general (and slowest) solver configuration.

---

## 9. Z3 TypeScript/WASM API

```typescript
import { init } from 'z3-solver';

// One-time initialization (cache this — WASM load ~1-3s)
const { Context } = await init();
const Z3 = Context('main');

// Variables
const x = Z3.Int.const('x');
const y = Z3.Int.const('y');

// Solver setup
const solver = new Z3.Solver();
solver.add(x.ge(Z3.Int.val(0)));
solver.add(y.ge(Z3.Int.val(0)));
solver.add(x.add(y).le(Z3.Int.val(10)));

// Check
const result = await solver.check();    // 'sat' | 'unsat' | 'unknown'
if (result === 'sat') {
    const model = solver.model();
    const xVal = model.eval(x);         // Z3 expression → concrete value
}

// Incremental solving (push/pop)
solver.push();
solver.add(x.ge(Z3.Int.val(6)));
const result2 = await solver.check();
solver.pop();

// Optimization
const opt = new Z3.Optimize();
opt.add(x.ge(Z3.Int.val(0)));
opt.addSoft(x.ge(Z3.Int.val(5)), '3'); // soft constraint, weight 3
opt.maximize(x);
await opt.check();
```

**Term→Z3 bridge pattern** (for compiling a DSL to Z3):
```typescript
function termToZ3(term: Term, ctx: Z3Context): Z3.Expr {
    switch (term.type) {
        case 'var':      return ctx.Int.const(term.name);
        case 'num':      return ctx.Int.val(term.value);
        case 'add':      return termToZ3(term.left, ctx).add(termToZ3(term.right, ctx));
        case 'mul':      return termToZ3(term.left, ctx).mul(termToZ3(term.right, ctx));
        case 'leq':      return termToZ3(term.left, ctx).le(termToZ3(term.right, ctx));
        case 'and':      return ctx.And(termToZ3(term.left, ctx), termToZ3(term.right, ctx));
        // ...
        default: throw new Error(`Unknown term type: ${term.type}`);
    }
}
```

**Performance characteristics**:
- WASM load: 1–3s first call; cache `Context` object across calls.
- Small problems (<100 constraints, QF_LIA): <50ms solve time.
- WASM overhead vs native Z3: 2–5×.
- `SharedArrayBuffer` required in browsers (needs COOP/COEP response headers).
- Node.js 16+: works without SharedArrayBuffer.

**Assumption literals** (faster than push/pop for many assumptions):
```typescript
const p = Z3.Bool.const('assumption_p');
solver.add(p.implies(x.ge(Z3.Int.val(5))));
// Check with assumption p=true:
const result = await solver.check([p]);   // assumption-based check; no push/pop overhead
```

---

## 10. Decidable Fragment Quick Reference

| Fragment | Decidable? | Complexity | Primary use |
|---|---|---|---|
| QF_LIA | Yes | NP-complete | Integer compliance constraints, Petri net state equations |
| QF_LRA | Yes | Polynomial (LP/simplex) | Real-valued thresholds, continuous domains |
| QF_NRA | Yes | 2-EXP (CAD) | Polynomial real constraints — use sparingly |
| QF_NIA | Incomplete | — | Heuristic only; set timeout; use QF_LIA when possible |
| QF_BV | Yes | NP-complete | Bit manipulation, hardware verification |
| QF_UF (EUF) | Yes | NP-complete | Symbolic equality, uninterpreted functions |
| QF_AX | Yes | NP-complete | Quantifier-free arrays |
| QF_AUFLIA | Yes | NP-complete | Arrays + integer arithmetic |
| LIA (Presburger) | Yes (decidable) | 2-EXP | Quantified integer arithmetic — rare |
| First-order LIA | Semi-decidable | — | Full first-order: no termination guarantee |

**Decision rule**: Before picking a fragment, identify the decidable subset. QF_LIA is the
workhorse for compliance verification. Any multiplication of two symbolic variables → QF_NIA → trouble.

---

## 11. Implementation Strategies (Priority-Ordered)

1. **Use QF_LIA for all integer compliance constraints** — it is decidable, NP-complete, and Z3
   handles practical instances in milliseconds. Avoid QF_NIA: the performance drop is 100×–1000×
   even for small instances.
2. **Use push/pop for incremental exploration** — when solving many related problems (e.g., per-tick
   constraint checking in a reactive runtime), push/pop avoids re-encoding shared prefix.
   For many independent assumptions, use assumption literals instead (lower overhead).
3. **Set timeouts and rlimits in production** — Z3 can diverge on hard fragments.
   `solver.set('timeout', 5000)` (5s). Always handle `'unknown'` as a possible result.
4. **Enable unsat cores** — `(set-option :produce-unsat-cores true)` with named assertions enables
   `(get-unsat-core)`. Essential for compliance debugging: identifies the minimal set of conflicting
   rules. Incurs ~10–20% overhead.
5. **UserPropagator: implement push/pop as an explicit stack** — use `Array<State>` and push/pop
   indices. Never store a single mutable state object — backtracking correctness depends on full
   stack discipline.
6. **Cache the WASM Context object** — `init()` takes 1–3s; subsequent `Context('main')` calls
   reuse the initialized WASM module. Create the context once at application startup.

---

## 12. Common Pitfalls

**Pitfall 1: Using QF_NIA when QF_LIA suffices.**
The most common catastrophic performance mistake. Any formula with `x * y` where both x and y are
symbolic lands in QF_NIA. Restructure: introduce a concrete constant on one side (`5 * x` is fine
in QF_LIA), or add a case split in the application layer. QF_NIA can cause Z3 to run for minutes
on formulas that QF_LIA solves in milliseconds.

**Pitfall 2: Forgetting purification in Nelson-Oppen combination.**
When manually constructing mixed-theory formulas (EUF + LIA + Arrays), alien subterms in theory
atoms cause theory solvers to receive input outside their signature. Symptoms: incorrect SAT/UNSAT
results, assertion errors inside Z3, or wrong model values. Fix: introduce fresh variables for
every cross-theory subterm.

**Pitfall 3: UserPropagator missing push()/pop().**
State leaks across backtracks. Symptom: Z3 returns incorrect results (SAT when UNSAT, or UNSAT
when SAT) — not performance degradation. The solver backtracks but the custom state does not.
Fix: every `push()` must save the complete propagator state; every `pop(n)` must undo n levels.
Test by asserting contradictory constraints in sequence and verifying UNSAT.

---

## 13. Key References

- de Moura, L. & Bjørner, N. (2008). Z3: An efficient SMT solver. *TACAS 2008*. LNCS 4963.
- Nieuwenhuis, R., Oliveras, A. & Tinelli, C. (2006). Solving SAT and SAT modulo theories. *JACM*, 53(6).
- Nelson, G. & Oppen, D.C. (1979). Simplification by cooperating decision procedures. *TOPLAS*, 1(2).
- Bjørner, N., Phan, A.-D. & Fleckenstein, L. (2015). νZ — An optimizing SMT solver. *TACAS 2015*.
- Bjørner, N. et al. (2020). The Z3 string solver. *JACM*.
- Barrett, C. et al. (2010). SMT-LIB: The satisfiability modulo theories library. *SMT Workshop*.
- Kroening, D. & Strichman, O. (2016). *Decision Procedures: An Algorithmic Point of View* (2nd ed.). Springer.
