# Skills conformance and agents-layer design

**Status:** draft for review
**Date:** 2026-06-04
**Branch:** `feature/shared-skill-config`
**Scope:** three neglected skills + four ported peer skills + new `agents/` distribution layer

## 1. Background

The `dev-skills` repository currently ships seven skills that have either never been brought into authoring-guide conformance or have been ported from upstream without the cleanup pass. Six of them are missing from the `README.md` skills table and `.claude-plugin/marketplace.json`. Meanwhile, the repo contains an `agents/` directory with six Claude Code subagent definitions, an undocumented convention with no portable counterpart for other hosts and no installer.

The initial trigger for this work was a review of three "neglected" skills — `create-tutorial`, `improve-prompt`, `formal-methods-expert`. A deeper review surfaced two larger gaps: the four peer skills that `formal-methods-expert` cross-references have been bulk-ported but not normalised, and the `agents/` layer needs to become a first-class repo convention.

### 1.1 Already done on this branch

The `feature/shared-skill-config` branch has 23 commits ahead of `main`. The following work overlaps with what this spec used to cover and is now considered done:

- `create-tutorial` frontmatter is spec-compliant.
- `create-tutorial` has full Pattern-2 configuration plumbing (`scripts/configure.py`, `resolve_config.py`, `find_project_root.py`, `read_shared_conventions.py`).
- `create-tutorial` is registered in `README.md` and `.claude-plugin/marketplace.json`.
- Four peer skills (`debugger-expert`, `petri-net-theory`, `srs-expert`, `type-theory-expert`) are imported into `skills/` from the AIQURIS upstream.
- A shared-conventions mechanism (`.agents/dev-skills.yaml`) is fully built and documented: canonical reader at `template/scripts/read_shared_conventions.py`, drift check in `evals/run.py`, installer at `scripts/setup-conventions.py`, refresher at `scripts/refresh-shared-reader.py`, and integrated into `developer-diary`, `update-todos`, `terminology`, `create-tutorial`.
- A `tests/` directory with 13+ pytest files for the shared-conventions reader, drift check, refresher, and per-skill integration tests.
- Resolution-order layer cake updated to five layers (env → project-skill → shared → user-skill → default), documented in `docs/install.md` and `docs/authoring-guide.md`.

`evals/run.py` currently passes ("OK — checked 13 skill(s)").

### 1.2 Still to do (the scope of this spec)

- Bring `create-tutorial` to full template conformance (`$ARGUMENTS` removal, Examples, Troubleshooting, paired agent, fixtures).
- Bring `improve-prompt` to full template conformance.
- Bring `formal-methods-expert` to full template conformance.
- Bring four ported peer skills to full template conformance.
- Rename four skill folders to drop the `-expert` suffix.
- Restructure `agents/` to ship Claude Code Markdown + Codex CLI TOML in parallel, with a host-detection installer.
- Register all six unregistered skills in `README.md` and `.claude-plugin/marketplace.json`.
- Add `evals/fixtures/<skill>/prompts.json` for every skill that doesn't yet have one.

## 2. Goals and non-goals

### 2.1 Goals

- Every skill in the repo passes the portability checklist.
- Every skill is discoverable from `README.md` and installable via `/plugin install`.
- Cross-references between skills resolve to real, in-repo skills (no dangling pointers).
- Agent definitions ship for both Claude Code and Codex CLI, with a documented install path per host.
- Naming is internally consistent: `<skill>-agent` for paired agents, no `-expert` suffix on either side.
- The shared-conventions layer extends naturally to all path-typed skills.

### 2.2 Non-goals

- Porting agents to Cursor / Windsurf / Goose. None of these has a file-based subagent equivalent today; the installer skips them silently.
- Achieving an open cross-vendor subagent standard. None exists; we ship per-host files and document them as non-universal.
- Registering or restructuring `skills/sanity-design-analysis/`. Out of scope for this work; can be revisited separately.
- Touching `agents/devAgent/`. Gitignored, out of scope.
- Extending `evals/run.py` to read `prompts.json` and run actual trigger-rate tests. Fixtures land in this spec; the runner extension is a follow-up.

## 3. End-state architecture

### 3.1 Skill inventory after this work

| Skill | Source | Notes |
|---|---|---|
| `example-skill` | unchanged | reference skill |
| `developer-diary` | unchanged | already conformant |
| `reason-through` | unchanged | already conformant |
| `update-todos` | unchanged | already conformant |
| `terminology` | unchanged | already conformant |
| `create-tutorial` | conformance pass | finish Layer A work |
| `improve-prompt` | conformance pass | finish Layer A work |
| `formal-methods` | renamed from `formal-methods-expert` + conformance pass | drops `-expert` |
| `debugger` | renamed from `debugger-expert` + conformance pass | drops `-expert` |
| `srs` | renamed from `srs-expert` + conformance pass | drops `-expert` |
| `type-theory` | renamed from `type-theory-expert` + conformance pass | drops `-expert` |
| `petri-net-theory` | conformance pass | no rename (no `-expert` to drop) |
| `sanity-design-analysis` | left alone | explicitly out of scope |

### 3.2 Agent inventory after this work

| Agent | Paired skill | Status |
|---|---|---|
| `improve-prompt-agent` | `improve-prompt` | renamed from `prompt-engineer` |
| `create-tutorial-agent` | `create-tutorial` | new |
| `formal-methods-agent` | `formal-methods` | renamed from `formal-methods-expert` |
| `petri-net-theory-agent` | `petri-net-theory` | renamed from `petri-net-expert` |
| `srs-agent` | `srs` | renamed from `srs-expert` |
| `type-theory-agent` | `type-theory` | renamed from `type-theory-expert` |
| `debugger-agent` | `debugger` | renamed from `debugger-expert` |

Naming rule: agent name = `<paired-skill-name>` + `-agent`. The skill name carries no `-expert` suffix, so the agent inherits a clean name.

### 3.3 `agents/` folder structure

```
agents/
├── README.md                          (overview, naming rule, format conventions)
├── create-tutorial-agent.md           (Claude Code subagent — YAML+Markdown)
├── create-tutorial-agent.toml         (Codex CLI subagent — TOML)
├── improve-prompt-agent.md
├── improve-prompt-agent.toml
├── formal-methods-agent.md
├── formal-methods-agent.toml
├── petri-net-theory-agent.md
├── petri-net-theory-agent.toml
├── srs-agent.md
├── srs-agent.toml
├── type-theory-agent.md
├── type-theory-agent.toml
├── debugger-agent.md
├── debugger-agent.toml
└── devAgent/                          (gitignored, untouched)
```

### 3.4 Frontmatter conventions per format

**Claude Code (`<name>.md`):** YAML frontmatter with required `name`, `description`. Optional `tools`, `model`, `skills` (declares paired skills to auto-load). Body is the system prompt.

**Codex CLI (`<name>.toml`):** TOML with required `name`, `description`, `developer_instructions`. The generator inherits parent settings. Claude skill dependencies are preserved through explicit loading instructions; no `skills.config` override is emitted. See [the current installation contract](../../../doc/requirements/installation-v1.md).

**Cross-format invariants** (enforced by an eval check):

- `name` field is identical across the `.md` and `.toml` for the same agent.
- `description` field is identical across both.
- Both files exist for every shipped agent.

### 3.5 Source-of-truth strategy

Markdown is canonical. `scripts/generate-codex-agents.py` reads each `<name>.md`, extracts frontmatter + body, and emits `<name>.toml`. Body becomes `developer_instructions` as a TOML multi-line string. The generator runs as a contributor step before committing generated files and is tested by `tests/test_generate_codex_agents.py`.

Hand-editing the TOML is unsupported. Edit the Markdown source and re-run the generator; the eval check rejects divergence.

### 3.6 Installer

`scripts/install-agents.py` (Python 3 stdlib, reuses `template/scripts/find_project_root.py`):

- Detects installed hosts using the same marker walk as `find_project_root.py` plus per-host probes.
- For each detected host with a file-based agent slot, copies the matching file:
  - **Claude Code** → `~/.claude/agents/<name>.md` (user) or `<scope>/.claude/agents/<name>.md` (project)
  - **Codex CLI** → `~/.codex/agents/<name>.toml` (user) or `<scope>/.codex/agents/<name>.toml` (project)
- **Cursor / Windsurf / Goose:** skip with an informational message — no file-based agent slot exists on these hosts as of 2026-06.
- Flags: `--agents <name>...` (subset), `-a <host>` (explicit host), `-g` (user scope), `--dry-run` (preview), `--update` (replace unmodified tracked files), `--force` (back up and replace conflicts). `-y` is a compatibility no-op. Full current semantics are in [the installation contract](../../../doc/requirements/installation-v1.md).
- Default behaviour refuses to overwrite existing files.

Distribution is per-host. There is no `npx skills`-style cross-host installer for agents; the `vercel-labs/skills` CLI only handles skills.

### 3.7 Plugin marketplace

`.claude-plugin/marketplace.json` gains an `agents:` array under `plugins[0]`:

```json
"agents": [
  "./agents/create-tutorial-agent.md",
  "./agents/improve-prompt-agent.md",
  "./agents/formal-methods-agent.md",
  "./agents/petri-net-theory-agent.md",
  "./agents/srs-agent.md",
  "./agents/type-theory-agent.md",
  "./agents/debugger-agent.md"
]
```

This ships Markdown agents to Claude Code via `/plugin install dev-skills@dev-skills`. Codex users use `scripts/install-agents.py` since the marketplace is Claude-Code-specific.

### 3.8 Documentation surface

**New files:**

- `docs/agents-guide.md` — author guide for agents (naming rule, frontmatter conventions per format, generator workflow, when to write an agent vs. a skill-only, banned constructs). Mirrors `docs/authoring-guide.md` in shape.
- `docs/agents-portability-checklist.md` — pre-PR checklist for agent additions. Mirrors `docs/portability-checklist.md`.
- `agents/README.md` — short overview, naming rule, link to `docs/agents-guide.md`.

**Updates:**

- `README.md` — new "Agents in this repository" section after the skills table. New rows in the skills table for `improve-prompt`, `formal-methods`, `debugger`, `srs`, `type-theory`, `petri-net-theory`.
- `docs/install.md` — new "Installing agents" subsection covering plugin route and `scripts/install-agents.py`. Explicit note about Cursor/Windsurf/Goose lack of support.
- `evals/run.py` — two new checks (agent-skill name pairing; agent format parity).

**Explicitly NOT updated:**

- `CLAUDE.md` — gitignored on this repo (`.gitignore` line 10). Editing it would not persist to the repo and would mislead future contributors.

## 4. Per-skill changes in detail

### 4.1 `create-tutorial`

Already done: spec-compliant frontmatter, pushy description, Pattern-2 config plumbing, registered in README + marketplace.

Still to do:

- Strip `$ARGUMENTS` from `SKILL.md:8`. Replace with an `## Inputs` section that documents the expected topic argument portably.
- Add explicit `## When to use` and `## When not to use` body sections (description carries the load, but the template requires headings).
- Add `## Examples` with at least two worked cases: typical (write a tutorial for an existing component) and edge (write a tutorial for a component that doesn't have code yet — infer from spec).
- Add `## Troubleshooting` covering the top three failure modes: missing `tutorials_dir`, topic too narrow / too broad, overwriting an existing file unintentionally.
- Add `agents/create-tutorial-agent.md` + `.toml`. Agent body is a thin wrapper that auto-loads the skill via `skills:` frontmatter.
- Add `evals/fixtures/create-tutorial/prompts.json` with five canonical trigger phrases from the description.

### 4.2 `improve-prompt`

Untouched on this branch. Full Layer A work needed:

- Relocate `evidence-appendix.md` from skill root to `references/evidence-appendix.md`. Update any internal references.
- Update the cross-reference at the bottom of `SKILL.md` from `.claude/agents/prompt-engineer.md` to `agents/improve-prompt-agent.md`.
- Promote the existing three Self-tests into a formal `## Examples` section, then also seed them into `evals/fixtures/improve-prompt/prompts.json`.
- Add a `## Troubleshooting` section covering: prompt looks too long (purpose class likely wrong); user reports no CoT triggered (check `math_symbolic` trigger column); few-shot exemplars look too uniform (check `[Order-flips]` / `[Format-flips]` rule).
- Tighten the description's "When NOT to use" coverage: explicit pointer at `superpowers:brainstorming` and `superpowers:writing-plans` for prompts whose real intent is a plan or brainstorm.
- Rename `agents/prompt-engineer.md` → `agents/improve-prompt-agent.md`. Update internal `name:` field. Generate `.toml` sibling.
- Update `improve-prompt-agent.md` body's banned-constructs list to match the latest SKILL.md if any drift exists.
- Register skill in `README.md` skills table.
- Register skill in `.claude-plugin/marketplace.json` plugins list.

No configuration changes — the skill is explicitly stateless and reads no project files.

### 4.3 `formal-methods` (renamed from `formal-methods-expert`)

- Rename folder: `skills/formal-methods-expert/` → `skills/formal-methods/`.
- Update `SKILL.md` frontmatter `name:` from `formal-methods-expert` to `formal-methods`.
- Tighten description to pushy phrasing: "Use whenever the user asks about SAT/SMT/CLP/CP, constraint satisfaction, theorem proving, temporal logic, TLA+, model checking, decidability, or formal verification — even if phrased casually ('is this provable?', 'will this terminate?'). Prefer this over generic CS advice for formal-method questions. Do not use for software testing strategy, type-system soundness (use `type-theory`), Petri-net-specific encodings (use `petri-net-theory`), reactive-system clock calculus (use `srs`), or trace/debug protocols (use `debugger`)."
- Relabel "Applicability signals" → `## When to use`; "Anti-signals" → `## When not to use`.
- Add new sections: `## Inputs`, `## Examples` (≥2: theory query + design-review query), `## Troubleshooting`.
- Tighten cross-references in body to use the renamed peer skills.
- Rename agent: `agents/formal-methods-expert.md` → `agents/formal-methods-agent.md`. Update internal `name:`. Generate `.toml` sibling.
- Update body cross-references to the renamed agent.
- Register in `README.md` skills table.
- Register in `.claude-plugin/marketplace.json` plugins list.
- Add `evals/fixtures/formal-methods/prompts.json` with canonical trigger phrases.

### 4.4 `petri-net-theory` (no rename)

- Add `## When to use`, `## When not to use`, `## Inputs`, `## Examples` (≥2), `## Troubleshooting` sections to `SKILL.md`. Preserve existing intake protocol and reference routing.
- Tighten description to pushy phrasing if needed; cross-reference `formal-methods`, `srs`, `type-theory`, `debugger`.
- Rename agent: `agents/petri-net-expert.md` → `agents/petri-net-theory-agent.md`. Update internal `name:`. Generate `.toml` sibling.
- Register in `README.md` skills table.
- Register in `.claude-plugin/marketplace.json` plugins list.
- Add `evals/fixtures/petri-net-theory/prompts.json`.

### 4.5 `srs` (renamed from `srs-expert`)

- Rename folder: `skills/srs-expert/` → `skills/srs/`.
- Update `SKILL.md` frontmatter `name:` to `srs`.
- Add `## When to use`, `## When not to use`, `## Inputs`, `## Examples` (≥2), `## Troubleshooting`.
- Tighten description; cross-reference `formal-methods`, `petri-net-theory`, `type-theory`, `debugger`.
- Rename agent: `agents/srs-expert.md` → `agents/srs-agent.md`. Update internal `name:`. Generate `.toml` sibling.
- Register in `README.md` skills table.
- Register in `.claude-plugin/marketplace.json` plugins list.
- Add `evals/fixtures/srs/prompts.json`.

### 4.6 `type-theory` (renamed from `type-theory-expert`)

- Rename folder: `skills/type-theory-expert/` → `skills/type-theory/`.
- Update `SKILL.md` frontmatter `name:` to `type-theory`.
- Add `## When to use`, `## When not to use`, `## Inputs`, `## Examples` (≥2), `## Troubleshooting`.
- Tighten description; cross-reference `formal-methods`, `petri-net-theory`, `srs`, `debugger`.
- Rename agent: `agents/type-theory-expert.md` → `agents/type-theory-agent.md`. Update internal `name:`. Generate `.toml` sibling.
- Register in `README.md` skills table.
- Register in `.claude-plugin/marketplace.json` plugins list.
- Add `evals/fixtures/type-theory/prompts.json`.

### 4.7 `debugger` (renamed from `debugger-expert`)

- Rename folder: `skills/debugger-expert/` → `skills/debugger/`.
- Update `SKILL.md` frontmatter `name:` to `debugger`.
- Add `## When to use`, `## When not to use`, `## Inputs`, `## Examples` (≥2), `## Troubleshooting`.
- Tighten description; cross-reference `formal-methods`, `petri-net-theory`, `srs`, `type-theory`.
- Rename agent: `agents/debugger-expert.md` → `agents/debugger-agent.md`. Update internal `name:`. Generate `.toml` sibling.
- Register in `README.md` skills table.
- Register in `.claude-plugin/marketplace.json` plugins list.
- Add `evals/fixtures/debugger/prompts.json`.

## 5. PR plan

### 5.1 PR 1 — scaffolding, naming, agents-layer infrastructure

Largest PR, mostly mechanical. Reviewable as one unit because most changes are renames and file moves.

**Renames:**

- `skills/formal-methods-expert/` → `skills/formal-methods/`
- `skills/debugger-expert/` → `skills/debugger/`
- `skills/srs-expert/` → `skills/srs/`
- `skills/type-theory-expert/` → `skills/type-theory/`
- `agents/prompt-engineer.md` → `agents/improve-prompt-agent.md`
- `agents/formal-methods-expert.md` → `agents/formal-methods-agent.md`
- `agents/petri-net-expert.md` → `agents/petri-net-theory-agent.md`
- `agents/srs-expert.md` → `agents/srs-agent.md`
- `agents/type-theory-expert.md` → `agents/type-theory-agent.md`
- `agents/debugger-expert.md` → `agents/debugger-agent.md`

For each renamed skill, update its `SKILL.md` `name:` field. For each renamed agent, update its `name:` field and any internal text that names the old identifier.

**New scripts:**

- `scripts/generate-codex-agents.py` — Markdown → TOML conversion. Stdlib only.
- `scripts/install-agents.py` — host detection + per-host install. Stdlib only.
- `tests/test_generate_codex_agents.py` — round-trip tests + invariant checks.
- `tests/test_install_agents.py` — mocked-host-detection tests.

**New TOML files:**

- `agents/<each-agent>.toml` — generated from the renamed `.md` files via `scripts/generate-codex-agents.py`.

**New docs:**

- `docs/agents-guide.md`
- `docs/agents-portability-checklist.md`
- `agents/README.md`

**Doc updates:**

- `README.md`: new "Agents in this repository" section; new rows in skills table for the six unregistered (post-rename) skills.
- `docs/install.md`: new "Installing agents" subsection.

**marketplace.json:**

- Update skill paths for renamed skills.
- Add new skill paths for unregistered ones.
- Add `agents:` array.

**Eval extensions:**

- `evals/run.py` adds two checks: agent-skill name pairing and format parity.
- `tests/test_evals_agent_checks.py` covers them.

**Surgical content fix in PR 1:**

- `create-tutorial`: strip `$ARGUMENTS` from `SKILL.md:8`. This is the only content fix needed before content PR; everything else waits for PR 2. The reason is that `$ARGUMENTS` is the last remaining portability blocker on create-tutorial and is one line — bundling it into PR 1 means PR 2 is purely content rather than mixed-content-plus-portability-fix.

PR 1 acceptance criteria:

- All renames clean.
- All `.toml` agent files generated and parity-valid.
- `evals/run.py` passes including new checks.
- `python3 -m unittest discover tests/` passes.
- README + marketplace.json reflect all 13 skills.
- `docs/agents-guide.md` complete and links to install.md.

### 5.2 PR 2 — content conformance for seven skills

Content-only. No renames, no new infrastructure. Done sequentially by skill so reviewer reads one skill at a time.

For each of the seven skills (`create-tutorial`, `improve-prompt`, `formal-methods`, `debugger`, `srs`, `type-theory`, `petri-net-theory`):

- Add the template sections it's missing.
- Add `evals/fixtures/<skill>/prompts.json`.
- Tighten description to pushy phrasing if not already done.
- For skills with a paired agent file body that names the skill, verify the body still reads correctly post-rename.

For `create-tutorial` specifically, also:

- Add paired `agents/create-tutorial-agent.md` + `.toml`.
- Update marketplace.json `agents:` array to include it.
- Update `agents/README.md` and `README.md` agents section.

PR 2 acceptance criteria:

- Every conforming skill has all seven template sections.
- Every skill has at least two worked Examples.
- Every skill has a Troubleshooting section.
- Every skill has `evals/fixtures/<name>/prompts.json` with at least three canonical trigger prompts.
- `evals/run.py` passes.
- `python3 -m unittest discover tests/` passes.

### 5.3 No PR 3

Layer C in the original plan (port four peer skills) is already done as bulk imports on this branch. The renames and conformance work for those skills land in PR 1 and PR 2 respectively.

## 6. Open items and decisions deferred

These do not block the PRs but should be tracked.

- **Skill name terseness.** `srs` and `debugger` are very terse. `srs` is opaque outside the formal-methods community; `debugger` may collide with IDE/VS-Code "debugger" terminology in user searches. Both are accepted in this design as the cost of the `-expert` drop. Revisit if trigger-rate testing later shows under-triggering.
- **`agents/devAgent/`.** Gitignored; not migrated to the new convention. Future work item.
- **`sanity-design-analysis` registration.** Out of scope here; should land in a separate PR.
- **`evals/run.py` trigger-rate testing.** This spec creates `prompts.json` fixtures but does not extend `evals/run.py` to actually run them against host agents. Follow-up work.
- **Agent test coverage in `tests/`.** PR 1 ships unit tests for the new scripts and eval checks. Agent-content tests (e.g. "every banned construct in `improve-prompt-agent.md` body is also listed in the SKILL.md") are not in this spec; revisit if drift becomes a problem.
- **Cursor / Windsurf / Goose agent support.** None has a file-based agent slot today. If any add one in the future, extend `scripts/install-agents.py` accordingly.

## 7. Risks

- **Rename churn.** Folder renames touch `name:` fields, cross-references, and any external docs that link to the skill path. Mitigation: PR 1 is mostly mechanical and reviewable as a single diff. The installer and generator scripts are isolated additions.
- **Generator drift.** If the Markdown → TOML generator becomes a real translation problem (escaping, fenced-code edge cases), the "Markdown is canonical" rule may need revisiting. Mitigation: the generator is small and well-tested; the eval parity check catches divergence between formats.
- **Codex CLI subagent format changes.** The TOML schema is from 2026 docs; OpenAI may revise it. Mitigation: regenerate `.toml` files from canonical Markdown.
- **CLAUDE.md gitignored.** Edits to `CLAUDE.md` will not persist. Mitigation: explicitly do not update `CLAUDE.md` in either PR. Use `README.md` and `docs/` as canonical surfaces.

## 8. Validation

After both PRs land:

- `python3 evals/run.py` returns OK with all 13 skills.
- `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null` exits 0.
- `python3 -m unittest discover tests/` passes.
- `python3 scripts/install-agents.py --dry-run` enumerates the expected target paths for at least Claude Code and Codex CLI.
- For each skill, `grep -c '^## ' skills/<name>/SKILL.md` returns at least 7 (the template's canonical sections).
- For each skill, `ls evals/fixtures/<name>/prompts.json` succeeds.
- The README skills table has 13 rows (or 12, excluding `sanity-design-analysis` per scope decision).

## 9. References

- `docs/authoring-guide.md` — skill authoring rules (5-layer config resolution, shared-conventions integration).
- `docs/install.md` — install matrix, shared conventions, env-var overrides.
- `docs/portability-checklist.md` — pre-PR checklist for skills.
- `template/SKILL.md` — canonical skill structure.
- `template/scripts/read_shared_conventions.py` — canonical reader (drift-checked).
- `evals/run.py` — structural validation runner.
- `agents/*.md` (current) — Claude Code subagent definitions to be renamed.
- AIQURIS upstream `.claude/skills/` — original source of bulk-ported peer skills (no re-port needed; PR 2 conformance pass operates on what's already in `skills/`).
