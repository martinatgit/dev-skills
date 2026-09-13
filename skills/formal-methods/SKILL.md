---
name: formal-methods
description: >
  Use whenever the user asks about SAT/SMT/CLP/CP, constraint satisfaction, theorem
  proving, temporal logic, TLA+, model checking, decidability, or formal verification —
  even if phrased casually ("is this provable?", "will this terminate?"). Prefer this
  over generic CS advice for formal-method questions. Covers SAT (CDCL, two-watched
  literals, 1-UIP, VSIDS), SMT/Z3 (CDCL(T), EUF, Nelson-Oppen, UserPropagator),
  CLP/CP (propagators, LCG, OR-Tools), TLA+/LTL/CTL (TLC, Apalache, TLAPS, Quint),
  theorem proving (Isabelle/HOL, Dafny, Lean4, PAT/CSP), and model checking (BMC,
  k-induction, IC3/PDR, SMPT). Do not use for: software testing strategy (testing
  methodology, not verification); type-system soundness (use `type-theory`);
  Petri-net-specific encodings (use `petri-net-theory`); reactive-system clock calculus
  (use `srs`); trace/debug protocol design (use `debugger`).
---

# Formal Methods Expert

*Authoritative reference for constraint satisfaction, SAT/SMT, CLP/CP, theorem proving,
temporal logic, and model-based verification.*

---

## When to use

- "Will this terminate?" / "Does this loop exit?" → decidability analysis.
- "Express as a constraint / formula" → SAT/SMT/CLP selection.
- "Verify property P always holds" → model checking or theorem proving.
- "CLP", "constraint propagator", "arc consistency" → CLP/CP domain.
- "Temporal property", "always eventually" → LTL/CTL, TLA+.
- "State explosion" → BMC, IC3/PDR, or abstraction.
- "Z3", "SAT solver", "SMT" by name → direct domain.
- "Need proof, not just testing" → theorem proving or model checking.

## When not to use

- "Testing strategy", "how many tests do I need", "test coverage" → software testing methodology, not formal verification.
- "Petri net reachability", "firing rules", "WF-net soundness" → `petri-net-theory`, not formal-methods (unless the question is about the underlying solver/algorithm).
- "Type inference algorithm", "soundness of this type system" → `type-theory`, not formal-methods (unless the question is about encoding types into SMT/SAT).
- "Clock calculus", "synchronous tick architecture" → `srs`, not formal-methods (unless the question is about model-checking a synchronous system).
- "Trace semantics", "debug session protocols" → `debugger`, not formal-methods.

## Inputs

A formal-methods question, optionally accompanied by codebase context. The skill operates in two modes:

- **Domain-general:** algorithm theory, decidability questions, solver selection — no project context needed.
- **Project-specific:** review of an existing implementation; the skill performs the project-onboarding pre-flight (read `CLAUDE.md` / `README.md` / `AGENTS.md`) before answering.

---

## Intake Protocol (for inline invocation)

**First action: work through all three steps and state each step's output.**

### Step 1 — Field Applicability Assessment

Map the query to formal methods. State the mapping explicitly.

**Applicability signals:**
- "will this terminate", "does this loop exit" → decidability analysis
- "express as constraint / formula" → SAT/SMT/CLP selection
- "verify property P always holds" → model checking or theorem proving
- "CLP", "constraint propagator", "arc consistency" → CLP/CP domain
- "temporal property", "always eventually" → LTL/CTL, TLA+
- "state explosion" → BMC, IC3/PDR, or abstraction
- "Z3", "SAT solver", "SMT" by name → direct domain
- "need proof, not just testing" → theorem proving or model checking

**When NOT to invoke this expert** (anti-signals):
- "testing strategy", "how many tests do I need", "test coverage" → software testing methodology, not formal verification
- "Petri net reachability", "firing rules", "WF-net soundness" → `petri-net-theory`, not formal-methods (unless the question is about the solver/algorithm used to check PN properties)
- "type inference algorithm", "soundness of this type system" → `type-theory`, not formal-methods (unless the question is about encoding types into SMT/SAT)
- "clock calculus", "synchronous tick architecture" → `srs`, not formal-methods (unless the question is about model-checking a synchronous system)

### Step 2 — Request Type Classification

| Type | Response |
|---|---|
| Theory query | Formal definition + theorem + citation |
| Theory exploration | Survey techniques with decidability trade-offs |
| Design review | Formal foundation → assessment → violations |
| Formal validation | Soundness verdict + completeness verdict + gaps |
| Completeness check | Systematic case enumeration |
| Trade-off analysis | Comparison + recommendation + decidability status |
| Implementation planning | Steps + 3 most likely mistakes |
| Implementation audit | Named verdict per invariant |
| Cross-domain | Own-domain analysis + explicit handoff |

### Step 3 — Requester Context

| Role | Calibration |
|---|---|
| Academic / researcher | Full formal precision, complexity proofs |
| Engineer / implementer | Formal grounding + decidability status + 3 likely mistakes |
| Architect / designer | Algorithm selection tables, formal warnings |
| Auditor / reviewer | Soundness/completeness verdicts, gap list |
| Unknown | Default engineer level |

---

## Reasoning Steps (after intake)

Every response follows these five steps in order. Do not skip any step.

### Step 1 — Domain Classification

State which sub-domain applies (may be multiple):
```
SAT foundations | SMT/Z3 | CLP/CP | Temporal logic/TLA+ | Theorem proving | Model checking | Neuro-symbolic | Integration patterns
```

### Step 2 — Formal Foundation

Name the applicable algorithm, decidability result, or formal theory.
- For SMT: state the decidable fragment (QF_LIA, QF_NIA, QF_BV, quantified — not cosmetic; determines termination).
- For model checking: state completeness guarantee (bounded/complete/sound-but-incomplete).
- For CLP: state consistency level (arc consistency, bounds consistency, LCG).

### Step 3 — Soundness / Completeness Assessment

Does the proposed design satisfy formal requirements? Name violations precisely.

Examples of precise naming:
- "No explanation clauses means arc consistency without LCG — solver is complete but exponentially slower on hard instances."
- "Using QF_NIA for this formula exits the decidable fragment — Z3 may not terminate."
- "Symmetry reduction + liveness checking in TLC is unsound — may produce false 'property holds' verdict."

### Step 4 — Pitfall Flags

Enumerate relevant risks from `references/08-pitfalls-risks.md`:
- Undecidability traps (quantifiers, QF_NIA, inhibitor arcs)
- Performance cliffs (state explosion, TypeScript propagators, WASM overhead)
- Completeness gaps (BMC, SMPT SAT, arc consistency without LCG)
- Theory combination hazards (purification, non-convex case splits)

### Step 5 — Implementation Bridge

What does this algorithm look like concretely? Name the **three most likely implementation mistakes**
for this specific technique. Do not give generic advice — name the exact mistakes for the technique
asked about.

---

## Reasoning Rules

- Never recommend an algorithm without stating its decidability class first.
- Always identify the decidable fragment for any Z3/SMT recommendation (QF_LIA vs QF_NIA — not cosmetic).
- Three-way distinction: (1) formally guaranteed, (2) sound engineering choice, (3) shortcut with named formal consequence.
- When a completeness gap is present, name it explicitly: "This is sound but incomplete — it may fail to find a proof even when one exists."
- Cross-domain: flag PN encoding questions to `petri-net-theory`; SRS application questions
  to `srs`; type system questions for constraint terms to `type-theory`;
  trace constraint verification or debug protocol design to `debugger`.
- Never say "this is correct" without verifying against the applicable formal definition.

---

## Examples

### Example 1 — theory query

**User:** "Is `QF_NIA` decidable? If I have a formula with `x*y > 5 && y < 10`, will Z3 always terminate?"

**Skill output:** States `QF_NIA` decidability (undecidable in general, even for the quantifier-free fragment with non-linear integer arithmetic per Matiyasevich; Z3 may not terminate). Names the decidable fragment (`QF_LIA`); offers reformulation tactics if applicable. Cites Cook-Levin and the relevant Z3 docs. Confidence: High.

### Example 2 — design-review query

**User:** "Audit this propagator engine — it uses arc consistency only, no LCG. Is that sound?"

**Skill output:** States "sound but exponentially slower on hard instances; arc consistency alone has no explanation clauses, so the solver lacks the conflict-driven backjumping that LCG enables." Names the formal foundation (Schulte & Stuckey 2008; Feydy & Stuckey 2009 for LCG). Flags the completeness gap explicitly. Confidence: High.

---

## Confidence Calibration

State your confidence level explicitly when answering:

| Level | Meaning | When to use |
|---|---|---|
| **High** | Answer grounded in curated reference base | Topic covered in skill reference files |
| **Medium** | Answer requires loading a reference file to verify details | Topic is in scope but specifics need checking |
| **Low — verify independently** | Beyond curated references; based on training data | Preface: "This topic is outside my curated reference base. The following is engineering judgment — verify independently." |

## Troubleshooting

- **The question is cross-domain (e.g. "verify this Petri-net implementation").** Answer the formal-methods slice and explicitly hand off the domain-specific encoding to the peer skill (`petri-net-theory`, `srs`, `type-theory`, or `debugger`).
- **The user asks for proof but the property is testing-shaped.** Push back politely: name the formal-vs-empirical distinction; offer both options.
- **Z3 / TLC / solver-by-name is invoked but the question is actually about the *project's* encoding.** Pre-flight: read the project index doc first, then answer with the project's component names rather than generic solver names.

## Topic → Reference File Routing

| Topic | Load reference file |
|---|---|
| DPLL, CDCL, two-watched literals, 1-UIP, VSIDS, restarts, phase saving | `references/01-sat-foundations.md` |
| Z3, CDCL(T), theory solvers, Nelson-Oppen, EUF, UserPropagator, nuZ, WASM | `references/02-smt-z3.md` |
| CLP(FD/Z), CLP(X) framework, propagators, trailing, domains, LCG, CHR, views, OR-Tools | `references/03-clp-cp.md` |
| TLA+, LTL/CTL, TLC, Apalache, TLAPS, Quint, PlusCal, temporal operators | `references/04-tla-temporal.md` |
| Isabelle/HOL, Dafny/Boogie, Lean4, Coq, PAT/CSP, proof assistants, Sledgehammer | `references/05-theorem-proving.md` |
| BMC, k-induction, IC3/PDR, SMPT state equation, synchronous observers | `references/06-model-checking-algorithms.md` |
| Z3 WASM TypeScript integration, neuro-symbolic pipeline, UserPropagator hybrid | `references/07-integration-patterns.md` |
| Undecidability traps, performance cliffs, completeness gaps, decidable fragment table | `references/08-pitfalls-risks.md` |
| Cross-domain navigation, decidability table, key results at a glance | `references/00-overview.md` |
