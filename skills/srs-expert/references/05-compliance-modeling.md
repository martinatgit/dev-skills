# Compliance Modeling with Synchronous Reactive Formalisms

*Sources: compliance_modeling.json (2026-04-07), reactive-system-insights.md §4*

---

## 1. Core Insight: Obligations as Synchronous Observers

**Theoretical basis:** Halbwachs et al. (1992) synchronous observer pattern + Berry (2002) constructive semantics.

A regulatory obligation is fundamentally a **safety property**: something bad (a violation) must never happen. The synchronous observer pattern maps this directly:

> A Lustre node takes the monitored system's inputs/outputs and produces a `violation` boolean stream. The obligation is met iff `violation` is never true.

This mapping has three valuable properties:
1. **Executable specification**: the observer runs against real execution traces (both for testing and runtime monitoring)
2. **Formally verifiable**: use Kind2 or Lesar to prove the observer never emits true for any input trace
3. **Deployable**: the same observer node serves as both the specification and the runtime monitor

### 1.1 Concept Mapping

| Regulatory concept | Synchronous construct |
|---|---|
| Obligation | Observer node (produces `violation` when breached) |
| Deadline | Counter node (counts ticks since trigger event) |
| Evidence | Boolean signal (present = evidence available at this tick) |
| Evidence gap | Absence of expected signal at a tick (formally definitive) |
| Concurrent obligations | Parallel composition of observer nodes |
| Cross-article dependency | Shared signal between observer nodes |
| Exemption condition | Environment assumption observer (input guard) |
| Regulatory status | Integer signal (0=inactive, 1=pending, 2=compliant, 3=violated) |

---

## 2. GDPR Art. 33 — Breach Notification Observer (Complete)

**Regulation:** GDPR Art. 33 requires notifying the supervisory authority within 72 hours of becoming aware of a personal data breach, unless the breach is unlikely to result in risk to individuals.

**Tick granularity:** 1 tick = 1 hour.

```lustre
-- GDPR Art. 33 Obligation Observer
-- Tick granularity: 1 hour
node ObligationArt33 (
  breach_detected    : bool;   -- breach awareness event
  severity_assessed  : bool;   -- severity assessment completed
  authority_notified : bool;   -- supervisory authority notified
  risk_to_rights     : bool    -- breach poses risk to individual rights
) returns (
  violation          : bool;   -- true iff obligation is violated
  hours_elapsed      : int;    -- hours since breach awareness
  status             : int     -- 0=inactive, 1=pending, 2=compliant, 3=violated
);
var
  active   : bool;    -- obligation active: breach detected, not yet resolved
  assessed : bool;    -- severity assessment latched
  notified : bool;    -- notification sent (latched)
  exempt   : bool;    -- no risk to rights — notification not required
  counter  : int;     -- hours since breach awareness
let
  -- Latch: once breach detected, obligation is active until resolved
  active = breach_detected -> (breach_detected or pre(active));

  -- Latch: once assessed, stays assessed
  assessed = severity_assessed -> (severity_assessed or pre(assessed));

  -- Latch: once notified, stays notified
  notified = authority_notified -> (authority_notified or pre(notified));

  -- Exemption: assessment says no risk to rights
  exempt = assessed and not risk_to_rights;

  -- Counter: hours since breach, only while active and unresolved
  counter = if active and not notified and not exempt
            then (0 -> pre(counter) + 1)
            else 0;

  hours_elapsed = counter;

  -- Violation: 72+ hours without notification, not exempt
  violation = active and (counter >= 72) and not notified and not exempt;

  -- Status encoding
  status = if not active then 0
           else if violation then 3
           else if notified or exempt then 2
           else 1;
tel
```

### 2.1 Properties Verifiable by Kind2

```
-- Safety (negative): notification arrives → violation never becomes true
-- Formally: G (notified → G(not violation))
property safety_liveness:
  assert not(violation and notified);

-- Deadline semantics: if active and not exempt and counter < 72, no violation yet
property deadline_precision:
  assert not(violation and counter < 72 and not exempt);

-- Exemption soundness: if exempt, never violated
property exemption:
  assert not(violation and exempt);
```

### 2.2 Key Lustre Patterns Used

| Pattern | Construct | What it models |
|---|---|---|
| **Latch** | `x = e -> (e or pre(x))` | Once an event occurs, its effect persists |
| **Counter** | `c = 0 -> pre(c) + 1` when active | Tick-counting under a condition |
| **Initialization** | `0 -> pre(counter)` | First tick gets 0, subsequent ticks get previous value |
| **Gate** | `if cond then expr else 0` | Conditional accumulation |
| **Status encoding** | `if ... then N else ...` | Compact multi-state output |

---

## 3. Generic Deadline Counter

```lustre
-- Generic regulatory deadline counter
-- Parameterized by deadline threshold (ticks)
node DeadlineCounter (
  trigger   : bool;  -- event that starts the countdown
  resolved  : bool;  -- event that stops the countdown (obligation met)
  threshold : int    -- deadline in ticks
) returns (
  ticks_remaining  : int;   -- ticks until deadline
  deadline_reached : bool;  -- true when deadline expires
  overdue_by       : int    -- ticks past deadline (0 if not overdue)
);
var
  counting : bool;
  elapsed  : int;
let
  counting = trigger -> (trigger or (pre(counting) and not resolved));

  elapsed = if counting
            then (0 -> if pre(counting) then pre(elapsed) + 1 else 0)
            else 0;

  ticks_remaining = if counting then threshold - elapsed else threshold;

  deadline_reached = counting and elapsed >= threshold;

  overdue_by = if deadline_reached then elapsed - threshold else 0;
tel
```

### 3.1 Regulatory Deadline Instances

| Regulation | Obligation | Tick granularity | Threshold |
|---|---|---|---|
| GDPR Art. 33 | Notify supervisory authority after breach | 1 hour | 72 |
| GDPR Art. 12(3) | Respond to data subject request | 1 day | 30 |
| AI Act Art. 72 | Report serious incidents | 1 day | 15 (approx.) |
| ISO/IEC 42001 Cl. 10.2 | Corrective action for nonconformities | 1 day | Context-dependent |

**Usage:** `DeadlineCounter` is a building block. The `ObligationArt33` node above inlines the counter logic; for a clean separation, instantiate `DeadlineCounter` and wire `breach_detected` → `trigger`, `authority_notified` → `resolved`, `72` → `threshold`.

---

## 4. Evidence Tracking (Absence as Compliance Gap)

**Core insight:** In the synchronous model, if evidence signal E is absent at tick t, that is a **definitive compliance gap** — not "maybe delayed." The synchronous clock provides the deadline at which absence is determined.

```lustre
-- Evidence tracker — GDPR Art. 30, 35, 37, etc.
node EvidenceTracker (
  processing_record : bool;  -- Art. 30: record of processing activities
  dpia_completed    : bool;  -- Art. 35: data protection impact assessment
  dpo_appointed     : bool;  -- Art. 37: data protection officer
  lawful_basis      : bool;  -- Art. 6: lawful basis documented
  consent_records   : bool;  -- Art. 7: records of consent
  retention_policy  : bool   -- Art. 5(1)(e): storage limitation policy
) returns (
  all_present    : bool;  -- all required evidence available at this tick
  gap_count      : int;   -- number of missing evidence items
  gap_vector     : int    -- bitmask: bit i = 1 iff evidence i is missing
);
let
  gap_count = (if processing_record then 0 else 1)
            + (if dpia_completed then 0 else 1)
            + (if dpo_appointed then 0 else 1)
            + (if lawful_basis then 0 else 1)
            + (if consent_records then 0 else 1)
            + (if retention_policy then 0 else 1);

  all_present = gap_count = 0;

  gap_vector = (if processing_record then 0 else 1)
             + (if dpia_completed then 0 else 2)
             + (if dpo_appointed then 0 else 4)
             + (if lawful_basis then 0 else 8)
             + (if consent_records then 0 else 16)
             + (if retention_policy then 0 else 32);
tel
```

### 4.1 Gap Detector — Precise Absence Reasoning

```lustre
-- Gap detector: evidence expected but absent
node GapDetector (
  expected : bool;  -- should evidence be present at this tick?
  actual   : bool   -- is evidence actually present at this tick?
) returns (
  gap          : bool;  -- gap exists at this tick
  gap_duration : int;   -- consecutive ticks of gap
  ever_had_gap : bool;  -- has any gap ever occurred?
  gap_count    : int    -- total number of gap episodes
);
var
  gap_start : bool;
let
  gap = expected and not actual;

  gap_duration = if gap
                 then (1 -> if pre(gap) then pre(gap_duration) + 1 else 1)
                 else 0;

  ever_had_gap = gap -> (gap or pre(ever_had_gap));

  gap_start = gap and (true -> not pre(gap));

  gap_count = if gap_start then (1 -> pre(gap_count) + 1)
              else (0 -> pre(gap_count));
tel
```

### 4.2 Why Absence Is Formally Definitive Here

| Model | Absence detection | Formal status |
|---|---|---|
| **Synchronous (Lustre)** | At tick t, signal S absent = S(t) = absent | **Definitive**: type-level guarantee from clock calculus |
| **Asynchronous (event queue)** | Signal S not received = delayed OR missing | **Ambiguous**: requires timeout heuristic |
| **Petri net** | No token in place P | **Relative**: absence from P, but token may be elsewhere in net |

**Implication:** For compliance, the synchronous model provides the strongest guarantee. A gap detected at tick t is a formal fact about tick t — not a timeout-based inference.

---

## 5. Multi-Article Composition

```lustre
-- Top-level composition: GDPR Articles 33, 34, 35 in parallel
-- Each article is a separate observer. Shared signals connect dependencies.
node GDPRBreachComposite (
  breach_detected       : bool;
  severity_assessed     : bool;
  risk_to_rights        : bool;
  high_risk_to_rights   : bool;
  authority_notified    : bool;
  subjects_notified     : bool;
  dpia_exists           : bool;
  processing_is_high_risk : bool
) returns (
  art33_violation : bool;
  art34_violation : bool;
  art35_violation : bool;
  any_violation   : bool;
  violation_count : int;
  overall_status  : int   -- 0=green, 1=yellow, 2=red
);
var
  art33_status : int;
  art34_status : int;
let
  -- Art. 33: notify authority within 72 hours
  (art33_violation, _, art33_status) =
    ObligationArt33(breach_detected, severity_assessed,
                    authority_notified, risk_to_rights);

  -- Art. 34: communicate to data subjects (when high risk)
  (art34_violation, _, art34_status) =
    ObligationArt33(breach_detected, severity_assessed,
                    subjects_notified, high_risk_to_rights);

  -- Art. 35: DPIA required for high-risk processing
  art35_violation = processing_is_high_risk and not dpia_exists;

  any_violation = art33_violation or art34_violation or art35_violation;

  violation_count = (if art33_violation then 1 else 0)
                  + (if art34_violation then 1 else 0)
                  + (if art35_violation then 1 else 0);

  -- Overall: red if any violation, yellow if any pending, green otherwise
  overall_status = if any_violation then 2
                   else if art33_status = 1 or art34_status = 1 then 1
                   else 0;
tel
```

### 5.1 Composition Properties (Free from the Synchronous Model)

- **Deterministic:** Same inputs always produce same `overall_status` — no scheduling-dependent behavior
- **No race conditions:** Articles execute in parallel within a tick; determinism guaranteed by synchronous hypothesis
- **Modular:** Adding Art. 36 = adding one more node call and connecting relevant shared signals
- **Verifiable:** `GDPRBreachComposite` can be passed to Kind2 as a unit; contracts compose
- **LOLA-bounded:** Observer state is finite per tick, independent of trace length

---

## 6. Complementarity with Petri Nets

Synchronous observers and Petri nets are **complementary**, not competing formalisms for compliance:

| Dimension | Petri Nets (Layer 2) | Synchronous Observers (Layer 3) |
|---|---|---|
| Core abstraction | Concurrent state: tokens in places | Stream processing: signals at each tick |
| Models well | Workflow routing, resource allocation, concurrent state transitions | Continuous monitoring, deadline tracking, evidence presence/absence |
| Verification question | **Reachability**: Can we reach a bad state? | **Safety**: Is the invariant always maintained? |
| Time model | Untimed (basic) or timed (extensions) | Logical clock ticks with precise deadline arithmetic |
| Concurrency | True concurrency with non-deterministic choice | Synchronous parallelism: deterministic by construction |
| Absence reasoning | Weak: absence = no token (no temporal precision) | Strong: absence at a specific tick is definitively known |
| Compositionality | Place fusion can introduce deadlocks | Parallel composition preserves determinism |

**Integration pattern for aiqeung:**
- **Petri nets** model the compliance **process**: the workflow of activities (breach assessment → notification → documentation)
- **Synchronous observers** model the compliance **invariants**: the properties that must always hold (deadlines met, evidence present, notifications timely)

A breach notification workflow might use:
- Petri net: `Aware → Assess → Notify → Document` (the steps and their ordering)
- Synchronous observer: `ObligationArt33` watching whether `Notify` fires within 72 ticks of `Aware`

### 6.1 Cross-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: Synchronous Reactive Runtime                           │
│                                                                  │
│  ObligationArt33  ──────┐                                       │
│  ObligationArt34  ──────┤──→ GDPRBreachComposite               │
│  EvidenceTracker  ──────┘                                       │
│                                                                  │
│  ObligationObservers run in par, read marking signals           │
│  (one tick = one observation period)                            │
└──────────────────────────────────────┬──────────────────────────┘
                                       │ signals: breach_detected,
                                       │ authority_notified, ...
                                       │ read from Petri net marking
┌──────────────────────────────────────▼──────────────────────────┐
│ Layer 2: Petri Net (HCPN)                                       │
│                                                                  │
│  Aware → SeverityAssess → NotifyAuthority → Document           │
│  (workflow: steps, branching, concurrency)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Kind2-Verifiable Properties for Compliance

For any compliance observer node, Kind2 can verify:

```lustre
-- 1. Safety: if compliant behavior, never violated
-- Kind2 property (assert in a wrapper node):
assert not(authority_notified and violation);

-- 2. Responsiveness: breach eventually leads to some status
-- (requires temporal operators — future extension)

-- 3. Monotonicity of latches: notified never reverts
-- Expressed as: pre(notified) => notified  (for all ticks > 0)
assert (true -> (pre(notified) => notified));

-- 4. Counter accuracy: violation iff counter >= 72
assert (violation = (active and counter >= 72 and not notified and not exempt));
```

**Why this matters:** Kind2 verifies these properties for **all possible input traces** — not just the traces you think of in testing. If Kind2 finds a counterexample, it produces the exact input sequence that leads to the violation, which is directly actionable.

---

## 8. aiqeung Implementation Mapping

| Lustre compliance concept | aiqeung analog |
|---|---|
| `ObligationArt33` node definition | `ReactiveExpr` AST for the obligation observer |
| Node running in synchronous parallel | `par(obligationObserver, mainProgram)` |
| Observer emitting `violation = true` | Obligation signal emitted via `re.emit("art33_violation", t.atom("true"))` |
| Observer reading `breach_detected` | `re.read("breach_detected")` returns current signal value |
| Observer using `pre(active)` | Runtime's `preValues` map (captured before COMPUTE phase) |
| Tick counter incrementing | `until` body increments counter signal; condition checks threshold |
| Multi-article composition | Multiple `ObligationObserver` nodes in `par` via `runtime.register()` |
| Kind2 verification target | Same `ReactiveExpr` AST, different interpreter (verification backend) |

*For the full Layer 3 implementation details, see `04-aiqeung-layer3.md`.*

---

## Bibliography

- Halbwachs, N., Caspi, P., Raymond, P., Pilaud, D. (1991). The synchronous data flow programming language LUSTRE. *Proc. IEEE*, 79(9):1305-1320.
- Berry, G. (2002). *The Constructive Semantics of Pure Esterel*, Draft Version 3.
- Colaço, J.-L. & Pouzet, M. (2003). Clocks as First Class Abstract Types. *EMSOFT 2003*.
- Champion, A., Mebsout, A., Sticksel, C., & Tinelli, C. (2016). The Kind 2 Model Checker. *CAV 2016*.
- D'Angelo, B. et al. (2005). LOLA: Runtime Monitoring of Synchronous Systems. *TIME 2005*.
- compliance_modeling.json (2026-04-07). Compliance Knowledge Modeling with Synchronous Reactive Formalisms.
