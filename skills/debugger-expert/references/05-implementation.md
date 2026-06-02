# Implementation Strategies — Preserving Formal Properties

## 1. Zero-Overhead Guarantee

**Requirement**: When no debugger is attached, the SUD incurs zero computational
overhead from the debug infrastructure.

**PEP 669 model** (Python sys.monitoring): Events are generated only when a
subscriber exists. If no handler is registered for a given event kind, the
event is not generated — not a no-op call, but genuinely not generated.

**Correct implementation**: The hook slot check must be at the call site before
any event data is assembled. Pattern:

```typescript
// CORRECT: check hook existence before assembling event data
if (solverHooks.onChoicePoint !== undefined) {
  const ctx = buildDebugContextHeader(...)  // Only assembled if needed
  const lazy = buildLazyFields(...)
  await solverHooks.onChoicePoint(ctx, lazy)
}

// INCORRECT: event data assembled unconditionally
const ctx = buildDebugContextHeader(...)   // Paid even when no hook
const lazy = buildLazyFields(...)
if (solverHooks.onChoicePoint !== undefined) {
  await solverHooks.onChoicePoint(ctx, lazy)
}
```

**LazyFields**: The `LazyFields` pattern is the implementation of deferred
event data. Fields are thunks (zero-argument functions) that compute state
only when called. If the debugger never calls `lazy.currentGoal?.()`, the
current goal's Term is never materialized — zero cost.

## 2. Hook Composition

When multiple hooks need to be installed on the same hook slot (e.g., a
tracing hook plus a breakpoint hook), they must be composed correctly.

**Composition for Observational hooks**: Run all hooks in sequence. Order
should not matter (observers are independent).

```typescript
function composeObservational<A extends any[]>(
  hooks: ObservationalHook<A>[]
): ObservationalHook<A> {
  return (...args) => { for (const h of hooks) h(...args) }
}
```

**Composition for SyncPoint hooks**: Run hooks in priority order. The first
hook that returns `{ kind: 'pause' }` wins — subsequent hooks are not called.
If all hooks return `{ kind: 'continue' }`, the engine proceeds.

**Correctness condition**: Hook composition must preserve the calling convention
contract. A composed SyncPoint hook must still return `Promise<SyncPointCommand> | SyncPointCommand`.

**Failure mode**: If hooks are installed by direct slot assignment (as in the
current implementation), the previous hook is overwritten. The current
implementation saves and restores exactly one previous hook, which is correct
only if at most one debugger attaches. Multiple debuggers require composition.

## 3. Observer-as-SyncNode for Reactive Debugging

**Pattern**: The debugger participates in the reactive tick as a SyncNode
that reads signals from the SUD nodes. It does not write signals that SUD
nodes read.

**Non-intrusiveness conditions** (Halbwachs et al. 1992):
1. The observer reads only signals that are already emitted by the SUD
2. The observer does not emit signals that the SUD reads
3. The observer's clock is compatible with the SUD's clock hierarchy

**Implementation guide**: The debug SyncNode should have:
- Input signals: all signals from any SUD node the user wants to observe
- Output signals: none that the SUD reads (diagnostic outputs only, e.g., to a trace buffer)
- Clock: the base clock (runs every tick)

**Violation to watch for**: If the debugger SyncNode's `clock_activate` event
causes a previously-absent signal to become "read", this changes the signal's
status in the synchronous semantics. In Esterel/Lustre, a signal is present
if it was emitted, absent if it was not — reading it does not affect its status.
Verify that aiqeung's signal model has this property.

## 4. Trace-as-Clauses Self-Debugging

**Pattern**: Trace events are asserted as `trace_event/5` clauses into a
dedicated ClauseDB. The trace is then queryable using the standard SLD solver.

```prolog
% Trace event schema
% trace_event(SpanId, ParentSpanId, SyncPointKind, Module, Data)
trace_event(42, 41, choice_point, "gdpr", call_data(obligation/2)).
trace_event(43, 42, choice_point, "gdpr", exit_data(obligation/2, [notify])).

% Example queries
% Find all goals that failed in module gdpr:
?- trace_event(Id, _, _, "gdpr", _), ...
```

**Formal elegance**: The trace is itself a knowledge base queryable via the
same reasoning engine. This is the Single Representation Principle applied
to debugging.

**Reentrance guard**: The `_asserting` flag prevents infinite recursion when
asserting trace events. See `04-pitfalls-risks.md §5` for the limitation —
trace queries can still trigger hooks on the solver.

**Scalability**: For large traces (millions of events), the ClauseDB becomes
large. Consider: (a) trace rotation (keep last N events), (b) abstract trace
summarization (Galois connection — see `02-algorithms.md §6`).

## 5. Module-Tagged Events

**Requirement**: Every trace event must carry `currentModule` from the
`ExecutionContext`. This enables filtering by module and cross-module
provenance tracking.

**Correctness condition**: `currentModule` must be monotone during resolution —
it must not change mid-clause (a clause belongs to one module; the module
context switches at clause boundaries, not mid-body).

**Module boundary events**: When the module context switches (a meta-predicate
call or a `::` qualified call), the trace must include a module-boundary event
that records the old and new module. Otherwise, module-tagged filtering is
ambiguous for cross-module calls.

**Qualified names in trace output**: Format trace events using qualified names:
`gdpr::obligation/2 [Call depth=3]`. This makes cross-module traces readable
without requiring the user to separately track module context.

## 6. Abstract Machine Observation Points

**Kishon, Marsland & Benford (1994)**: Not every abstract machine transition
is a legal observation point. Observable transitions are those where the
abstract machine's observable state changes in a distinguishable way.

**For the SLD solver**:
- Legal observation points: clause head unification (call), clause body
  completion (exit), choice point creation (before redo), alternative
  exhaustion (fail)
- Internal transitions (not observation points): internal registers, trail
  manipulation, temporary unification variables

**Rule**: If you cannot specify what the observable state is at a proposed
hook point, it is probably not a legal observation point. An observation point
must have a well-defined `DebugContextHeader` that can be materialized.

## 7. Program Slicing Connection to Provenance

**Weiser (1984) program slicing**: A slice of program P with respect to
criterion (v, p) (variable v at point p) is the minimal subset of P's
statements that contributed to v's value at p.

**Kamkar (1993) logic program slicing**: Extended to Prolog — the slice of a
goal G is the set of clauses that contributed to G's proof. Computed from
the SLD proof tree.

**Green (2007) semiring provenance generalises slicing**: The Boolean semiring
instance (each base fact is 0 or 1) gives the slice — the set of facts that
contributed. Richer semirings give more information (counting semiring: how
many derivation paths used each fact; tropical semiring: which path was
shortest).

**Implementation connection**: The `ProofNode` records the derivation tree.
Extracting the Boolean semiring provenance from a `ProofNode` gives the
slice — which clauses contributed to the result. This is the formal foundation
for "why did this compliance conclusion hold?" queries.
