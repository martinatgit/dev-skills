---
name: petri-net-theory-overview
description: Navigation map, decidability quick-reference, key results at a glance,
  and full bibliography for the petri-net-theory knowledge base. Load first when
  unsure which reference file to consult.
type: reference
---

# Petri Net Theory — Navigation Overview

## Topic -> Reference File Routing

| Topic | Load |
|---|---|
| P/T nets, CPNs, HCPNs, WF-nets, CLP(PN), net unfolding | `01-core-formalisms.md` |
| Inhibitor arcs, PrT-nets, algebraic PN, object PN, stochastic PN | `02-extensions.md` |
| Decidability classes, stratum table, complexity | `03-decidability.md` |
| Deontic mappings, CTL/LTL templates, compliance literature | `04-compliance-modeling.md` |
| Modelling patterns | `05-patterns.md` |
| TypeScript implementation patterns | `06-implementation.md` |
| Pitfall table | `07-pitfalls.md` |
| aiqeung worked examples | `08-worked-examples.md` |

## Quick-Reference Decidability Table

| Formalism / Property | Decidability | Complexity | Notes |
|---|---|---|---|
| P/T net reachability | Decidable | **Ackermann-complete** (Czerwinski 2021) | Beyond any fixed exponential tower |
| P/T net coverability | Decidable | EXPSPACE-complete (Rackoff 1978) | Approximation for reachability |
| P/T net boundedness | Decidable | EXPSPACE-complete | |
| P/T net deadlock-freedom | Decidable | EXPSPACE | |
| P/T net liveness | Decidable | EXPSPACE-hard | |
| WF-net soundness | Decidable | EXPSPACE | Layer 3 obligations only |
| P-invariant derivation | Decidable | Polynomial | Stratum 1 — safe inline |
| CPN (finite colours) | Same as P/T | EXPSPACE/Ackermann | Unfolds to P/T net |
| CPN (infinite colours) | **Turing-complete** | Undecidable | No general results |
| Inhibitor arcs (any property) | **Undecidable** | — | Zero-testing -> Turing-complete |
| PrT-nets (finite domains) | Decidable | EXPSPACE | |
| Algebraic PN (bounded+finite) | Decidable | EXPSPACE | |
| Object PN reachability | **Undecidable** | — | Synchronisation simulates zero-testing |

## Stratum Gate — The Critical Architectural Invariant

| Stratum | Method | Complexity | Safe inline in fire()? |
|---|---|---|---|
| 0 | Structural check (token presence) | O(1) | YES |
| 1 | P-invariant / LP | Polynomial | YES (at load time) |
| 2 | Causal ordering, before() | Polynomial | YES |
| 3 | Reachability, soundness, liveness | EXPSPACE / Ackermann | **NO — NEVER INLINE** |

## Bibliography

### Foundational
1. Petri, C.A. (1962). *Kommunikation mit Automaten*. PhD thesis, Universitat Hamburg.
2. Murata, T. (1989). "Petri nets: Properties, analysis and applications." *Proc. IEEE*, 77(4):541-580.
3. Jensen, K. & Kristensen, L.M. (2009). *Coloured Petri Nets: Modelling and Validation of Concurrent Systems*. Springer.
4. van der Aalst, W.M.P. (1997). "Verification of workflow nets." *ICATPN 1997*, LNCS 1248.
5. Reisig, W. (2013). *Understanding Petri Nets: Modeling Techniques, Analysis Methods, Case Studies*. Springer.

### Extensions
6. Minsky, M.L. (1967). *Computation: Finite and Infinite Machines*. Prentice-Hall.
7. Agerwala, T. (1974). "A complete model for representing the coordination of asynchronous processes." *Symposium on Computer Architecture 1974*.
8. Genrich, H.J. & Lautenbach, K. (1981). "System modelling with high-level Petri nets." *TCS* 13(1):109-136.
9. Reisig, W. (1991). "Petri nets and algebraic specifications." *TCS* 80(1):1-34.
10. Valk, R. (2004). "Object Petri nets: Using the nets-within-nets paradigm." In *Advances in Petri Nets*, LNCS 3098.
11. Molloy, M.K. (1982). "Performance analysis using stochastic Petri nets." *IEEE Trans. Computers* C-31(9):913-917.
12. Berthomieu, B. & Diaz, M. (1991). "Modeling and verification of time dependent systems using time Petri nets." *IEEE TSE* 17(3):259-273.
13. McMillan, K.L. (1993). "Using unfoldings to avoid the state explosion problem in the verification of asynchronous circuits." *CAV 1993*, LNCS 697.

### Decidability
14. Rackoff, C. (1978). "The covering and boundedness problems for vector addition systems." *TCS* 6(2):223-231.
15. Czerwinski, W., Lasota, S., Lazic, R., Leroux, J. & Mazowiecki, F. (2021). "The reachability problem for Petri nets is not elementary." *JACM* 68(1):7:1-7:28.

### Compliance / Deontic / Regulatory
16. Padget, J. & Vasconcelos, W.W. (2009). "A logic-based framework for normative multi-agent systems." In *Normative Multi-Agent Systems*, Dagstuhl Seminar.
17. Lokhorst, G. (1996). "Mally's deontic logic." *The Stanford Encyclopedia of Philosophy*.
18. Sileno, G., Boer, A. & van Engers, T. (2018). "A logic programming approach to normative specification and reasoning." In *Rules and Reasoning*, LNCS 11092.
19. Elgammal, A., Turetken, O., van den Heuvel, W. & Papazoglou, M. (2016). "Formalizing and appling compliance patterns for business process compliance." *Software & Systems Modeling* 15(1):119-146.
20. Pesic, M., Schonenberg, H. & van der Aalst, W.M.P. (2007). "DECLARE: Full support for loosely-structured processes." *EDOC 2007*.
21. van der Aalst, W.M.P. & de Medeiros, A.K.A. (2005). "Process mining and security: Detecting anomalous process executions and checking process conformance." *ENTCS* 121:3-21.

### Tools
22. Ratzer, A.V. et al. (2003). "CPN Tools for editing, simulating, and analysing coloured Petri nets." *ICATPN 2003*, LNCS 2679.
23. ISO/IEC 15909-1:2019. *High-level Petri nets — Part 1: Concepts, definitions and graphical notation*.
24. ISO/IEC 15909-2:2011. *High-level Petri nets — Part 2: Transfer format (PNML)*.
