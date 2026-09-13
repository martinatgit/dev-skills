# SAT Foundations

*Source: CDCL_T_Framework.json (Nieuwenhuis/Oliveras/Tinelli 2006), SAT/SMT literature.*

---

## 1. DPLL Algorithm

The Davis-Putnam-Logemann-Loveland (DPLL, 1962) algorithm is a backtracking search for satisfying
assignments of propositional formulas in Conjunctive Normal Form (CNF). The problem class is NP-complete
(Cook-Levin theorem, 1971) — no polynomial algorithm is known.

```
function DPLL(F, assignment):
    F = unit_propagate(F, assignment)    // simplify using unit clauses
    if F contains empty clause: return UNSAT
    if F is empty: return SAT

    l = choose_literal(F)                // branching heuristic
    if DPLL(F ∪ {l}, assignment + l) == SAT: return SAT
    return DPLL(F ∪ {¬l}, assignment + ¬l)
```

Key rules applied at each step:
- **Unit propagation (BCP)**: If a clause has exactly one unassigned literal and all others are false,
  that literal must be true. Apply immediately — no choice.
- **Pure literal elimination**: If a variable appears with only one polarity across all clauses, assign
  it to satisfy those clauses (safe to do without branching).
- **Conflict detection**: If any clause becomes empty (all literals false), backtrack.

DPLL is correct but uses chronological backtracking (undo the most recent decision). Modern SAT uses CDCL.

---

## 2. Conflict-Driven Clause Learning (CDCL)

CDCL transforms DPLL from a recursive procedure into an iterative loop with three major innovations:
non-chronological backtracking (backjumping), conflict analysis via the implication graph, and
learned clause addition. This is the modern SAT algorithm — all industrial solvers (MiniSAT, Glucose,
CaDiCaL, Z3's internal SAT core) implement CDCL.

```
function CDCL(F):
    trail = []           // decision/propagation trail
    level = 0            // current decision level
    clauses = cnf(F)     // clause database

    loop:
        // Phase 1: Boolean Constraint Propagation (BCP / Unit Propagation)
        conflict = BCP(clauses, trail)

        if conflict != NULL:
            if level == 0:
                return UNSAT      // conflict at root level: formula is unsatisfiable
            // Conflict Analysis — find 1UIP cut in implication graph
            (learned_clause, backtrack_level) = analyze_conflict(conflict, trail)
            add_clause(clauses, learned_clause)
            backtrack_to(trail, backtrack_level)
            level = backtrack_level
            // Learned clause is immediately unit after backjump → BCP propagates
            continue

        // Phase 2: Decision
        if all_variables_assigned(trail):
            return SAT (with model from trail)

        level = level + 1
        literal = VSIDS_pick(trail)          // pick highest-activity unassigned variable
        trail.push(Decision(literal, level))
```

After UNSAT: the learned clauses form a resolution refutation.
After SAT: the trail gives a satisfying assignment.

---

## 3. Implication Graph

An implication graph is a DAG built from the trail:
- **Nodes**: One per literal assignment (literal + decision level annotation).
- **Decision nodes**: No incoming edges — chosen by the solver.
- **Propagation nodes**: Edges from the other literals in the reason clause (those that forced BCP).
- **Conflict node**: A special sink node with edges from all literals in the conflict clause.

```
Example:
  Decision level 3: d₃ = (x=T)            // no edges in
  BCP from clause (¬x ∨ y):  y=T  ←  x=T  // y forced by x
  BCP from clause (¬y ∨ z):  z=T  ←  y=T
  BCP from clause (¬z ∨ ¬w): w=F  ←  z=T
  Conflict: clause (w) is empty because w=F → conflict node ← w=F
```

The implication graph is implicitly represented by the trail and reason arrays — no explicit graph object needed in implementation.

---

## 4. Conflict Analysis — 1-UIP

A **UIP (Unique Implication Point)** is any node in the implication graph whose removal disconnects
all current-level decision nodes from the conflict node. The **First UIP** is the UIP closest to
the conflict node.

1-UIP gives an **asserting clause**: after backjumping, exactly one literal of the learned clause is
unassigned, so BCP immediately forces it. This is the key property that makes CDCL efficient.

```
function analyze_conflict(conflict_clause, trail):
    learned = set(conflict_clause)

    while count_at_current_level(learned) > 1:
        // Pick the most recently assigned literal at the current level
        lit = last_assigned_in(learned, trail)
        reason = get_reason(lit, trail)            // clause that forced lit
        // Resolution: eliminate lit from learned, add reason literals
        learned = (learned \ {¬lit}) ∪ (reason \ {lit})

    // learned now contains exactly one literal at current level = 1-UIP
    backtrack_level = max decision level among all other literals in learned
    return (learned, backtrack_level)
```

**Why 1-UIP**: Resolution step eliminates the chosen literal from the learned clause. When only one
literal remains at the current level, that literal IS the 1-UIP. The resulting clause immediately
unit-propagates after backjumping.

After backjump: the solver is at `backtrack_level`, and the single current-level literal in the
learned clause has all its other literals false (they are at levels ≤ backtrack_level and were
assigned false). BCP propagates the current-level literal immediately.

---

## 5. Two-Watched Literals

**The invariant**: Each clause watches exactly 2 non-false literals. A watched literal is stored in
a watch list indexed by its literal.

**Maintenance rule**:
- When literal L is assigned false, scan L's watch list.
- For each clause C in the watch list:
  - If C has another watched literal that is true: clause is satisfied, no action needed.
  - If C has an unwatched non-false literal W: swap watches (replace L with W). C stays consistent.
  - If C has no unwatched non-false literal but one watched literal U is unassigned: unit! Propagate U.
  - If both watched literals are false: conflict.

**Why this is fast**: Only clauses where a watched literal becomes false are touched. Satisfied clauses
and clauses with slack (extra true literals) are never visited. This gives amortized O(1) per literal
assignment in practice.

**Critical pitfall**: Watch lists must be correctly maintained on backtrack. When undoing an assignment
(popping the trail), watches must remain valid. Common mistake: updating watches in a way that the
invariant breaks after backjump.

**Example** (watching literals at indices 0 and 1 in each clause):
```
Clause [¬x, y, z]: watches ¬x and y.
x assigned true → ¬x is false → visit clause.
z is unassigned → swap: now watches y and z. Done.
```

---

## 6. VSIDS Heuristic

**Variable State Independent Decaying Sum** (Chaff, 2001).

Each variable v has an activity score `activity[v]`, initially 0.

**Bump**: When a learned clause is created, bump all variables appearing in it:
```
for v in learned_clause:
    activity[v] += bump_amount
```

**Decay**: Periodically (or equivalently, increase bump_amount instead of decaying):
```
bump_amount *= (1 / decay_factor)    // decay_factor = 0.95 typical
```
This effectively divides all scores by decay_factor every interval.

**Decision**: Pick the unassigned variable with highest activity score (binary heap or indexed priority queue).

**Why VSIDS works**: Variables involved in recent conflicts tend to appear in future conflicts.
Exponential decay gives recent conflicts more weight than old ones. In practice, VSIDS provides
~30–50% of CDCL's performance advantage over random/DLIS heuristics.

---

## 7. Clause Database and Deletion

**Two classes of clauses**:
1. **Original clauses**: Never deleted.
2. **Learned clauses**: Added during CDCL; must be managed to prevent memory exhaustion.

**LBD (Literal Block Distance)**: The number of distinct decision levels among the literals of a
learned clause. Low LBD = high quality (clause is "deep" in the conflict structure).

**Deletion policy** (Glucose strategy):
- Keep all clauses with LBD ≤ 2 ("glue clauses") — never deleted.
- Periodically: sort remaining learned clauses by (LBD desc, activity asc), remove bottom half.

**Activity for clauses**: Each clause C's activity increases when C participates in a conflict.

---

## 8. Restarts

Restarts escape local minima: search is restarted from scratch (level 0) but **all learned clauses
are kept**. The retained learning prevents the solver from re-exploring the same dead ends.

**Luby sequence**: 1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8, ... (multiply by a base unit, e.g., 100 conflicts)
- Theoretically optimal restart schedule for black-box search (Luby, Sinclair & Zuckerman, 1993).
- Universal: no tuning required.

**Geometric restart**: Each restart threshold = previous × constant (e.g., 1.5×).
- Grows unboundedly; may get stuck on hard instances. Less preferred than Luby.

**LBD-based restart** (Glucose): Restart when moving average of recent clause LBDs is higher than
global average. Empirically strong on structured instances.

---

## 9. Phase Saving

When a variable's assignment is undone during backjump, **save its last polarity**.
On next decision for that variable, try the saved polarity first.

**Effect**: The solver tends to re-explore similar regions — useful for optimization (solution-improve
cycles) and for problems where solutions cluster in assignment-space.

**Implementation**: One bit per variable. Flipped when solver decides a variable; saved when backtracked.

---

## 10. Resolution Proof System

Two clauses `(A ∨ x)` and `(B ∨ ¬x)` resolve to `(A ∨ B)` (the resolvent).

Every learned clause in CDCL is a resolution consequence of the original formula: the conflict analysis
is a sequence of resolution steps. An UNSAT proof is a **resolution refutation**: a sequence of
resolution steps deriving the empty clause (⊥) from the original clauses.

**DRUP/DRAT proof formats**: Modern solvers emit a sequence of clause additions and deletions.
An external checker (drat-trim) verifies the proof independently. Critical for competition UNSAT results.

**Connection to LCG**: In lazy clause generation (Section 11), each propagator explanation clause is a
resolution consequence of the original constraints. The SAT layer learns from these clauses exactly as
in standard CDCL.

---

## 11. SAT in Constraint Programming: Lazy Clause Generation (LCG)

Lazy Clause Generation (Ohrimenko, Stuckey & Codish, 2009 — implemented in Chuffed) embeds a CDCL
SAT engine inside a CLP(FD) constraint solver:

- **Order encoding**: Boolean literals `[[x ≤ d]]` for each variable x and bound d. Domain: D(x) = {1..n}.
  - `[[x ≤ d]] → [[x ≤ d+1]]` (structural clauses, added once at setup)
- **Each FD propagator** must implement `explain(pruning_event) → clause`:
  - Pruning `[[x ≤ d]]` to false (raising lower bound of x above d) must produce a clause expressing
    "which previously true order literals forced this bound change."
- **Integration**: FD propagation fires; resulting domain changes become unit clauses in the SAT layer;
  SAT learns from conflicts; non-chronological backjumping applies to the combined FD+SAT state.

**Result**: 1–2 orders of magnitude speedup on hard combinatorial problems vs. pure FD propagation.

**Why it matters**: LCG is the algorithmic foundation of Chuffed (MiniZinc competition winner) and
OR-Tools CP-SAT. Any TypeScript CLP(FD) implementation aiming at performance should consider LCG.

---

## 12. Implementation Strategies (Priority-Ordered)

1. **Two-watched literals from day one** — naive "check all clauses" is 100× slower; there is no
   intermediate step worth taking.
2. **VSIDS before other heuristics** — biggest single performance factor after 2WL; use a binary heap.
3. **Clause deletion before large problems** — without deletion, memory exhaustion is certain on any
   serious instance.
4. **Luby restarts as default** — geometric is acceptable, fixed-cutoff is wrong.
5. **Phase saving** — implement after basic solver works; adds ~15–20% performance with trivial code cost.
6. **LBD tracking** — needed for good clause deletion; add alongside clause database management.

---

## 13. Common Pitfalls

**Pitfall 1: Watches not correctly maintained on backtrack.**
When undoing assignments (popping the trail), a watch list entry may point to a clause where the
backtracked literal is no longer false. If you added a clause to the watch list during propagation
and the variable is now unassigned, the watch state may be inconsistent. Fix: watches are invariant
under backtracking — only BCP updates watches; backtracking never modifies them. The invariant holds
because watches only require "non-false", and an unassigned literal is non-false.

**Pitfall 2: Forgetting to bump activity of all literals in the learned clause.**
The VSIDS bump must apply to all literals in the learned clause at the moment of conflict analysis,
not just the 1-UIP literal. Many tutorials only show bumping the 1-UIP, which produces suboptimal
heuristic behavior.

**Pitfall 3: Clause deletion too aggressive or too conservative.**
Too aggressive: deleting "active" clauses (ones currently propagating units) causes incorrect solver
behavior — untracked units or dangling reason pointers. Too conservative: memory exhaustion halts
the solver. Fix: never delete a clause that is a reason clause for any current trail entry; use
LBD ≤ 2 as the permanent-keep threshold.

---

## 14. Key References

- Davis, M. & Putnam, H. (1960). A computing procedure for quantification theory. *JACM*, 7(3).
- Davis, M., Logemann, G. & Loveland, D. (1962). A machine program for theorem-proving. *CACM*, 5(7).
- Marques-Silva, J. & Sakallah, K. (1999). GRASP: A search procedure for propositional satisfiability. *IEEE Trans. Comp.*, 48(5).
- Moskewicz, M. et al. (2001). Chaff: Engineering an efficient SAT solver. *DAC 2001*.
- Audemard, G. & Simon, L. (2009). Predicting learnt clauses quality in modern SAT solvers. *IJCAI 2009*. [LBD/Glucose]
- Biere, A. et al. (eds.) (2021). *Handbook of Satisfiability* (2nd ed.). IOS Press.
- Ohrimenko, O., Stuckey, P.J. & Codish, M. (2009). Propagation via lazy clause generation. *Constraints*, 14(3).
