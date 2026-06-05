# Cross-Formalism Trace Semantics

## 1. The Fundamental Incompatibility

Systems that combine formalisms with **incompatible notions of time, state,
and causality** require careful cross-formalism trace design. A single
compliance analysis may involve:

| Formalism | State | Time | Causality |
|---|---|---|---|
| SLD resolution | Substitution + choice point stack | Resolution depth (ordered, backtracking) | Sequential, reversible |
| Petri nets | Marking (multiset of tokens) | Firing sequence (partial order) | Concurrent, irreversible per step |
| Synchronous reactive | Signal values per tick | Tick count (total order of ticks) | Simultaneous within tick |
| Constraint propagation | Domain assignments | Propagation steps (order not fixed) | Demand-driven, non-deterministic order |

**The naive approach** — compositing events from each formalism into a single
log — gives you a *sequence* of events but not a *causal structure*. A
timestamp-ordered log does not tell you whether event A from the SLD solver
*caused* event B in the Petri net, or whether they happened to be adjacent
in physical time.

**The correct approach** requires defining cross-formalism causality explicitly.

## 2. Boudol & Castellani (1994) — Permutation of Transitions

Boudol & Castellani (1994) "Permutation of Transitions: An Event Structure
Semantics for CCS and CSP" defines when two events from different processes
can be reordered in a trace without changing the observable result.

**Key result**: Events A and B can be permuted (reordered) iff they are
*independent* — neither causally precedes the other, and swapping their order
produces an observationally equivalent execution.

**For cross-formalism traces**: Two events A (SLD) and B (Petri) are
permutable iff:
1. A does not cause B (the SLD step did not trigger the net transition), AND
2. B does not cause A (the net transition did not affect the SLD state), AND
3. Swapping their order produces observationally equivalent results

**Implication**: The trace must record which events *do* have cross-formalism
causal dependencies. Events without explicit cross-formalism dependencies
are permutable — their relative order in the trace is arbitrary.

## 3. Charron-Bost (1991) — Causal Consistency

Charron-Bost (1991) "Concerning the Size of Logical Clocks in Distributed
Systems" formalises what it means for a trace to be *causally consistent*:
every event in the trace can see all events that causally precede it.

**Formal condition**: A trace T is causally consistent iff:
for all events e, f ∈ T: if f → e (f causally precedes e), then f appears
before e in T and e's context reflects f's effects.

**For multi-formalism systems**: An SLD choice event that fires a Petri net
transition causally precedes the `transition_fire` event. The trace is
causally consistent only if the `transition_fire` event's context reflects
the SLD state at the time of the choice. If these are logged separately and
naively merged, causal consistency is not guaranteed.

## 4. The Span Model as Engineering Approximation

The span model (OpenTelemetry-inspired, parent/child span tree) is an
engineering approximation of causal structure:

**What it captures**: Parent-child relationships (A spawned B). In aiqeung,
an SLD resolution step that triggers a Petri net firing is modelled as a
parent span (the SLD step) with a child span (the firing).

**What it does NOT capture**:
- Sibling causality: two events with the same parent may have a causal
  dependency not expressed by their common parentage
- Cross-layer causality without a direct call: a reactive signal emitted
  by a Petri net firing that wakes a constraint propagator — this is a
  two-hop causal chain that the span model represents only if all three
  spans are explicitly linked

**When the span model is sufficient**: For a single compliance query that
flows linearly through the layers (SLD → Petri → reactive → constraint),
the span tree faithfully captures causality because each step is a direct
call to the next layer.

**When the span model fails**: When events in the same layer causally affect
each other without a shared parent span — e.g., two constraint propagators
that both narrow the same variable, where the second's wakeup is caused by
the first's narrowing.

**Recommendation**: Document span model limitations explicitly. For cases where
the span model is insufficient, use vector clocks (per formalism) with explicit
cross-formalism causal annotations.

## 5. Interleaving Semantics at Formalism Boundaries

When execution crosses a formalism boundary (SLD calls into a Petri net
transition; a reactive tick wakes a constraint propagator), the boundary
crossing must be a **first-class event** in the trace.

**Why**: Without boundary events, the trace has two consecutive events from
different formalisms with no record of *how* control passed between them.
Causal consistency is unverifiable.

**Required boundary events**:
- SLD → Petri: a `choice_point` event records the SLD decision; the `pre_fire`
  event records the Petri net entry; a parent-child span link records causality
- Petri → Reactive: `transition_fire` causes `tick_start`; span link required
- Reactive → Constraint: `signal_emit` causes `propagator_wake`; span link required
- Constraint → SLD: `fixpoint_reached` allows SLD to resume; span link required

Each of these boundary crossings corresponds to a **session advance** event
in the Layer 4 session type — the debug session's session type position advances
at each boundary.

## 6. Bisimulation as the Faithfulness Criterion

A debugger is **faithful** iff its model of SUD execution is a bisimulation
(Milner 1989) of the SUD's actual transition system.

**Why this is the right criterion**: Bisimulation is the largest relation that
preserves observational equivalence. If the debugger's model bisimulates the
SUD, then everything the user observes in the debugger corresponds to something
the SUD actually did, and the SUD did nothing the debugger didn't show.

**Strong bisimulation** (in-process case): Every SUD transition corresponds to
an identical debugger model transition. The `DebugContextHeader` must faithfully
encode the SUD state at the time of each sync point.

**Weak bisimulation** (remote case): Silent transport transitions (messages in
flight) may be inserted or omitted without affecting the observable behaviour.
The consistent-cut condition (Fromentin et al. 1995) ensures the debugger only
observes causally consistent snapshots, which is the weak bisimulation condition
for distributed observations.

**Concrete failure mode**: If the `LazyFields` materialisation is deferred and
the SUD continues to make transitions before materialisation is triggered,
the materialised value may not correspond to the SUD state at the sync point.
This is a bisimulation violation: the debugger's model shows a state the SUD
was not actually in when the sync point fired.

## 7. Completeness of Algorithmic Debugging in Multi-Formalism Settings

Shapiro (1983) proves completeness for pure Horn clause logic. This result
fails in multi-formalism settings:

### 7.1 Failure under Cut (Pereira & Calejo 1993)

Cut (`!`) prunes the search space irrevocably. If a bug is in a branch pruned
by cut, the algorithmic debugger can never present it to the oracle. The oracle
answers correctly on every query it sees, but the bug is invisible.

**Implication**: If the SLD solver supports cut, algorithmic debugging is
incomplete. This must be documented as a known limitation. The debugger must
warn the user when cut is detected in the call stack.

### 7.2 Failure under Negation-as-Failure (Apt & Doets 1994)

The SLDNF proof procedure for `\+G` does not produce a Byrd-compatible trace.
`\+G` succeeds if G has no proof — this is a meta-level property of the
derivation, not a derivation step. The Byrd box model has no port for "failed
to prove G".

**Implication**: The `fail` port fires for G, but the inference that `\+G`
succeeds is not explicitly represented in the trace. Algorithmic debugging over
`\+` goals requires the debugger to inspect the negated goal's failure trace.

### 7.3 Failure under Cross-Formalism Side Effects

A Petri net transition that fires as a side effect of an SLD resolution step
introduces a non-logical side effect. If the transition changes global state
(e.g., a shared marking), the SLD resolution's result may depend on firing
order — which is non-deterministic for concurrent Petri nets.

**Implication**: Algorithmic debugging's completeness theorem assumes a
functional correspondence between calls and results. Cross-formalism side
effects break this assumption. The debugger cannot guarantee it will find
the bug in the presence of concurrent Petri net side effects.

### 7.4 Summary

| Condition | Algorithmic debugging complete? |
|---|---|
| Pure Horn clause, no cut, no \+, no side effects | Yes (Shapiro 1983 Thm 4.1) |
| Cut present | No (Pereira & Calejo 1993) |
| \+ (negation-as-failure) present | Incomplete (Apt & Doets 1994) |
| Cross-formalism side effects | No guarantee |

The debugger must detect and warn about these conditions rather than silently
producing incomplete results.
