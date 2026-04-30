# Theoretical grounding

The skill operationalises three established knowledge-management traditions. Each principle is mapped to a specific mechanism in the skill — not citation theatre.

| Source | Principle | Mechanism in this skill |
|---|---|---|
| Zettelkasten (Luhmann, 1981) | Atomic notes, permanent IDs, explicit links | One TODO per file; permanent `TODO-YYYYMMDD-NNNN` ids that never change; ≥1 `related` link enforced at clarify-time; orphans flagged in `review`. |
| Getting Things Done (Allen, 2015) | Capture → Clarify → Organise → Reflect → Engage | Two-phase flow: `capture` writes to `inbox/`; `clarify` promotes to `active/`. The mandatory `very-next-action` field at clarify-time is Allen's "physical and visible action" test. `review` mode forces the weekly-style sweep. |
| Second Brain / PARA (Forte, 2022) | Projects vs Areas vs Resources vs Archives | `scope: project \| area \| resource` frontmatter field. `archive/` folder for resolved/wont-fix/discarded items. |
| GTD forced-triage | Nothing is "someday" without an expiry | `expires` field (default `default_expiry_days`, default 90 days). `review` refuses to proceed past an expired TODO without recording extend / resolve / wont-fix / discard. |

## Why each principle applies here

**Atomic notes (Zettelkasten).** A single concept per file means a TODO can move between folders (`inbox/` → `active/` → `archive/`) without re-fragmenting the corpus. The permanent ID is the citation key.

**Capture → Clarify (GTD).** Capture must be cheap or it is not used. Clarification must be deliberate or the corpus is full of half-thoughts. Two phases preserve both properties.

**`very-next-action` (GTD).** Allen's empirical observation: lists rot when items are stated in mental verbs ("think about X", "consider Y"). Forcing a physical, visible next action is the mechanism that makes a TODO actually actionable.

**PARA scope (Forte).** Distinguishes time-bounded work (project) from ongoing responsibility (area) from reference material (resource). Without this distinction, "ongoing concerns" silently age into stale projects.

**Forced triage (GTD).** The reason most TODO systems fail is that they never close the loop. An expiry date with `review`'s hard refusal is the closure mechanism.

## References

- Allen, D. (2015). *Getting Things Done: The Art of Stress-Free Productivity* (rev. ed.). Penguin.
- Forte, T. (2022). *Building a Second Brain*. Atria Books.
- Luhmann, N. (1981). "Kommunikation mit Zettelkästen. Ein Erfahrungsbericht." Reprinted in *Universität als Milieu*. Bielefeld: Haux, 1992.
