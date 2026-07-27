---
name: petri-net-worked-examples
description: aiqeung as a worked example for Petri net compliance modelling. Five
  complete examples: GDPR Art. 33 breach notification (HCPN + timed), Art. 25 data
  protection by design (CLP(PN) + net contract), Art. 17 right to erasure (AND-split/join),
  Art. 36 prior consultation (inhibitor arcs + pausable deadlines), ISO 24970 AI system
  lifecycle HCPN. All examples are self-contained — no live source file links.
type: reference
---

# aiqeung Worked Examples

**Note:** This file describes the aiqeung implementation state at authoring time (2026-04-13).
Type definitions and file structures may have changed. When this file conflicts with the
live source, trust the source. The Petri net constructs and compliance patterns described
here are authoritative; the TypeScript type names may need updating.

aiqeung is the **worked example**, not the reason the patterns exist. These patterns apply
to any Petri-net-based compliance system.

All examples cross-reference theory sections. See `src/aiqeung-core/petri/` in the project for current types.

---

## Example 1: GDPR Art. 33 — Breach Notification (S1.3 HCPN + S1.5 Timed + S5 patterns)

72-hour notification procedure with partial-order compliance.

```
Page: art33_notification
Places:
  breach_detected          [In port]   — fused with Art. 34 page AND lifecycle net
  assessment_started
  risk_assessed_partial
  risk_assessed_full
  partial_notified         [Out port]
  complete_notified        [Out port]
  documented_only          [Out port]  — Art. 33(5): documentation without notification
  deadline_expires         [fusion: deadline_watch]  — timed, marked 72h after breach

Transitions:
  start_assessment         guard: aware_of_breach(Case)
  assess_low_risk          guard: \+ high_risk(Breach)
  assess_high_risk         guard: high_risk(Breach)
  submit_partial           consumes: [assessment_started, risk_assessed_partial]
  submit_complete          consumes: [assessment_started, risk_assessed_full]
  submit_supplemental      consumes: [partial_notified, full_info_available]
  document_only            guard: not_required_to_notify(Breach)

NetContract:
  invariants:  []   -- no stratum-0 invariants needed here
  obligations: [    -- deferred to Layer 3 (stratum 2-3)
    before(submit_partial, deadline_expires)    -- stratum 2 (CLP(PN))
    before(submit_complete, deadline_expires)   -- stratum 2 (CLP(PN))
    reachable(complete_notified OR documented_only)  -- stratum 3
  ]
```

**11 GDPR Insights from this model:**
1. Procedural/substantive orthogonality — normative articles (6, 7, 9) -> SLD; procedural (33, 34) -> PN
2. Fusion sets for multi-article sync (`breach_detected` fused across Art. 33, 34, lifecycle)
3. Goal-valued bounds — `min_necessary(Purpose)` is KB-derived (R5)
4. Partial-order compliance — WF-net soundness, not sequential checking
5. Irreducible undetermination — "likely to result in risk" must surface as `undetermined`
6. Coloured tokens carry legal state across procedures
7. Stratum-2/3 boundary is critical — `before()` is stratum-2, `reachable()` is stratum-3
8. Fan-out parallel (Art. 17) — AND-split/AND-join
9. Inhibitor arc semantics required for Art. 36 prohibition
10. Pausable deadlines required for Art. 36(2) — `before_with_suspension` (R11 gap)
11. Priority-ordered routing for Art. 44-49 — NAF guards

---

## Example 2: GDPR Art. 25 — Data Protection by Design (S1.6 CLP(PN) + S4 Net Contract)

Structural compliance — design-time property, not runtime procedure.

```typescript
// Source: constrained-net.ts (verify current field names)
const contract: NetContract = {
  invariants: [
    // Stratum 0 — checked step-wise in fire():
    compound("not_marked", [atom("data_publicly_accessible_indefinitely")]),
    compound("no_incoming_arc", [atom("excessive_data_collection")])
  ],
  obligations: [
    // Stratum 3 — deferred to Layer 3 reactive runtime:
    compound("reachable", [atom("data_erased_or_anonymised")])
  ],
  assumptions: [
    // KB preconditions verified before contract applies:
    compound("processing_purpose", [variable("Purpose"),
      compound("lawful_basis", [variable("_")])])
  ]
}
```

Key insight: `min_necessary(Purpose)` bound is goal-valued — depends on purpose in KB.

---

## Example 3: GDPR Art. 17 — Right to Erasure (S5 AND-split/join pattern)

Fan-out parallel procedure with three branches:

```
Page: art17_erasure
Places: erasure_request_received [In], grounds_validated,
        internal_erasure_complete, downstream_notification_complete,
        recipient_notification_complete, erasure_fully_complete [Out]

Transitions:
  validate_grounds    guard: erasure_ground(Subject, _), \+ erasure_exception(Subject, _)
  fork_erasure        -- AND-split -> marks all three branch places
  complete_internal
  notify_downstream   guard: data_was_public(Subject)
  skip_downstream     guard: \+ data_was_public(Subject)
  notify_recipients   guard: recipients_exist(Subject)
  skip_recipients     guard: \+ recipients_exist(Subject) ; disproportionate_effort(Subject)
  join_complete       -- AND-join <- waits for all three branches

NetContract obligations:
  before(complete_internal, undue_delay)    -- stratum 2
  reachable(erasure_fully_complete)         -- stratum 3
```

"Disproportionate effort" exception is irreducible normative judgment — surfaces as `undetermined`.

---

## Example 4: GDPR Art. 36 — Prior Consultation (S1.8 Inhibitor + S5 Pausable Deadline)

Strongest case for inhibitor arcs in GDPR. "Must not process until consultation concludes."

```
Inhibitor arc: consultation_ongoing --O--> process_data
(controller cannot process while consultation is in progress)

Pausable deadline (R11 gap — not yet in aiqeung):
  before_with_suspension(
    submit_consultation,
    consultation_deadline_8wk,
    sa_requesting_additional_info    -- deadline pauses while this holds
  )
```

**Impact on analysis:** Inhibitor arc makes strata 1-2 CLP(PN) refuse (unless net is
k-bounded). This is the correct behavior — the undecidability must be acknowledged.

---

## Example 5: ISO 24970 — AI System Lifecycle HCPN (S1.3 + S3.4)

Lifecycle stages (design -> development -> testing -> deployment -> monitoring -> decommission)
as places. Logging triggers (Clause 7) as port places fused with logging sub-pages.

**Canonical coloured token types (Annex A):**
```typescript
// Log entries as algebraic PN tokens (Terms):
type LogToken =
  | { kind: "txn_init";    EventRef: string; SystemRef: string; ModelId: string;
      Timestamp: Date; InputRef: string; OutputRef: string }
  | { kind: "txn_outcome"; EventRef: string; SystemRef: string; ModelId: string;
      Timestamp: Date; OutputPayload: any; ConfidenceLevel: number }
  | { kind: "sw_error";    EventRef: string; SystemRef: string; Timestamp: Date }
  | { kind: "human_intervention"; EventRef: string; SystemRef: string;
      Timestamp: Date; ControllerRef: string; Reason: string; Outcome: string }
  // ... 8 canonical types from Annex A
```

**Key insight:** WF-net soundness for triggered procedures; liveness+boundedness for
continuous reactive nets (Figure 1/2 — NOT WF-nets). Read arcs needed for watchdog/
anomaly monitor (non-consuming observation — R12 gap in current aiqeung).
