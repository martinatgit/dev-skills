# Five-Whys Rubric — Silent Intent Extraction

> Purpose: extract the intent behind the user's rough text without burdening
> the user with questions. This is a **private internal dialogue**: never
> narrated in the emitted prompt and never shown to the user except via the
> ambiguity gate.
>
> Output: a fixed 4-field record (goal / audience / success / failure) plus a
> classification triple (length / purpose / context shape) used by the
> template-matrix.

---

## Why this is silent

Asking the user 5 questions before every prompt would be hostile. The "why
chain" is run by the skill against itself, using whatever signal is in the
user's input text plus default heuristics. Only when self-questioning does
**not** resolve the four record fields does the **ambiguity gate** fire and
escalate to the user (max 3 questions).

This is the same pattern as bidirectional type-checking: synthesize as much as
possible, only check (ask) when synthesis is insufficient.

---

## The why chain

For each "why", ask **of the input text itself**, not of the user. Record the
answer or `unknown`. Stop early if a field is already pinned.

### Why 1 — What is the user **literally** asking the LLM to do?
- Look for the verb. ("extract", "summarise", "write", "classify",
  "convert", "solve", "review", "draft", "explain", …)
- Look for the noun. ("contact info", "blog post", "function", "label",
  "summary", …)
- Record: **primary goal** (one sentence, declarative).

### Why 2 — Why does the user need this output?
- What downstream use does the output serve?
- If the output is structured (JSON, CSV, code, schema), the downstream is a
  parser → typed contract is mandatory.
- If the output is for a human, audience matters → tone/voice constraint.
- If the output is one-shot vs reused, the prompt-robustness budget differs.
- Record: **audience** (parser / specific human role / general reader / unknown).

### Why 3 — How will the user judge the output as good?
- Is there an exact-match ground truth (extraction, classification, code that
  must compile)?
- Is there a measurable property (length, structure, presence of fields)?
- Is it subjective (style, tone, persuasiveness)?
- Record: **success criterion** (one sentence; ideally testable).

### Why 4 — What would make the output **unacceptable**?
- Hallucinated fields, missing required fields, wrong format, wrong tone,
  refusal failure (e.g. answering when the input is invalid).
- Identify a refusal/null-handling rule that prevents the worst case.
- Record: **failure criterion** (one sentence; ideally what the prompt's
  refusal rule must cover).

### Why 5 — Why is the rough input the way it is?
- This last "why" is for **classification**, not for the record. Use it to pin:
  - **purpose class** (the column in template-matrix): one of
    `math_symbolic`, `code_gen`, `extraction_qa`, `classification`,
    `structured_output`, `summarization`, `creative_content`,
    `agentic_tool_use`, `research_analysis`, `governance_safety`,
    `instruction_transform`, `general_llm_prompt`.
  - **length class**: `short` (<60 words of emitted prompt), `moderate`
    (60–400, default), `long` (>400). By task complexity, not input length.
  - **context shape**: `zero_shot`, `few_shot`, `rag`, `tool_calling`,
    `multi_turn`. Default `zero_shot`.

---

## Decision rules for ambiguous inputs

| Symptom | Default | Escalate-to-gate condition |
|---|---|---|
| No verb in input | Synthesise from noun ("blog post" → write; "JSON schema" → produce schema) | Verb still unclear after synthesis |
| Audience absent | If output is parseable → "parser"; if output is prose → "general reader, professional tone" | Output is creative content (blog, story, marketing) AND audience is undefined → **gate** |
| Success criterion absent | If output type is structured → "valid against the schema"; if classification → "label from the closed set" | Output is open-ended (essay, review) AND no length / structure / quality cue → **gate** |
| Failure criterion absent | Default to "do not invent fields not present in the input" or "refuse if unparseable" | If failure is fundamentally task-defining (e.g. policy review) AND not stated → **gate** |
| Two purposes equally plausible AND templates do not compose | n/a | **Gate immediately** |
| Input self-conflicts (e.g. "be brief but include all details") | n/a | **Gate immediately** |

---

## Examples (worked, silent — do not narrate to user)

### Example 1 — `"extract contact info from this email"`

- Why 1: extract structured fields (name / email / phone / etc.)
- Why 2: downstream is a parser → typed JSON contract.
- Why 3: success = JSON validates against schema, fields present when in input.
- Why 4: failure = inventing fields not in input; missing fields when present.
- Why 5: purpose = `extraction_qa`; length = `moderate`; context = `zero_shot`.
- → No gate. Use `extraction_qa × moderate` template. No CoT, no persona.

### Example 2 — `"solve quadratic equations in Python"`

- Why 1: produce Python code that solves a quadratic.
- Why 2: parser is the Python interpreter.
- Why 3: success = compiling, correct roots for any well-formed input.
- Why 4: failure = wrong roots; not handling complex discriminant; not
  validating coefficients.
- Why 5: purpose = `code_gen` (PAL flavour); length = `moderate`; context =
  `zero_shot`.
- → No gate. Use `code_gen × moderate` with PAL framing — emit a Python
  function whose execution is the answer. No CoT in prose.

### Example 3 — `"write a blog post"`

- Why 1: produce a blog post (creative content).
- Why 2: audience = **unknown** (developers? executives? general public?).
- Why 3: success = **unknown** (length? tone? topic angle?).
- Why 4: failure = **unknown** (off-topic? wrong register? AI-cliché phrases?).
- Why 5: purpose = `creative_content`; but length / audience / success all
  `unknown` → **ambiguity gate fires**.
- → Halt. Ask up to 3 questions via `AskUserQuestion`: audience, length, tone.

---

## What this rubric is NOT

- It is **not** a free-form reasoning loop — that would invite
  `[Self-correction-fails]` failure modes. It is a fixed 5-step deterministic
  walk.
- It is **not** narrated in the emitted prompt. The 5-whys record stays
  private; only its consequences (in the form of declarative role, schema,
  refusal rule) appear in the emitted prompt.
- It is **not** a substitute for the ambiguity gate; it is what **decides**
  whether the gate fires.
