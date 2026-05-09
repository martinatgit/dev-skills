---
name: improve-prompt
description: Use when the user supplies rough text describing a task they want an LLM to perform and wants a polished, paste-ready prompt back. Triggers on inputs like "improve this prompt", "write a prompt for X", "I want an LLM to Y", or pasted draft prompts that need tightening. Output is exactly one prompt.
---

# improve-prompt

Transform a block of rough user-intent text into one polished, copy-pasteable
LLM prompt, evidence-guarded against the well-replicated failure modes of
prompt engineering (CoT misuse, persona on factual tasks, lost-in-middle,
unwrapped untrusted input, free-form self-correction, paraphrase fragility).

The skill is **self-contained**: it draws only on its own four `references/`
files. It does **not** read project files at runtime.

## Output contract — non-negotiable

The skill emits **exactly one** of:

1. **The polished prompt.** No preface ("Here is your prompt:"), no postscript
   ("Let me know if you need adjustments."), no markdown fence around the
   prompt unless the target system requires fenced output. This is the
   default emission.
2. **Up to 3 clarifying questions** via `AskUserQuestion`. Permitted **only**
   when the ambiguity gate (workflow step 6) fires. After the user answers,
   restart from step 1.

Never narrate the workflow, the 5-whys, the template chosen, or the research
findings cited. The user pastes the prompt; everything else is private
scaffolding.

## When to use

- The user pasted a rough or under-specified prompt and wants it improved.
- The user described a task in natural language ("I want the LLM to …") and
  needs a structured prompt.
- The user asked for "a prompt for X" or "the best way to ask the LLM to Y".

## When NOT to use

- The user wants the **answer** to the task (not a prompt to ask another
  model). Then just answer.
- The user asked specifically for a brainstorm / plan / design — those have
  their own skills.

## Internal workflow (silent — never narrated)

1. **Intent via 5-whys.** Walk `references/five-whys-rubric.md` against the
   user's text. Privately record: primary goal, audience, success criterion,
   failure criterion. Unknowns feed the ambiguity gate (step 6).
2. **Classify.** Pin the three axes:
   - **Length class**: `short` (<60 words), `moderate` (60–400, default),
     `long` (>400). By task complexity, not input length.
   - **Purpose class**: one of `math_symbolic`, `code_gen`, `extraction_qa`,
     `classification`, `structured_output`, `summarization`,
     `creative_content`, `agentic_tool_use`, `research_analysis`,
     `governance_safety`, `instruction_transform`, `general_llm_prompt`.
   - **Context shape**: `zero_shot` | `few_shot` | `rag` | `tool_calling` |
     `multi_turn`. Default `zero_shot`.
3. **Template select.** Look up the (purpose × length) cell in
   `references/template-matrix.md`. The cell specifies role, output contract,
   exemplar placement, and any optional reasoning scaffold.
4. **Evidence-guarded assembly.** Apply only techniques the embedded research
   supports for the chosen purpose. Defaults baked in:
   - **Default-on** (every prompt): explicit output contract, untrusted-content
     envelopes around any user-supplied / retrieved / tool-returned text,
     critical instructions placed at primacy AND recency, 3–5 lexically
     diverse exemplars with varied order when few-shot.
   - **Default-off** (require evidence-backed trigger): CoT, persona,
     self-consistency, in-prompt reflection. Apply only when the purpose
     class matches the trigger column in `references/research-findings.md` §3.
5. **Adversarial critique.** Run `references/critique-checklist.md` end to end
   (Stages A–E). It is deterministic — no free-form reflection (banned by
   `[Self-correction-fails]`, Huang ICLR 2024). Maximum **2 revision cycles**.
6. **Ambiguity gate.** Fire when any of: a 5-whys field is `unknown` and
   blocks the prompt; the inputs self-conflict; the purpose is genuinely
   multi-class and templates do not compose. On fire: halt, ask **≤3**
   targeted questions via `AskUserQuestion`, then restart from step 1. The
   gate may also fire mid-critique (Stage E) if the checklist surfaces
   structural ambiguity.
7. **Emit.** The prompt alone, per the output contract above.

## Reference files (load on demand inside the workflow)

| File | When to read |
|---|---|
| `references/five-whys-rubric.md` | Step 1 (always) |
| `references/template-matrix.md` | Step 3 (always); revisit at step 5 if a checklist fix demands a different cell |
| `references/research-findings.md` | Step 4 (always); cited in step 5 violations by short tag |
| `references/critique-checklist.md` | Step 5 (always) |

These files are the entire evidence base. Do not read project files (the skill
does not need `doc/research-insights/` or `archive/research/` at runtime —
they were distilled into the references at skill-creation time).

## Self-tests (the skill is not done until all three pass)

1. **`extract contact info from this email`** → emit a structured-output
   prompt with an explicit JSON schema (name, email, phone, etc.), an
   `<UNTRUSTED_DATA>` envelope around the email, primacy/recency restatement
   of "JSON only, no prose", and **no CoT scaffold, no persona**.
2. **`solve quadratic equations in Python`** → emit a code-contract prompt
   delegating arithmetic to execution: a typed Python function signature
   (e.g. `def solve_quadratic(a: float, b: float, c: float) -> tuple[complex, complex]`),
   spec, edge-case rules (`a == 0`, complex discriminant), and "Output only
   the code". PAL-flavoured per `[PAL-dominates-arithmetic]`.
3. **`write a blog post`** → ambiguity gate fires; ask up to 3 targeted
   questions covering audience, length, and tone via `AskUserQuestion`.

## Cross-references

A peer **agent** `prompt-engineer` (in `.claude/agents/prompt-engineer.md`)
runs the same workflow as a dispatchable subagent. Use the agent when
multiple prompt-improvement requests should run in parallel, or when the work
should be isolated from the main conversation context. Otherwise invoke the
skill directly.
