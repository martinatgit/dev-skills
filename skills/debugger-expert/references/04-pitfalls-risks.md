# Engineering Shortcuts — Formal Shortcut Catalogue

Each entry: shortcut description → formal property violated → citation → sound alternative.

---

## 1. JSON Term Serialization for Cross-Process Transport

**Shortcut**: Use `JSON.stringify` / `JSON.parse` to serialize Terms for the
stdio/socket transport.

**Formal property violated**: The serialization must be a bijection on the
set of Term values — serialize(t₁) = serialize(t₂) implies t₁ = t₂, and
every serialized value deserializes to a valid Term.

**Violations in current implementation** (`process-transport.ts`):
- `Map` fields (in Record terms, Subst maps): `JSON.stringify` converts Maps
  to empty objects `{}`. Deserialized Subst is structurally wrong.
- `BigInt` values: `JSON.stringify` throws `TypeError: Do not know how to
  serialize a BigInt`. Any Term containing BigInt causes a transport failure.
- Variable IDs: Variable terms carry integer IDs unique within one process.
  Across processes, two variables may have the same ID. Unification over the
  transport using these IDs is unsound — two distinct variables may be
  conflated.

**Sound alternative**: Implement a complete `toTerm(t: Term): JsonEncoding` /
`fromTerm(j: JsonEncoding): Term` bijection that handles all Term variants
including Map fields, BigInt, and globally unique variable IDs (e.g., prefixed
with process ID).

---

## 2. `as any` Casts in Hook Installation

**Shortcut**: Cast hook targets to `any` before writing to readonly hook slots:
```typescript
const solverHooks = this.targets.solverHooks as any
solverHooks.onChoicePoint = this.makeSyncPointHook()
```

**Formal property violated**: TypeScript's type system verifies that the
installed hook matches the hook slot's declared calling convention. The `as any`
cast bypasses this verification.

**Risk**: If `makeSyncPointHook()` returns a function with a different signature
than `SolverHooks.onChoicePoint` expects, the mismatch is undetected until
runtime. The calling convention type (`SyncPointHook<[DebugContextHeader, LazyFields]>`)
is load-bearing — it ensures the hook can receive the right arguments and return
the right command type.

**Sound alternative**: Either make hook slots mutable with explicit types
(remove `readonly` from the hook slots, document that only the debug interface
may write them), or use a type-safe hook registry that validates the installed
hook's signature before installation.

---

## 3. `queryTrace` Stub

**Shortcut**: `queryTrace` in `DebugSessionImpl` throws `"Not yet implemented"`.

**Formal property violated**: The `DebugSession` interface contract includes
`queryTrace`. A stub that throws does not implement the contract — it is a
broken API. Callers who check only the interface (not the implementation) will
encounter runtime errors.

**Risk**: Any code that calls `session.queryTrace(filter)` at runtime will
crash, including any LLM-driven debugging tool that uses the trace query API.

**Sound alternative**: Either remove `queryTrace` from the `DebugSession`
interface until implemented (breaking API change, but honest), or implement
a minimal version (query the in-memory `TraceStore` synchronously) even if
it lacks full functionality.

---

## 4. Missing Fixpoint/Propagator Hooks

**Shortcut**: The `PropagatorEngine` (Layer 4.5) has no debug hooks in the
current implementation. The `fixpoint` SyncPoint kind is defined in
`SyncPointKind` but no hook fires it.

**Formal property violated**: The constraint store is not fully observable —
constraint propagation steps are invisible to the debugger. A complete event
model (§01-event-model.md §3.4) requires `propagator_wake`, `domain_narrow`,
`domain_wipeout`, and `fixpoint_reached` events.

**Risk**: Bugs in constraint propagation (wipeout conditions, incorrect domain
narrowing) are undetectable by the debugger. The user cannot inspect the
constraint store's evolution.

**Sound alternative**: Add `PropagatorHooks` to the PropagatorEngine with
the same three-tier calling convention structure (Observational for passive
observation, SyncPoint for pause-at-fixpoint). This parallels `SolverHooks`.

---

## 5. Observer Effect Risk in Self-Debugging

**Shortcut**: The `TraceStore` asserting reentrance guard (`_asserting` flag)
prevents infinite recursion in `assertEvent`, but does not prevent the SLD
solver used for trace queries from triggering solver hooks.

**Formal property violated**: Shapiro (1983) §7 identifies the meta-level
problem: a debugger that is itself a debuggable system generates its own trace
events, which the debugger must either ignore or handle without infinite regress.

**Concrete risk**: When `TraceStore.query(goal)` invokes the SLD solver to
search the trace ClauseDB, if solver hooks are installed (e.g., a SyncPoint
hook for breakpoints), the trace query solver will also trigger breakpoints.
This is an observer effect: observing the trace changes the trace.

**Sound alternative**: The trace query solver must run with all debug hooks
disabled, or with a dedicated hook configuration that identifies trace-query
calls and skips them. The meta-level of the trace should be outside the
observational scope of the debug hooks.

---

## 6. Variable ID Collision Across Processes

**Shortcut**: Variable terms carry integer IDs generated monotonically within
one process. When transmitted across the stdio transport to a second aiqeung
process, two distinct variables may have the same ID.

**Formal property violated**: The substitution σ must be a function from
variable IDs to Terms. If two variables share an ID across processes,
σ(x) is ambiguous — it cannot distinguish which variable is being mapped.
Unification over the combined substitution is unsound.

**Risk**: In the two-instance SUD/DBG architecture, the DBG process's variables
and the SUD process's variables may collide. Any unification that the DBG
attempts over SUD-transmitted Terms may incorrectly merge distinct variables.

**Sound alternative**: Variable IDs must include a process-unique prefix in
the cross-process serialization. The `toTerm`/`fromTerm` layer must namespace
variables by process or connection, ensuring global uniqueness.

---

## 7. Cut Incompleteness — Undocumented Limitation

**Shortcut**: The debugger's algorithmic debugging mode does not warn when
cut (`!`) is present in the call stack, even though this makes algorithmic
debugging incomplete (Pereira & Calejo 1993).

**Formal property violated**: The user relies on the debugger to locate bugs.
If the debugger cannot guarantee completeness and does not warn, the user may
conclude "no bug found" when in fact the bug is in a cut-pruned branch.

**Sound alternative**: Detect cut events in the trace. When algorithmic
debugging is active and a cut event is observed, emit a warning: "Cut detected
in call stack — algorithmic debugging may not locate bugs in cut-pruned branches."

---

## 8. Observation Interference / Heisenbug Risk

**Shortcut**: The debugger's SyncNode observer is assumed to be non-intrusive
because it reads signals without writing to them. Non-intrusiveness is asserted
without formal verification.

**Formal property violated**: Berry & Gonthier (1992) prove conditions under
which adding an observer to an Esterel program preserves semantics. The
conditions are non-trivial and require proof for each observer. For the
synchronous reactive layer, no such proof exists.

**Risk**: Adding a SyncNode debugger may change which signals are present/absent
in a tick if the observer creates new signal dependencies. This is a Heisenbug:
the observed program behaves differently when observed.

**Sound alternative**: Require that all debugger SyncNodes are provably
input-only with respect to the signals they observe. Document any signal the
debugger reads and verify that the signal's presence/absence status is
determined by the SUD, not by whether the debugger reads it.

---

## 9. Spy Point Re-Fire on Redo — Undefined Behaviour

**Shortcut**: Whether a spy point (or breakpoint at a clause head) re-fires
when backtracking re-enters the clause via Redo is not specified.

**Formal property violated**: The formal semantics of spy points (§01-event-model.md §5)
requires an explicit definition. If Redo behaviour is unspecified, different
implementations may behave differently, making the debugger non-deterministic.

**Sound alternative**: Specify explicitly: a spy point fires on all Byrd ports
including Redo. A breakpoint at a clause head fires on Call and Redo (both
correspond to "entering the clause"). Document this in the debug API.

---

## 10. Socket/IPC Transports Unimplemented

**Shortcut**: `createProcessTransport` for `'socket'` and `'ipc'` throws
`"not yet implemented"`. Remote debugging over a network or IPC pipe is
unavailable.

**Formal property violated**: The `DebugTransport` interface contract claims
to support `'socket'` and `'ipc'` kinds. The implementation does not.

**Risk**: Any tool that attempts to use socket or IPC transport will fail at
runtime with an unimplemented error. The API is misleading.

**Sound alternative**: Remove `'socket'` and `'ipc'` from `ProcessTransportOptions`
until implemented, OR implement them. The stdio transport is a correct reference
implementation; a TCP socket transport is straightforward using Node.js `net`.

---

## 11. LazyFields Materialisation Race (Bisimulation Violation)

**Shortcut**: `LazyFields` provides deferred evaluation of expensive state.
If the SUD continues to make transitions between the SyncPoint call and the
DBG's call to `lazyFields.get()`, the materialised value may not correspond
to the SUD state at the sync point.

**Formal property violated**: Milner (1989) bisimulation faithfulness criterion
(§03-cross-formalism.md §6). The debugger's model shows a state the SUD was
not actually in when the sync point fired.

**Sound alternative**: The SUD must be fully paused before any lazy field
evaluation occurs. The cooperative pause model (Promise-based blocking) ensures
this for in-process debugging. For remote debugging, the SUD must not make
transitions between sending the sync_point message and receiving the
request_fields/continue response.
