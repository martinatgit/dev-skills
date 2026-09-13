# Pitfalls, Risks, and Limitations in Synchronous Reactive Systems

*Sources: reactive-system-insights.md §5.6, §8; theoretical_foundations.json; foundational_languages.json*

---

## 1. Causality Errors (Circular Signal Dependencies)

**Category:** Formal soundness violation  
**Severity:** Fatal — program rejected at compile time

### 1.1 What It Is

A causality error occurs when signal dependencies within a single tick form a cycle that the constructive fixpoint cannot resolve. The Kleene iteration reaches a fixpoint with some signals still at ⊥ (undetermined).

```esterel
-- Classic causality error
present A then emit B;   -- A must be known to determine if B is emitted
present B then emit A;   -- B must be known to determine if A is emitted
-- Fixpoint: A = ⊥, B = ⊥ → causality error
```

### 1.2 Detection

**Esterel:** Run the constructive fixpoint algorithm. If any signal remains ⊥, report a causality error with the names of the unresolved signals.

**Lustre:** Build the intra-tick dependency DAG. If the DAG has a cycle (not through `pre`), the program is ill-formed. `pre` breaks cycles because it reads the previous tick's value.

**aiqeung:** The `inter_node_cycle` clock error from `inferClocks` is the node-level analog. A cycle in the `SyncNode` dependency graph (where each node depends on another's current-tick outputs) is a causality error.

### 1.3 How to Fix

**Option 1 — Break the cycle with `pre`:**
```lustre
-- Broken cycle: A reads B from previous tick
A = ... some function of ... pre(B);
B = ... some function of ... A;
-- A depends on pre(B), not current B → DAG, no cycle
```

**Option 2 — Reorder computations sequentially:**
If A really needs B's current value: put B before A in a sequential execution order (make them different nodes, or use `bind` instead of `par`).

**Option 3 — Redesign the state machine:**
If the cycle represents a real circular dependency in the design, reconsider the design. Often a causality error reveals that two "concurrent" elements should be sequential.

### 1.4 aiqeung-Specific: `par` with ClauseDB Writes

```typescript
// Causality risk in aiqeung par
re.par(
  re.bind(re.goal(t.atom("active")), _ => re.assertFact(/* some clause */)),
  re.goal(/* query that depends on the asserted clause */)
)
```

Under **strict synchronous** semantics (recommended), the `goal` in the right branch reads the frozen snapshot — the assertion from the left branch is NOT visible. No causality error, but the dependency is invisible.

Under **confluent writes** semantics, if the right branch's goal query depends on the left branch's assertion, this IS a causality error — or at minimum, a non-deterministic ordering issue.

**Rule:** If branch B needs to see branch A's assertions, use `bind(A, _ => B)`, not `par(A, B)`.

---

## 2. Schizophrenia / Signal Reincarnation Problem

**Category:** Formal semantics trap  
**Severity:** Semantic error — program compiles but has wrong behavior if not handled

### 2.1 What It Is

In Esterel, a loop body may complete and restart within the same logical tick (if it contains no `pause`). When the loop restarts, a signal that was emitted in the first traversal has a "fresh" status in the second traversal — but the first emission still affects the current tick's signal environment.

```esterel
loop
  emit S;       -- S is emitted in first traversal
  -- loop body is instantaneous (no pause) → body restarts in same tick
  -- In second traversal: S is present (from first emission) AND has a fresh incarnation
  -- "Schizophrenic" behavior: S is both the signal emitted and a new instance
end loop
```

### 2.2 Why It Matters

Signal reincarnation can cause:
1. **Incorrect status propagation:** the second incarnation of S is treated as present (from the first emission), but logically it should be absent at the start of the second traversal
2. **Non-termination:** if the signal check in the second traversal sees S as present from the first traversal, the loop may behave unexpectedly

### 2.3 The Solution: Loop Body Must Not Be Instantaneous

**Fundamental constraint:** Every `loop` body must contain at least one `pause` statement. This prevents instantaneous re-entry.

```esterel
-- Correct: loop body pauses
loop
  emit S;
  pause;        -- suspends until next tick — loop restarts at tick N+1
end loop        -- S's status is reset at tick N+1

-- Wrong: loop body may be instantaneous
loop
  present X then emit S;  -- if X is absent, this terminates without pause
  -- → may re-enter in same tick with S still present from prior iteration
end loop
```

**The Berry-Tardieu transformation** handles cases where the compiler detects potential reincarnation. It renames each incarnation of a signal as a separate logical signal, adding initialization logic. This is linear in program size.

### 2.4 aiqeung Analog

In aiqeung's `until` operator, each iteration is a full tick — not an instantaneous restart. There is no schizophrenia problem because `until` always advances the tick counter between iterations. The loop body executes, the tick commits, and the next iteration sees a fresh tick-N+1 snapshot.

```typescript
re.until(body, cond)  // body executes once per tick; no intra-tick restart
// equivalent to: while not cond(db) { step() }
// Each iteration is a distinct tick → no reincarnation
```

---

## 3. Intra-Tick DB Visibility Trap (aiqeung-Specific)

**Category:** Design decision with formal consequences  
**Severity:** Potentially breaking — affects determinism guarantees

### 3.1 The Problem

Inside a `par` expression, both branches may modify the ClauseDB (via `assertFact` / `retract`). The question is: do these modifications become visible to other branches within the same tick?

**Three options:**

| Option | What `goal` sees | Formal model |
|---|---|---|
| **A: Strict synchronous** | Only frozen SNAPSHOT — no intra-tick writes | Synchronous hypothesis: all par branches see tick-N state |
| **B: Superdense time** | Own microstep's writes only | Lingua Franca logical time tags |
| **C: Confluent writes** | All par writes immediately visible | Violation of synchronous hypothesis |

### 3.2 Why Option C Is Dangerous

If branches can see each other's intra-tick writes:

1. **Order-dependence:** If branch A asserts `p` and branch B queries `p`, the result depends on whether A runs before or after B — **non-determinism** if branches are truly parallel.

2. **Causality error potential:** If A's assertion changes what B queries, and B's results affect what A asserts, there is a circular dependency within the tick — a causality error.

3. **Implementation complexity:** Confluent writes require either a total order (defeating parallelism) or proof of confluence (all orderings produce the same result) — complex to verify.

### 3.3 Recommendation: Option A (Strict Synchronous)

**DR-1 recommendation:** All `par` branches read from the frozen snapshot. Assertions accumulate in `pendingAssertions` and are applied only at COMMIT. No branch sees another branch's intra-tick writes.

**aiqeung current behavior:** The `runtime.step()` creates `snapshotDb` via `copyDb(db)` before COMPUTE. Each node gets a `nodeDb = copyDb(snapshotDb)`. Node writes go to `pendingAssertions`, not to `snapshotDb`.

**How to use `bind` when intra-tick communication is needed:**
```typescript
// WRONG: par — assertion from left not visible to right goal
re.par(
  re.assertFact(fact("status", t.atom("active"))),
  re.goal(t.compound("status", [t.var("S")]))  // may not see "active"
)

// CORRECT: bind — sequential; assertion visible to subsequent goal
re.bind(
  re.assertFact(fact("status", t.atom("active"))),
  _ => re.goal(t.compound("status", [t.var("S")]))  // always sees "active"
)
```

### 3.4 Option B (Superdense Time) as a Middle Ground

For sequential `fire()` chains that need intra-tick causal ordering, microstep advancement is appropriate:

```typescript
// Sequential fire chain: T2 sees T1's marking update
re.bind(
  re.fire("net1", "page", "T1"),  // fires at (N, 0)
  _ => re.fire("net1", "page", "T2")  // fires at (N, 1), sees T1's marking
)
```

This uses Option B for Petri net markings (sequential `bind` uses microsteps) while using Option A for `par` branches. This is the recommended hybrid.

---

## 4. Clock Mismatch in Polychronous Composition

**Category:** Type error (clock calculus violation)  
**Severity:** Compile-time error — well-clocked programs cannot exhibit this

### 4.1 What It Is

A clock mismatch occurs when stream expressions on incompatible clocks are combined:

```lustre
-- Clock mismatch example
sensor_fast : int on base            -- ticks every tick
sensor_slow : int on (base on slow)  -- ticks only when slow = true

-- WRONG: combining streams on different clocks
average = (sensor_fast + sensor_slow) / 2;
-- sensor_fast ticks at base, sensor_slow at (base on slow)
-- Clock unification fails: clock mismatch error
```

### 4.2 The Fix

**Option 1 — Subsample the faster stream:**
```lustre
fast_when_slow = sensor_fast when slow;  -- fast subsampled to slow clock
average = (fast_when_slow + sensor_slow) / 2;  -- both on (base on slow)
```

**Option 2 — Upsample the slower stream (sample-and-hold):**
```lustre
slow_held = current(sensor_slow);  -- hold last value of slow at every base tick
average = (sensor_fast + slow_held) / 2;  -- both on base
```

### 4.3 aiqeung Clock Errors

The `clock_mismatch` error from `inferClocks` is the aiqeung analog. When two signals are defined on different clock conditions and used in the same equation without proper guarding, clock inference fails.

**Prevention:** Use `when` (subsampling) and `merge` (reconstruction) to explicitly reconcile clock domains before combining streams.

---

## 5. Single-Clock vs. Multi-Clock Trade-Offs

**Category:** Architectural decision  
**Severity:** Design-level — affects expressiveness and complexity

### 5.1 Single-Clock Model (Lustre-style)

**Advantages:**
- Simpler semantics: one tick = one reaction for all signals
- Absence reasoning is straightforward: absent at this tick = absent at the unique tick
- Clock inference is simpler (one base clock, subclocks derived from it)
- Easier to verify (model checker operates on one tick at a time)

**Limitations:**
- Multi-rate systems require explicit subsampling: sensors at different rates need `when` operators
- Clock hierarchy can become complex for many different rates
- No native support for truly independent clocks

### 5.2 Multi-Clock Model (Signal-style, polychronous)

**Advantages:**
- Directly models GALS (Globally Asynchronous, Locally Synchronous) architectures
- Each component can have its own clock — no forced synchronization
- More natural for embedded systems with heterogeneous timing

**Limitations:**
- Non-compositionality: clock compatibility must be checked between components
- More complex inference: constraint solving across multiple clock domains
- Harder to verify: multi-clock systems require more sophisticated model checking

**For aiqeung:** The single-clock model (base clock, with optional `when` subclocks) is the correct choice for the compliance monitoring use case. Compliance monitoring typically has a single observation period (the tick), not multiple independent clocks.

### 5.3 Multi-Rate in aiqeung

If different compliance obligations need to be checked at different rates:

```lustre
-- Slow clock: every 24 ticks (daily check)
daily = (false -> (if (true -> pre(tick_count) + 1) >= 24 then true else false));

-- Daily obligation check (only at daily clock)
art33_check = ObligationArt33(
  breach_detected when daily,   -- only sample at daily ticks
  ...
) when daily;
```

This uses Lustre-style subsampling within the single-clock model — no need for Signal's polychronous model.

---

## 6. Performance Pitfalls

**Category:** Engineering risk  
**Severity:** Runtime — may cause latency or memory issues

### 6.1 Snapshot Cost

Every `step()` creates a copy of the ClauseDB (`copyDb` in runtime.ts). For large databases:

- **Risk:** `copyDb` is O(n) in number of clauses — expensive for large knowledge bases
- **Mitigation:** Use persistent/immutable data structures for the ClauseDB (O(1) snapshot via structural sharing). The `db.snapshot()` method should be O(1) reference capture, not O(n) copy.

**Current aiqeung implementation:** `copyDb` does a full copy (runtime.ts, copyDb function). This is correct but O(n). For large databases, this becomes the bottleneck.

**Sound optimization:** Implement ClauseDB as a persistent trie or hash-array mapped trie (HAMT). Then `snapshot()` is O(1) and `copyDb` is also O(1).

### 6.2 Transaction Merge Complexity

When `par` branches accumulate many assertions/retractions, the COMMIT phase must merge them all. Conflicts (two branches asserting contradictory facts) must be detected:

- **Risk:** O(assertions²) conflict detection if done naively
- **Mitigation:** Under strict synchronous discipline (Option A), there are no intra-tick conflicts — each node's writes target different predicate keys (by design). Verify this constraint statically.

### 6.3 Observer Memory Growth

Obligation observers that track history across ticks can accumulate unbounded state:

- **Risk:** An observer that stores every past marking (for debugging) grows without bound
- **Mitigation:** LOLA-style bounded memory: observers should require O(1) state per tick. The `PetriObligationStore` in aiqeung is immutable but does NOT grow per tick — it stores the current set of obligations, not the history.

**Check:** Each `ObligationObserver.observe()` call should return a verdict without retaining the marking. If historical markings are needed, store at most a fixed window.

### 6.4 SLD Resolution Depth

`goal` queries inside a tick run SLD resolution. Deep resolution trees can be expensive:

- **Risk:** A query that triggers a long chain of rule applications can make a single tick take unbounded time
- **Mitigation:** Use the `tablingMaxStates` limit in `RuntimeOptions` to bound resolution depth. Design knowledge bases to avoid deep recursive rules.

---

## 7. Endochrony vs. Isochrony Non-Compositionality

**Category:** Formal property pitfall  
**Severity:** Architectural — affects modular system design

### 7.1 Endochrony

**Definition:** A synchronous component is **endochronous** when it can infer the presence/absence of each input from its internal state and currently known inputs — it can self-determine its activation pattern.

**Problem:** Endochrony is **NOT compositional**: the parallel composition of two endochronous programs is not guaranteed to be endochronous. This was proven by Benveniste et al. (2003).

**Implication for aiqeung:** Do not rely on endochrony of individual `par` branches to guarantee endochrony of the composed system. The composition must be analyzed as a whole.

### 7.2 Isochrony (the compositional alternative)

**Definition:** A synchronous component is **isochronous** if it is flow-preserving under desynchronization — its behavior is the same whether scheduled by a global clock or by individual component clocks.

**Key property:** Isochrony IS compositional: the parallel composition of two isochronous components is isochronous (Benveniste et al. 2003).

**How to achieve:** Use endochrony where possible within each node. At the composition level, verify isochrony of the interface. Kind2 can model-check isochrony properties.

### 7.3 Practical Impact

For aiqeung's compliance observer composition:

```
GDPRBreachComposite = ObligationArt33 || ObligationArt34 || ObligationArt35
```

Even if each obligation observer is individually endochronous (can determine its own activation), the composed system may not be. Verify the composed system's temporal behavior with Kind2, not individual components.

---

## 8. Common Engineering Shortcut Antipatterns

| Shortcut | Formal violation | Sound alternative |
|---|---|---|
| Using `par` when intra-tick communication is needed | Violates synchronous hypothesis (branches may see stale state) | Use `bind` for sequential dependence |
| Omitting `pause` in a loop body | Schizophrenia risk in Esterel; undefined in aiqeung `until` | Always ensure `tick` advances between loop iterations |
| Using ABSENT as a default value, not a sentinel | Breaks closed-world assumption | Never compare to ABSENT directly; use `isAbsent()` |
| Assuming absence means "not yet arrived" | Violated the synchronous hypothesis | Treat absence as a formal fact: "definitively absent at this tick" |
| Mixing clocks without `when`/`merge` | Clock calculus violation → clock mismatch error | Explicitly reconcile clocks at the composition boundary |
| Assuming endochrony composes | Non-compositionality of endochrony (Benveniste 2003) | Verify the composed system, not just individual components |
| Making observers stateful across ticks with unbounded history | Memory growth; LOLA bound violated | Store O(1) state per tick; discard old data |

---

## Bibliography

- Berry, G. (2002). *The Constructive Semantics of Pure Esterel*, Draft Version 3.
- Berry, G. & Tardieu, O. (2007). SCADES. In *Compiling Esterel* (Potop-Butucaru et al.).
- Benveniste, A. et al. (2003). The Synchronous Languages 12 Years Later. *Proc. IEEE*, 91(1):64-83.
- Colaço, J.-L. & Pouzet, M. (2003). Clocks as First Class Abstract Types. *EMSOFT 2003*.
- D'Angelo, B. et al. (2005). LOLA: Runtime Monitoring of Synchronous Systems. *TIME 2005*.
- Lohstroh, M. et al. (2021). Toward a Lingua Franca for Deterministic Concurrent Systems. *ACM TECS*, 20(4).
