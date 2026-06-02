---
name: petri-net-patterns
description: Concrete modelling patterns for Petri net compliance systems: WF-net soundness
  verification strategy, fusion set atomicity enforcement, AND-split/AND-join parallel
  obligations, pausable deadlines, priority-ordered routing with NAF guards, inhibitor
  prohibition patterns, and partial-order compliance witnesses.
type: reference
---

# Petri Net Modelling Patterns

## WF-net Soundness Verification
Soundness check = strata-3 (EXPSPACE). Use bounded state-space exploration with
`tablingMaxStates` limit. For polynomial approximation: check structural properties
(all nodes on i->o path) as necessary condition.

## Fusion Set Atomicity
Compute new token multiset FIRST, then replace all fusion members simultaneously.
```typescript
// WRONG — observable intermediate state:
fusionSet.forEach(place => marking.set(place, newMultiset));

// CORRECT — immutable snapshot, atomic replace:
const next = new Map(current); // snapshot
fusionSet.forEach(place => next.set(place, newMultiset)); // compute new state
return next; // replace entire marking atomically
```

## AND-Split / AND-Join (Fan-out Parallel)
```
fork_transition ->  branch_A_place
                ->  branch_B_place
                ->  branch_C_place
join_transition <- [branch_A, branch_B, branch_C all marked]
```
AND-join fires only when ALL branches have deposited their token. Standard HCPN pattern
for parallel obligations (GDPR Art. 17 erasure: internal + downstream + recipient).

## Pausable Deadlines
`before_with_suspension(T1, T2, SuspensionCondition)`. Clock pauses while
SuspensionCondition holds. Polynomial — stratum-2 CLP(PN) extension. Required for
GDPR Art. 36: SA's 8-week response deadline suspends when SA requests information.

## Priority-Ordered Routing
NAF guards encode priority cascade:
```prolog
guard: adequacy_decision(Case), \+ safeguards_required(Case)  % first priority
guard: safeguards_ok(Case), \+ derogation_applies(Case)       % second priority
```
Free-choice net structure -> polynomial soundness verification.

## Inhibitor Prohibition Pattern
"Must NOT fire unless place is empty":
```
inhibitor arc: permission_NOT_given --O--> prohibited_transition
```
Or: "Must NOT fire while process is ongoing":
```
inhibitor arc: ongoing_process --O--> prohibited_action
```
Reminder: inhibitor arcs make strata 1-2 CLP(PN) refuse unless net is k-bounded.

## Partial-Order Compliance Witness
Use net unfolding for compliance certificates — not sequential firing sequences.
Concurrent events appear as independent nodes in the unfolding, capturing true
parallelism. Compliance property: proved over partial-order runs, not interleavings.
