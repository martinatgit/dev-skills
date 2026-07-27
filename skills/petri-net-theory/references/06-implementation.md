---
name: petri-net-implementation
description: TypeScript implementation patterns for Petri nets: marking representation,
  arc type discrimination (including inhibitor/read arc extensions), incidence matrix
  construction, P-invariant LP setup, state space exploration with tabling, fusion
  atomicity enforcement, stratum gate code, marking equality for tabling, and test
  harness patterns.
type: reference
---

# Petri Net Implementation Strategies

## Marking Representation
```typescript
// P/T net:
type Marking = Map<string, number>;  // place -> token count

// CPN / Algebraic (tokens as Terms):
type Marking = Map<string, Term[]>;  // place -> multiset of Terms

// Hashing for tabling:
function markingHash(m: Map<string, Term[]>): string {
  return JSON.stringify([...m.entries()].sort(([a], [b]) => a.localeCompare(b)));
}
```

## Arc Type Discrimination
At time of authoring, the aiqeung Arc type had no `kind` field — verify current state in `petri/types.ts`.
Future extension (R8 gap):
```typescript
type Arc =
  | { kind: "normal";    from: string; to: string; expression?: Term }
  | { kind: "inhibitor"; from: string; to: string }           // R8: not yet implemented
  | { kind: "read";      from: string; to: string; expression?: Term }  // R12: not yet implemented

// In fire():
switch (arc.kind) {
  case "normal":    /* consume tokens */    break;
  case "inhibitor": /* check M(p) = 0 */   break;
  case "read":      /* check presence, no consume */ break;
}
```

## Incidence Matrix for P-invariants
```typescript
// C[p][t] = W(t,p) - W(p,t)  (production minus consumption)
function buildIncidenceMatrix(places: string[], transitions: string[], arcs: Arc[]) {
  const C: number[][] = Array.from({length: places.length},
    () => new Array(transitions.length).fill(0));
  for (const arc of arcs.filter(a => a.kind === "normal")) {
    const [pi, ti] = resolveIndices(arc, places, transitions);
    if (isPlaceToTransition(arc)) C[pi][ti] -= arc.weight ?? 1; // consumption
    else                          C[pi][ti] += arc.weight ?? 1; // production
  }
  return C;
}
// Note: inhibitor arcs are NOT in C — P-invariant analysis is incomplete on inhibitor nets
```

## P-Invariant LP Setup (Stratum 1)
```
Minimize: 0 (feasibility LP)
Subject to: Y * C = 0 (invariant equation)
            Y[p] >= 0 for all p
            Y[p0] = 1 for some designated place p0 (non-trivial solution)
```
A non-trivial solution Y proves the net is bounded (token count `Y * M` is constant).

## State Space Exploration (Stratum 3 — Layer 3 only)
```typescript
// Bounded BFS with tabling:
async function exploreReachable(net, initialMarking, maxStates = 10_000) {
  const visited = new Set<string>();
  const worklist = [initialMarking];
  while (worklist.length > 0) {
    if (visited.size > maxStates) return { status: "bounded_exploration_limit_reached" };
    const marking = worklist.pop()!;
    const hash = markingHash(marking);
    if (visited.has(hash)) continue;
    visited.add(hash);
    for (const t of enabledTransitions(net, marking)) {
      worklist.push(fire(net, t, marking));
    }
  }
  return { status: "explored", statesVisited: visited.size };
}
```

---

# Implementation Tips

## Fusion Set Atomicity Enforcement
Never update fusion set members one-by-one. Use immutable marking snapshots:
```typescript
function fireWithFusion(
  marking: Marking,
  fusionGroups: Map<string, string[]>,
  updates: Map<string, Term[]>
): Marking {
  const next = new Map(marking); // snapshot
  for (const [place, newTokens] of updates) {
    const group = fusionGroups.get(place);
    if (group) {
      // Atomic: update ALL fusion members to same value
      group.forEach(fusionPlace => next.set(fusionPlace, newTokens));
    } else {
      next.set(place, newTokens);
    }
  }
  return next; // old marking never mutated
}
```

## Inhibitor Arc Isolation
Before running strata 1-2 CLP(PN) on any net:
```typescript
function assertCLPSafe(net: Net): void {
  const hasInhibitor = net.arcs.some(a => a.kind === "inhibitor");
  if (hasInhibitor && !net.isKBounded) {
    throw new Error(
      "CLP(PN) strata 1-2 analysis refused: net has inhibitor arcs and is not " +
      "proven k-bounded. All verification becomes undecidable (Agerwala 1974). " +
      "Restrict to k-bounded fragment or remove inhibitor arcs."
    );
  }
}
```

## Stratum Gate — Never Cross Inline
```typescript
// In fire() — Layer 2.5:
function fire(page, transition, db, opts, marking) {
  // Stratum 0: structural check — OK inline
  checkStratum0Invariants(contract.invariants, marking);
  // Strata 1-2: CLP(PN) — OK inline (polynomial)
  // checkStrata12(contract) — handled at load time, not per-fire
  
  // NEVER call these inline:
  // checkReachability(...)   // Ackermann-complete
  // checkSoundness(...)      // EXPSPACE
  // checkLiveness(...)       // EXPSPACE
  // These are Layer 3 obligations only
}
```

## Marking Equality for Tabling
```typescript
// Sort by place name for canonical form:
function markingHash(m: Map<string, Term[]>): string {
  return JSON.stringify(
    [...m.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([place, tokens]) => [place, tokens.map(termToString).sort()])
  );
}
```

## Test Harness Pattern for PN Verification
```typescript
import { NetBuilder } from "./net-builder.js";
import { solve } from "../solver.js";

test("transition fires correctly, invariant preserved", async () => {
  const net = new NetBuilder()
    .addPlace("p1").addPlace("p2")
    .addTransition("t1", { guard: atom("can_fire") })
    .addArc({ from: "p1", to: "t1" })
    .addArc({ from: "t1", to: "p2" })
    .build();
  const m0: Marking = new Map([["p1", [atom("token")]], ["p2", []]]);
  const db = buildDB([clause(atom("can_fire"), [])]);
  const result = await net.fire("root", "t1", db, undefined, m0);
  expect(result.status).toBe("ok");
  expect(result.marking.get("p1")).toHaveLength(0);
  expect(result.marking.get("p2")).toHaveLength(1);
});

test("stratum-0 invariant violated stops firing", async () => {
  // ... setup net with not_marked invariant on a place that IS marked ...
  const result = await net.fire("root", "t1", db, undefined, marking_with_violation);
  expect(result.status).toBe("invariant_violated");
});
```
