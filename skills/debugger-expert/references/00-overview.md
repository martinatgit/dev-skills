# Debugger Expert — Navigation Overview

## When to load which reference

| You are working on... | Load |
|---|---|
| Designing the event model for a new layer or formalism | `01-event-model.md` |
| Checking soundness or completeness of an existing event model | `01-event-model.md` |
| Understanding spy points / breakpoints / watchpoints formally | `01-event-model.md` |
| Pause/resume mechanism, cooperative stepping | `02-algorithms.md` |
| Time-travel, checkpoint strategy, immutable state replay | `02-algorithms.md` |
| Breakpoint filter compilation correctness | `02-algorithms.md` |
| Failure minimization, delta-debugging | `02-algorithms.md` |
| Multi-formalism trace: when formalisms are combined | `03-cross-formalism.md` |
| Causal consistency across SLD + Petri + reactive + constraint | `03-cross-formalism.md` |
| Whether the debugger faithfully represents the SUD | `03-cross-formalism.md` |
| Completeness of algorithmic debugging under cut/negation | `03-cross-formalism.md` |
| Engineering shortcuts in current implementation | `04-pitfalls-risks.md` |
| Known formal violations in the codebase | `04-pitfalls-risks.md` |
| Zero-overhead instrumentation | `05-implementation.md` |
| Hook composition, module-tagged events, self-debugging | `05-implementation.md` |
| Abstract machine observation points | `05-implementation.md` |
| Remote debug transport, wire format | `06-remote-debugging.md` |
| Session types, duality verification, consistent cuts | `06-remote-debugging.md` |
| Vector clocks, partial order reconstruction | `06-remote-debugging.md` |
| Session resumption after drop, security model | `06-remote-debugging.md` |
| DAP (VS Code Debug Adapter Protocol) comparison | `06-remote-debugging.md` |
| aiqeung-specific implementation examples | `07-worked-example.md` |
| Petri net debugging (firing sequences, reachability) | invoke `petri-net-theory` skill |

---

## Quick-Reference Formal Results

| Result | Source | What it guarantees |
|---|---|---|
| Port completeness | Byrd (1980) | All SLD port crossings produce an event |
| Algorithmic debugging completeness | Shapiro (1983) Thm 4.1 | Terminates and finds bug — pure Horn clause only |
| Cut incompleteness | Pereira & Calejo (1993) | Algorithmic debugging can fail to locate bug under cut |
| SLDNF breakdown | Apt & Doets (1994) | Byrd box has no formal semantics for \+ |
| Stuttering equivalence | Lamport (1983) | Defines what "same observable state" means for time-travel |
| Non-intrusiveness | Halbwachs et al. (1992) | Conditions under which observer preserves target semantics |
| Observer topology risk | Berry & Gonthier (1992) | Adding SyncNode to reactive program may change synchronization |
| Bisimulation faithfulness | Milner (1989) | Formal criterion: debugger model is bisimilar to SUD |
| Session type duality | Honda (1993) | Dual types on both ends → deadlock-free protocol |
| CSP conformance | Roscoe (1994) | Protocol implementation conforms to session type spec |
| Consistent cut | Fromentin et al. (1995) | Remote observation corresponds to causally consistent SUD snapshot |
| Causal consistency | Charron-Bost (1991) | Formal characterization of "A caused B" in heterogeneous systems |
| Permutation of transitions | Boudol & Castellani (1994) | Condition for reordering events across formalisms |
| Abstract trace correctness | Cousot & Cousot (1979) | Galois connection preserves soundness of abstract queries |
| Slice = Boolean semiring | Weiser (1984) + Green (2007) | Dynamic slice is a special case of provenance semiring |

---

## Glossary

**Algorithmic debugging**: Oracle-based bug location protocol (Shapiro 1983). User answers "correct / incorrect" to queries; the algorithm narrows to the bug site.

**Bisimulation**: A relation R on transition systems where each side can match the other's transitions. Strongest correctness criterion for a debugger model.

**Byrd box**: The four-port visual model of SLD resolution (Call, Exit, Redo, Fail).

**Calling convention**: The contract between an execution engine and a hook. Three types: Observational (fire-and-forget), Filter (boolean predicate), SyncPoint (returns a command, may block).

**Consistent cut**: A snapshot of a distributed execution that respects causal ordering — no event in the cut has a cause outside the cut.

**Galois connection**: A pair of monotone functions (α, γ) between two ordered sets satisfying α(x) ≤ y ⟺ x ≤ γ(y). Used to relate concrete traces to abstract summaries.

**Happened-before (→)**: Lamport's (1978) partial order on events: A → B if A causally precedes B.

**Oracle problem**: In algorithmic debugging, the user must answer whether a call result is correct. The oracle approximation problem asks: which query to present to minimize the number of oracle calls.

**Provenance semiring**: An algebraic structure (K, +, ×, 0, 1) that annotates query results with derivation witnesses. Different semirings give different explanations.

**Session type**: A type for a communication channel that specifies the sequence of send/receive operations. Dual session types on both ends guarantee protocol safety.

**Spy point**: A Prolog debugging primitive — a predicate-level marker that triggers Byrd port events for all calls to that predicate. Different from a breakpoint (program-point) and a watchpoint (data-conditional).

**Stuttering equivalence**: Two execution sequences are stuttering-equivalent if one can be obtained from the other by inserting/removing finite repetitions of states.

**SUD**: System Under Debug — the engine instance being observed.

**DBG**: Debugger engine — the instance (or component) performing the observation.

**Why-did / Why-didn't**: Ko & Myers (2008) interrogative debugging queries. Why-did traces the derivation tree to a successful result; why-didn't identifies which alternatives failed and why.
