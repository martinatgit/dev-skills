---
name: petri-net-pitfalls
description: Eight critical pitfalls in Petri net implementation: inhibitor arcs with
  strata 1-2 analysis, reachability computation inline, CPN unbounded colour domains,
  fusion atomicity violations, object net synchronisation, strata-3 inside SLD loop,
  Ackermann complexity misunderstanding, and missing before_with_suspension. Each
  entry includes consequence, detection method, and mitigation.
type: reference
---

# Petri Net Pitfalls & Limits

| Pitfall | Consequence | How to Detect | Mitigation |
|---|---|---|---|
| Inhibitor arcs + strata 1-2 analysis | P-invariant analysis incomplete — may prove false boundedness or miss violations | Net has arcs with `kind: "inhibitor"` | Refuse strata 1-2 on inhibitor nets unless k-bounded |
| P/T net reachability inline | Ackermann-complete — computation never terminates in practice | Any call to `checkReachability()` outside Layer 3 | Stratum gate: strata-3 ONLY in Layer 3 reactive runtime |
| CPN unbounded colour domain | Turing-complete — no verification results hold | Colour set is `any`/`Term` without finite enumeration | Restrict to finite colour sets for decidable fragment |
| Fusion atomicity violation | Incoherent global marking — silent state corruption | Multiple separate `marking.set()` calls for fusion members | Immutable snapshots, atomic update of all fusion members |
| Object net synchronisation | Undecidable — zero-testing via synchronisation | Any net where token-nets synchronise with parent transitions | Avoid synchronisation primitives in elementary object nets |
| Strata-3 inside SLD loop | EXPSPACE computation in hot path — catastrophic latency | `checkSoundness()` or `checkReachability()` in `fire()` | Code review: strata-3 calls only in Layer 3 obligation scheduler |
| Ackermann complexity of reachability | Beyond any fixed exponential tower (Czerwinski 2021) — do NOT assume EXPSPACE is a tight bound | Any reachability query on unbounded net | Use coverability (EXPSPACE) as approximation; accept incompleteness |
| Missing `before_with_suspension` | Pausable deadlines modelled incorrectly as fixed deadlines | Art. 36-style "deadline suspends while X" requirements | R11 gap: add `before_with_suspension(T1, T2, SuspCond)` to CLP(PN) stratum 2 |
