# Core Algorithms — Formal Correctness Conditions

## 1. Cooperative Pause/Resume

**Mechanism**: At a SyncPoint, the SUD calls `syncPointHook(ctx, lazy)` and
receives either a synchronous `SyncPointCommand` or a `Promise<SyncPointCommand>`.
If the returned Promise is pending, the SUD's async task is blocked — it cannot
make progress until the Promise resolves.

**Formal semantics as continuation**: The SUD's future execution after the
SyncPoint is a continuation K. Pausing = storing K without applying it.
Resuming = applying K with the command that determines next state.

**Correctness condition**: The state observable at pause time must be identical
to the state that would have been observable if execution had continued. No
intermediate transitions may occur between the hook call and the observer's
read of `ctx` and `lazy`.

**Completeness risk**: If the SUD can make progress on other tasks while
paused (e.g., via concurrent evaluation or microtasks), the pause is not
complete — the observer may read a state that has already advanced. The
cooperative model assumes single-threaded execution within the hook boundary.

**Verify**: In aiqeung's Node.js implementation, the async Promise correctly
blocks the event loop for the paused SUD because `solve()` is a generator
(not truly async). Verify this assumption when the solver migrates to full async.

## 2. Breakpoint Filter Compilation

**Purpose**: Evaluate `BreakpointFilter` predicates against `DebugContextHeader`
without allocating or deserializing when the filter does not match. This is the
zero-overhead guarantee for the hot path.

**Correctness condition**: `compileFilter(id, filter)` must produce a function f
such that `f(ctx) = true` iff `ctx` satisfies all predicates in `filter`.

- **No false negatives**: If `ctx` should match, f(ctx) must return true.
  A false negative causes a breakpoint to be silently missed.
- **No false positives**: If `ctx` should not match, f(ctx) must return false.
  A false positive causes spurious pauses.

**Predicate composition**: All sub-predicates in BreakpointFilter are conjoined
(AND). Within a predicate (e.g., `byrdPorts: ['call', 'exit']`), the elements
are disjoint (OR). Verify this in `fast-filter.ts`.

**Module filter correctness**: If `filter.modules = ['gdpr']`, the filter must
match events where `ctx.module === 'gdpr'`. Unqualified module names must be
resolved consistently.

## 3. SLD Trace Construction

A complete SLD trace requires capturing events at all Byrd ports for every goal
in the resolution tree, including:
- Every call to a user-defined predicate
- Every call to a built-in predicate (if builtins are observable)
- All backtracking re-entries (Redo events)
- All failure paths (Fail events)

**Reentrance guard for self-debugging**: When trace events are asserted into
a `TraceStore` (ClauseDB), and the trace is queryable via the SLD solver,
the query itself may trigger further trace events — causing infinite recursion.

**Solution**: The `_asserting` flag in `trace-store.ts` is a mutual exclusion
lock on the trace DB assertion path. When asserting, any recursive call to
`assertEvent` is a no-op.

**Formal limitation**: The `_asserting` flag prevents infinite recursion on
the assertion path, but does not prevent the SLD query itself from triggering
hooks on the solver. A complete solution requires either:
(a) A separate solver instance for trace queries with hooks disabled, or
(b) A guard on the solver hooks that detects meta-level queries.

**Shapiro's meta-interpreter risk**: Shapiro (1983) §7 notes that algorithmic
debuggers implemented as meta-interpreters have a meta-level problem — the
debugger's execution generates its own events, which the debugger must ignore.
The `_asserting` guard is an instance of this known problem.

## 4. Time-Travel Under Immutable Value Semantics

**Why immutability enables time-travel for free**: When all Terms, Substitutions,
Markings, and PropagatorEngine states are immutable values, every historical
state is still a valid, reachable value — it has not been mutated. No defensive
copying is needed for historical states.

**Formal model**: Define a history H = [s₀, s₁, ..., sₙ] where each sᵢ is
an immutable state value. Time-travel to state sₖ = present sₖ to the user
without replaying any actions. Cost = O(1) lookup in H.

**Stuttering equivalence question** (Lamport 1983): When the user says "step
to state 5", what exactly is state 5? If the trace has intermediate microstates
that are observationally equivalent (stuttering), is state 5 the k-th distinct
observable state, or the k-th event in the trace?

**Design choice required**: Define the time-travel index space. Options:
1. Index by event count (every event is a step) — fine-grained but noisy
2. Index by SyncPoint count (every cooperative pause is a step) — coarser, more meaningful
3. Index by logical tick (reactive ticks, SLD depth increments) — formalism-aware

The design must specify which events count as "steps" for time-travel purposes.
This is the stuttering equivalence class definition.

## 5. Checkpoint Strategy

When full history storage is too expensive:

| Strategy | Space | Replay cost | Best for |
|---|---|---|---|
| Store every state | O(states) | O(1) | Small problems, interactive |
| Checkpoints every N states | O(states/N) | O(N replay steps) | Medium |
| Initial state + event log | O(events) | O(full replay) | Large, batch |

**aiqeung's advantage**: Immutable value semantics means "store every state"
has cost = the delta of new values created at each step (structural sharing
means unchanged subtrees are not re-allocated). In practice, much cheaper
than O(states) in a mutable system.

**rr model** (O'Callahan et al. 2017, "Engineering Record and Replay for
Deployability"): Records at the OS system call level; replays deterministically.
For aiqeung's in-process case, the analogous level is the SLD choice point
(log which clause was selected at each choice point; replay = re-run from
initial state applying the logged choices). This is cheaper than storing
full term values if term structures are large.

## 6. Galois Connection for Abstract Trace Summarization

When concrete traces are too large (millions of events), abstract traces
provide sound summaries via a Galois connection (Cousot & Cousot 1979):

```
(α: concrete traces → abstract traces, γ: abstract traces → concrete traces)
where α(T) ≤ₐ A ⟺ T ≤_c γ(A)
```

**Provenance semiring as Galois abstraction**: The Boolean semiring provenance
is an abstract trace summary — it maps the concrete derivation tree to the
set of base facts that contributed. The Galois connection is:
- α(T) = { f ∈ Facts | f contributed to any query answer in T }
- γ(F) = { T | every fact contributing to any answer in T is in F }

**For why-did/why-didn't queries**: An abstract trace is sufficient to answer
these if the abstraction preserves the contributing-fact relation. The Boolean
semiring provenance does this.

**Limitation**: Abstract traces cannot answer fine-grained questions (which
specific substitution was used). For those, the concrete trace is needed.

## 7. Delta-Debugging (Zeller & Hildebrandt 2002)

Delta-debugging minimises a failing input to a 1-minimal subset that still
causes the failure. "1-minimal" = removing any single element makes the test pass.

**Algorithm** (simplified):
1. Start with a failing input set S
2. Try removing half of S; if still failing, recurse on the smaller set
3. If removing half doesn't fail, switch to the complement; recurse
4. When no single element can be removed: report as 1-minimal

**Connection to proof trees**: A proof tree is a structured input to a
compliance analysis. Delta-debugging over proof trees = finding the minimal
set of clauses/facts whose removal changes the analysis result. This is the
formal foundation for "minimal counterexample" generation.

**Application to multi-formalism systems**: When a compliance check fails,
delta-debugging can identify which specific module contribution, which
specific Petri net marking, or which specific reactive signal caused the failure.
