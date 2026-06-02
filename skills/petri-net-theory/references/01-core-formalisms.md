---
name: petri-net-core-formalisms
description: Formal definitions for P/T nets, Coloured Petri Nets, Hierarchical CPNs,
  Workflow Nets, Timed Petri Nets, CLP(PN), and Net Unfoldings. Includes firing rules,
  enabling conditions, marking representations, and decidability results for each.
type: reference
---

# Petri Net Core Formalisms (S1.1-1.7)

## 1.1 Classical P/T Nets

**Definition:** `N = (P, T, F, W, M0)` where:
- `P` = finite set of **places** (circles — conditions, resource pools)
- `T` = finite set of **transitions** (rectangles — events, actions)
- `F <= (P x T) U (T x P)` = **flow relation** (arcs)
- `W: F -> N+` = **arc weight** function
- `M0: P -> N` = **initial marking** (token counts)

**Transition enabling:** `t` is enabled in `M` iff `for all p in *t: M(p) >= W(p,t)`
where `*t = {p | (p,t) in F}` (preset of t).

**Firing rule:** Firing enabled `t` in `M` produces `M'` where:
`M'(p) = M(p) - W(p,t) + W(t,p)` for all `p in P`.

**State space:** all markings reachable from `M0` via firing sequences.

**Key decidability results:**
- Reachability: **Ackermann-complete** (Czerwinski et al. 2021) — beyond any fixed exponential tower
- Coverability: **EXPSPACE-complete**
- Boundedness: **EXPSPACE-complete**
- Deadlock-freedom: decidable

---

## 1.2 Coloured Petri Nets (CPNs)

**Jensen & Kristensen (2009) formulation:**
- Each place `p` has **colour set** `CS(p)` — the type of tokens it holds
- Tokens are typed **values** (colours), not indistinguishable units
- Arc **expressions** are functions over the colour domain -> multisets of tokens
- Transition **guards** are Boolean functions over the colour domain
- Marking: `M: P -> Bag(CS(p))` — multiset of typed tokens per place

**Firing:** requires substitution sigma such that input arcs evaluate to tokens present.
Output arcs evaluated under same sigma produce new tokens.

**Expressiveness:** CPNs are **Turing-complete** with unbounded colour domains.
No general decidability results hold. State-space analysis via CPN Tools uses tabling
with configurable bounds — inspiration for aiqeung's `tablingMaxStates`.

---

## 1.3 Hierarchical CPNs (HCPNs)

**Page decomposition:** large net divided into pages (self-contained CPNs).
A **substitution transition** on page P represents sub-page Q entirely.

**Ports** (interface of sub-page Q):
- `In`: tokens flow into sub-page when transition fires
- `Out`: tokens flow out of sub-page
- `InOut`: bidirectional — fusion across the boundary

**Fusion sets:** A set of places across ANY pages (not just parent/child) that always
carry identical token multisets. Any firing that updates one fusion member
**atomically updates all members**. No observable intermediate state.

**CRITICAL — Fusion atomicity:** If fusion members diverge, the global marking is
incoherent. All implementations must ensure no observable intermediate state exists
between the read and write of fusion set members. This is non-negotiable.

**Regulatory modelling:** Each legal article with a procedural component = one page.
Cross-article synchronisation = fusion sets. Root page = system-level interface.

---

## 1.4 Workflow Nets (WF-nets)

**van der Aalst (1997):** P/T-net with:
- Distinguished source place `i` (initial) — `*i = empty`
- Distinguished sink place `o` (final) — `o* = empty`
- Every node on a directed path from `i` to `o`

**Soundness (three conditions):**
1. **Option-to-complete:** from every marking reachable from `[i]`, `[o]` is reachable
2. **Proper completion:** `[o]` is the only terminal marking reachable from `[i]`
3. **No dead transitions:** every transition fires in some reachable marking

WF-net soundness is **decidable (EXPSPACE)**. Regulatory procedures are a natural fit:
trigger event -> `[i]`, all obligations discharged -> `[o]`.

---

## 1.5 Timed Petri Nets and Deadline Modelling

**Timed transitions:** exponentially or deterministically delayed.
**Deadline arcs:** fire only within a time window.

**Key construct:** `before(T1, T2)` — transition T1 must fire before T2 becomes
enabled/fires. Maps to a timed place `deadline_expires` marked at `M0 + tau` time
units after a trigger. Stratum-2 — polynomial via CLP(PN).

**Example:** GDPR Art. 33 — 72-hour breach notification:
```
before(submit_initial_notification, deadline_expires)
```
where `deadline_expires` is a timed place marked 72h after `breach_detected`.

---

## 1.6 CLP(PN) — Constraint Logic Programming over Petri Nets

**Berthomieu & Diaz (1991):** Embeds PN reasoning as a constraint domain in LP.

**P-invariant:** vector `Y: P -> Z` such that `Y * M = Y * M0` for all reachable M.
- Derivation: solve `Y * C = 0`, `Y >= 0` (LP, **polynomial**)
- `C` = incidence matrix: `C[p][t] = W(t,p) - W(p,t)`
- Non-trivial solution -> token count is conserved -> net is bounded (without reachability)

**T-invariant:** `X: T -> N` such that `C * X = 0`.
- Represents a repeatable firing sequence returning to initial marking.

**aiqeung strata 1-2:** CLP(PN) domain in `ConstraintStore` handles:
- Stratum 1: LP on incidence matrix (boundedness)
- Stratum 2: P-invariant derivation (causal ordering, firing counts)

Neither requires explicit state-space enumeration — safe to call inline.

---

## 1.7 Net Unfolding and Partial-Order Semantics

**McMillan (1993):** A **net unfolding** is an (possibly infinite) acyclic net
representing all runs in partial-order (concurrent) semantics.
- Branching points = non-deterministic choices
- Concurrent transitions appear as independent events

**Significance for compliance:** Compliance witness = **partial-order run** (set of
events with causal dependencies). Proves "Art. 33 notification within 72h" without
committing to a particular interleaving.

**Recent:** FoldA (arXiv 2506.08627) — alignments for partially-ordered traces through
unfoldings, directly addressing concurrent compliance scenarios.
