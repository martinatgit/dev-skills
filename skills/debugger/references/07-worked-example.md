# aiqeung as Worked Example

This file illustrates how the principles in `01-06` apply to one concrete
multi-formalism system: aiqeung. aiqeung is a **worked example**, not the reason
the principles exist. The principles apply to any multi-formalism runtime.

**Self-contained:** All type definitions and code snippets below are embedded directly.
No live source file links are used. Verify field names against the current source if
implementing from this reference.

**Staleness note:** This file describes the implementation state at 2026-04-13.
Type names and field structures may have changed. When this file conflicts with
the live source, trust the source. The formal mappings (Byrd ports → event kinds,
Lamport ticks → logical time, etc.) are architecturally stable.

*Source module: `src/aiqeung-core/debug/` (verify current field names against live source).
Key files: `types.ts` (calling conventions, event types), `debug-interface.ts` (attach/detach,
pause/resume), `protocol-session-type.ts` (Honda session type as Term), `transport.ts`
(transport abstraction), `trace-store.ts` (self-debugging via SLD).*

---

## 1. DebugContextHeader Instantiates the Event Model

From `src/aiqeung-core/debug/types.ts`:

```typescript
interface DebugContextHeader {
  readonly syncPoint: SyncPointKind         // which formalism layer is firing
  readonly spanId: number                    // unique event ID
  readonly parentSpanId: number | null       // parent span (cross-layer causality)
  readonly tick: number                      // Layer 3: logical tick count
  readonly depth: number                     // Layer 0: SLD resolution depth
  readonly module: string | null             // Layer 5: current module
  readonly predicateFunctor: string | null   // Layer 0: predicate name
  readonly predicateArity: number | null     // Layer 0: predicate arity
  readonly netId: string | null              // Layer 2: Petri net ID
  readonly transitionName: string | null     // Layer 2: transition name
  readonly wipeoutOccurred: boolean          // Layer 4.5: domain wipeout flag
}
```

**Mapping to formal model** (§01-event-model.md):
- `syncPoint` maps to the event kind taxonomy (choice_point = SLD Byrd ports, tick_boundary = reactive, pre_fire = Petri, fixpoint = constraint)
- `spanId`/`parentSpanId` implement the span tree (cross-layer causal structure)
- `tick` implements logical time for Layer 3 (Lamport: not wall clock)
- `depth` implements logical time for Layer 0 (SLD resolution depth)
- `module` implements module-tagged events

**Formal gap in current header**: The header does not record which Byrd port
(Call/Exit/Redo/Fail) fired at a `choice_point` sync point. The Byrd port is
part of the event kind and should be in the header. Currently it would need
to be inferred from `LazyFields.candidateIndex` and `LazyFields.failedCandidates`.

## 2. LazyFields Instantiates Deferred Event Data

```typescript
interface LazyFields {
  // tick_boundary
  readonly signalValues?: () => ReadonlyMap<string, Term>
  readonly markings?: () => ReadonlyMap<string, HierarchicalMarking>
  readonly dbSnapshot?: () => ClauseDB
  // choice_point
  readonly currentGoal?: () => Term
  readonly currentSubst?: () => Subst
  readonly candidateIndex?: () => number
  readonly candidateClauses?: () => readonly Clause[]
  readonly failedCandidates?: () => readonly Clause[]
  readonly proofPathSoFar?: () => readonly ProofNode[]
  // pre_fire
  readonly enablingBinding?: () => Subst
  readonly inputTokens?: () => ReadonlyMap<string, readonly Term[]>
  readonly currentMarking?: () => HierarchicalMarking
  readonly contractInvariants?: () => readonly Term[]
  readonly guardProof?: () => ProofNode
  // fixpoint
  readonly allDomains?: () => ReadonlyMap<number, Domain>
  readonly lastNarrowings?: () => readonly DomainNarrowing[]
  readonly iterationCount?: () => number
  readonly wipeoutVariable?: () => number | null
  readonly wipeoutPropagator?: () => number | null
}
```

**Formal principle**: Each field is a thunk — a zero-argument function that
materialises the value on demand. This is the implementation of the zero-overhead
guarantee (§05-implementation.md §1): if the debugger never calls `lazy.currentGoal?.()`,
the goal's Term is never materialised.

**Correctness risk** (§03-cross-formalism.md §6): The thunks capture the SUD state
at the moment of the sync point via closure. If the SUD advances before the thunks
are called, the closures may capture stale state. Verify that all thunks close over
immutable values or snapshots, not mutable references.

## 3. protocol-session-type.ts — Honda Session Type as aiqeung Term

The session type is expressed as a nested `t.compound(...)` structure — a Term
that encodes the type using aiqeung's own term algebra. This is the single
representation principle applied to protocol specification.

**Formal principle** (§06-remote-debugging.md §4): The SUD-side type expressed
in `protocol-session-type.ts` and the DBG-side type (its dual) must be
complementary. Verify duality by examining the protocol:
- SUD sends `capabilities` → DBG must receive `capabilities`
- DBG sends `attach` → SUD must receive `attach`
- etc.

**How to use this for verification**: The session type Term can be evaluated
by aiqeung's existing session type checker (Layer 4). Running `dualOf(debugProtocolSessionType())`
should give the DBG-side type. Checking that both sides satisfy their types
against a recorded protocol trace verifies protocol conformance.

## 4. trace-store.ts — Self-Debugging Pattern

```typescript
// Reentrance guard for self-debugging
assertEvent(header: DebugContextHeader, data: Term): void {
  if (_asserting) return  // Prevent infinite recursion
  _asserting = true
  try {
    db.assert(fact(t.compound("trace_event",
      t.int(header.spanId),
      header.parentSpanId !== null ? t.int(header.parentSpanId) : t.atom("nil"),
      t.atom(header.syncPoint),
      header.module ? t.atom(header.module) : t.atom("nil"),
      data,
    )))
  } finally {
    _asserting = false
  }
}
```

**Formal principle**: Trace events are asserted as `trace_event/5` Horn clauses.
The trace is then queryable via SLD: `queryAll([t.compound("trace_event", ...)], db)`.
This is the self-debugging pattern (§05-implementation.md §4).

**Known limitation** (§04-pitfalls-risks.md §5): `_asserting` prevents recursion
in `assertEvent`, but does not prevent the SLD solver in `query()` from triggering
solver hooks. If solver hooks are installed (e.g., breakpoints), trace queries
trigger breakpoints on the trace query itself — an observer effect.

## 5. Plans A-D — Implementation Phasing

**Plan A** (completed): Unified hook system with typed calling conventions.
Establishes the formal invariant: all hook slots use Observational, Filter,
or SyncPoint calling conventions. The `DebugContextHeader` and `LazyFields`
types are defined.

**Plan B** (completed): `DebugInterface` with attach/detach, breakpoint management,
pause/resume. The cooperative pause mechanism is implemented. The fast-filter
compilation is implemented.

**Plan C** (in progress): Trace storage (`TraceStore`) and self-debugging queries.
The `queryTrace` method is stubbed (see §04-pitfalls-risks.md §3).

**Plan D** (in progress): Cross-process transport (`DebugTransport` abstraction,
stdio implementation). Socket and IPC transports are stubs.

**What is NOT yet implemented**:
- Propagator/fixpoint hooks (§04-pitfalls-risks.md §4)
- Complete `toTerm`/`fromTerm` serialization layer (§06-remote-debugging.md §3)
- Security model for the debug transport (§06-remote-debugging.md §8)
- Algorithmic debugging completeness warnings (§04-pitfalls-risks.md §7)
- Session resumption after transport drop (§06-remote-debugging.md §7)

## 6. Known Engineering Shortcuts in the Current Implementation

All shortcuts are documented in `04-pitfalls-risks.md`. From the worked example perspective:

| File | Shortcut | Formal violation |
|---|---|---|
| `process-transport.ts:10-17` | JSON Term serialization | Bijection fails for Map, BigInt, variable IDs |
| `debug-interface.ts:156` | `as any` cast on solverHooks | TypeScript type safety bypassed |
| `debug-interface.ts:64` | queryTrace throws | DebugSession interface contract unmet |
| `process-transport.ts:33-36` | socket/IPC throw | ProcessTransportOptions interface misleading |
| `types.ts` (absent) | Missing propagator hooks | PropagatorEngine not observable |
