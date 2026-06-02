# aiqeung Layer 3 — Synchronous Reactive Runtime (Worked Example)

**Scope:** This file describes the aiqeung Layer 3 implementation as a self-contained
worked example for SRS theory. All type definitions and code snippets are embedded
directly — no live source file links are used.

**Staleness notice:** Field names, variant counts, and implementation details described
here reflect the state at 2026-04-13. When this file conflicts with the live source,
trust the source. The architectural patterns (three-phase tick, frozen snapshot,
ABSENT sentinel, free monad + interpreter separation) are stable; specific field names
may have changed.

*aiqeung is the worked example, not the reason the SRS patterns exist. These patterns
apply to any synchronous reactive runtime (Esterel, Lustre, Lingua Franca, etc.).*

*Sources: aiqeung_integration.json (2026-04-07), reactive-system-insights.md §5*

---

## 1. Architecture Overview

Layer 3 (`src/aiqeung-core/reactive/`) is aiqeung's synchronous reactive runtime. It implements a tick-based execution engine grounded in the synchronous hypothesis (Berry & Gonthier 1992) and Lustre dataflow semantics (Halbwachs et al. 1991).

**Key design principle — Spec-Execution Duality:**
> The `ReactiveExpr` free monad AST IS the synchronous program specification (analogous to a Lustre node definition). The runtime interpreter IS the compiler + runtime combined. Multiple interpreters can operate on the same AST: synchronous execution, simulation, formal verification.

This is not a coincidence: both free monads and synchronous languages embody the "description/interpretation" separation principle. The monad describes WHAT to compute; the interpreter determines WHEN and HOW.

*Source module: `src/aiqeung-core/reactive/` — key files: `types.ts` (ReactiveExpr,
Signal, ABSENT), `runtime.ts` (tick engine), `clock.ts` (clock inference),
`obligations.ts` (obligation store). Verify current field names against the live source.*

---

## 2. Three-Phase Tick Architecture (DR-1)

**Formal basis:** Synchronous hypothesis — computation within a tick is instantaneous; all outputs are produced before the next input arrives.

The `runtime.step()` function (runtime.ts, step function) implements a strict three-phase cycle:

```
PHASE 1: SNAPSHOT
  - Copy ClauseDB into snapshotDb (cross-node isolation)
  - Capture current signal values into signalValues (frozen)
  - Capture current Petri net markings into snapshotMarkings (frozen)
  - Capture preValues for pre(x) semantics (current → previous for next tick)

PHASE 2: COMPUTE
  - Evaluate each SyncNode in topologically-sorted order (nodeOrder from seal())
  - Each node receives the FROZEN snapshot (no node sees writes from other nodes this tick)
  - Writes are buffered: pendingSignalWrites, pendingAssertions, pendingRetractions, pendingMarkingUpdates

PHASE 3: COMMIT (atomic)
  - Apply all buffered signal writes to sig.current
  - Apply all DB assertions and retractions
  - Apply all marking updates
  - Notify subscribers
  - Advance tick counter
```

**Rollback on error:** The runtime saves state before every tick and restores it on failure (runtime.ts, rollback logic). `TickRollbackError` is thrown when a tick fails and is rolled back.

**Why this matters for determinism:** All `par` branches see the same frozen snapshot during COMPUTE. The order in which branches execute does not affect what they see — the synchronous hypothesis is preserved. This is the fundamental invariant that makes synchronous concurrency race-condition free.

### 2.1 The TickTransaction Pattern

The design recommendation (DR-1) formalizes COMPUTE-phase writes as a transaction:

```typescript
interface TickTransaction {
  readonly signalWrites: Map<string, { signal: Signal; value: Term }>;
  readonly dbAssertions: Clause[];
  readonly dbRetractions: Term[];
  readonly markingUpdates: Map<string, HierarchicalMarking>;
  readonly obligationsAdded: Array<{ netId: string; obligation: Term }>;
}
```

All writes during COMPUTE target this buffer. COMMIT applies the buffer atomically. **No write is visible to other nodes until COMMIT.** This implements the closed-world semantics of the synchronous tick.

---

## 3. Signal Model — Closed-World Absence (DR-2)

**Formal basis:** Lustre stream semantics + clock calculus absence guarantee.

### 3.1 Signal Type (types.ts:82)

```typescript
// From src/aiqeung-core/reactive/types.ts
export interface Signal<A = Term> {
  readonly name: string
  current: A  // deliberately mutable — changed at tick boundaries
}
```

`current` holds the stream value at the **current** tick. It is frozen during COMPUTE, mutated only during COMMIT.

### 3.2 ABSENT Sentinel (types.ts:19)

```typescript
// From src/aiqeung-core/reactive/types.ts
export const ABSENT: Term = Object.freeze(t.atom("$absent"))
export function isAbsent(term: Term): boolean {
  return term.kind === "atom" && term.name === "$absent"
}
```

**Formal significance:** `ABSENT` implements the closed-world assumption of the synchronous hypothesis. A signal with value `ABSENT` is **definitively absent** at this tick — not "not yet arrived," not "unknown." This distinction is the formal basis for absence reasoning:

- Absence is decidable: `isAbsent(sig.current)` is a well-defined check
- Absence is compositional: if a downstream computation receives ABSENT, it propagates ABSENT (see eval.ts `when` case)
- Absence enables compliance gap detection: a missing evidence signal is definitively absent at a tick, not potentially delayed

**Contrast with asynchronous:** In an asynchronous system, there is no way to distinguish "not yet arrived" from "definitively absent." The synchronous tick boundary provides this definiteness.

### 3.3 Signal Semantics vs. Double-Buffering Design (DR-2)

The design recommendation specifies **double-buffering** for full Lustre compliance:

```typescript
// Design recommendation pseudocode (DR-2)
interface SignalImpl<A> {
  current: A;              // frozen at tick start (readable during COMPUTE)
  next: A | typeof ABSENT; // buffered writes for this tick (visible at tick N+1)
  readonly tag: Tag;       // (tick, microstep) — superdense time
}
```

The current implementation uses `sig.current` with a separate `pendingSignalWrites` map during COMPUTE (equivalent semantics, different structure). `pre(x)` is handled by `preValues` captured before COMPUTE begins (runtime.ts, preValues capture).

### 3.4 ABSENT Propagation in StreamExpr Evaluator (eval.ts)

The `evaluateExpr` function propagates ABSENT following the clock calculus:

```typescript
// From src/aiqeung-core/reactive/eval.ts
case "input":
case "local":
  return values.get(expr.name) ?? ABSENT   // undefined → ABSENT

case "pre":
  return preValues.get(exprKey(expr.expr)) ?? ABSENT   // no prior value → ABSENT

case "when": {
  const clockVal = values.get(expr.clock) ?? ABSENT
  if (isFalsy(clockVal)) return ABSENT     // clock false → substream is absent
  return await evaluateExpr(expr.expr, ...)
}
```

The `when` case directly implements the Lustre clock calculus: if the clock condition is false, the subsampled stream is absent (ABSENT), not evaluated. This is the runtime implementation of the compile-time absence-as-type guarantee from the clock calculus.

---

## 4. ReactiveExpr — Free Monad as Lustre Node (DR-6)

**Formal basis:** ReactiveExpr AST = Lustre node definition; interpreter = compiler + runtime.

### 4.1 The 14 Variants (types.ts:180)

```typescript
// From src/aiqeung-core/reactive/types.ts
export type ReactiveExpr<A = Term> =
  | { readonly kind: "pure"; readonly value: A }           // return value
  | { readonly kind: "bind"; readonly ma: ReactiveExpr; readonly f: ReactiveExprContinuation }
  | { readonly kind: "goal"; readonly term: Term }          // SLD query (read-only DB)
  | { readonly kind: "fire"; readonly net: string; readonly page: string; readonly transition: string }
  | { readonly kind: "assert"; readonly clause: Clause }   // DB write
  | { readonly kind: "retract"; readonly pattern: Term }   // DB retract
  | { readonly kind: "read"; readonly signal: string }     // read current signal value
  | { readonly kind: "emit"; readonly signal: string; readonly value: Term }  // buffer signal write
  | { readonly kind: "tick" }                              // advance to next tick
  | { readonly kind: "par"; readonly left: ReactiveExpr; readonly right: ReactiveExpr }  // sync parallel
  | { readonly kind: "race"; readonly left: ReactiveExpr; readonly right: ReactiveExpr }  // preemption
  | { readonly kind: "until"; readonly body: ReactiveExpr; readonly cond: Term }          // temporal loop
  | { readonly kind: "constrain_pn"; readonly net: string; readonly obligation: Term }
  | { readonly kind: "verify_pn"; readonly net: string }
```

**Companion types** (verify field names against live source):

```typescript
// Signal<A> — frozen during COMPUTE phase
interface Signal<A> {
  readonly name: string;
  current: A | typeof ABSENT;      // frozen during COMPUTE
  next:    A | typeof ABSENT;      // written during COMPUTE, committed in COMMIT
}
const ABSENT: unique symbol = Symbol("$absent");  // closed-world absence sentinel
```

**Free monad structure:** `bind` chains computations; `pure` terminates. The remaining 12 variants are the "effects" — primitive operations that the interpreter handles. This is exactly the structure of a free monad over the functor of primitive reactive operations.

### 4.2 Spec-Execution Duality

| Synchronous programming concept | aiqeung analog |
|---|---|
| Lustre node definition | `ReactiveExpr` AST (data structure, not code) |
| Lustre node compilation | Interpreter construction from AST |
| Production runtime | Synchronous interpreter (tick-discipline) |
| Simulation | Step-through interpreter (explicit tick control for testing) |
| Formal verification | Model-checking interpreter (explores all paths) |

The same `ReactiveExpr` AST can be interpreted by different backends without changing the program. This is the "description/interpretation separation principle" that makes the free monad directly analogous to synchronous language compilation.

### 4.3 SyncNode — The Formal Node Concept (types.ts:72)

```typescript
// From src/aiqeung-core/reactive/types.ts
export interface SyncNode {
  readonly name: string
  readonly inputs: ReadonlyMap<string, SyncStream>   // named input streams with clock types
  readonly outputs: ReadonlyMap<string, SyncStream>  // named output streams with clock types
  readonly equations: ReadonlyArray<StreamEquation>  // the dataflow equations
  readonly localStreams: ReadonlyMap<string, SyncStream>
}
```

`SyncNode` is the formal Lustre node concept in aiqeung: a stream transformer with named inputs, outputs, and a system of stream equations. The clock analysis pass (`inferClocks` in clock.ts) verifies that all stream equations are well-clocked before execution.

---

## 5. `par` — Synchronous Parallel Composition (DR-7)

**Formal basis:** Esterel `p ∥ q` — both branches execute in the same instant, see the same signal environment, and their outputs are merged.

**aiqeung semantics:** Both left and right branches of `par` execute against the **same frozen snapshot** from PHASE 1. Neither branch sees the other's writes during COMPUTE.

```typescript
// Design recommendation pseudocode (DR-7)
async function interpretPar(left, right, snapshot, tx) {
  // Both branches see the SAME frozen snapshot (synchronous hypothesis)
  // Both buffer writes to the SAME transaction (merged at tick boundary)
  const [leftResult, rightResult] = await Promise.all([
    interpretExpr(left, snapshot, tx),
    interpretExpr(right, snapshot, tx),
  ]);
  return mergeParResults(leftResult, rightResult);
}
```

**Determinism guarantee:** Since both branches read from the same frozen snapshot, the execution order of the two branches does not affect what they see. This is determinism by construction, not by locking.

**Conflict resolution:** If both branches emit the same signal with different values, the runtime applies a deterministic merge strategy (left-wins by convention). This should be rare and is a design smell — if two `par` branches need to write the same signal, they probably should be in sequence.

**DB assertions in `par`:** Assertions from either branch go into the same `pendingAssertions` buffer. They become visible to subsequent `goal` calls in the **next tick** (strict synchronous discipline). *See `07-pitfalls-risks.md §3` for the intra-tick visibility design decision.*

---

## 6. `race` — Esterel-Style Preemption (DR-7)

**Formal basis:** Esterel `abort p when S` — run p and kill it when condition S becomes true.

**aiqeung semantics:** Both branches start in the same tick. The first to complete wins; the loser's buffered writes are **discarded** from the transaction.

```typescript
// Design recommendation pseudocode (DR-7)
async function interpretRace(left, right, ctx) {
  const leftTx = forkTransaction(ctx.tx);   // sub-transaction for left
  const rightTx = forkTransaction(ctx.tx);  // sub-transaction for right

  const winner = await Promise.race([
    interpretExpr(left, {...ctx, tx: leftTx}).then(v => ({side:'left', value:v, tx:leftTx})),
    interpretExpr(right, {...ctx, tx: rightTx}).then(v => ({side:'right', value:v, tx:rightTx})),
  ]);

  // Cancel loser, discard its transaction
  cancelLoser(winner.side, leftCancel, rightCancel);

  mergeTransaction(ctx.tx, winner.tx);  // only winner's writes apply
  return winner.value;
}
```

**Key property:** The losing branch's writes never reach the parent transaction. This is the synchronous preemption semantics: the loser's outputs are absent (discarded), not partially applied. This prevents a half-executed branch from corrupting the signal environment.

**Soundness requirement:** `race` is sound under the synchronous hypothesis because: (1) both branches read from the same frozen snapshot, (2) only the winner's writes apply, (3) the decision is made within a single tick based on tick-N state.

---

## 7. `until` — Temporal Loop with Absence Reasoning (DR-8)

**Formal basis:** Lustre temporal loop — body executes once per tick; condition checked at tick boundary using closed-world assumption.

**aiqeung semantics:** Execute `body` once per tick. At each tick boundary, query `cond` against the DB. If `cond` holds (SLD finds at least one solution), terminate and return `body`'s result. If `cond` fails (no solutions — definitively absent by closed-world assumption), advance to the next tick and repeat.

```typescript
// Design recommendation pseudocode (DR-8)
async function interpretUntil(body, cond, ctx) {
  while (true) {
    const lastResult = await interpretExpr(body, ctx);

    // Absence reasoning: SLD returning no solutions = cond is definitively absent
    const solutions = queryAll(ctx.snapshot.db, cond);
    if (solutions.length > 0) {
      return lastResult;           // condition holds — terminate
    }
    await advanceToNextTick(ctx);  // condition absent — continue next tick
  }
}
```

**Formal significance of absence reasoning here:** `cond` failing is not "maybe it will hold later" — it is a definitive answer from the SLD resolver under the closed-world assumption (CWA). The CWA is the logic programming analog of the synchronous hypothesis: what is not known to be provable is false. This makes `until` formally well-defined, unlike a polling loop in asynchronous code.

---

## 8. Clock Calculus in aiqeung (types.ts:28)

**Formal basis:** Colaço & Pouzet (2003) — clocks as types, ML-style inference.

### 8.1 ClockType Representation

```typescript
// From src/aiqeung-core/reactive/types.ts
export type ClockType =
  | { readonly kind: "base" }                                              // base clock
  | { readonly kind: "on"; readonly parent: ClockType; readonly condition: string }  // subclock
  | { readonly kind: "not"; readonly clock: ClockType }                   // complement

export const baseClock: ClockType = Object.freeze({ kind: "base" as const })
```

This directly implements the Lustre clock type syntax: `base`, `ck on c`, and `ck on not c`. The `when` stream operator produces streams on `{ kind: "on", parent: ck, condition: c }`.

### 8.2 Clock Inference and Errors

The `inferClocks` function (clock.ts) runs the clock analysis pass on the `SyncNode` graph:

```typescript
// From src/aiqeung-core/reactive/types.ts
export type ClockError =
  | { readonly kind: "clock_mismatch"; readonly node: string; readonly stream: string; ... }
  | { readonly kind: "unguarded_pre"; readonly node: string; readonly stream: string }
  | { readonly kind: "inter_node_cycle"; readonly nodes: readonly string[] }
  | { readonly kind: "duplicate_fire"; readonly node: string; readonly net: string }
```

`seal()` on the runtime runs clock inference. If errors are found, `status: "errors"` is returned and the runtime refuses to `step()`. This is the compile-time guarantee from the clock calculus: ill-clocked programs are rejected before execution.

**`inter_node_cycle`** is the aiqeung analog of Lustre's causality error: a circular dependency between `SyncNode`s that cannot be resolved by the constructive fixpoint. The topologically sorted `nodeOrder` from `seal()` is the valid schedule — it only exists if the dependency graph is acyclic.

---

## 9. Obligation Observers (DR-5)

**Formal basis:** Lustre observer pattern — safety properties as synchronous nodes running in parallel with the system.

### 9.1 PetriObligationStore (types.ts:111, obligations.ts)

```typescript
// From src/aiqeung-core/reactive/types.ts
export interface PetriObligationStore {
  readonly obligations: ReadonlyMap<string, Term[]>
  add(netId: string, obligation: Term): PetriObligationStore  // returns NEW store
  discharge(net: ConstrainedHierarchicalNet, marking: HierarchicalMarking): VerificationResult
}
```

The store is **immutable** — `add()` returns a new store (functional update). This enables zero-cost rollback: saving and restoring `_obligations` is O(1) reference swap.

### 9.2 Observer Semantics

Each obligation in the store is a **synchronous observer** in the Lustre sense:
- It runs implicitly in parallel with the main program
- It observes marking changes (the "signals" of the Petri net layer)
- It produces a verdict: `satisfied`, `conflict`, or `undetermined`
- `discharge()` performs the observation check against the current marking

The `avoid` observer fires immediately if a forbidden place has tokens. The `before(T1, T2)` observer maintains state across ticks — analogous to a stateful Lustre observer node.

### 9.3 Obligation Types (VerificationResult)

```typescript
// From src/aiqeung-core/reactive/types.ts
export type VerificationResult =
  | { readonly status: "satisfied"; readonly witnesses: ReadonlyMap<string, HierarchicalMarking> }
  | { readonly status: "conflict"; readonly obligation: Term; readonly counterExample?: ReadonlyArray<HierarchicalMarking> }
  | { readonly status: "undetermined"; readonly openObligations: ReadonlyArray<Term> }
```

- `satisfied`: observer discharged — obligation met
- `conflict`: observer detected violation — counterexample provided (analogous to observer emitting `violation = true` in Lustre)
- `undetermined`: observation ongoing — not enough evidence yet

---

## 10. Superdense Time Tags (DR-2)

**Formal basis:** Tagged Signal Model (Lee & Sangiovanni-Vincentelli 1998) — tags `(tick, microstep)` for causally ordered intra-tick events.

The design recommendation specifies:

```typescript
// Design recommendation (DR-2)
interface Tag {
  readonly tick: number;
  readonly microstep: number;
}
```

**Ordering:** `(t1, m1) < (t2, m2)` iff `t1 < t2`, or `t1 = t2 and m1 < m2`. This is lexicographic ordering on `(tick, microstep)`.

**Purpose in aiqeung:** When sequential `fire()` calls in a `bind` chain need to be causally ordered within the same tick (fire T1, then fire T2 on the same net), microsteps provide the causal order without violating the synchronous hypothesis. `bind(fire(net,t1), _ => fire(net,t2))` uses `microstep=0` for t1 and `microstep=1` for t2 — both within the same tick boundary.

**Rule:** Sequential operations in `bind` can use microsteps for intra-tick ordering. Parallel operations in `par` use the frozen snapshot (tick-N values only).

---

## 11. RuntimeHooks — Synchronous Side Channels

The `RuntimeHooks` interface (types.ts, RuntimeHooks definition) provides tick-level callbacks for cross-layer integration:

```typescript
export interface RuntimeHooks {
  readonly onTickStart?: (tick: number, db: ClauseDB) => Promise<void>
  readonly onTickEnd?: (tick: number, db: ClauseDB, signals: ReadonlyMap<string, Term>) => Promise<void>
  readonly onNodeEvaluated?: (nodeName: string, outputs: ReadonlyMap<string, Term>) => Promise<void>
  readonly onTransitionFired?: (...) => Promise<void>
  readonly onObligationAdded?: (...) => Promise<void>
  readonly onSignalChange?: (...) => Promise<void>
  readonly onTickBoundary?: SyncPointHook   // debugger sync point
  readonly onPreFire?: SyncPointHook        // debugger sync point
}
```

**Synchronous model:** `onTickStart` fires before SNAPSHOT (giving hooks a chance to mutate the DB so mutations are included in the snapshot). `onTickEnd` fires after COMMIT. This preserves the synchronous tick structure while enabling observability.

---

## 12. Design Recommendations Summary

| DR | Principle | Status |
|---|---|---|
| DR-1 | Three-phase tick (snapshot-compute-commit) | Implemented in `runtime.step()` |
| DR-2 | Double-buffered signals with ABSENT sentinel | ABSENT sentinel implemented; double-buffer via pendingSignalWrites |
| DR-3 | Solver as synchronous node over frozen snapshot | Implemented: evaluateExpr reads snapshotDb |
| DR-4 | `fire()` as synchronous instruction; marking buffered | Implemented: pendingMarkingUpdates |
| DR-5 | ObligationObserver following synchronous observer pattern | Implemented: PetriObligationStore |
| DR-6 | Free monad as Lustre node def; multiple interpreters | Implemented: single interpreter; simulation/verify interpreters are future work |
| DR-7 | `par` as synchronous parallel; `race` as preemption | Implemented |
| DR-8 | `until` as temporal loop; absence = condition fails | Implemented |
| DR-9 | Static clock analysis on ReactiveExpr AST | Partially: `inferClocks` on SyncNodes; not on bare ReactiveExpr |
| DR-10 | Zero-cost tick rollback via immutable ClauseDB | Implemented: `db.snapshot()` + restore |

---

## 13. Open Design Question: Intra-Tick DB Visibility

*See `07-pitfalls-risks.md §3` for full analysis.*

Three options for what a `goal` call inside a `par` branch can see:

| Option | What `goal` sees | Formal model |
|---|---|---|
| **Strict synchronous (recommended)** | Only SNAPSHOT DB — asserts from other par branches are invisible | Synchronous hypothesis: all par branches see tick-N state |
| **Superdense time** | Own microstep's assertions only | Lingua Franca logical time tags |
| **Confluent writes** | All par assertions immediately visible | Violation of synchronous hypothesis; non-deterministic without commutativity proof |

**DR-1 recommendation:** Strict synchronous. Assertions from `par` branches become visible at tick N+1. This is the conservative, formally correct choice. If intra-tick DB communication is needed, use `bind` (sequential) not `par` (parallel).

---

## Bibliography

- Berry, G. & Gonthier, G. (1992). The Esterel synchronous programming language. *Science of Computer Programming*, 19(2):87-152.
- Halbwachs, N., Caspi, P., Raymond, P., Pilaud, D. (1991). The synchronous data flow programming language LUSTRE. *Proc. IEEE*, 79(9):1305-1320.
- Colaço, J.-L. & Pouzet, M. (2003). Clocks as First Class Abstract Types. *EMSOFT 2003*, Philadelphia.
- Lee, E.A. & Sangiovanni-Vincentelli, A. (1998). A Framework for Comparing Models of Computation. *IEEE Trans. CAD*, 17(12):1217-1229.
- Lohstroh, M. et al. (2021). Toward a Lingua Franca for Deterministic Concurrent Systems. *ACM TECS*, 20(4).
- aiqeung_integration.json (2026-04-07). Synchronous Reactive Principles for AIQEUNG-Core Layer 3 Runtime Design.
