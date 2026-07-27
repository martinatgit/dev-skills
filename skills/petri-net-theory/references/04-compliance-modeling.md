---
name: petri-net-compliance-modeling
description: Deontic logic to Petri net mappings (obligation, permission, prohibition,
  deadline). CTL/LTL compliance property templates. Regulatory compliance PN literature:
  Norm Nets, Logic+PN normative modelling, DECLARE constraint-based compliance,
  conformance checking. Elgammal 55 control-flow compliance rules. Tool ecosystem:
  CPN Tools, LoLA, PNML. Cross-document modelling patterns.
type: reference
---

# Petri Net Compliance Modelling

## 3. Deontic Mappings

| Deontic Concept | PN Construct | Verification Property | Stratum |
|---|---|---|---|
| Obligation(A) | Transition A must fire | Liveness: `AG(EF(A_fired))` | 3 |
| Permission(A) | Transition A enabled in some reachable M | Enabledness | 3 |
| Prohibition(A) | Inhibitor arc on A / dead transition | Safety: `AG(!A_fired)` | 1 or 3 |
| Conditional Obligation(A if B) | Place B-dependent enabling of A | CTL: `AG(B -> AF(A))` | 3 |
| Deadline(A before t) | `before(A, deadline)` constraint | Timed reachability | 2 |
| Contrary-to-duty | Exception handling subnet | Compensating transition | 3 |

**Established by:** Padget & Vasconcelos (2009), Lokhorst (1996), Sileno et al. (2018).

---

## 4. CTL/LTL Compliance Property Templates

| Compliance Requirement | Temporal Logic | PN Property | Stratum |
|---|---|---|---|
| "X must always happen" | `AG(EF(X_done))` | Liveness | 3 |
| "X must never happen" | `AG(!X_done)` | Dead transition | 3 |
| "X must happen before Y" | `!Y U X` | `before(X, Y)` ordering | 2 |
| "After X, Y must eventually follow" | `AG(X -> AF(Y))` | Response property | 3 |
| "X and Y cannot both happen" | `G(!(X & Y))` | Mutual exclusion invariant | 1 |
| "Process must complete" | `AG(EF(end))` | WF-net soundness | 3 |
| "No deadlocks" | `AG(EX(true))` | Deadlock-freedom | 3 |
| "Resource limits respected" | Bounded `M(p) <= k` | k-boundedness | 1 |

**55 control-flow compliance rules** (Elgammal et al., Eindhoven) across 15 categories,
validated on 1400+ cases — candidate pattern library for Layer 6-7.

---

## 5. Regulatory Compliance PN Literature

### 5.1 Normative Systems and Logic Programming + Petri Nets

**Sileno, Boer & van Engers (2018)** combines logic programming with Petri nets for
normative specification: Prolog handles the normative conditions (who is obligated,
under what conditions), while Petri nets govern procedural execution (in what sequence).
This is the foundational paper for aiqeung's hybrid architecture.

**Padget & Vasconcelos (2009)** introduces Logic Programming + Petri Nets (LPPNs) for
multi-agent normative systems. Key insight: deontic modalities (obligation, permission,
prohibition) are encoded as CPN places with appropriate guard conditions.

**Norm Net pattern** (after Sileno et al.): A Norm Net is a Petri net where:
- Transitions represent normatively regulated actions
- Places represent agent roles and their deontic states
- Guards encode normative conditions using first-order predicates
- Inhibitor arcs model prohibitions

### 5.2 Business Process Compliance Checking

**van der Aalst & de Medeiros (2005)** establishes conformance checking: given a
process model (Petri net) and an event log (sequence of fired transitions), compute
the deviation between observed and specified behavior.

Three conformance dimensions:
1. **Fitness** (recall): what fraction of traces in the log are possible in the model?
2. **Appropriateness** (precision): how much behavior does the model allow beyond the log?
3. **Structural quality**: is the model sound (WF-net soundness)?

**DECLARE (Pesic et al. 2007)** is a constraint-based process modelling language where
compliance requirements are expressed as temporal constraints (not procedural nets).
DECLARE constraints include: Response, Precedence, Succession, Alternate response,
Chain succession. These map to CTL formulas and can be translated to Petri nets via
automata-theoretic techniques.

**Practical implication for aiqeung**: Conformance checking is a Layer 8 capability —
comparing actual execution traces (from the debugger) against the compliance net model.
This requires the partial-order semantics from net unfolding (S1.7 of 01-core-formalisms.md).

### 5.3 Control-Flow Compliance Patterns

**Elgammal, Turetken, van den Heuvel & Papazoglou (2016)** catalogue **55 control-flow
compliance rules** across 15 categories, validated on 1400+ business process cases.

The 15 categories:
1. Existence (something must happen)
2. Absence (something must not happen)
3. Exactly N (something happens exactly N times)
4. Precedence (A before B)
5. Response (after A, eventually B)
6. Succession (A before B, and after A eventually B)
7. Alternation (A and B alternate)
8. Chain (A immediately before B)
9. Exclusive Choice (either A or B, not both)
10. Co-Existence (if A then eventually B)
11. Not Co-Existence (not both A and B)
12. Reciprocal Precedence (A before B and B before A — mutual)
13. Not Succession (not: after A eventually B)
14. Not Response (not: after A, B triggers)
15. Not Precedence (not: A must happen before B)

Each maps to a CTL/LTL formula and to a Petri net construction. This is the authoritative
pattern library for Layer 6-7 compliance vocabularies.

### 5.4 Tool Ecosystem

**CPN Tools** (Ratzer et al. 2003, Jensen group at Aarhus):
- State-space exploration with tabling (configurable bound)
- Simulation and animation
- Automated verification with configurable coverage
- ML (SML) for arc expressions and guards
- Direct inspiration for aiqeung's `tablingMaxStates` pattern

**LoLA** (Wolf, Univ. Rostock):
- Focused on P/T net verification (not CPN)
- Efficient reachability checking via stubborn sets and partial-order reduction
- EXPSPACE-aware — reports incompleteness when bound exceeded

**PIPE** (Platform Independent Petri net Editor):
- Open-source, Java, educational
- P/T nets only
- Useful for visualisation, less so for verification

**PNML (Petri Net Markup Language)** ISO/IEC 15909-2:
- XML interchange format for all PN types
- Enables tool interoperability
- Relevant if aiqeung needs to export nets for external verification tools

### 5.5 Cross-Document Compliance Modelling

When multiple regulatory documents apply simultaneously (e.g., GDPR + EU AI Act + ISO 24970):

**Architecture**: Use HCPN with one page per regulatory document (or per article cluster).
Cross-document synchronisation via fusion sets on shared concepts (e.g., `data_subject`,
`ai_system`, `processing_event`).

**Canonical vocabulary** (from the aiqeung GDPR + ISO 24970 modelling experiments):
- Subject place: `data_subject` or `ai_system` carrying identity tokens
- Event place: `processing_event` fused across GDPR + ISO pages
- Compliance status: `compliance_status` place with token `{status, evidence, timestamp}`

**Design principle**: The root page represents the system boundary (the entity being regulated).
Sub-pages represent individual regulatory instruments. Fusion sets at the root level
connect the sub-pages without requiring explicit message-passing arcs.

### 5.6 Domain Applications

- **Privacy (GDPR):** PA-DFD to Petri net transformations; IoT device privacy evaluation
- **Smart contracts:** CPN verification of blockchain smart contracts (Liu & Liu 2019)
- **Access control:** CPN frameworks for RBAC policy verification (SOX compliance)
- **Railway safety:** CPN for CBTC train control under CENELEC EN 50128
- **Healthcare:** Coloured Timed Petri Nets for IHE alarm management
- **Financial:** Petri net framework for accounting information systems (SOX, audit analytics)
- **NLP pipelines:** Sarmiento & Leite (2024) — NLP to Petri nets for requirements analysis
