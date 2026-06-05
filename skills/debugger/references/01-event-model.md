# Event Model — Formal Foundations

## 1. What is a Trace?

A **trace** is a sequence (or partial order) of **events**, where each event
records one observable transition in the SUD.

Formal definition: A trace T over event set E is a structure (E, ≤, λ) where:
- E is a set of event occurrences
- ≤ is a partial order on E (causal ordering)
- λ: E → EventKind assigns each event a kind

For a sequential system (SLD resolution), ≤ is total order. For a concurrent
system (Petri net + reactive), ≤ is a partial order.

## 2. Soundness and Completeness

**Soundness**: Every event in the trace corresponds to an actual transition in
the SUD. The trace contains no spurious events. Formally: λ(e) fires at the
SUD state recorded in e's context.

**Completeness**: Every observable transition in the SUD produces at least one
event in the trace. No observable transition is silently skipped. Formally:
if the SUD makes a transition t at an observable point, then ∃e ∈ T: e records t.

**Observable transition**: Not every internal step of the abstract machine is
an observable transition. Kishon, Marsland & Benford (1994) "Explicating
Abstract Machines" formalise this: observable transitions are those at which
the abstract machine's observable state changes in a way that the user can
distinguish. Internal bookkeeping (register allocation, garbage collection)
is not observable.

**Why both matter**: A sound-but-incomplete trace lies by omission — it hides
transitions. A complete-but-unsound trace lies by commission — it invents
transitions. Both undermine the debugger's correctness.

## 3. Per-Formalism Event Taxonomy

### 3.1 SLD Resolution (Layer 0)

Based on Byrd (1980) four-port model, extended:

| Event kind | Port | Triggered when |
|---|---|---|
| `call` | Call | Goal is entered for the first time |
| `exit` | Exit | Goal succeeds, producing a binding |
| `redo` | Redo | Backtracking re-enters goal seeking another alternative |
| `fail` | Fail | All alternatives for goal are exhausted |
| `exception` | Exception | Goal throws an error term |
| `cut` | Cut | `!` commits, pruning remaining alternatives |
| `builtin_call` | — | A built-in predicate is invoked |
| `builtin_result` | — | A built-in predicate returns its result |

**Completeness check for SLD**: Is there any SLD transition not covered by
these 8 kinds? Specifically: unification events (Unify port in some systems)
and meta-interpretation crossings (calling a goal in a different module).

### 3.2 Petri Net (Layer 2)

Refer to `petri-net-theory` skill for Petri net formal foundations.
From the debugger perspective:

| Event kind | Triggered when |
|---|---|
| `transition_enabled` | A transition becomes enabled (precondition satisfied) |
| `transition_fire` | A transition fires, consuming and producing tokens |
| `transition_blocked` | A transition was enabled but blocked (guard failed, contract violated) |
| `marking_change` | The marking changes (consequence of firing) |

**Completeness for Petri nets**: The firing sequence is observable; the
enabledness relation changes are observable. Internal marking computation is
not observable.

**Petri net pause semantics**: "Pausing" a Petri net mid-firing is semantically
undefined (a firing is atomic in P/T nets). A breakpoint must fire at
pre-fire or post-fire, not during. This is a fundamental constraint on
Petri net debugger design.

### 3.3 Synchronous Reactive (Layer 3)

Based on Halbwachs (1991) Lustre/SCADE observer model:

| Event kind | Triggered when |
|---|---|
| `tick_start` | A reactive tick begins |
| `snapshot` | Signal values are snapshotted at tick start |
| `compute` | A node computes its output for this tick |
| `commit` | Tick results are committed; state updates |
| `signal_emit` | A signal is emitted with a value |
| `signal_read` | A signal value is read by a node |
| `clock_activate` | A clock signal becomes active |
| `clock_deactivate` | A clock signal becomes inactive |

### 3.4 Constraint Propagation (Layer 4.5)

Extended from ECLiPSe delay/wake model:

| Event kind | Triggered when |
|---|---|
| `propagator_wake` | A propagator is scheduled (domain change woke it) |
| `domain_narrow` | A variable's domain is narrowed by a propagator |
| `domain_wipeout` | A variable's domain becomes empty (failure) |
| `fixpoint_reached` | Propagation converges: no propagator can narrow further |
| `theory_assert` | A theory-level equality or disequality is asserted |
| `equality_shared` | Nelson-Oppen equality propagation between theories |

**Constraint pause semantics**: A breakpoint during propagation observes a
*pre-fixed-point* state — the constraint store is not in a semantically
valid state (it is in the process of converging). Per Frühwirth (1998)
Constraint Handling Rules, valid states are only fixed points. A debugger
must document whether it shows pre-fixed-point states and what their
interpretation is.

### 3.5 Reasoning Contexts (Layer 4)

| Event kind | Triggered when |
|---|---|
| `context_open` | A scoped reasoning context is opened |
| `context_promote` | Context results are promoted to the parent |
| `context_discard` | Context is discarded, results abandoned |
| `channel_send` | A message is sent on a session-typed channel |
| `channel_recv` | A message is received |
| `session_advance` | The session type position advances |

### 3.6 Module System (Layer 5)

| Event kind | Triggered when |
|---|---|
| `module_load` | A module is loaded and its clauses asserted |
| `module_seal` | A module is sealed (no further contributions) |
| `contribution_merge` | An open predicate receives a new clause contribution |
| `stratification_check` | Module stratification is verified |

## 4. Formal Semantics of the Three Calling Conventions

### 4.1 Observational Hook

`ObservationalHook<Args>: (...args: Args) => void`

- **Contract**: Fire-and-forget. The hook is called with the current state; it
  observes but cannot affect execution.
- **Formal guarantee**: The hook has no effect on the SUD's next state.
  Formally: next_state(SUD) is independent of whether the hook is present.
- **Soundness condition**: The hook must not mutate shared state. If it does,
  the non-intrusiveness condition (Halbwachs 1992) is violated.

### 4.2 Filter Hook

`FilterHook<Args>: (...args: Args) => boolean`

- **Contract**: Returns a boolean. True = include this candidate; False = skip.
  Used for clause/candidate selection.
- **Formal guarantee**: The filter is applied before the SUD commits to a
  candidate. The SUD's search space is pruned by the filter's results.
- **Soundness risk**: A filter that incorrectly returns false can prune a
  branch that the SUD would have explored, changing the SUD's observable
  semantics. Filters must be semantics-preserving or explicitly documented
  as semantics-altering.

### 4.3 SyncPoint Hook

`SyncPointHook<Args>: (...args: Args) => Promise<SyncPointCommand> | SyncPointCommand`

- **Contract**: The SUD calls this at a sync point and blocks until the hook
  resolves. The resolved command steers execution: continue, pause, step,
  deny_fire, detach.
- **Formal guarantee**: The SUD is in a defined observable state when the hook
  is called; no further SUD transitions occur until the command is resolved.
- **Cooperative semantics**: Pause is implemented as an unresolved Promise.
  The SUD's event loop is blocked (it cannot make progress). This is the
  formal mechanism for cooperative debugging.
- **Correctness condition**: The state observed at a SyncPoint must be exactly
  the state the SUD was in when the hook fired — no intermediate transitions.
  The Promise chain must not introduce intermediate transitions.

## 5. Formal Semantics of Spy Points, Breakpoints, and Watchpoints

These are three distinct primitives with different formal semantics. Conflating
them is a common implementation error.

### 5.1 Spy Point

A **spy point** is a predicate-level marker. When a goal with the marked
predicate functor/arity passes through any Byrd port, a trace event fires.

**Formal model**: A spy point S on predicate p is a relation over the trace:
  `spy_event(e, S) ↔ (λ(e).predicate = p) ∧ (λ(e).kind ∈ {call, exit, redo, fail, exception})`

**Interaction with backtracking**: A spy point fires on Redo — when backtracking
re-enters the clause. This is correct and expected behaviour.

### 5.2 Breakpoint

A **breakpoint** is a program-point annotation — it fires when execution
reaches a specific location in the source code or abstract machine.

**Formal model**: A breakpoint B at location L fires when the SUD's program
counter (or analogous location marker) equals L.

**Critical question — Redo behaviour**: If a breakpoint is at the head of
clause C, and C is called, fails, and is re-entered via backtracking (Redo):
does the breakpoint fire on Redo?

**Answer depends on definition**: If the breakpoint is defined over the trace
as a stream of events, it fires every time the event for location L appears,
including on Redo. If defined as a program-point condition on the abstract
machine, it fires only when the PC moves to L, which includes Redo. Either
way, the definition must be explicit — not implicit.

### 5.3 Watchpoint

A **watchpoint** is a data-conditional halt — it fires when a specified data
condition becomes true (e.g., a variable is bound, a domain narrows below a
threshold).

**Formal model**: A watchpoint W with condition φ fires at the first event e
in the trace such that φ(state(e)) is true.

**Interaction with backtracking**: If a watchpoint fires during a branch that
subsequently fails, backtracking restores the pre-binding state. The watchpoint
must be re-armed for the restored state. Whether the watchpoint re-fires on
the Redo branch is an implementation choice that must be documented.

## 6. Concrete Instantiation: DebugContextHeader

The `DebugContextHeader` type (from `src/aiqeung-core/debug/types.ts`) is one
concrete instantiation of the abstract event model defined above. See
`07-worked-example.md` for the full mapping.

Key properties:
- `syncPoint: SyncPointKind` maps to the four SyncPoint kinds (tick_boundary,
  choice_point, pre_fire, fixpoint)
- `spanId / parentSpanId` implement the span tree (cross-layer parent-child)
- `tick: number` is the logical tick count (Lamport logical time, not wall clock)
- `depth: number` is the SLD resolution depth (logical time for the solver)
- `module: string | null` implements module-tagged events
