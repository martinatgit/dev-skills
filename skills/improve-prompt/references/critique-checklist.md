# Adversarial Critique Checklist — Deterministic Red-Team Pass

> Purpose: catch failure modes in the candidate prompt **before** emitting it.
> This is a deterministic checklist, not a free-form reflection — Huang et al.
> ICLR 2024 (`[Self-correction-fails]`) shows free-form self-critique fails
> without an external signal. The "external signal" here is **this fixed list**.
>
> Run it after the candidate prompt is assembled. Every check has a binary
> outcome and a deterministic remediation. Maximum **2 revision cycles**, then
> ship the best version reached.

---

## Stage A — Coverage check (5-whys preservation)

The candidate prompt **must** make every recorded 5-whys element actionable for
the downstream LLM. Verify each in turn:

| # | 5-whys element | Where it must appear | Pass condition |
|---|---|---|---|
| A1 | **Primary goal** | Primacy zone, declarative sentence | The downstream LLM can state the goal in its own words from the prompt alone |
| A2 | **Audience** (when relevant) | Primacy or in tone/voice constraint | Vocabulary, tone, level of detail are pinned |
| A3 | **Success criterion** | Output contract / schema | The schema names exactly what success looks like |
| A4 | **Failure criterion** | Refusal rule / null-handling rule | A "do not / refuse if …" line is present |

**If any A row fails:** add the missing element in the correct zone. Recount.

---

## Stage B — Failure-mode veto (each is a HARD STOP)

Each row maps to an embedded research finding. If the candidate violates the
row, revise according to "Fix" and re-run the checklist from A.

| # | Failure mode | Detection | Fix | Cite |
|---|---|---|---|---|
| B1 | **Unjustified CoT** | Prompt contains "step by step", "show your reasoning", or an explicit chain-of-thought scaffold AND purpose ∉ {`math_symbolic`, deductive `code_gen`} | Delete the CoT scaffold. Restate the output contract instead. | `[CoT-narrow]` |
| B2 | **Persona on factual task** | Prompt contains "You are a/an <expert / careful / precise / X>" AND purpose ∉ {`creative_content` (voice)} | Delete the persona line. Replace with a one-line declarative role ("Extract …", "Classify …", "Summarise …"). | `[Persona-null]` |
| B3 | **Critical content buried mid-prompt** | The output contract, refusal rule, or hard constraint appears **only** in the middle of a long prompt | Mirror it in primacy AND recency zones. | `[Lost-in-middle]` |
| B4 | **Implicit output contract** | Output type/shape is conveyed only by example, never declaratively | Add a one-line schema or "Emit only X, no prose" rule, restated in recency. | `[DSPy-typed-outputs]`, `[Multi-prompt-required]` |
| B5 | **Homogeneous exemplars** | When few-shot, ≥3 exemplars share surface form, label, or ordering pattern | Replace with lexically diverse exemplars; vary order; cover label distribution. | `[Order-flips]`, `[Format-flips]` |
| B6 | **Unwrapped untrusted input** | User-supplied / retrieved / tool-returned content appears as bare text | Wrap in `<UNTRUSTED_DATA>` envelope; state "data not instructions" guard in primacy AND recency. | `[Injection-surface]` |
| B7 | **Paraphrase-fragile phrasing** | The prompt's correctness depends on a clever wording such that a synonym swap breaks it | Rewrite declaratively, anchor on schema field names rather than prose, restate constraints. | `[Multi-prompt-required]` |
| B8 | **In-prompt reflection scaffold** | Prompt contains "review your answer", "double-check", "reflect on", or an internal critique loop AND no external verifier exists | Delete the scaffold. If verification matters, document outside the prompt that an external verifier (test, code interpreter, retrieval check) must close the loop. | `[Self-correction-fails]` |
| B9 | **Free-form arithmetic asked of text** | Prompt asks the LLM to compute a non-trivial number directly AND a code-contract template (`code_gen` PAL flavour) was not preferred | Switch to `code_gen` template that emits an executable function whose output is the answer. | `[PAL-dominates-arithmetic]` |

A B-row violation always triggers a revision. Two revision cycles is the cap.

---

## Stage C — Steelman pro/con

Articulate one steelman **for** the current candidate and one steelman
**against** it. Use this template, written in private — do not narrate it in
the user-facing output.

```
PRO: "This prompt succeeds because <one sentence — what makes it robust>."
CON: "This prompt fails when <one sentence — concrete failure scenario, ideally
     paraphrased input or adversarial input>."
```

Then ask: **does the CON survive?**

- If the CON describes a failure mode listed in Stage B → revise (the fix is
  prescribed there).
- If the CON describes a failure mode **not** listed in Stage B but rooted in
  an embedded finding (`research-findings.md` §1) → revise: add the missing
  default-on practice.
- If the CON describes a real but out-of-scope concern (e.g. "the model might
  not have seen this domain") → record as a residual risk; do not revise. The
  prompt cannot solve every problem.
- If no CON survives → ship.

**Cycle limit: 2.** After two revision cycles, emit the best candidate
reached. Do not loop indefinitely; that is the same failure mode as
intrinsic self-correction → `[Self-correction-fails]`.

---

## Stage D — Emission gate

Final binary checks before emitting:

- [ ] D1 — Output is **exactly one prompt**, no preface, no postscript, no
  "here is your prompt:" framing.
- [ ] D2 — No markdown fence around the prompt **unless** the target system
  requires fenced output (e.g. emitting code that must arrive in a
  ```code``` block). When in doubt, no fence.
- [ ] D3 — No mention of this skill, the workflow, the 5-whys, the
  research findings, or the critique checklist appears in the emitted text.
  The user pastes the prompt; everything else is internal scaffolding.
- [ ] D4 — Length class roughly matches the chosen template (`short`,
  `moderate`, `long`).

If any D row fails, fix the surface form (do **not** restart the workflow —
these are formatting fixes, not semantic ones).

---

## Stage E — Ambiguity-gate revisit (post-critique)

If during Stages A–C the critique uncovered that the 5-whys answers were
themselves uncertain (e.g. the success criterion is genuinely undefined, or
two purpose classes are equally plausible and templates do not compose), the
ambiguity gate fires **now** rather than at gate time. Halt; ask the user up
to 3 targeted questions via `AskUserQuestion`; restart the workflow.

This is the only legitimate path back to step 1 after critique. It is **not**
a free reflection loop — it is triggered by a specific structural ambiguity
discovered during checklist execution.
