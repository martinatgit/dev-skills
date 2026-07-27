---
name: petri-net-extensions
description: Inhibitor arcs (Turing-completeness, zero-testing, undecidability),
  Predicate/Transition nets, Algebraic Petri Nets, Object Petri Nets (nets-within-nets),
  and Stochastic Petri Nets. Each section covers formal definition, decidability impact,
  regulatory relevance, and implementation implications.
type: reference
---

# Petri Net Extensions (S1.8-1.12)

## 1.8 Inhibitor Arcs and Zero-Testing

**Extended net:** `PN_I = (P, T, F, I, W, M0)` where `I <= P x T` is the inhibitor arc relation.

**Extended enabling:** `t` enabled iff:
1. Standard: `for all p in *t: M(p) >= W(p,t)`
2. Inhibitor: `for all (p,t) in I: M(p) = 0`

Graphically: inhibitor arc drawn with hollow circle instead of arrowhead.

**Turing-completeness (Agerwala 1974, following Minsky 1967):**
Inhibitor arcs provide zero-testing -> simulate two-counter machines -> Turing-complete.
Consequence: **all non-trivial verification problems become undecidable**
(reachability, boundedness, liveness, coverability).

**Impact on P-invariant analysis:** Inhibitor arcs not captured in the incidence matrix.
P-invariant analysis remains structurally applicable but becomes **incomplete** — token
conservation holds, but does not characterise all reachable markings.

**Strategies to preserve decidability:**
1. **Bounded inhibitor nets:** If k-bounded, state space is finite -> exhaustive exploration
2. **Structural restriction:** Limit inhibitor arcs to boolean flag (1-safe) places
3. **Prioritised transitions:** Can sometimes substitute for inhibitor arcs

**Regulatory value:**
- "Shall NOT deploy if no conformity assessment" -> inhibitor arc from `assessment_done` to `deploy`
- "Unless", "except when", "provided that ... not" patterns
- Art. 36 GDPR: "must not process until consultation concludes" — requires inhibitor semantics
- Art. 78(2) GDPR: remedy enabled only when SA has NOT responded within 3 months

---

## 1.9 Predicate/Transition Nets (PrT-Nets)

**Genrich & Lautenbach (1981):** `PrT = (S, T, F, A, phi, M0)` where:
- `A: F -> Bags(Var^n)` = arc inscriptions as multisets of variable tuples
- `phi: T -> L(Var)` = first-order logic guards
- `M0: S -> Bags(Ind^n)` = ground tuple multisets

Firing requires substitution sigma satisfying input arc inscriptions AND guard `phi(t)`.

**Regulatory relevance:** Conditional regulatory requirements:
- "If high-risk AND biometric data -> conformity assessment required" = conjunction guard
- Role-based obligations with predicate-place inscriptions

---

## 1.10 Algebraic Petri Nets

**APN = (SPEC, P, T, F, A, phi, M0)** where `SPEC = (Sigma, E)` = algebraic specification.
Tokens = ground terms from `T_Sigma`. Arc inscriptions contain term variables -> assignment
via **unification**.

**Direct aiqeung alignment:** aiqeung tokens ARE Terms (Layer 0). Arc expressions
pattern-matched via SLD. This is the most natural formalism for aiqeung.

**Decidability:** Finite carrier sets + bounded nets -> decidable. Infinite carriers ->
most properties undecidable.

---

## 1.11 Object Petri Nets (Nets-within-Nets)

**Valk (2004):** Tokens in designated places are themselves **Petri net instances** with
internal markings. System net transitions can synchronise with object net transitions.

**Decidability:** Reachability **undecidable** (synchronisation simulates zero-testing).
Boundedness decidable for elementary systems.

**Regulatory relevance:** AI systems, data subjects, organisations as object nets
carrying lifecycle state. Hierarchical regulation (EU AI Act -> national -> org -> system)
maps to nesting depth.

---

## 1.12 Stochastic Petri Nets

**Molloy (1982):** Exponentially distributed firing rate `lambda(t)` per transition.
Bounded SPN reachability graph is isomorphic to a **Continuous-Time Markov Chain (CTMC)**.

**GSPNs:** Timed transitions (exponential) + immediate (zero delay, priority over timed).
Vanishing markings (only immediate transitions enabled) eliminated analytically.

**Regulatory uses:** Risk quantification (firing rates = incident frequencies), temporal
compliance probability, audit frequency modelling.
