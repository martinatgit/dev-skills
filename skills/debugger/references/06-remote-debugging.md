# Remote Debugging — Transport, Protocol, and Formal Correctness

## 1. DebugTransport Interface — Formal Requirements

Any transport implementation must satisfy:

```typescript
interface DebugTransport {
  send(message: Term): Promise<void>       // Reliable, ordered delivery
  receive(): AsyncIterable<Term>           // Complete: terminates when connection closes
  close(): void                            // Terminates both directions
  onClose(handler: () => void): void       // Transport-level close notification
  readonly connected: boolean
}
```

**Formal requirements on `send`**:
1. Reliable: if `send(m)` resolves, m will eventually be delivered to the receiver
2. Ordered: messages are delivered in send order (FIFO per connection)
3. Atomic: each Term is delivered as a complete unit (no partial messages)

**Formal requirements on `receive`**:
1. Complete: the async iterable completes (yields done:true) when the connection closes
2. Non-blocking: if no message is available, the iterator parks (waits) rather than returning undefined

**Correctness condition for close**: `close()` must resolve any parked receivers
with `done:true`. If receivers are not resolved on close, the receiver will hang
forever (a deadlock in the debug session cleanup).

## 2. In-Process Zero-Copy Correctness

In the in-process transport, Terms are passed by reference — no serialization.

**Correctness condition**: This is correct if and only if Terms are immutable.
If any Term is mutable (fields can change after construction), passing by
reference means the receiver may observe a different Term than what was sent.

**Guarantee required**: Terms must be structurally immutable (readonly fields,
plain objects with no class state). This guarantee must be preserved. If any
Term type gains mutable state, the in-process transport must switch to deep
copying.

## 3. Cross-Process Serialization Requirements

The stdio (and future socket/IPC) transport serializes Terms to a wire format.

**Required bijection**: The serialization `encode: Term → Bytes` and
deserialization `decode: Bytes → Term` must form a bijection:
`decode(encode(t)) = t` for all valid Terms.

**Current violation**: JSON.stringify/parse is not a bijection on Terms.
See `04-pitfalls-risks.md §1` for the full enumeration of violations.

**Required `toTerm`/`fromTerm` layer**: The complete serialization layer must handle:
- All Term variants: Atom, Compound, Variable, Integer, Float, List, Record
- Map fields in Record terms: JSON encodes as `{}` — must use array of pairs
- BigInt: JSON throws — must encode as `{type: "bigint", value: "123"}`
- Variable IDs: must be globally unique across processes — prefix with process UUID
- Compound arity: must be preserved exactly (no conflation of f(a) and f(a, b))

## 4. Session-Typed Debug Protocol

The debug protocol between SUD and DBG is expressed as a session type
(Honda 1993). The SUD-side type is:

```
SUD_type =
  send(capabilities);
  recv(attach);
  send(attached);
  recv(filter_set);
  μloop.
    send(sync_point);
    branch {
      recv(continue): loop
      recv(request_fields): send(fields); branch { recv(continue): loop | recv(pause): pause_loop }
      recv(detach): end
    }

pause_loop =
  μpause.
    branch {
      recv(inspect): send(inspection_result); pause
      recv(continue): loop
      recv(step): loop
      recv(detach): end
    }
```

**Duality check**: The DBG-side type must be the exact dual of this type —
every send becomes a recv and vice versa, every branch on SUD becomes a selection
on DBG. Verify using a session type checker or by manual inspection.

**Deadlock freedom**: Dual session types on both ends guarantee deadlock freedom
(Honda 1993, Theorem 2). Any protocol deviation from the session type creates
a potential deadlock.

**Progress guarantee**: Session types also guarantee progress — both ends will
always be able to make progress (no livelock). This assumes the transport is
fair (messages are eventually delivered).

**Limitation**: Session types specify protocol shape. They do NOT guarantee
semantic consistency of the observations made over the protocol. For that,
see Consistent Cuts (§5 below). Deadlock freedom from duality ≠ correctness
of the observations.

## 5. Consistent Cuts — Remote Observation Semantics

In a remote debugging session, the DBG observes a proxy of the SUD state, not
the SUD state directly. The formal question: what is the relationship between
the proxy and the actual SUD state?

**Fromentin et al. (1995) consistent cut**: A snapshot of a distributed
execution is consistent iff it corresponds to a consistent cut — a prefix of
the execution history such that no event in the cut has a cause outside the cut.

**Formal requirement**: Every state the DBG observes via `sync_point` and
`fields` messages must correspond to a consistent cut of the SUD's execution.

**How to ensure it**: The SyncPoint protocol ensures this — the SUD sends the
`sync_point` message only when it is at a well-defined sync point, at which
point its state is stable (no concurrent transitions). The DBG's view of this
state is a consistent cut because the SUD is not advancing.

**Risk**: If the SUD makes transitions between sending `sync_point` and the
DBG reading the materialized `fields`, the view is inconsistent. The SyncPoint
protocol must block the SUD from advancing until the DBG sends `continue`,
`step`, or `detach`.

## 6. Partial Order Reconstruction — Vector Clocks

When events arrive over the transport out of causal order (possible with
buffering), the DBG must reconstruct causal ordering.

**Fidge (1988) / Mattern (1988) vector clocks**: Assign each process a vector
of logical timestamps. When process P sends event e with vector clock V, the
receiver updates its clock to max(local, V) + 1. The happened-before relation
is recoverable from vector clocks.

**For two-process debugging**: There are (at least) two event streams — the
SUD's events and the DBG's commands. Vector clocks allow the DBG to determine
which SUD events causally precede which DBG commands.

**Multi-formalism complication**: Each formalism has its own logical time
(SLD depth, tick count, context depth). A full vector clock would have one
component per formalism. The `DebugContextHeader` captures these separately
(`depth`, `tick`) — this is a form of per-formalism logical time.

## 7. Session Resumption After Transport Drop

The session-typed protocol specifies the happy path. Transport drops require
a resumption protocol.

**Caires & Pfenning (2010)** on linear logic session types: Session types
with linear logic provide a formal framework for session resumption — the
linear resource (the channel) must be explicitly disposed or resumed.

**Practical reference**: VS Code Debug Adapter Protocol handles this via:
1. DBG sends `initialized` event after reconnect
2. SUD responds with `capabilities`
3. Both sides re-negotiate to a known state before resuming

**Requirements after a transport drop and reconnect**:
1. The SUD must know whether it is still paused (resolveCommand ≠ null) or running
2. If paused: the DBG can re-attach and resume the pause loop
3. If running: the DBG must re-attach and re-set breakpoints
4. **Auto-detach on drop**: On transport close, the SUD should auto-detach (release
   the paused Promise with `{ kind: 'detach' }`). This ensures the SUD is never
   permanently blocked by a disconnected DBG.

**Formal guarantee**: Without auto-detach, a transport drop permanently deadlocks
the SUD at the last SyncPoint. This is a liveness violation — the SUD can never
make progress. Auto-detach preserves liveness.

## 8. Security Model

**The debug transport is an RCE (Remote Code Execution) vector**: The DBG
can instruct the SUD to `assertFact`, `retractFact`, and `forceFire`. These
operations modify the SUD's knowledge base and Petri net markings. A compromised
DBG is a compromised SUD.

**Required security controls**:

1. **Authentication**: The SUD must verify the identity of the attaching DBG.
   Minimum: a shared secret (token) sent during the `attach` handshake.
   Stronger: mutual TLS for socket transports.

2. **Authorization**: Not all DBG instances should have `interact` mode.
   The attach handshake must negotiate the mode (observe vs. interact) and
   the SUD must enforce it.

3. **Command audit log**: All `assertFact`, `retractFact`, `forceFire` commands
   must be logged (timestamp, DBG identity, command, result). This is
   especially critical in a compliance context — modifying facts during a
   compliance check is a compliance event.

4. **Scope restriction**: The SUD may restrict which knowledge base predicates
   the DBG can modify. For example, regulatory module predicates (`gdpr::*`)
   may be read-only even in interact mode.

**Cross-process risk**: Because SUD and DBG are the same runtime, a DBG that
asserts a fact into the SUD's knowledge base can affect the SUD's reasoning
in ways that are semantically indistinguishable from the SUD's own reasoning.
This makes unauthorized DBG access particularly dangerous in a formal compliance
context.

## 9. Debug Adapter Protocol (DAP) — Reference Implementation

VS Code Debug Adapter Protocol (Wilson 2016, Microsoft) is the production-grade
reference for frontend/backend debug protocol design.

**DAP solutions worth adopting**:

- **`stepIn`/`stepOut`/`stepOver`**: DAP defines these for non-standard execution
  models. Analogues: `stepGoal` (one SLD step), `stepFire` (one Petri net
  firing), `stepTick` (one reactive tick), `stepFixpoint` (one propagation
  fixpoint).

- **Logpoints**: Non-halting breakpoints that log a message without pausing.
  Implemented as Observational hooks (fire-and-forget) — a logpoint is a
  breakpoint with `{ kind: 'continue' }` always returned.

- **Exception breakpoints**: A breakpoint that fires specifically when an
  exception is thrown, regardless of where in the code it occurs. In SLD,
  this is a breakpoint on the `exception` Byrd port.

- **Capability negotiation**: DAP's `initialize` / `initialized` handshake
  lets the DBG report what it supports and the SUD adapt. The `capabilities`
  message in the session type serves this purpose.

**Where session-typed approaches are richer than DAP**: The session-typed
protocol formally guarantees deadlock freedom and progress; DAP does not have
a formal protocol specification. Cross-formalism breakpoints (breakpoints that
fire on Petri net transitions and reactive tick boundaries, not just program
points) have no DAP equivalent.
