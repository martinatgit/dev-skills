# Integration Patterns

*Source: Z3_TypeScript_WASM_Bindings.json, Neuro_Symbolic_Compliance_LLM_Z3.json,
ConstraintLLM_Neuro_Symbolic.json, Grants4Companies_Regulatory_CLP.json, tla-z3-insights.md §5.*

---

## 1. Architectural Pattern: Layered Formal Reasoning Library

This is an **illustrative example** of how formal methods tools fit into a layered architecture.
It is NOT project-specific. Before applying it, read your project's CLAUDE.md / README.md,
understand the actual layer structure, and identify where formal methods components belong.

```
Illustrative layered architecture (not prescriptive):

Layer A: Resolution / Inference Engine
    Purpose: Core search strategy — SLD resolution, SAT-based CDCL, or Prolog-style backtracking
    Formal role: The SAT solver is the search engine; theory solvers are plugins to this layer
    Integration: TheorySolver interface (push/pop/assert/check/propagate/explain)

Layer B: Constraint Domain
    Purpose: Domain-specific constraint types and propagators
    Formal role: CLP propagator engine; FD/Z domains; trailing-based backtracking
    Integration: Propagator.propagate() + explain() for LCG; trail push/pop for backtracking

Layer C: Specification Language
    Purpose: High-level syntax for expressing constraints, properties, or processes
    Formal role: Temporal operators (TLA+/LTL), deontic operators, synchronous nodes (Lustre)
    Integration: Compiler from spec language → SMT formula or constraint model

Layer D: Compliance / Verification Layer
    Purpose: Check that system behaviors satisfy external requirements
    Formal role: MaxSMT (nuZ) for minimal-violation compliance; model checking for protocol safety;
                 synchronous observers for reactive system invariants
    Integration: Z3 Optimize for MaxSMT; Kind2 / IC3 for protocol checking; TLAPS for proofs

DO NOT assume these exact names or this structure in your actual project.
```

**How to apply**:
1. Read `CLAUDE.md` and `README.md` to understand your project's actual layer structure.
2. Identify which existing layer handles Boolean reasoning / search.
3. Identify where domain-specific constraint types live.
4. Map formal methods tools to those actual layers.
5. The theory solver interface (Section 3) is the key integration point in most architectures.

---

## 2. Z3 WASM TypeScript Integration

### 2.1 Setup

```bash
npm install z3-solver
```

**Node.js**: Works on 16+. No special headers needed.
**Browser**: Requires `SharedArrayBuffer` → server must send:
```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

### 2.2 Initialization (Cache This!)

```typescript
import { init } from 'z3-solver';

// WASM load time: 1-3s. Cache the Context — never call init() per request.
let Z3: Awaited<ReturnType<typeof init>>['Context'] extends ((...args: any[]) => infer R) ? R : never;

async function initZ3(): Promise<void> {
    const { Context } = await init();
    Z3 = Context('main');   // named context — reuse for all operations
}
```

### 2.3 Basic API Usage

```typescript
// Integer variables
const x = Z3.Int.const('x');
const y = Z3.Int.const('y');

// Solver
const solver = new Z3.Solver();
solver.add(x.ge(Z3.Int.val(0)));
solver.add(y.ge(Z3.Int.val(0)));
solver.add(x.add(y).le(Z3.Int.val(10)));

const result = await solver.check();   // 'sat' | 'unsat' | 'unknown'

if (result === 'sat') {
    const model = solver.model();
    const xVal = Number(model.eval(x).value());
    const yVal = Number(model.eval(y).value());
}
```

### 2.4 Incremental Solving (push/pop)

```typescript
// For exploring multiple related queries:
solver.push();                          // save current state
solver.add(x.ge(Z3.Int.val(5)));       // add additional constraint
const r = await solver.check();
solver.pop();                           // restore to saved state
```

**push/pop vs. assumption literals**:
- `push/pop`: Stack-based; good when adding many constraints for a sub-problem.
- Assumption literals: `solver.check([p1, p2])` with Boolean assumptions — avoids push/pop overhead
  for single-assumption-per-check patterns. No state push needed.

```typescript
// Assumption literal pattern:
const p = Z3.Bool.const('assumption_p');
solver.add(p.implies(x.ge(Z3.Int.val(5))));   // activate only when p=true
const r = await solver.check([p]);             // check with p as true
// Note: solver state unchanged; p assumption is not added to the stack
```

### 2.5 Term→Z3 Bridge (Compiling a DSL)

```typescript
function termToZ3(term: Term, ctx: typeof Z3): z3.Expr {
    switch (term.kind) {
        case 'var':      return ctx.Int.const(term.name);
        case 'num':      return ctx.Int.val(term.value);
        case 'bool':     return ctx.Bool.val(term.value);
        case 'add':      return (termToZ3(term.left, ctx) as z3.ArithExpr)
                                .add(termToZ3(term.right, ctx) as z3.ArithExpr);
        case 'mul':      return (termToZ3(term.left, ctx) as z3.ArithExpr)
                                .mul(termToZ3(term.right, ctx) as z3.ArithExpr);
        case 'leq':      return (termToZ3(term.left, ctx) as z3.ArithExpr)
                                .le(termToZ3(term.right, ctx) as z3.ArithExpr);
        case 'and':      return ctx.And(
                                termToZ3(term.left, ctx) as z3.BoolExpr,
                                termToZ3(term.right, ctx) as z3.BoolExpr
                             );
        case 'not':      return ctx.Not(termToZ3(term.arg, ctx) as z3.BoolExpr);
        default:         throw new Error(`Unknown term kind: ${term.kind}`);
    }
}
```

**Key**: Recursively translate term structure; use Z3's typed API (Int, Bool, BV) matching the
term's type. All leaf cases bottomed out; no non-exhaustive branches.

### 2.6 Optimization (MaxSMT)

```typescript
const opt = new Z3.Optimize();

// Hard constraints (must hold)
opt.add(x.ge(Z3.Int.val(0)));
opt.add(y.ge(Z3.Int.val(0)));

// Soft constraints with weights (maximize satisfaction)
opt.addSoft(x.ge(Z3.Int.val(5)), '3', 'group1');   // weight=3
opt.addSoft(y.ge(Z3.Int.val(3)), '2', 'group1');   // weight=2

// Objective: minimize total cost
const h = opt.minimize(x.neg().add(y.neg()));       // maximize x+y

if (await opt.check() === 'sat') {
    console.log(opt.model().eval(x));
}
```

### 2.7 Performance Characteristics

| Scenario | Typical latency |
|---|---|
| WASM initialization (first call) | 1–3 seconds |
| WASM initialization (cached Context) | <1 ms |
| QF_LIA, <50 constraints | <5 ms |
| QF_LIA, <200 constraints | <50 ms |
| QF_NIA with nonlinear products | 100ms–minutes (non-predictable) |
| Z3 WASM vs native Z3 overhead | 2–5× |

**Always set timeout**:
```typescript
solver.set('timeout', 5000);           // 5 second timeout
// OR:
Z3.setParam('timeout', 5000);         // global timeout
```
Always handle `'unknown'` as a possible return from `solver.check()`. Production code that assumes
only `sat`/`unsat` will fail silently on timeout or hard instances.

---

## 3. Constraint Store Integration Pattern

How a CLP constraint store integrates with a backward-chaining resolver (Prolog-style or custom):

```typescript
class ConstraintStore {
    private constraints: Constraint[] = [];
    private solver: Z3.Solver;

    // Called by the resolver when a constraint goal is encountered
    addConstraint(c: Constraint): 'consistent' | 'failed' {
        this.constraints.push(c);
        return this.checkSatisfiability();
    }

    // Periodic or leaf-node flush: check full store consistency
    private checkSatisfiability(): 'consistent' | 'failed' {
        const formula = this.constraintsToZ3(this.constraints);
        const r = await this.solver.check([formula]);
        return r === 'unsat' ? 'failed' : 'consistent';
    }

    // On backtrack: restore previous constraint list
    save(): ConstraintCheckpoint { return { length: this.constraints.length }; }
    restore(cp: ConstraintCheckpoint): void { this.constraints.length = cp.length; }

    // Extract residual constraint answer (for CLP(Z)-style answers)
    residualAnswer(): Constraint[] {
        return this.constraints.filter(c => !c.isGround());
    }
}
```

**Integration with resolver**:
- Resolver accumulates constraints during SLD resolution.
- On each constraint goal: call `store.addConstraint()`. If `'failed'`: backtrack.
- On each leaf (all goals solved): call `store.residualAnswer()` for the answer substitution.
- On backtrack: call `store.restore(checkpoint)` to undo constraint additions.

---

## 4. Neuro-Symbolic Compliance Pipeline

Four-stage pipeline from arXiv:2601.06181 (Koreeda & Manning 2021, extended):

```
Stage 1: Segment
    Input: Regulatory text (e.g., GDPR Article 17)
    Output: Individual rule clauses (one sentence per rule)
    Tool: LLM (GPT-4 / Claude) with section-splitting prompt
    Goal: Identify atomic, verifiable rules

Stage 2: Translate
    Input: Individual rule clause
    Output: SMT-LIB2 assertion
    Tool: LLM with few-shot examples of regulation → formal encoding
    Quality: 86% first-pass syntactic correctness (from arXiv paper)
    Repair loop: If Z3 rejects the formula (parse error), send error to LLM → retry (up to 3 times)
    Result: ~95% accuracy after repair loop

Stage 3: Check
    Input: Set of SMT-LIB2 assertions (all rules for one regulation)
    Output: CONSISTENT | INCONSISTENT(core)
    Tool: Z3 with (set-option :produce-unsat-cores true) and named assertions
    On INCONSISTENT: unsat-core identifies the minimal conflicting rule subset
    Use case: Regulations may be internally contradictory (rare but legally significant)

Stage 4: Optimize (Compliance Gap Analysis)
    Input: Rule assertions (hard) + factual assertions (soft, with violation cost weights)
    Output: Minimal-violation assignment (which facts can be changed to achieve compliance)
    Tool: Z3 Optimize (nuZ MaxSMT)
    Encoding:
        - Each regulation rule: hard constraint (must hold)
        - Each factual claim: soft constraint (prefer to hold, weight = legal cost of violation)
        - check() → model gives minimal-violation assignment
    Result: Which facts must change and at what cost to achieve compliance

Overall performance gain: 2 orders of magnitude faster than LLM-only chain-of-thought.
```

**Implementation notes**:
- The LLM is responsible for NL→formal translation (not formal reasoning).
- Z3 is responsible for formal reasoning (not NL understanding).
- The bridge: a well-designed prompt template with SMT-LIB2 examples + a repair loop.
- Named assertions enable unsat-core reporting — essential for explaining compliance failures.

---

## 5. Petri Net → SMT Integration Pattern

Use SMPT state equation (see `06-model-checking-algorithms.md` Section 5 for full pseudocode).

**Quick summary for integration context**:
```typescript
function checkReachability(net: PetriNet, m0: Marking, mTarget: Marking): 'unreachable' | 'potentially-reachable' {
    const solver = new Z3.Solver();
    solver.add(Z3.setLogic('QF_LIA'));

    // Firing count variables (one per transition)
    const x = net.transitions.map(t => Z3.Int.const(`x_${t.id}`));

    // Non-negativity
    x.forEach(xi => solver.add(xi.ge(Z3.Int.val(0))));

    // State equation per place: m_target[p] = m0[p] + sum(C[p][t] * x[t])
    net.places.forEach(p => {
        const sum = Z3.Int.val(m0[p]);
        net.transitions.forEach((t, i) => {
            const C_pt = net.incidence(p, t);  // = post[p][t] - pre[p][t]
            if (C_pt !== 0) sum.add(x[i].mul(Z3.Int.val(C_pt)));
        });
        solver.add(sum.eq(Z3.Int.val(mTarget[p])));
    });

    return solver.check() === 'unsat' ? 'unreachable' : 'potentially-reachable';
}
```

---

## 6. Reactive System → Model Checker Integration Pattern

Export a synchronous/reactive system as a transition relation, then apply BMC/k-Induction.

```typescript
// System state as Z3 variables (per-step)
function stateVars(step: number): SystemState {
    return {
        x: Z3.Int.const(`x_${step}`),
        mode: Z3.Int.const(`mode_${step}`),
        tick: Z3.Int.const(`tick_${step}`)
    };
}

// Init predicate
function init(s: SystemState): z3.BoolExpr {
    return Z3.And(s.x.eq(Z3.Int.val(0)), s.mode.eq(Z3.Int.val(0)));
}

// Transition predicate
function trans(s: SystemState, s_next: SystemState): z3.BoolExpr {
    // Encode system transition as SMT formula
    const mode0 = Z3.And(
        s.mode.eq(Z3.Int.val(0)),
        s_next.mode.eq(Z3.Int.val(1)),
        s_next.x.eq(s.x.add(Z3.Int.val(1)))
    );
    const mode1 = Z3.And(
        s.mode.eq(Z3.Int.val(1)),
        s_next.mode.eq(Z3.Int.val(0)),
        s_next.x.eq(Z3.Int.val(0))
    );
    return Z3.Or(mode0, mode1);
}

// Safety property (observer output)
function prop(s: SystemState): z3.BoolExpr {
    return s.x.le(Z3.Int.val(100));   // x never exceeds 100
}
```

Then pass `init`, `trans`, `prop` to the BMC or k-Induction implementation from
`06-model-checking-algorithms.md` Section 8.

---

## 7. Adoption Priority Framework

General ordering for integrating formal methods into a project (by increasing cost and decreasing ROI):

**P0: SMT-backed constraint solving** (immediate value, low integration cost)
- Use Z3 WASM for checking rule consistency and compliance gap analysis.
- MaxSMT for minimal-violation assignment.
- Cost: 1 week. Value: high (constraint checking, unsat-core debugging).

**P1: Bounded verification for core algorithms** (medium cost, high value for correctness)
- BMC of key state machines / data structures.
- k-Induction for simple invariants.
- Cost: 1–2 weeks per algorithm. Value: catches design bugs before implementation.

**P2: Compliance gap analysis via MaxSMT** (medium cost, direct compliance value)
- Encode all regulation rules as hard/soft constraints.
- MaxSMT identifies minimum-cost compliance modifications.
- Cost: 2–3 weeks for encoding + LLM pipeline. Value: automated compliance reasoning.

**P3: TLA+/Quint specs for critical protocols** (higher cost, highest assurance for protocols)
- Use at design time, not runtime.
- TLC model checks the protocol spec; TLAPS for proofs of critical invariants.
- Cost: 2–4 weeks per protocol. Value: eliminates distributed system design bugs.

**Future: Interactive theorem provers for foundational invariants**
- Isabelle/HOL or Lean4 for proving algorithm correctness (sorting, consensus).
- Cost: high (months per major theorem). Value: absolute correctness guarantee for core.

---

## 8. CLP(Z) → Real Compliance: Lessons from Production

From Triska et al., FLOPS 2024 (Grants4Companies — Austrian startup grants regulatory compliance):

**Key patterns**:
- **Systematic naming**: Each legal paragraph → one Prolog predicate with the paragraph identifier
  as the functor name. This creates audit-traceable proof trees — every decision maps to a specific
  legal paragraph.
  ```prolog
  % KMU Section 3.1 eligibility:
  fonds_kmu_3_1(Eligible) :-
      company_employees(N), N < 250,
      company_revenue(R), R =< 50_000_000,
      Eligible = true.
  ```
- **CLP(Z) for thresholds**: Numeric thresholds encoded as integer constraints — exact arithmetic,
  no floating-point rounding errors.
- **Demand-driven questionnaire**: The system poses only questions whose answers are not yet
  determined by previously established constraints. Each answer narrows the constraint store;
  determined variables are skipped in the questionnaire.
- **Proof tree → explanation**: The Prolog proof tree directly provides the justification for every
  compliance decision, mapping each step to the relevant regulation paragraph.
- **Formalization bottleneck**: The primary challenge is translating NL regulations into formal
  predicates. This requires domain expert + programmer collaboration. LLM-assisted translation
  (Section 4) reduces this bottleneck.

---

## 9. UserPropagator Hybrid Architecture

Pattern: Z3 handles Boolean/arithmetic structure; custom propagator handles domain-specific constraints.

```typescript
class MyCustomPropagator extends Z3.UserPropagatorBase {
    private stateStack: MyState[] = [this.initialState()];
    private current: MyState = this.initialState();

    push(): void {
        // Z3 made a new decision: save complete state
        this.stateStack.push(this.deepCopy(this.current));
    }

    pop(numScopes: number): void {
        // Z3 backtracked numScopes levels: restore saved state
        for (let i = 0; i < numScopes; i++) {
            this.current = this.stateStack.pop()!;
        }
    }

    fixed(x: z3.Expr, val: z3.Expr): void {
        // Z3 assigned variable x = val: run custom propagation
        const newFact = this.toFact(x, val);
        const conflict = this.propagateCustom(newFact);
        if (conflict !== null) {
            // Report conflict to Z3 (it will learn a clause and backtrack)
            this.conflict([x], []);
        } else {
            // Report consequences (optional: proactively assign other variables)
            for (const consequence of this.deducedFacts) {
                this.propagate(consequence.expr, [x], []);
            }
        }
    }

    final(): void {
        // All Z3 variables assigned: check completeness
        if (this.hasViolation()) {
            // Full conflict: all assigned variables are the antecedent
            this.conflict(this.allWatchedVars(), []);
        }
    }
}
```

**Use cases**:
- Petri net firing constraints (token conservation) embedded in Z3 search
- Custom temporal constraint types not expressible in Z3's built-in theories
- Domain-specific global constraints (e.g., resource allocation invariants)

**Non-negotiable requirements**:
1. `push()` must save the complete propagator state (not a reference).
2. `pop(n)` must correctly undo n levels.
3. `fixed()` must be idempotent (may be called multiple times for same assignment).
4. `final()` is the last chance to catch constraint violations.

---

## 10. Key References

- Koreeda, Y. & Manning, C.D. (2021). Capturing failures of large language models via human cognitive biases. *EMNLP 2021*. [NL→formal pipeline]
- arXiv:2601.06181. Neuro-symbolic compliance verification.
- Triska, M. et al. (2024). Grants4Companies: CLP(Z) for regulatory compliance. *FLOPS 2024*.
- z3-solver npm package: https://www.npmjs.com/package/z3-solver
- OR-Tools CP-SAT: https://developers.google.com/optimization
