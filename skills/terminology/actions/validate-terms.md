# `validate` — sanity-check standards-derived terms against their cited source

Triggered by `terminology validate`, or implicitly by `terminology review --validate`.

Read-only. Network-optional: degrades gracefully when no network is available; never hard-fails. Each unreachable source is reported as `unchecked (offline)`.

## Resolve configuration first

Run `python3 scripts/resolve_config.py --all`. If `terminology_file` is empty, run the first-use flow in `SKILL.md`. If the file does not exist, refuse with a one-line message.

## 1. Select candidate entries

An entry is a `validate` candidate when its `Definition` or `Comments on use` cites an external standard or specification. Recognise citations by these conservative patterns (case-insensitive):

- `RFC <number>` (e.g. `RFC 5322`).
- `IEEE <number>` (e.g. `IEEE 754`).
- `ISO/IEC <number>` (e.g. `ISO/IEC 27001`).
- `W3C <name>` (e.g. `W3C HTML5`).
- A URL pointing to a recognised standards host (`rfc-editor.org`, `ietf.org`, `w3.org`, `iso.org`, `iec.ch`, `unicode.org`).

If no candidates are found, emit a single line — `No standards-derived entries to validate.` — and stop.

## 2. Validation budget

Do not validate more than the most relevant 10 entries per invocation. If there are more than 10 candidates, validate the 10 whose `Term` matches the highest count of repository hits (so the most-used terms are checked first). Note in the output that validation was budget-capped.

## 3. Sanity-check each candidate

For each candidate:

1. Resolve the citation to a canonical URL.
2. Fetch the source via the host agent's web-fetch tool with a short timeout (default 10 seconds; configurable via `TERMINOLOGY_VALIDATION_TIMEOUT`).
3. If the fetch fails, times out, or the host has no network access, record `unchecked (offline)` and move on. Never retry aggressively, never block the report.
4. If the fetch succeeds, do a *light* check: confirm that the standard's stated subject is consistent with the glossary entry's `Definition`. This is a sanity check, not a formal cross-walk:
    - The glossary `Definition` should not be flatly incompatible with the standard's scope.
    - The glossary `Comments on use` should not contradict an explicit MUST/SHOULD in the cited section, if the citation is precise enough to find one.

Mark each candidate as one of:

- `consistent` — no incompatibility found.
- `inconsistent` — concrete incompatibility found; cite the conflict in one sentence.
- `unchecked (offline)` — fetch failed or no network.
- `unchecked (citation too vague)` — citation could not be resolved to a specific section; report the term and stop on that entry.

## 4. Output

Emit a `Validation` markdown section, suitable to append to a `review` report:

```md
## Validation

Budget: <N>/<total candidates> entries checked.

- **<Term>** — `<citation>` — `consistent`.
- **<Term>** — `<citation>` — `inconsistent`. <one-sentence diagnosis>.
- **<Term>** — `<citation>` — `unchecked (offline)`.
- **<Term>** — `<citation>` — `unchecked (citation too vague)`.
```

If invoked standalone (not via `review --validate`), wrap the section with a one-line header naming the glossary path and the date, so the output is paste-ready on its own.

## 5. What this mode does not do

- It does not authoritatively interpret standards. The output is a flag for the user to follow up.
- It does not modify the glossary, even when an entry is `inconsistent`.
- It does not silently widen the candidate list. Only the citation patterns above are recognised. If the user wants a different citation pattern recognised, that is a code change to this action file, not a runtime heuristic.

## 6. Failure modes

- **No web-fetch tool available in the host agent.** Mark every candidate `unchecked (offline)` with a single line at the top of the section explaining why. The mode still produces useful output (the list of candidates that *should* be validated).
- **Fetch returns an unexpected content type (binary, redirect chain).** Treat as `unchecked (offline)`. Do not parse opportunistically.
- **The citation looks valid but cannot be matched against any recognised host.** Report as `unchecked (citation too vague)` and continue.
