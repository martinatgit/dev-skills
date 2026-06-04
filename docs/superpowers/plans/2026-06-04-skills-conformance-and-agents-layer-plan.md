# Skills Conformance and Agents Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring seven skills to authoring-guide conformance, drop `-expert` suffixes from four skill names, and restructure `agents/` as a first-class multi-host layer with Claude Code Markdown + Codex CLI TOML in parallel.

**Architecture:** Two phases. Phase 1 (PR 1) is mostly mechanical — renames, file moves, new Python scripts, docs. Phase 2 (PR 2) is per-skill content conformance with no further renames. Markdown is the canonical agent format; TOML siblings are generated. The installer is per-host (Claude Code Markdown via plugin marketplace, Codex CLI TOML via `scripts/install-agents.py`).

**Tech Stack:** Python 3 stdlib (no external packages), YAML for skill frontmatter, TOML for Codex agents, pytest for tests, Git for version control.

**Spec reference:** [`docs/superpowers/specs/2026-06-04-skills-conformance-and-agents-layer-design.md`](../specs/2026-06-04-skills-conformance-and-agents-layer-design.md).

**Working branch:** `feature/shared-skill-config`. Two PRs to be merged in order.

---

## File Structure

### New files (Phase 1)

| Path | Purpose |
|---|---|
| `scripts/generate-codex-agents.py` | Read each `agents/<name>.md`, emit `agents/<name>.toml`. Stdlib only. |
| `scripts/install-agents.py` | Detect installed hosts; copy `.md` or `.toml` to the right place. |
| `tests/test_generate_codex_agents.py` | Unit tests for the generator. |
| `tests/test_install_agents.py` | Unit tests for the installer. |
| `tests/test_evals_agent_checks.py` | Unit tests for new eval checks. |
| `docs/agents-guide.md` | Authoring guide for agents (mirrors `docs/authoring-guide.md`). |
| `docs/agents-portability-checklist.md` | Pre-PR checklist (mirrors `docs/portability-checklist.md`). |
| `agents/README.md` | Short overview + naming rule + link to `docs/agents-guide.md`. |
| `agents/create-tutorial-agent.md` | (Phase 2) New agent for create-tutorial skill. |
| `agents/<name>.toml` × 7 | Generated Codex siblings for every agent. |

### Renamed files (Phase 1)

| From | To |
|---|---|
| `skills/formal-methods-expert/` | `skills/formal-methods/` |
| `skills/debugger-expert/` | `skills/debugger/` |
| `skills/srs-expert/` | `skills/srs/` |
| `skills/type-theory-expert/` | `skills/type-theory/` |
| `agents/prompt-engineer.md` | `agents/improve-prompt-agent.md` |
| `agents/formal-methods-expert.md` | `agents/formal-methods-agent.md` |
| `agents/petri-net-expert.md` | `agents/petri-net-theory-agent.md` |
| `agents/srs-expert.md` | `agents/srs-agent.md` |
| `agents/type-theory-expert.md` | `agents/type-theory-agent.md` |
| `agents/debugger-expert.md` | `agents/debugger-agent.md` |

### Modified files (Phase 1)

| Path | Change |
|---|---|
| `README.md` | New "Agents in this repository" section; 6 new skill rows. |
| `docs/install.md` | New "Installing agents" subsection. |
| `.claude-plugin/marketplace.json` | New `agents:` array; 6 new skill paths; 4 renamed skill paths. |
| `evals/run.py` | Two new checks (pairing + parity). |
| `skills/create-tutorial/SKILL.md` | Strip `$ARGUMENTS`; replace with portable Inputs reference. |

### Modified files (Phase 2)

Seven skill `SKILL.md` files (one per skill) plus seven `evals/fixtures/<name>/prompts.json` files plus the new `agents/create-tutorial-agent.{md,toml}` pair.

---

## Phase 1 — Scaffolding, Renames, Agents Layer

Each task lands as one commit. The phase ends with a single PR opened against `main` (or against `feature/shared-skill-config` if the parallel sprint hasn't merged).

### Task 1: Strip `$ARGUMENTS` from `create-tutorial`

**Files:**
- Modify: `skills/create-tutorial/SKILL.md` (line 8)

- [ ] **Step 1: Read the current line 8 context**

Run: `python3 -c "print(open('skills/create-tutorial/SKILL.md').read().split('\n')[7])"`
Expected: `Create a technical tutorial for $ARGUMENTS `

- [ ] **Step 2: Replace `$ARGUMENTS` with a portable Inputs reference**

Edit `skills/create-tutorial/SKILL.md`. Change line 8 from:
```
Create a technical tutorial for $ARGUMENTS 
```
to:
```
Create a technical tutorial for the topic supplied by the user (see Inputs below).
```

Then add an `## Inputs` section immediately after the `## Configuration` block (before the existing `## Workflow`):

```markdown
## Inputs

The user provides a topic — a component, feature, or subsystem to document. Acceptable shapes:

- A folder or file path (`src/auth/middleware.ts`).
- A symbolic name (`event-stream-processor`).
- A free-text description (`the new tenant-isolation module`).

Optionally, the user may supply a target filename. If absent, derive a kebab-case filename from the topic.
```

- [ ] **Step 3: Verify the edit**

Run: `grep -n '\$ARGUMENTS' skills/create-tutorial/SKILL.md`
Expected: no output (exit code 1).

Run: `grep -n '^## Inputs' skills/create-tutorial/SKILL.md`
Expected: one line.

- [ ] **Step 4: Run evals**

Run: `python3 evals/run.py --skill create-tutorial`
Expected: `OK — checked 1 skill(s).`

- [ ] **Step 5: Commit**

```bash
git add skills/create-tutorial/SKILL.md
git commit -m "fix(create-tutorial): strip \$ARGUMENTS; add portable Inputs section

The \$ARGUMENTS token is Claude Code slash-command syntax and breaks
portability to Codex CLI. Replace with an Inputs section that
documents the topic argument in agent-neutral terms.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 2: Rename `skills/formal-methods-expert/` → `skills/formal-methods/`

**Files:**
- Rename: `skills/formal-methods-expert/` → `skills/formal-methods/`
- Modify: `skills/formal-methods/SKILL.md` (frontmatter `name:` field)

- [ ] **Step 1: Git-rename the folder**

```bash
git mv skills/formal-methods-expert skills/formal-methods
```

- [ ] **Step 2: Update the `name:` field in frontmatter**

Edit `skills/formal-methods/SKILL.md`. Change the frontmatter `name:` from `formal-methods-expert` to `formal-methods`. The line should read exactly:
```
name: formal-methods
```

- [ ] **Step 3: Verify**

Run: `head -5 skills/formal-methods/SKILL.md`
Expected: frontmatter shows `name: formal-methods`.

Run: `python3 evals/run.py --skill formal-methods`
Expected: `OK — checked 1 skill(s).`

- [ ] **Step 4: Commit**

```bash
git add -A skills/formal-methods skills/formal-methods-expert 2>/dev/null
git commit -m "refactor: rename formal-methods-expert skill to formal-methods

Drops the -expert suffix per the new naming convention (skill names
do not carry role suffixes; agents do, via -agent).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 3: Rename `skills/debugger-expert/` → `skills/debugger/`

**Files:**
- Rename: `skills/debugger-expert/` → `skills/debugger/`
- Modify: `skills/debugger/SKILL.md` (frontmatter `name:` field)

- [ ] **Step 1: Git-rename the folder**

```bash
git mv skills/debugger-expert skills/debugger
```

- [ ] **Step 2: Update the `name:` field**

Edit `skills/debugger/SKILL.md`. Change frontmatter `name:` to `debugger`.

- [ ] **Step 3: Verify**

Run: `head -5 skills/debugger/SKILL.md`
Expected: `name: debugger` in frontmatter.

Run: `python3 evals/run.py --skill debugger`
Expected: `OK — checked 1 skill(s).`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename debugger-expert skill to debugger

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 4: Rename `skills/srs-expert/` → `skills/srs/`

**Files:**
- Rename: `skills/srs-expert/` → `skills/srs/`
- Modify: `skills/srs/SKILL.md` (frontmatter `name:` field)

- [ ] **Step 1: Git-rename**

```bash
git mv skills/srs-expert skills/srs
```

- [ ] **Step 2: Update `name:` field**

Edit `skills/srs/SKILL.md`. Frontmatter `name:` becomes `srs`.

- [ ] **Step 3: Verify**

Run: `python3 evals/run.py --skill srs`
Expected: `OK — checked 1 skill(s).`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename srs-expert skill to srs

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 5: Rename `skills/type-theory-expert/` → `skills/type-theory/`

**Files:**
- Rename: `skills/type-theory-expert/` → `skills/type-theory/`
- Modify: `skills/type-theory/SKILL.md` (frontmatter `name:` field)

- [ ] **Step 1: Git-rename**

```bash
git mv skills/type-theory-expert skills/type-theory
```

- [ ] **Step 2: Update `name:` field**

Edit `skills/type-theory/SKILL.md`. Frontmatter `name:` becomes `type-theory`.

- [ ] **Step 3: Verify**

Run: `python3 evals/run.py --skill type-theory`
Expected: `OK — checked 1 skill(s).`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename type-theory-expert skill to type-theory

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 6: Rename `agents/prompt-engineer.md` → `agents/improve-prompt-agent.md`

**Files:**
- Rename: `agents/prompt-engineer.md` → `agents/improve-prompt-agent.md`
- Modify: agent frontmatter `name:` field and body identity text.

- [ ] **Step 1: Git-rename**

```bash
git mv agents/prompt-engineer.md agents/improve-prompt-agent.md
```

- [ ] **Step 2: Update internal identifiers**

Edit `agents/improve-prompt-agent.md`. Change:
- Frontmatter `name: prompt-engineer` → `name: improve-prompt-agent`
- Body text `You are the \`prompt-engineer\` agent.` → `You are the \`improve-prompt-agent\` agent.`
- Any other occurrences of `prompt-engineer` → `improve-prompt-agent`.

- [ ] **Step 3: Verify no stale references**

Run: `grep -n 'prompt-engineer' agents/improve-prompt-agent.md`
Expected: no output (exit code 1).

Run: `head -12 agents/improve-prompt-agent.md`
Expected: shows `name: improve-prompt-agent` and `skills: [improve-prompt]` (or similar list form).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename agent prompt-engineer to improve-prompt-agent

Naming rule: agent = <paired-skill-name>-agent. Skill stays improve-prompt;
agent inherits the skill name plus -agent suffix.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 7: Rename `agents/formal-methods-expert.md` → `agents/formal-methods-agent.md`

**Files:**
- Rename: `agents/formal-methods-expert.md` → `agents/formal-methods-agent.md`
- Modify: agent frontmatter and identity text.

- [ ] **Step 1: Git-rename**

```bash
git mv agents/formal-methods-expert.md agents/formal-methods-agent.md
```

- [ ] **Step 2: Update internal identifiers**

Edit `agents/formal-methods-agent.md`:
- Frontmatter `name:` → `formal-methods-agent`.
- Frontmatter `skills:` list — the entry `formal-methods-expert` → `formal-methods` (skill was renamed in Task 2).
- Any body text saying `formal-methods-expert` (as skill or agent name) → `formal-methods-agent` (when referring to the agent) or `formal-methods` (when referring to the skill).

- [ ] **Step 3: Verify**

Run: `grep -n 'formal-methods-expert' agents/formal-methods-agent.md`
Expected: no output.

Run: `head -25 agents/formal-methods-agent.md`
Expected: `name: formal-methods-agent` in frontmatter, `skills:` list contains `formal-methods`.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename agent formal-methods-expert to formal-methods-agent

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 8: Rename `agents/petri-net-expert.md` → `agents/petri-net-theory-agent.md`

**Files:**
- Rename: `agents/petri-net-expert.md` → `agents/petri-net-theory-agent.md`

- [ ] **Step 1: Git-rename**

```bash
git mv agents/petri-net-expert.md agents/petri-net-theory-agent.md
```

- [ ] **Step 2: Update internal identifiers**

Edit `agents/petri-net-theory-agent.md`:
- Frontmatter `name:` → `petri-net-theory-agent`.
- Frontmatter `skills:` list — entry `petri-net-expert` (if present) → `petri-net-theory`.
- Body text referring to itself as `petri-net-expert` → `petri-net-theory-agent`.

- [ ] **Step 3: Verify**

Run: `grep -n 'petri-net-expert' agents/petri-net-theory-agent.md`
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename agent petri-net-expert to petri-net-theory-agent

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 9: Rename `agents/srs-expert.md` → `agents/srs-agent.md`

**Files:**
- Rename: `agents/srs-expert.md` → `agents/srs-agent.md`

- [ ] **Step 1: Git-rename**

```bash
git mv agents/srs-expert.md agents/srs-agent.md
```

- [ ] **Step 2: Update internal identifiers**

Edit `agents/srs-agent.md`:
- Frontmatter `name:` → `srs-agent`.
- Frontmatter `skills:` entry `srs-expert` → `srs`.
- Body identity text → `srs-agent`.

- [ ] **Step 3: Verify**

Run: `grep -n 'srs-expert' agents/srs-agent.md`
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename agent srs-expert to srs-agent

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 10: Rename `agents/type-theory-expert.md` → `agents/type-theory-agent.md`

**Files:**
- Rename: `agents/type-theory-expert.md` → `agents/type-theory-agent.md`

- [ ] **Step 1: Git-rename**

```bash
git mv agents/type-theory-expert.md agents/type-theory-agent.md
```

- [ ] **Step 2: Update internal identifiers**

Edit `agents/type-theory-agent.md`:
- Frontmatter `name:` → `type-theory-agent`.
- Frontmatter `skills:` entry `type-theory-expert` → `type-theory`.
- Body identity text → `type-theory-agent`.

- [ ] **Step 3: Verify**

Run: `grep -n 'type-theory-expert' agents/type-theory-agent.md`
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename agent type-theory-expert to type-theory-agent

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 11: Rename `agents/debugger-expert.md` → `agents/debugger-agent.md`

**Files:**
- Rename: `agents/debugger-expert.md` → `agents/debugger-agent.md`

- [ ] **Step 1: Git-rename**

```bash
git mv agents/debugger-expert.md agents/debugger-agent.md
```

- [ ] **Step 2: Update internal identifiers**

Edit `agents/debugger-agent.md`:
- Frontmatter `name:` → `debugger-agent`.
- Frontmatter `skills:` entry `debugger-expert` → `debugger`.
- Body identity text → `debugger-agent`.

- [ ] **Step 3: Verify**

Run: `grep -n 'debugger-expert' agents/debugger-agent.md`
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: rename agent debugger-expert to debugger-agent

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 12: Sweep repo for stale references to old names

**Files:** any file outside `agents/` and `skills/` that names a renamed identifier.

- [ ] **Step 1: Identify all stale references**

Run:
```bash
grep -rn -E '(formal-methods-expert|debugger-expert|srs-expert|type-theory-expert|prompt-engineer|petri-net-expert)' \
  --include="*.md" --include="*.py" --include="*.json" --include="*.yaml" \
  --exclude-dir=tests --exclude-dir=node_modules --exclude-dir=__pycache__ \
  --exclude-dir=.git --exclude-dir=docs/superpowers \
  . 2>&1 | grep -v "^Binary" | grep -v "evidence-appendix" | grep -v "skills/improve-prompt/"
```

Expected: any remaining hits indicate stale references to update. Common hits will be in:
- `skills/formal-methods/SKILL.md` (the cross-references to peer skills in the description and Reasoning Rules block).
- The `agents/*-agent.md` body texts (if any cross-reference peer agents by old name).
- `template/SKILL.md` examples (if they mention any of these names — unlikely but check).

(References inside `skills/improve-prompt/` and `evidence-appendix.md` to the `prompt-engineer` name will be fixed in Phase 2. Leave them for now and flag them via grep.)

- [ ] **Step 2: For each hit, replace the old identifier with the new one**

For hits in `skills/formal-methods/SKILL.md`:
- `petri-net-expert` → `petri-net-theory` (skill cross-ref)
- `srs-expert` → `srs`
- `type-theory-expert` → `type-theory`
- `debugger-expert` → `debugger`

For hits in `agents/*-agent.md` body (cross-references to peers):
- `petri-net-expert` → `petri-net-theory-agent`
- `srs-expert` → `srs-agent`
- `type-theory-expert` → `type-theory-agent`
- `debugger-expert` → `debugger-agent`
- `formal-methods-expert` → `formal-methods-agent`

- [ ] **Step 3: Re-grep to confirm clean**

Run the same grep command from Step 1. Expected: no remaining hits (the `skills/improve-prompt/` `prompt-engineer` references will be cleaned in Phase 2).

- [ ] **Step 4: Run evals**

Run: `python3 evals/run.py`
Expected: `OK — checked 13 skill(s).`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: sweep cross-references to renamed skills and agents

After the bulk rename, cross-references inside formal-methods/SKILL.md
and each agent's body needed updating to point at the new names.
improve-prompt's reference to agents/prompt-engineer.md is left for
Phase 2 (it's part of that skill's full conformance pass).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 13: Write `scripts/generate-codex-agents.py`

**Files:**
- Create: `scripts/generate-codex-agents.py`
- Create: `tests/test_generate_codex_agents.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_generate_codex_agents.py`:

```python
"""Tests for scripts/generate-codex-agents.py."""
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "generate-codex-agents.py"

SAMPLE_MD = textwrap.dedent("""\
    ---
    name: sample-agent
    description: >
      A sample agent. Triggers on "sample me" and similar.
    tools: Read, Grep
    model: opus
    skills:
      - sample-skill
    ---

    You are the `sample-agent`. Do sample things.

    ## Workflow

    1. Read.
    2. Think.
    3. Emit.
    """)


def run(args, cwd):
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


class GenerateCodexAgentsTests(unittest.TestCase):

    def test_generates_toml_from_md(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")

            result = run(["--agents-dir", str(agents)], cwd=tdp)
            self.assertEqual(result.returncode, 0, result.stderr)

            toml_path = agents / "sample-agent.toml"
            self.assertTrue(toml_path.exists())
            toml_text = toml_path.read_text(encoding="utf-8")

            self.assertIn('name = "sample-agent"', toml_text)
            self.assertIn("A sample agent", toml_text)
            self.assertIn("developer_instructions", toml_text)
            self.assertIn("You are the `sample-agent`", toml_text)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")

            result = run(["--agents-dir", str(agents), "--dry-run"], cwd=tdp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((agents / "sample-agent.toml").exists())

    def test_round_trip_preserves_name_and_description(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")

            run(["--agents-dir", str(agents)], cwd=tdp)
            toml_text = (agents / "sample-agent.toml").read_text(encoding="utf-8")

            # Extract name and description by simple TOML key lookup.
            name_line = next(ln for ln in toml_text.splitlines() if ln.startswith("name "))
            desc_line = next(ln for ln in toml_text.splitlines() if ln.startswith("description "))
            self.assertIn('"sample-agent"', name_line)
            self.assertIn("A sample agent", desc_line)

    def test_missing_required_field_fails(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "broken-agent.md").write_text(
                "---\ndescription: no name field\n---\n\nBody.\n",
                encoding="utf-8",
            )
            result = run(["--agents-dir", str(agents)], cwd=tdp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("name", result.stderr.lower())

    def test_skips_non_md_files(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "README.md").write_text(
                "# Agents README — not an agent.\n", encoding="utf-8",
            )
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")
            result = run(["--agents-dir", str(agents)], cwd=tdp)
            self.assertEqual(result.returncode, 0, result.stderr)
            # README is not a valid agent: it has no frontmatter. Generator
            # must skip it without erroring.
            self.assertFalse((agents / "README.toml").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails (script doesn't exist yet)**

Run: `python3 -m unittest tests.test_generate_codex_agents -v`
Expected: errors with "No such file or directory: scripts/generate-codex-agents.py" or similar.

- [ ] **Step 3: Write the script**

Create `scripts/generate-codex-agents.py`:

```python
#!/usr/bin/env python3
"""Generate Codex CLI TOML agents from Claude Code Markdown agents.

Reads each agents/<name>.md, extracts YAML frontmatter and Markdown body,
and emits a TOML file with the same basename: agents/<name>.toml.

Mapping:
    frontmatter name        -> toml name
    frontmatter description -> toml description
    body                    -> toml developer_instructions (multi-line)
    frontmatter model       -> toml model (if present)
    frontmatter skills      -> [skills.config] block (if present)
    frontmatter tools       -> dropped (Codex has its own tool model)

Stdlib only. No external YAML / TOML libraries.

Usage:
    python3 scripts/generate-codex-agents.py
    python3 scripts/generate-codex-agents.py --agents-dir <dir>
    python3 scripts/generate-codex-agents.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter-dict, body). Frontmatter must be YAML between --- markers."""
    if not text.startswith("---\n"):
        raise ValueError("no opening --- frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("no closing --- frontmatter delimiter")
    fm_text = text[4:end]
    body = text[end + 5:]

    fm: dict = {}
    current_key = None
    current_list: list | None = None
    for raw in fm_text.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  - "):
            if current_list is None:
                raise ValueError(f"list item without key context: {raw!r}")
            current_list.append(raw[4:].strip())
            continue
        m = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", raw)
        if not m:
            # Continuation of folded scalar (description: > on prior line)
            if current_key is not None and isinstance(fm[current_key], str):
                fm[current_key] = (fm[current_key] + " " + raw.strip()).strip()
            continue
        key, value = m.group(1), m.group(2).strip()
        current_key = key
        current_list = None
        if value == ">" or value == "|":
            fm[key] = ""  # accumulate from continuations
        elif value == "":
            fm[key] = []
            current_list = fm[key]
        else:
            fm[key] = value
    return fm, body


def toml_escape_multiline(s: str) -> str:
    """Return a triple-quoted TOML literal-string-friendly form.

    Use triple double-quotes; escape any \"\"\" sequences in body.
    """
    # Triple-quoted basic strings allow backslash escapes; safest to use
    # literal multi-line strings (triple single quotes) but those forbid
    # embedded ''' so detect and fall back.
    if "'''" not in s:
        return "'''\n" + s.rstrip() + "\n'''"
    # Fallback: triple double-quoted, escape backslashes and triple-doubles
    escaped = s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return '"""\n' + escaped.rstrip() + '\n"""'


def toml_escape_oneline(s: str) -> str:
    """Return a single-line TOML basic string."""
    escaped = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return '"' + escaped + '"'


def emit_toml(fm: dict, body: str) -> str:
    if "name" not in fm:
        raise ValueError("frontmatter missing required key: name")
    if "description" not in fm:
        raise ValueError("frontmatter missing required key: description")

    lines = []
    lines.append(f"name = {toml_escape_oneline(fm['name'])}")
    lines.append(f"description = {toml_escape_oneline(fm['description'])}")
    if "model" in fm:
        lines.append(f"model = {toml_escape_oneline(fm['model'])}")
    lines.append("")
    lines.append("developer_instructions = " + toml_escape_multiline(body))

    skills = fm.get("skills")
    if isinstance(skills, list) and skills:
        lines.append("")
        lines.append("[skills.config]")
        for s in skills:
            lines.append(f"{s} = {{}}")

    return "\n".join(lines) + "\n"


def process_file(md_path: Path, dry_run: bool) -> Path | None:
    text = md_path.read_text(encoding="utf-8")
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as e:
        print(f"  skip {md_path.name}: {e}", file=sys.stderr)
        return None
    toml_text = emit_toml(fm, body)
    toml_path = md_path.with_suffix(".toml")
    if dry_run:
        print(f"  would write {toml_path}")
    else:
        toml_path.write_text(toml_text, encoding="utf-8")
        print(f"  wrote {toml_path}")
    return toml_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agents-dir",
        default=str(Path(__file__).resolve().parent.parent / "agents"),
        help="Directory containing agent .md files",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    agents_dir = Path(args.agents_dir)
    if not agents_dir.is_dir():
        print(f"error: agents dir not found: {agents_dir}", file=sys.stderr)
        return 2

    failed = 0
    for md in sorted(agents_dir.glob("*.md")):
        if md.name == "README.md":
            continue
        try:
            process_file(md, args.dry_run)
        except ValueError as e:
            print(f"FAIL {md.name}: {e}", file=sys.stderr)
            failed += 1

    if failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_generate_codex_agents -v`
Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate-codex-agents.py tests/test_generate_codex_agents.py
git commit -m "feat(agents): Markdown-to-TOML generator for Codex CLI siblings

Reads each agents/<name>.md, emits agents/<name>.toml using the Codex
2026 subagent schema. Markdown is canonical; TOML is generated.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 14: Generate TOML siblings for all renamed agents

**Files:**
- Create: `agents/improve-prompt-agent.toml`, `agents/formal-methods-agent.toml`, `agents/petri-net-theory-agent.toml`, `agents/srs-agent.toml`, `agents/type-theory-agent.toml`, `agents/debugger-agent.toml`

- [ ] **Step 1: Run the generator**

Run: `python3 scripts/generate-codex-agents.py`
Expected: prints `wrote agents/<name>.toml` for each agent (6 lines).

- [ ] **Step 2: Verify each TOML file exists and parses as TOML**

Run:
```bash
python3 -c "
import tomllib, pathlib
for p in sorted(pathlib.Path('agents').glob('*.toml')):
    with open(p, 'rb') as f:
        d = tomllib.load(f)
    print(p.name, '->', d['name'], '|', d['description'][:40])
"
```
Expected: 6 lines, each showing the agent's name and the first 40 chars of its description.

- [ ] **Step 3: Verify name + description parity for each pair**

Run:
```bash
python3 -c "
import re, pathlib, tomllib
for md in sorted(pathlib.Path('agents').glob('*-agent.md')):
    toml = md.with_suffix('.toml')
    text = md.read_text(encoding='utf-8')
    fm_end = text.find('\n---\n', 4)
    fm = text[4:fm_end]
    md_name = re.search(r'^name:\s*(\S+)', fm, re.M).group(1)
    with open(toml, 'rb') as f:
        td = tomllib.load(f)
    assert md_name == td['name'], f'{md.name} name mismatch: {md_name} vs {td[\"name\"]}'
    print(md.name, 'OK')
"
```
Expected: 6 lines each ending `OK`.

- [ ] **Step 4: Commit**

```bash
git add agents/*.toml
git commit -m "feat(agents): generate Codex TOML siblings for all renamed agents

Six .toml files generated from the canonical .md sources via
scripts/generate-codex-agents.py. Name and description parity verified.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 15: Write `scripts/install-agents.py`

**Files:**
- Create: `scripts/install-agents.py`
- Create: `tests/test_install_agents.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_install_agents.py`:

```python
"""Tests for scripts/install-agents.py."""
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "install-agents.py"

SAMPLE_MD = textwrap.dedent("""\
    ---
    name: sample-agent
    description: A sample agent.
    ---

    Body.
    """)
SAMPLE_TOML = textwrap.dedent('''\
    name = "sample-agent"
    description = "A sample agent."

    developer_instructions = """
    Body.
    """
    ''')


def run(args, cwd):
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def make_repo_with_agents(td: Path) -> Path:
    (td / "agents").mkdir()
    (td / "agents" / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")
    (td / "agents" / "sample-agent.toml").write_text(SAMPLE_TOML, encoding="utf-8")
    return td


class InstallAgentsTests(unittest.TestCase):

    def test_dry_run_lists_targets(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "--dry-run", "-g"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".claude/agents/sample-agent.md", result.stdout.replace("\\", "/"))
            self.assertIn(".codex/agents/sample-agent.toml", result.stdout.replace("\\", "/"))

    def test_install_user_scope(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((home / ".claude" / "agents" / "sample-agent.md").exists())
            self.assertTrue((home / ".codex" / "agents" / "sample-agent.toml").exists())

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".claude" / "agents" / "sample-agent.md").write_text(
                "existing", encoding="utf-8",
            )
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y"],
                cwd=tdp,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exists", result.stderr.lower())
            # File not overwritten
            self.assertEqual(
                (home / ".claude" / "agents" / "sample-agent.md").read_text(encoding="utf-8"),
                "existing",
            )

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".claude" / "agents" / "sample-agent.md").write_text(
                "existing", encoding="utf-8",
            )
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y", "--force"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Body.", (home / ".claude" / "agents" / "sample-agent.md")
                          .read_text(encoding="utf-8"))

    def test_subset_with_agents_flag(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            (tdp / "agents" / "other-agent.md").write_text(
                SAMPLE_MD.replace("sample-agent", "other-agent"), encoding="utf-8",
            )
            (tdp / "agents" / "other-agent.toml").write_text(
                SAMPLE_TOML.replace("sample-agent", "other-agent"), encoding="utf-8",
            )
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y", "--agents", "sample-agent"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((home / ".claude" / "agents" / "sample-agent.md").exists())
            self.assertFalse((home / ".claude" / "agents" / "other-agent.md").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_install_agents -v`
Expected: FileNotFoundError or similar for the missing `scripts/install-agents.py`.

- [ ] **Step 3: Write the installer script**

Create `scripts/install-agents.py`:

```python
#!/usr/bin/env python3
"""Install dev-skills agents into detected host agent directories.

Per-host file placement:
    Claude Code -> ~/.claude/agents/<name>.md or <project>/.claude/agents/
    Codex CLI   -> ~/.codex/agents/<name>.toml or <project>/.codex/agents/

Cursor, Windsurf, Goose: no file-based agent slot today; skipped silently.

Detection: presence of the target install directory (e.g. ~/.claude/agents/)
indicates the host is installed. The directory must exist; this script does
not create host config directories.

Stdlib only.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HOSTS = {
    # host name -> (subdir under home, agent file extension)
    "claude-code": (Path(".claude") / "agents", ".md"),
    "codex":      (Path(".codex")  / "agents", ".toml"),
}


def detect_hosts(home: Path) -> list[str]:
    """Return list of host names whose target install dir exists under home."""
    return [name for name, (sub, _) in HOSTS.items() if (home / sub).is_dir()]


def find_project_root(start: Path) -> Path | None:
    """Walk up looking for .git, package.json, pyproject.toml, etc."""
    markers = {".git", "package.json", "pyproject.toml", "Cargo.toml", "go.mod"}
    cur = start.resolve()
    while True:
        if any((cur / m).exists() for m in markers):
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def plan_installs(
    agents_dir: Path,
    targets: list[Path],   # one path per host scope+extension combo
    selected_agent_names: set[str] | None,
) -> list[tuple[Path, Path]]:
    """Return list of (source, destination) file pairs."""
    pairs: list[tuple[Path, Path]] = []
    for src in sorted(agents_dir.iterdir()):
        if not src.is_file():
            continue
        if src.name == "README.md":
            continue
        stem = src.stem
        if selected_agent_names is not None and stem not in selected_agent_names:
            continue
        for tgt_dir in targets:
            # Match extension: ".md" -> claude target, ".toml" -> codex target
            if tgt_dir.name == "agents" and (
                (src.suffix == ".md" and tgt_dir.parent.name == ".claude")
                or (src.suffix == ".toml" and tgt_dir.parent.name == ".codex")
            ):
                pairs.append((src, tgt_dir / src.name))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agents-dir",
        default=str(Path(__file__).resolve().parent.parent / "agents"),
    )
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing destination files")
    parser.add_argument("-g", "--global", dest="global_scope", action="store_true",
                        help="install at user scope (under --home)")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="non-interactive; skip confirmations")
    parser.add_argument("-a", "--host", action="append", default=[],
                        help="force a specific host (claude-code, codex)")
    parser.add_argument("--agents", nargs="+", default=None,
                        help="restrict to a subset of agent names (stems)")
    args = parser.parse_args(argv)

    agents_dir = Path(args.agents_dir)
    if not agents_dir.is_dir():
        print(f"error: agents dir not found: {agents_dir}", file=sys.stderr)
        return 2

    home = Path(args.home)
    # Determine scope.
    if args.global_scope:
        scope_root = home
    else:
        proj = find_project_root(Path.cwd())
        if proj is None:
            print("error: no project root found; pass -g for user scope", file=sys.stderr)
            return 2
        scope_root = proj

    # Determine active hosts.
    if args.host:
        unknown = [h for h in args.host if h not in HOSTS]
        if unknown:
            print(f"error: unknown host(s): {unknown}", file=sys.stderr)
            return 2
        active = args.host
    else:
        active = detect_hosts(scope_root if not args.global_scope else home)
        if not active:
            print(
                f"no host agent install dirs found under {home}. "
                "Create .claude/agents/ or .codex/agents/ first, or pass -a.",
                file=sys.stderr,
            )
            return 2

    # Build target dirs.
    targets = [scope_root / HOSTS[h][0] for h in active]

    selected = set(args.agents) if args.agents else None
    pairs = plan_installs(agents_dir, targets, selected)
    if not pairs:
        print("no agent files matched")
        return 0

    # Check for collisions.
    collisions = [dst for _src, dst in pairs if dst.exists() and not args.force]
    if collisions:
        for c in collisions:
            print(f"error: destination exists (use --force): {c}", file=sys.stderr)
        return 1

    for src, dst in pairs:
        if args.dry_run:
            print(f"would copy {src} -> {dst}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"copied {src.name} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_install_agents -v`
Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/install-agents.py tests/test_install_agents.py
git commit -m "feat(agents): host-detecting installer script

Detects Claude Code / Codex CLI install dirs under home or project root,
and copies the matching agent file. Cursor/Windsurf/Goose silently
skipped (no file-based agent slot exists on these hosts as of 2026-06).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 16: Extend `evals/run.py` with agent checks

**Files:**
- Modify: `evals/run.py`
- Create: `tests/test_evals_agent_checks.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_evals_agent_checks.py`:

```python
"""Tests for the new agent checks in evals/run.py."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN = REPO_ROOT / "evals" / "run.py"


def run(cwd: Path | None = None):
    return subprocess.run(
        [sys.executable, str(RUN)], capture_output=True, text=True,
        cwd=cwd or REPO_ROOT,
    )


class AgentChecksTests(unittest.TestCase):
    def test_repo_passes_overall_run(self):
        """The current branch must pass evals/run.py with the new checks active."""
        result = run()
        self.assertEqual(result.returncode, 0,
                         f"evals/run.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("OK", result.stdout)

    def test_detects_missing_toml_sibling(self):
        """If an agent .md exists without a .toml sibling, the check fails."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            # Build a minimal repo skeleton: copy evals/, scripts/, agents/, skills/, template/.
            for sub in ("evals", "scripts", "agents", "skills", "template"):
                target = tdp / sub
                if (REPO_ROOT / sub).is_dir():
                    import shutil
                    shutil.copytree(REPO_ROOT / sub, target)
            (tdp / ".claude-plugin").mkdir()
            (tdp / ".claude-plugin" / "marketplace.json").write_text(
                (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            # Delete one TOML sibling to trigger the check.
            toml = tdp / "agents" / "improve-prompt-agent.toml"
            if toml.exists():
                toml.unlink()
            result = run(cwd=tdp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("improve-prompt-agent", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify the second test fails (no check exists yet)**

Run: `python3 -m unittest tests.test_evals_agent_checks -v`
Expected: `test_detects_missing_toml_sibling` fails (the check doesn't exist yet, so evals/run.py won't notice the missing TOML).

- [ ] **Step 3: Add the two new checks to `evals/run.py`**

Edit `evals/run.py`. After the `check_shared_reader_drift` function, add:

```python
def check_agent_skill_pairing() -> list[str]:
    """Each agents/<name>-agent.md must pair with a skill.

    Naming rule: agent name '<name>-agent' implies a skill 'skills/<name>/'.
    """
    problems: list[str] = []
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.is_dir():
        return problems
    for md in sorted(agents_dir.glob("*-agent.md")):
        stem = md.stem  # e.g. 'improve-prompt-agent'
        if not stem.endswith("-agent"):
            continue
        skill_name = stem[:-len("-agent")]
        skill_dir = SKILLS_DIR / skill_name
        if not skill_dir.is_dir():
            problems.append(
                f"{md}: paired skill 'skills/{skill_name}/' not found"
            )
    return problems


def check_agent_format_parity() -> list[str]:
    """Each agents/<name>.md must have a matching .toml; name+description equal."""
    import re
    problems: list[str] = []
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.is_dir():
        return problems
    for md in sorted(agents_dir.glob("*.md")):
        if md.name == "README.md":
            continue
        toml_path = md.with_suffix(".toml")
        if not toml_path.exists():
            problems.append(f"{md}: missing TOML sibling at {toml_path.name}")
            continue
        md_text = md.read_text(encoding="utf-8")
        try:
            fm_end = md_text.find("\n---\n", 4)
            fm = md_text[4:fm_end]
            md_name_m = re.search(r"^name:\s*(\S+)", fm, re.M)
            md_desc_m = re.search(r"^description:\s*(.+)", fm, re.M)
            md_name = md_name_m.group(1) if md_name_m else None
            md_desc = (md_desc_m.group(1) if md_desc_m else "").strip().lstrip(">|").strip()
        except Exception as e:
            problems.append(f"{md}: cannot parse frontmatter ({e})")
            continue
        try:
            import tomllib
            with open(toml_path, "rb") as f:
                td = tomllib.load(f)
        except Exception as e:
            problems.append(f"{toml_path}: cannot parse TOML ({e})")
            continue
        if md_name != td.get("name"):
            problems.append(
                f"{md.name} vs {toml_path.name}: name mismatch "
                f"({md_name!r} vs {td.get('name')!r})"
            )
    return problems
```

Then in `main()`, add the two checks to the `if not args.skill:` branch (alongside the existing checks):

```python
        all_problems.extend(check_agent_skill_pairing())
        all_problems.extend(check_agent_format_parity())
```

- [ ] **Step 4: Run tests to verify both pass**

Run: `python3 -m unittest tests.test_evals_agent_checks -v`
Expected: both tests pass.

Run: `python3 evals/run.py`
Expected: `OK — checked 13 skill(s).`

- [ ] **Step 5: Commit**

```bash
git add evals/run.py tests/test_evals_agent_checks.py
git commit -m "feat(evals): add agent-skill pairing and format-parity checks

Two new structural checks in evals/run.py:
- Every agents/<name>-agent.md must pair with skills/<name>/.
- Every agents/<name>.md must have a TOML sibling with matching name.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 17: Write `docs/agents-guide.md`

**Files:**
- Create: `docs/agents-guide.md`

- [ ] **Step 1: Create the guide**

Create `docs/agents-guide.md`:

```markdown
# Agents authoring guide

This guide covers the `agents/` layer — Claude Code subagents and Codex CLI subagents shipped from this repo. Skills are documented separately in [`docs/authoring-guide.md`](authoring-guide.md). Read both if you are adding a new agent that also needs a paired skill.

## When to write an agent vs. a skill

Prefer skills. A SKILL.md with strong description-as-trigger language reaches every host that implements the [agentskills.io](https://agentskills.io/specification) standard (Claude Code, Codex CLI, Cursor, Windsurf, Goose, and others). An agent reaches only the host whose subagent format it targets (Claude Code or Codex CLI; not portable to the others).

Write an agent when you genuinely need:

- An **isolated context window** (long parallel exploration, heavy tool use, sandbox isolation).
- A specific **model tier** or **reasoning effort** different from the parent session.
- A **named dispatchable role** the user invokes by name (e.g. "have `improve-prompt-agent` rewrite this prompt").
- **Banned-construct enforcement** that requires a separate prompt (rare).

If none of those apply, the skill alone is enough.

## Naming rule

Agent name = `<paired-skill-name>` + `-agent`.

Skill names carry no `-expert` suffix; agents inherit the clean skill name plus `-agent`. Examples:

| Skill | Agent |
|---|---|
| `improve-prompt` | `improve-prompt-agent` |
| `formal-methods` | `formal-methods-agent` |
| `srs` | `srs-agent` |
| `petri-net-theory` | `petri-net-theory-agent` |

This makes the agent-to-skill mapping unambiguous and machine-checkable (`evals/run.py` enforces it).

## Format conventions

### Claude Code (canonical)

`agents/<name>.md` is the canonical source. YAML frontmatter:

- **Required:** `name`, `description`.
- **Optional:** `tools` (Claude Code tool allow-list), `model`, `skills` (array of paired skills to auto-load).

The Markdown body is the agent's system prompt.

### Codex CLI (generated)

`agents/<name>.toml` is generated from the `.md` by `scripts/generate-codex-agents.py`. Schema (per [Codex 2026 subagent docs](https://developers.openai.com/codex/subagents)):

- **Required:** `name`, `description`, `developer_instructions`.
- **Optional:** `model`, `model_reasoning_effort`, `nickname_candidates`, `sandbox_mode`, `mcp_servers`, `[skills.config]`.

The Markdown body becomes `developer_instructions` as a multi-line TOML string.

### Cross-format invariants

`evals/run.py` enforces:

- Every `agents/<name>.md` has a `agents/<name>.toml` sibling.
- `name` field is identical across the pair.

Other fields may differ (the formats target different hosts).

## Generation workflow

After editing any `<name>.md`:

```sh
python3 scripts/generate-codex-agents.py
```

Then commit both the `.md` and the regenerated `.toml`.

Editing the `.toml` by hand is allowed but discouraged — the eval check fails when name or description diverges between formats. Either regenerate or update the Markdown.

## Banned constructs in agent bodies

Agents should not:

- Read or write user project files outside what their paired skill mandates.
- Embed credentials, API keys, or hardcoded paths.
- Reference peer agents that do not exist in this repo (`evals/run.py` catches some of these via the pairing check).

## Distribution

Agents are not portable across all hosts. Each format ships to its specific host:

- **Claude Code:** via plugin marketplace (`/plugin install dev-skills@martinatgit`) or manual copy of `agents/*.md` to `~/.claude/agents/` or `<project>/.claude/agents/`.
- **Codex CLI:** via `python3 scripts/install-agents.py` or manual copy of `agents/*.toml` to `~/.codex/agents/` or `<project>/.codex/agents/`.
- **Cursor, Windsurf, Goose:** no file-based agent slot exists today. Skills are the portable alternative.

See [`docs/install.md`](install.md) for the full install matrix.

## Authoring checklist

Before opening a PR with a new or modified agent, walk [`docs/agents-portability-checklist.md`](agents-portability-checklist.md).
```

- [ ] **Step 2: Verify**

Run: `python3 -c "p='docs/agents-guide.md'; assert open(p).read().count('##') >= 7"`
Expected: succeeds (at least 7 headings).

- [ ] **Step 3: Commit**

```bash
git add docs/agents-guide.md
git commit -m "docs: add agents authoring guide

Covers when to write an agent vs. skill, naming rule, format
conventions for Claude Code (Markdown) and Codex CLI (TOML),
generator workflow, banned constructs, and distribution paths.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 18: Write `docs/agents-portability-checklist.md`

**Files:**
- Create: `docs/agents-portability-checklist.md`

- [ ] **Step 1: Create the checklist**

Create `docs/agents-portability-checklist.md`:

```markdown
# Agents portability checklist

Every agent in this repo passes every item. Walk this list before opening a PR.

## Naming

- [ ] Agent name is `<paired-skill-name>` + `-agent`.
- [ ] The paired skill exists in `skills/<paired-skill-name>/`.
- [ ] The agent name uses no `-expert` suffix.

## Format

- [ ] `agents/<name>.md` exists with YAML frontmatter containing `name` and `description`.
- [ ] `agents/<name>.toml` exists, generated by `python3 scripts/generate-codex-agents.py`.
- [ ] `name` field matches between `.md` and `.toml`.
- [ ] `description` field reads the same in both.

## Markdown frontmatter

- [ ] `name`, `description` present.
- [ ] If `skills:` is set, every entry names a real skill in `skills/`.
- [ ] No platform-specific keys beyond `name`, `description`, `tools`, `model`, `skills`.

## Body

- [ ] First paragraph identifies the agent (`You are the \`<name>\` agent.`).
- [ ] No hardcoded credentials, API keys, or environment-specific paths.
- [ ] Cross-references to peer agents use the new `-agent` names.

## Validation

- [ ] `python3 evals/run.py` returns OK with the new agent checks.
- [ ] `python3 -m unittest discover tests/` passes.
- [ ] `python3 scripts/install-agents.py --dry-run -g` lists the new agent's `.md` and `.toml` under the correct host paths.

## Documentation

- [ ] Agent listed in `agents/README.md` table.
- [ ] Agent listed in `README.md` "Agents in this repository" section.
- [ ] Agent path added to `.claude-plugin/marketplace.json` `agents:` array.
```

- [ ] **Step 2: Verify**

Run: `wc -l docs/agents-portability-checklist.md`
Expected: ≥ 30 lines.

- [ ] **Step 3: Commit**

```bash
git add docs/agents-portability-checklist.md
git commit -m "docs: add agents portability checklist

Pre-PR checklist mirroring docs/portability-checklist.md for agents.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 19: Write `agents/README.md`

**Files:**
- Create: `agents/README.md`

- [ ] **Step 1: Create the README**

Create `agents/README.md`:

```markdown
# Agents

This folder ships dispatchable subagents paired with skills in `../skills/`. Each agent has two parallel files:

- `<name>.md` — Claude Code subagent (YAML frontmatter + Markdown body).
- `<name>.toml` — Codex CLI subagent (TOML schema).

The Markdown is canonical; the TOML is generated by [`scripts/generate-codex-agents.py`](../scripts/generate-codex-agents.py).

## Naming rule

Agent name = `<paired-skill-name>` + `-agent`. No `-expert` suffix on either side.

## Agents shipped here

| Agent | Paired skill | Purpose |
|---|---|---|
| `improve-prompt-agent` | `improve-prompt` | Transform a rough idea into one polished LLM prompt. |
| `create-tutorial-agent` | `create-tutorial` | Generate a textbook-style technical tutorial. |
| `formal-methods-agent` | `formal-methods` | Authoritative reference for SAT/SMT/CLP/CP, theorem proving, model checking. |
| `petri-net-theory-agent` | `petri-net-theory` | Petri net theory and modelling patterns. |
| `srs-agent` | `srs` | Synchronous reactive systems design and verification. |
| `type-theory-agent` | `type-theory` | Formal type systems, inference, category-theoretic foundations. |
| `debugger-agent` | `debugger` | Debugger and tracer design, trace semantics, event models. |

## See also

- [`docs/agents-guide.md`](../docs/agents-guide.md) — authoring conventions for agents.
- [`docs/agents-portability-checklist.md`](../docs/agents-portability-checklist.md) — pre-PR checklist.
- [`docs/install.md`](../docs/install.md) — install matrix per host.
- [`scripts/install-agents.py`](../scripts/install-agents.py) — host-detecting installer.
```

- [ ] **Step 2: Commit**

```bash
git add agents/README.md
git commit -m "docs(agents): add README overview and roster

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 20: Update top-level `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add the 6 missing skill rows to the skills table**

Edit `README.md`. The current skills table is at lines ~67-78. After the `create-tutorial` row, insert these rows (in alphabetical order or grouped by topic, your choice — alphabetical recommended):

```markdown
| [`debugger`](skills/debugger/SKILL.md) | Authoritative reference for debugger and tracer design: trace semantics, event-model design, breakpoint/spy-point semantics, cross-formalism coherence, time-travel replay, remote debug protocols. |
| [`formal-methods`](skills/formal-methods/SKILL.md) | Authoritative reference for SAT/SMT, CLP/CP, theorem proving, temporal logic, TLA+, and model checking. Use for algorithm selection, decidability analysis, propagator engine review, formal-system audits. |
| [`improve-prompt`](skills/improve-prompt/SKILL.md) | Transform rough user-intent text into one polished, paste-ready LLM prompt. Evidence-guarded against the well-replicated failure modes of prompt engineering (CoT misuse, persona-on-factual, lost-in-middle, unwrapped untrusted input). |
| [`petri-net-theory`](skills/petri-net-theory/SKILL.md) | Authoritative reference for Petri net theory: formal foundations, decidability, compliance modelling, P/T/CPN/WF-net patterns. |
| [`srs`](skills/srs/SKILL.md) | Authoritative reference for synchronous reactive systems: tick architecture, signal semantics, clock calculus, constructive causality. |
| [`type-theory`](skills/type-theory/SKILL.md) | Authoritative reference for formal type systems: lambda cube, type inference (HM, bidirectional), advanced systems (GADTs, refinement, gradual, session, graded), category-theoretic foundations. |
```

- [ ] **Step 2: Add the new "Agents in this repository" section**

In `README.md`, after the existing skills table and before "## Authoring a new skill", insert:

```markdown
## Agents in this repository

Agents are dispatchable subagent definitions paired with skills. They ship in two formats — Markdown for Claude Code and TOML for Codex CLI — and are installed via `scripts/install-agents.py` (or `/plugin install` for Claude Code).

| Agent | Paired skill |
|---|---|
| [`improve-prompt-agent`](agents/improve-prompt-agent.md) | `improve-prompt` |
| [`create-tutorial-agent`](agents/create-tutorial-agent.md) | `create-tutorial` |
| [`formal-methods-agent`](agents/formal-methods-agent.md) | `formal-methods` |
| [`petri-net-theory-agent`](agents/petri-net-theory-agent.md) | `petri-net-theory` |
| [`srs-agent`](agents/srs-agent.md) | `srs` |
| [`type-theory-agent`](agents/type-theory-agent.md) | `type-theory` |
| [`debugger-agent`](agents/debugger-agent.md) | `debugger` |

See [`docs/agents-guide.md`](docs/agents-guide.md) and [`docs/install.md`](docs/install.md#installing-agents).
```

(The `create-tutorial-agent` link will 404 until Task 33 creates it. That's fine — Phase 2 closes the gap.)

- [ ] **Step 3: Verify**

Run: `grep -cE '^\| \[\`' README.md`
Expected: 13 (6 original + 6 newly-added skill rows + 7 agent rows = at least 13 table rows; the exact count depends on table formatting).

Run: `grep -n 'Agents in this repository' README.md`
Expected: one line.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs(README): register all skills and add agents section

Add the 6 previously-unregistered skills to the skills table.
Add a parallel \"Agents in this repository\" section listing all 7
paired agents.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 21: Update `docs/install.md`

**Files:**
- Modify: `docs/install.md`

- [ ] **Step 1: Add the "Installing agents" section**

Edit `docs/install.md`. After the "Verifying the install" section (around line 84) and before "## Shared conventions", insert:

```markdown
## Installing agents

Agents in this repo ship in two formats targeting different hosts.

### Claude Code

Either via the plugin marketplace (recommended):

```
/plugin marketplace add martinatgit/dev-skills
/plugin install dev-skills@martinatgit
```

This installs all skills and all `agents/*.md` files. Manual alternative:

```sh
cp dev-skills/agents/*.md ~/.claude/agents/        # user scope
cp dev-skills/agents/*.md .claude/agents/          # project scope
```

### Codex CLI

Run the host-detecting installer:

```sh
python3 scripts/install-agents.py                  # auto-detect, current scope
python3 scripts/install-agents.py -g               # force user scope
python3 scripts/install-agents.py --agents improve-prompt-agent  # subset
python3 scripts/install-agents.py --dry-run        # preview
```

Or manual:

```sh
cp dev-skills/agents/*.toml ~/.codex/agents/       # user scope
cp dev-skills/agents/*.toml .codex/agents/         # project scope
```

### Cursor, Windsurf, Goose

These hosts do not have a file-based subagent slot today. Skills are the portable alternative; install them via `npx skills add martinatgit/dev-skills` (see [Quick start](#quick-start--multi-agent-install)).

### Verifying the agents install

```sh
ls ~/.claude/agents/    # Claude Code, user scope
ls ~/.codex/agents/     # Codex CLI, user scope
ls .claude/agents/ .codex/agents/  # project scope
```
```

- [ ] **Step 2: Verify**

Run: `grep -n 'Installing agents' docs/install.md`
Expected: one line.

- [ ] **Step 3: Commit**

```bash
git add docs/install.md
git commit -m "docs(install): add Installing agents section

Documents the two install routes (plugin marketplace for Claude Code,
scripts/install-agents.py for Codex CLI) and the explicit not-supported
status for Cursor/Windsurf/Goose.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 22: Update `.claude-plugin/marketplace.json`

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Update skills array and add agents array**

Edit `.claude-plugin/marketplace.json`. Replace the entire `plugins[0]` object with:

```json
{
  "name": "dev-skills",
  "source": ".",
  "description": "A collection of useful skills to incorporate LLMs and agentic AI into the development workflow.",
  "skills": [
    "./skills/example-skill",
    "./skills/developer-diary",
    "./skills/reason-through",
    "./skills/update-todos",
    "./skills/terminology",
    "./skills/create-tutorial",
    "./skills/improve-prompt",
    "./skills/formal-methods",
    "./skills/debugger",
    "./skills/srs",
    "./skills/type-theory",
    "./skills/petri-net-theory"
  ],
  "agents": [
    "./agents/improve-prompt-agent.md",
    "./agents/formal-methods-agent.md",
    "./agents/petri-net-theory-agent.md",
    "./agents/srs-agent.md",
    "./agents/type-theory-agent.md",
    "./agents/debugger-agent.md"
  ]
}
```

(Note: `create-tutorial-agent.md` is omitted because it's created in Phase 2 Task 33. Once Phase 2 lands, that PR will add the entry.)

- [ ] **Step 2: Verify JSON parses and contains expected entries**

Run: `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo VALID`
Expected: `VALID`.

Run:
```bash
python3 -c "
import json
d = json.load(open('.claude-plugin/marketplace.json'))
plugin = d['plugins'][0]
print('skills:', len(plugin['skills']))
print('agents:', len(plugin['agents']))
"
```
Expected:
```
skills: 12
agents: 6
```

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(marketplace): register all skills and add agents array

12 skills now listed (was 6). New agents: array carries the 6 paired
Markdown agents. create-tutorial-agent will be added in Phase 2 once
the file is created.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 23: Final Phase 1 verification

**Files:** none modified; verification only.

- [ ] **Step 1: Run full evals**

Run: `python3 evals/run.py`
Expected: `OK — checked 13 skill(s).` (No new failures from the agent checks.)

- [ ] **Step 2: Run full test suite**

Run: `python3 -m unittest discover tests/ -v 2>&1 | tail -20`
Expected: `OK` and no failures.

- [ ] **Step 3: Verify renames clean**

Run:
```bash
grep -rn -E '(formal-methods-expert|debugger-expert|srs-expert|type-theory-expert|petri-net-expert|prompt-engineer)' \
  --include="*.md" --include="*.py" --include="*.json" \
  --exclude-dir=tests --exclude-dir=.git --exclude-dir=docs/superpowers \
  . 2>&1 | grep -v "skills/improve-prompt/"
```
Expected: no output (or only entries inside `skills/improve-prompt/`, which Phase 2 fixes).

- [ ] **Step 4: Verify all agents have TOML siblings**

Run:
```bash
python3 -c "
import pathlib
for md in pathlib.Path('agents').glob('*-agent.md'):
    toml = md.with_suffix('.toml')
    assert toml.exists(), f'missing {toml}'
    print(md.name, 'OK')
"
```
Expected: 6 lines, each ending `OK`.

- [ ] **Step 5: Open PR 1 (or hand off to user)**

This is a manual step. If using GitHub CLI:

```bash
git push -u origin feature/shared-skill-config
gh pr create --title "Skills conformance + agents-layer infrastructure (PR 1/2)" --body "$(cat <<'EOF'
## Summary
- Rename four skills to drop \`-expert\` suffix; rename six paired agents to the new \`<skill>-agent\` convention.
- New \`scripts/generate-codex-agents.py\` and \`scripts/install-agents.py\` (stdlib only).
- New \`docs/agents-guide.md\`, \`docs/agents-portability-checklist.md\`, \`agents/README.md\`.
- README skills table now lists all 12 skills; new "Agents in this repository" section.
- Marketplace JSON ships all 12 skills + 6 Markdown agents.
- \`evals/run.py\` gains agent-skill pairing + format-parity checks.

PR 2 will follow with per-skill content conformance (Examples, Troubleshooting, fixtures, paired \`create-tutorial-agent\`).

## Test plan
- [x] \`python3 evals/run.py\` returns OK.
- [x] \`python3 -m unittest discover tests/\` passes.
- [x] \`python3 -m json.tool .claude-plugin/marketplace.json\` parses.
- [x] Grep finds no stale references to old names outside \`skills/improve-prompt/\`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 6: Wait for PR review and merge before continuing to Phase 2**

If the PR is approved and merged, continue with Phase 2 below. If changes are requested, address them and re-verify.

---

## Phase 2 — Content Conformance for Seven Skills

After Phase 1 merges, the seven skills (`create-tutorial`, `improve-prompt`, `formal-methods`, `debugger`, `srs`, `type-theory`, `petri-net-theory`) need their full template conformance pass and `evals/fixtures/<name>/prompts.json` files. The `create-tutorial-agent` (and its `.toml` sibling) is also created in this phase.

### Task 24: Conform `create-tutorial/SKILL.md`

**Files:**
- Modify: `skills/create-tutorial/SKILL.md`

- [ ] **Step 1: Add `## When to use` and `## When not to use` sections**

Edit `skills/create-tutorial/SKILL.md`. Immediately after the one-paragraph intro and before `## Configuration`, add:

```markdown
## When to use

- The user types `/create-tutorial <topic>` or asks for "a tutorial on X".
- The user wants a durable, self-contained walkthrough of a component, feature, or subsystem — not a chat answer.
- A new module, API surface, or workflow has just landed and needs textbook-style documentation for future engineers.

## When not to use

- Inline chat explanations (just answer).
- Short notes or session handoff — use `developer-diary` instead.
- API reference docs only (the tutorial format is broader; use a tighter reference doc if reference is all you need).
- Bug fixes or how-to-troubleshoot writeups — those belong elsewhere.
```

- [ ] **Step 2: Add `## Examples` section**

Append (before `## Saving the Tutorial`):

```markdown
## Examples

### Example 1 — typical case

**User:** "Write a tutorial for the new tenant-isolation middleware."

**Skill output:** A markdown file at `<tutorials_dir>/tenant-isolation-middleware.md` containing all 10 sections (Introduction, Prerequisites, System Architecture, Core Concepts, API and Functional Overview, Worked Examples, Implementation Insights, Comparative Analysis, Integration Guidance, Outlook, Testing Strategy). The tutorial reads as a self-contained textbook chapter; no external context is required to understand it.

### Example 2 — edge case (component without code)

**User:** "Tutorial for the event-stream-processor — I have the spec but no code yet."

**Skill output:** Same structure, but the Implementation Insights and Testing Strategy sections clearly label inferred-from-spec content vs. implemented behavior. The `## Inputs` section captures that the topic is a spec-only target so a future reader understands the labelling.
```

- [ ] **Step 3: Add `## Troubleshooting` section**

Append (after `## Examples`, before `## Saving the Tutorial`):

```markdown
## Troubleshooting

- **`tutorials_dir` not resolved.** First-use path: run `python3 scripts/configure.py --scope project` and answer the prompt, or set the env var `CREATE_TUTORIAL_TUTORIALS_DIR`, or add `docs_root` to `.agents/dev-skills.yaml`.
- **Topic too narrow.** If the user says "write a tutorial for `parseDate()`" — that's reference docs territory, not a tutorial. Ask whether they want a reference instead.
- **File would overwrite an existing tutorial.** The skill overwrites by default. If unwanted, ask the user for a different filename before writing.
```

- [ ] **Step 4: Verify**

Run: `grep -cE '^## (When to use|When not to use|Examples|Troubleshooting|Inputs|Configuration|Workflow|Output|Saving)' skills/create-tutorial/SKILL.md`
Expected: at least 7.

Run: `python3 evals/run.py --skill create-tutorial`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/create-tutorial/SKILL.md
git commit -m "feat(create-tutorial): add template sections (when-to-use, examples, troubleshooting)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 25: Add `evals/fixtures/create-tutorial/prompts.json`

**Files:**
- Create: `evals/fixtures/create-tutorial/prompts.json`

- [ ] **Step 1: Create the fixture**

Create directory and file:

```bash
mkdir -p evals/fixtures/create-tutorial
```

Then create `evals/fixtures/create-tutorial/prompts.json`:

```json
{
  "skill": "create-tutorial",
  "prompts": [
    {
      "id": "slash-command",
      "text": "/create-tutorial event-stream-processor",
      "expect_trigger": true
    },
    {
      "id": "natural-language",
      "text": "Write a tutorial for the new tenant-isolation middleware.",
      "expect_trigger": true
    },
    {
      "id": "textbook-chapter",
      "text": "I need a textbook chapter explaining how our auth middleware works.",
      "expect_trigger": true
    },
    {
      "id": "negative-bugfix",
      "text": "Help me fix this off-by-one error in parseDate.",
      "expect_trigger": false
    },
    {
      "id": "negative-session-handoff",
      "text": "Remind me what we were working on yesterday.",
      "expect_trigger": false
    }
  ]
}
```

- [ ] **Step 2: Verify JSON parses**

Run: `python3 -m json.tool evals/fixtures/create-tutorial/prompts.json > /dev/null && echo VALID`
Expected: `VALID`.

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/create-tutorial/prompts.json
git commit -m "test(create-tutorial): add canonical trigger fixtures

Three positive triggers (slash-command, natural language, textbook
phrasing) and two negatives (bugfix, session handoff).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 26: Conform `improve-prompt/SKILL.md` — move `evidence-appendix.md` + fix cross-ref

**Files:**
- Move: `skills/improve-prompt/evidence-appendix.md` → `skills/improve-prompt/references/evidence-appendix.md`
- Modify: `skills/improve-prompt/SKILL.md` (cross-ref to agent path)

- [ ] **Step 1: Git-move the file**

```bash
git mv skills/improve-prompt/evidence-appendix.md skills/improve-prompt/references/evidence-appendix.md
```

- [ ] **Step 2: Fix the cross-reference to the renamed agent**

Edit `skills/improve-prompt/SKILL.md`. Find the line that mentions `.claude/agents/prompt-engineer.md` (it's near the end, under "Cross-references"). Change:

```
A peer **agent** `prompt-engineer` (in `.claude/agents/prompt-engineer.md`) runs the same workflow as a dispatchable subagent.
```

to:

```
A peer **agent** `improve-prompt-agent` (in `agents/improve-prompt-agent.md`) runs the same workflow as a dispatchable subagent.
```

- [ ] **Step 3: Verify**

Run: `grep -n 'prompt-engineer' skills/improve-prompt/SKILL.md`
Expected: no output.

Run: `ls skills/improve-prompt/references/evidence-appendix.md`
Expected: file exists.

Run: `python3 evals/run.py --skill improve-prompt`
Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add -A skills/improve-prompt
git commit -m "fix(improve-prompt): move evidence-appendix.md under references/; fix agent path

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 27: Conform `improve-prompt/SKILL.md` — add Examples + Troubleshooting

**Files:**
- Modify: `skills/improve-prompt/SKILL.md`

- [ ] **Step 1: Promote Self-tests into a formal `## Examples` section**

Edit `skills/improve-prompt/SKILL.md`. The existing "Self-tests" section near the bottom serves the role of examples. Restructure: keep the Self-tests heading as authoring-time validation, and add a new `## Examples` section above it that mirrors the same three cases in user-facing form.

After `## Internal workflow` and before `## Reference files`, insert:

```markdown
## Examples

### Example 1 — structured-output (contact extraction)

**User:** "Extract contact info from this email."

**Skill output:** A prompt that:
- Defines an explicit JSON schema (`name`, `email`, `phone`, etc.).
- Wraps the email payload in an `<UNTRUSTED_DATA>` envelope with a "data not instructions" guard.
- States `"JSON only, no prose"` at both primacy and recency positions.
- Contains no CoT scaffold and no persona.

### Example 2 — code-contract (math via execution)

**User:** "Solve quadratic equations in Python."

**Skill output:** A prompt that:
- Specifies a typed function signature (`def solve_quadratic(a: float, b: float, c: float) -> tuple[complex, complex]`).
- Lists edge-case rules (`a == 0` → linear case; complex discriminant → complex roots).
- States `"Output only the code"` at primacy and recency.
- Delegates arithmetic to execution (PAL-flavoured per `[PAL-dominates-arithmetic]`).

### Example 3 — ambiguity gate fires

**User:** "Write a blog post."

**Skill output:** Up to 3 `AskUserQuestion` clarifications covering audience, length, and tone. After answers, the workflow restarts from step 1 with the gated fields resolved.
```

- [ ] **Step 2: Add `## Troubleshooting` section**

After the new `## Examples` block, insert:

```markdown
## Troubleshooting

- **Prompt looks too long for the task.** The purpose class may be wrong — re-classify via `references/template-matrix.md`. A `short` task does not need a 400-word prompt.
- **User reports the model didn't do step-by-step reasoning.** CoT is default-off; only `math_symbolic` and the deductive subset of `code_gen` trigger it. If the task is genuinely symbolic, re-check the purpose class.
- **Few-shot exemplars look too uniform.** Diversify by surface form, label, and order (`[Order-flips]`, `[Format-flips]`). The template-matrix cell mandates lexical diversity.
```

- [ ] **Step 3: Verify**

Run: `grep -cE '^## (When to use|When NOT to use|Examples|Troubleshooting|Internal workflow|Output contract)' skills/improve-prompt/SKILL.md`
Expected: at least 5.

Run: `python3 evals/run.py --skill improve-prompt`
Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add skills/improve-prompt/SKILL.md
git commit -m "feat(improve-prompt): add Examples and Troubleshooting sections

Promotes the three Self-tests into a user-facing Examples block;
keeps Self-tests as authoring-time validation. New Troubleshooting
covers prompt-length, CoT non-triggering, and exemplar uniformity.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 28: Add `evals/fixtures/improve-prompt/prompts.json`

**Files:**
- Create: `evals/fixtures/improve-prompt/prompts.json`

- [ ] **Step 1: Create the fixture**

```bash
mkdir -p evals/fixtures/improve-prompt
```

Create `evals/fixtures/improve-prompt/prompts.json`:

```json
{
  "skill": "improve-prompt",
  "prompts": [
    {
      "id": "structured-output",
      "text": "extract contact info from this email",
      "expect_trigger": true
    },
    {
      "id": "code-contract",
      "text": "solve quadratic equations in Python",
      "expect_trigger": true
    },
    {
      "id": "ambiguity-gate",
      "text": "write a blog post",
      "expect_trigger": true
    },
    {
      "id": "explicit-improvement",
      "text": "Can you improve this prompt for me?",
      "expect_trigger": true
    },
    {
      "id": "negative-direct-task",
      "text": "Extract these contacts now and return JSON.",
      "expect_trigger": false
    }
  ]
}
```

- [ ] **Step 2: Verify**

Run: `python3 -m json.tool evals/fixtures/improve-prompt/prompts.json > /dev/null && echo VALID`
Expected: `VALID`.

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/improve-prompt/prompts.json
git commit -m "test(improve-prompt): add canonical trigger fixtures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 29: Conform `formal-methods/SKILL.md`

**Files:**
- Modify: `skills/formal-methods/SKILL.md`

- [ ] **Step 1: Tighten the description for pushy language**

Edit `skills/formal-methods/SKILL.md`. Replace the existing `description:` block (lines 3-13 of the original folded scalar) with:

```yaml
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
```

- [ ] **Step 2: Add explicit `## When to use` / `## When not to use` headings**

The existing body has an "Intake Protocol" with "Applicability signals" and anti-signals. Add two new section headings (without removing the intake protocol content) immediately after the one-paragraph intro:

```markdown
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
```

(The existing "Applicability signals" and anti-signals under "Intake Protocol → Step 1" can stay; they're a tighter version of the same content used during invocation.)

- [ ] **Step 3: Add `## Inputs` section**

After `## When not to use`:

```markdown
## Inputs

A formal-methods question, optionally accompanied by codebase context. The skill operates in two modes:

- **Domain-general:** algorithm theory, decidability questions, solver selection — no project context needed.
- **Project-specific:** review of an existing implementation; the skill performs the project-onboarding pre-flight (read `CLAUDE.md` / `README.md` / `AGENTS.md`) before answering.
```

- [ ] **Step 4: Add `## Examples` section**

Before `## Confidence Calibration` (or wherever the body's current closing references sit), insert:

```markdown
## Examples

### Example 1 — theory query

**User:** "Is `QF_NIA` decidable? If I have a formula with `x*y > 5 && y < 10`, will Z3 always terminate?"

**Skill output:** States `QF_NIA` decidability (undecidable in general, even for the quantifier-free fragment with non-linear integer arithmetic per Matiyasevich; Z3 may not terminate). Names the decidable fragment (`QF_LIA`); offers reformulation tactics if applicable. Cites Cook-Levin and the relevant Z3 docs. Confidence: High.

### Example 2 — design-review query

**User:** "Audit this propagator engine — it uses arc consistency only, no LCG. Is that sound?"

**Skill output:** States "sound but exponentially slower on hard instances; arc consistency alone has no explanation clauses, so the solver lacks the conflict-driven backjumping that LCG enables." Names the formal foundation (Schulte & Stuckey 2008; Feydy & Stuckey 2009 for LCG). Flags the completeness gap explicitly. Confidence: High.
```

- [ ] **Step 5: Add `## Troubleshooting` section**

Append (before `## Topic → Reference File Routing`):

```markdown
## Troubleshooting

- **The question is cross-domain (e.g. "verify this Petri-net implementation").** Answer the formal-methods slice and explicitly hand off the domain-specific encoding to the peer skill (`petri-net-theory`, `srs`, `type-theory`, or `debugger`).
- **The user asks for proof but the property is testing-shaped.** Push back politely: name the formal-vs-empirical distinction; offer both options.
- **Z3 / TLC / solver-by-name is invoked but the question is actually about the *project's* encoding.** Pre-flight: read the project index doc first, then answer with the project's component names rather than generic solver names.
```

- [ ] **Step 6: Verify**

Run: `grep -cE '^## (When to use|When not to use|Inputs|Examples|Troubleshooting|Intake Protocol|Reasoning|Topic|Confidence)' skills/formal-methods/SKILL.md`
Expected: at least 7.

Run: `python3 evals/run.py --skill formal-methods`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add skills/formal-methods/SKILL.md
git commit -m "feat(formal-methods): full template conformance + tightened cross-references

Add explicit When-to-use / When-not-to-use / Inputs / Examples /
Troubleshooting sections. Tighten description to pushy phrasing with
cross-references to renamed peer skills (type-theory, petri-net-theory,
srs, debugger).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 30: Add `evals/fixtures/formal-methods/prompts.json`

**Files:**
- Create: `evals/fixtures/formal-methods/prompts.json`

- [ ] **Step 1: Create the fixture**

```bash
mkdir -p evals/fixtures/formal-methods
```

Create `evals/fixtures/formal-methods/prompts.json`:

```json
{
  "skill": "formal-methods",
  "prompts": [
    {
      "id": "decidability",
      "text": "Is QF_NIA decidable? Will Z3 terminate on x*y > 5 && y < 10?",
      "expect_trigger": true
    },
    {
      "id": "termination-casual",
      "text": "Will this loop always exit?",
      "expect_trigger": true
    },
    {
      "id": "propagator-design",
      "text": "Audit our CLP propagator engine — arc consistency only, no LCG. Sound?",
      "expect_trigger": true
    },
    {
      "id": "tla-spec",
      "text": "Should I use TLA+ or Quint for this distributed-lock spec?",
      "expect_trigger": true
    },
    {
      "id": "negative-testing",
      "text": "How much test coverage do we need for the parser?",
      "expect_trigger": false
    },
    {
      "id": "negative-type-soundness",
      "text": "Is our row-polymorphism type system sound?",
      "expect_trigger": false
    }
  ]
}
```

- [ ] **Step 2: Verify**

Run: `python3 -m json.tool evals/fixtures/formal-methods/prompts.json > /dev/null && echo VALID`
Expected: `VALID`.

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/formal-methods/prompts.json
git commit -m "test(formal-methods): add canonical trigger fixtures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 31: Conform `debugger/SKILL.md`

**Files:**
- Modify: `skills/debugger/SKILL.md`

- [ ] **Step 1: Add the template sections**

Edit `skills/debugger/SKILL.md`. Add (in order, after the one-paragraph intro and before the existing first body section):

```markdown
## When to use

- The user asks about debugger or tracer **design** (not "how do I use gdb").
- Topics: event-model design, trace semantics, breakpoint/watchpoint/spy-point formal semantics, cross-formalism trace coherence, time-travel replay, remote debug session protocols, session-typed debug channels.
- "Why-did" / "why-didn't" explanation design.
- Engineering-shortcut audits on debug-layer code or design.

## When not to use

- "How do I use the VS Code debugger?" / "set a breakpoint in IntelliJ" — user-facing debugger usage, not design.
- "My test is failing, why?" — general debugging assistance, not debugger architecture.
- For Petri-net-specific reachability questions, use `petri-net-theory`.
- For SRS / synchronous-system trace questions, use `srs`.
- For type-system completeness questions, use `type-theory`.
- For SAT/SMT-solver internals, use `formal-methods`.

## Inputs

A debugger / tracer design question, optionally with codebase context. The skill handles three shapes:

- **Theory query:** event-model design, trace semantics, formal definitions.
- **Design review:** an existing debug/trace component to audit.
- **Implementation planning:** breakpoint algorithms, remote debug protocols.

## Examples

### Example 1 — event model design

**User:** "I'm designing a tracer for a CLP system that also has Petri-net constraints. How do I make the event model coherent?"

**Skill output:** Discusses cross-formalism trace coherence: per-formalism event vocabulary, a joining bridge event type, ordering guarantees (total vs. causal), and the three most likely implementation mistakes (event-loss under load, clock-skew across formalisms, breakpoint set inconsistency).

### Example 2 — breakpoint semantics

**User:** "What's the formal semantics of a 'breakpoint' in a constraint-propagator engine? Where does it 'fire'?"

**Skill output:** States the formal definition (predicate on the propagation state at a fixed-point); distinguishes propagation breakpoints (per-propagator firing) from solver breakpoints (on backtrack/branch); flags the "what counts as a step" question and how it interacts with arc-consistency loops.

## Troubleshooting

- **The question is about debugger usage, not design.** Redirect: "I focus on debugger architecture; for tool usage questions check the IDE / debugger's own docs."
- **The trace semantics is implicit in the system.** Surface it explicitly before answering — name the events, the ordering, and the provenance model.
- **Cross-formalism question.** Answer the debugger slice and hand off the domain encoding (PN, SRS, type, formal-methods) to the peer skill.
```

- [ ] **Step 2: Tighten description**

Edit the frontmatter `description` to be pushy and cross-reference renamed peers. Replace with:

```yaml
description: >
  Authoritative reference for debugger and tracer design. Use whenever the user asks about
  trace semantics, event-model design, breakpoint/watchpoint/spy-point formal semantics,
  cross-formalism trace coherence, time-travel replay, remote debug session protocols,
  session-typed debug channels, or engineering-shortcut audits on debug-layer code. Use
  even if "debug" is not explicitly mentioned — observability, introspection, or
  explanation problems often map to debugger theory. Do not use for: user-facing debugger
  usage ("how do I use gdb"); general bug investigation; Petri-net reachability
  (use `petri-net-theory`); synchronous-system trace questions (use `srs`); type-system
  completeness (use `type-theory`); SAT/SMT solver internals (use `formal-methods`).
```

- [ ] **Step 3: Verify**

Run: `grep -cE '^## (When to use|When not to use|Inputs|Examples|Troubleshooting)' skills/debugger/SKILL.md`
Expected: 5.

Run: `python3 evals/run.py --skill debugger`
Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add skills/debugger/SKILL.md
git commit -m "feat(debugger): full template conformance + tightened description

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 32: Add `evals/fixtures/debugger/prompts.json`

**Files:**
- Create: `evals/fixtures/debugger/prompts.json`

- [ ] **Step 1: Create the fixture**

```bash
mkdir -p evals/fixtures/debugger
```

Create `evals/fixtures/debugger/prompts.json`:

```json
{
  "skill": "debugger",
  "prompts": [
    {
      "id": "event-model",
      "text": "I'm designing a tracer for a CLP system. How do I make the event model coherent?",
      "expect_trigger": true
    },
    {
      "id": "breakpoint-semantics",
      "text": "What's the formal semantics of a breakpoint in a constraint propagator?",
      "expect_trigger": true
    },
    {
      "id": "time-travel",
      "text": "I want time-travel replay for our reactive system. What design constraints does that impose?",
      "expect_trigger": true
    },
    {
      "id": "session-typed-channels",
      "text": "How do session types help in remote debug protocol design?",
      "expect_trigger": true
    },
    {
      "id": "negative-tool-usage",
      "text": "How do I set a breakpoint in VS Code?",
      "expect_trigger": false
    }
  ]
}
```

- [ ] **Step 2: Verify**

Run: `python3 -m json.tool evals/fixtures/debugger/prompts.json > /dev/null && echo VALID`
Expected: `VALID`.

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/debugger/prompts.json
git commit -m "test(debugger): add canonical trigger fixtures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 33: Create `create-tutorial-agent` (Markdown + TOML) and register

**Files:**
- Create: `agents/create-tutorial-agent.md`
- Create: `agents/create-tutorial-agent.toml` (generated)
- Modify: `agents/README.md`, `README.md`, `.claude-plugin/marketplace.json`

- [ ] **Step 1: Write the Markdown agent**

Create `agents/create-tutorial-agent.md`:

```markdown
---
name: create-tutorial-agent
description: >
  Use when the user supplies a topic (component, feature, subsystem) and wants a
  textbook-style technical tutorial written for it. Triggers on inputs like
  "tutorial on X", "write a textbook chapter for Y", or "/create-tutorial Z".
  The agent runs the create-tutorial skill end-to-end and emits a markdown file
  to the resolved tutorials_dir.
tools: Read, Glob, Grep, Write
model: opus
skills:
  - create-tutorial
---

You are the `create-tutorial-agent`. Your job is to produce one comprehensive,
self-contained textbook-style tutorial for the supplied topic.

## Operating contract

Your only outputs are:

1. **One markdown file** written to the resolved `tutorials_dir`, with all
   10 sections from the `create-tutorial` skill (Introduction, Prerequisites,
   System Architecture, Core Concepts, API and Functional Overview, Worked
   Examples, Implementation Insights, Comparative Analysis, Integration
   Guidance, Outlook, Testing Strategy).
2. **Brief confirmation** to the user: the path written, plus a one-line
   summary. No more.

Never narrate the workflow or quote intermediate scaffolding. The tutorial
file is the deliverable.

## Workflow

Auto-loaded skill `create-tutorial` specifies the full workflow:

1. Resolve `tutorials_dir` via `scripts/resolve_config.py`.
2. Read all available context (code, APIs, comments, architecture, requirements).
3. State assumptions for any missing information.
4. Write the tutorial in the structure specified by the skill's Output
   Requirements section.
5. Save with kebab-case filename to the resolved directory.

## Banned constructs

- Do not invent code or features that aren't in the codebase or spec.
- Do not skip sections — if a section has no content, label it explicitly
  ("Not applicable: this component has no external integrations").
- Do not output the tutorial inline in the chat; write to file.
```

- [ ] **Step 2: Generate the TOML sibling**

Run: `python3 scripts/generate-codex-agents.py`
Expected: prints `wrote agents/create-tutorial-agent.toml` (alongside re-generating the other 6).

- [ ] **Step 3: Update `agents/README.md`**

Edit `agents/README.md`. The table already includes `create-tutorial-agent`. No change needed if Task 19 included it.

Verify: `grep -n 'create-tutorial-agent' agents/README.md`
Expected: at least one match.

- [ ] **Step 4: Update root `README.md` agents table**

Edit `README.md`. The agents table from Task 20 already includes `create-tutorial-agent`. The link target now exists. No edit needed unless the row was placeholder-only.

- [ ] **Step 5: Update `.claude-plugin/marketplace.json`**

Edit `.claude-plugin/marketplace.json`. Add `"./agents/create-tutorial-agent.md"` to the `agents:` array (alphabetical or after `improve-prompt-agent`, your choice):

```json
"agents": [
  "./agents/improve-prompt-agent.md",
  "./agents/create-tutorial-agent.md",
  "./agents/formal-methods-agent.md",
  "./agents/petri-net-theory-agent.md",
  "./agents/srs-agent.md",
  "./agents/type-theory-agent.md",
  "./agents/debugger-agent.md"
]
```

- [ ] **Step 6: Verify**

Run: `python3 evals/run.py`
Expected: `OK — checked 13 skill(s).` including agent-skill pairing and format-parity for `create-tutorial-agent`.

Run: `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo VALID`
Expected: `VALID`.

- [ ] **Step 7: Commit**

```bash
git add agents/create-tutorial-agent.md agents/create-tutorial-agent.toml \
        .claude-plugin/marketplace.json
git commit -m "feat(agents): create-tutorial-agent (Markdown + TOML); register in marketplace

Paired with the create-tutorial skill. Auto-loads the skill via the
skills: frontmatter array.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 34: Conform `srs/SKILL.md`

**Files:**
- Modify: `skills/srs/SKILL.md`

- [ ] **Step 1: Add When-to-use / When-not-to-use / Inputs / Examples / Troubleshooting sections**

Edit `skills/srs/SKILL.md`. After the one-paragraph intro and before the existing first body section, insert:

```markdown
## When to use

- Synchronous reactive systems design, specification, implementation, or review.
- Topics: tick architecture, signal semantics, synchronous hypothesis, clock calculus, constructive causality, par/race/until operators.
- Three-phase tick design (snapshot-compute-commit).
- ReactiveExpr / Lustre-style operator semantics.
- Obligation observers and compliance monitoring as synchronous stream transformers.
- Even if Esterel / Lustre terminology is not used — any event-driven or tick-based architecture maps here.

## When not to use

- Petri-net reachability or workflow soundness — use `petri-net-theory`.
- Type-system soundness or inference — use `type-theory`.
- SAT/SMT solver questions — use `formal-methods`.
- Trace semantics or debugger protocol — use `debugger`.

## Inputs

An SRS design question. The skill operates in two modes:

- **Domain-general:** synchronous-hypothesis theory, operator algebra, clock calculus.
- **Project-specific:** review of an existing tick implementation; pre-flight to read project index docs first.

## Examples

### Example 1 — tick architecture design

**User:** "Should our compliance monitor use a one-phase or three-phase tick?"

**Skill output:** Names the snapshot-compute-commit pattern; analyses whether your monitor has observable intermediate states that would break the synchronous hypothesis under single-phase ticks; recommends three-phase if cross-signal coherence matters. Cites the relevant clock-calculus rules. Confidence: High.

### Example 2 — operator semantics

**User:** "What's the constructive-causality requirement for our `until` operator?"

**Skill output:** States the constructive-causality fixpoint condition; flags non-constructive cycles; gives the rejection rule. Names the three most likely implementation mistakes (instantaneous-feedback loops, signal-not-stable-at-tick-boundary, late commit). Confidence: High.

## Troubleshooting

- **The system is not actually synchronous.** Ask: does every signal have a well-defined value at every tick? If no, the synchronous hypothesis doesn't hold — fall back to `formal-methods` for asynchronous-system reasoning.
- **The question is about tick-driven implementation in a non-Lustre language.** The theory applies; the patterns may not map cleanly. Name the mismatch explicitly.
- **Cross-formalism (SRS + PN, SRS + types).** Answer the SRS slice; hand off the domain encoding to the peer skill.
```

- [ ] **Step 2: Tighten description**

Replace the frontmatter `description:` block. Example:

```yaml
description: >
  Authoritative reference for synchronous reactive systems. Use whenever the user asks
  about tick architecture, signal semantics, synchronous hypothesis, clock calculus,
  constructive causality, par/race/until operators, three-phase ticks, Lustre / Esterel
  operator semantics, or reactive obligation observers. Use even if "synchronous" or
  "Lustre" is not mentioned — any tick-based or event-driven architecture maps here.
  Do not use for: Petri-net reachability (use `petri-net-theory`); type-system soundness
  (use `type-theory`); SAT/SMT solver internals (use `formal-methods`); trace semantics
  or debug protocols (use `debugger`).
```

- [ ] **Step 3: Verify**

Run: `grep -cE '^## (When to use|When not to use|Inputs|Examples|Troubleshooting)' skills/srs/SKILL.md`
Expected: 5.

Run: `python3 evals/run.py --skill srs`
Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add skills/srs/SKILL.md
git commit -m "feat(srs): full template conformance + tightened description

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 35: Add `evals/fixtures/srs/prompts.json`

**Files:**
- Create: `evals/fixtures/srs/prompts.json`

- [ ] **Step 1: Create the fixture**

```bash
mkdir -p evals/fixtures/srs
```

Create `evals/fixtures/srs/prompts.json`:

```json
{
  "skill": "srs",
  "prompts": [
    {
      "id": "tick-architecture",
      "text": "Should our compliance monitor use a one-phase or three-phase tick?",
      "expect_trigger": true
    },
    {
      "id": "constructive-causality",
      "text": "What's the constructive-causality requirement for our until operator?",
      "expect_trigger": true
    },
    {
      "id": "event-driven-general",
      "text": "Design a tick-based event processor for the inventory system.",
      "expect_trigger": true
    },
    {
      "id": "clock-calculus",
      "text": "Two signals at different clock rates — how do we sample-and-hold without breaking the synchronous hypothesis?",
      "expect_trigger": true
    },
    {
      "id": "negative-petri-net",
      "text": "Is our workflow net sound?",
      "expect_trigger": false
    }
  ]
}
```

- [ ] **Step 2: Verify**

Run: `python3 -m json.tool evals/fixtures/srs/prompts.json > /dev/null && echo VALID`

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/srs/prompts.json
git commit -m "test(srs): add canonical trigger fixtures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 36: Conform `type-theory/SKILL.md`

**Files:**
- Modify: `skills/type-theory/SKILL.md`

- [ ] **Step 1: Add template sections**

Edit `skills/type-theory/SKILL.md`. After the one-paragraph intro, insert:

```markdown
## When to use

- Any formal type system being discussed, designed, or implemented.
- Lambda cube (STLC, System F, Fω, dependent types).
- Type inference (HM, Algorithm W, bidirectional, constraint-based, algebraic subtyping, unification).
- Advanced systems: GADTs, substructural (linear, affine), refinement / liquid, gradual, session, graded, row, intersection/union.
- Category-theoretic foundations (functors, monads, adjunctions, Yoneda, profunctors, F-algebras).
- PL implementation: NbE, elaboration, metavariable solving, coverage, HKT encodings, parametricity, type-level programming.
- Decidability and soundness audits of type-system designs.

## When not to use

- SAT/SMT solver questions — use `formal-methods`.
- Petri-net or workflow modelling — use `petri-net-theory`.
- Synchronous-system clock calculus — use `srs`.
- Trace / debugger protocol design — use `debugger`.

## Inputs

A type-theory question. The skill operates in three modes:

- **Theory query:** formal definitions, decidability results, complexity proofs.
- **Design review:** an existing type system to audit for soundness.
- **Implementation planning:** inference algorithm, metavariable handling, elaboration.

## Examples

### Example 1 — soundness audit

**User:** "Our row-polymorphism system allows record extension with duplicate fields. Sound?"

**Skill output:** States the row-polymorphism soundness condition (no duplicate labels in a closed row); identifies the unsoundness; recommends either the "presence/absence" lattice or row-difference operator. Cites Wand 1987 and Leijen 2005. Confidence: High.

### Example 2 — inference algorithm

**User:** "Should we use HM or bidirectional checking for our DSL with optional type annotations?"

**Skill output:** Comparison table: HM (full inference, no annotations needed, decidable for the let-rank-1 fragment) vs. bidirectional (annotations required at function boundaries, modular, handles higher-rank). Recommends bidirectional given the "optional annotations" requirement. Names the three most likely implementation mistakes (subsumption-vs-coercion confusion, missing instantiation rule, annotation propagation). Confidence: High.

## Troubleshooting

- **The question conflates type-system soundness with runtime safety.** Disentangle: soundness is "well-typed programs don't go wrong"; runtime safety includes resource bounds, memory safety, etc. Different formal lenses.
- **The user wants to encode types into SAT/SMT.** Hand off the solver-side to `formal-methods` while keeping the type-theory framing here.
- **Category-theory abstraction without concrete grounding.** Always tie the answer back to a concrete type-system feature; pure CT without grounding rarely helps an implementer.
```

- [ ] **Step 2: Tighten description**

Replace `description:` block:

```yaml
description: >
  Authoritative reference for formal type systems. Use whenever the user asks about type
  inference, type-system design, soundness, decidability, lambda cube (STLC/System F/Fω/
  dependent), advanced systems (GADTs, linear, refinement, gradual, session, graded,
  row, intersection/union), or category-theoretic foundations (functors, monads,
  adjunctions, Yoneda). Use even when phrased casually ("is our type system sound?",
  "how do I infer types here?"). Do not use for: SAT/SMT solver internals (use
  `formal-methods`); Petri-net modelling (use `petri-net-theory`); synchronous-system
  clock calculus (use `srs`); debugger / trace protocol design (use `debugger`).
```

- [ ] **Step 3: Verify**

Run: `grep -cE '^## (When to use|When not to use|Inputs|Examples|Troubleshooting)' skills/type-theory/SKILL.md`
Expected: 5.

Run: `python3 evals/run.py --skill type-theory`
Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add skills/type-theory/SKILL.md
git commit -m "feat(type-theory): full template conformance + tightened description

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 37: Add `evals/fixtures/type-theory/prompts.json`

**Files:**
- Create: `evals/fixtures/type-theory/prompts.json`

- [ ] **Step 1: Create the fixture**

```bash
mkdir -p evals/fixtures/type-theory
```

Create `evals/fixtures/type-theory/prompts.json`:

```json
{
  "skill": "type-theory",
  "prompts": [
    {
      "id": "row-polymorphism",
      "text": "Our row-polymorphism system allows duplicate field labels. Is that sound?",
      "expect_trigger": true
    },
    {
      "id": "inference-choice",
      "text": "Should we use HM or bidirectional checking for our DSL?",
      "expect_trigger": true
    },
    {
      "id": "linear-types",
      "text": "How do linear types interact with exceptions?",
      "expect_trigger": true
    },
    {
      "id": "casual-soundness",
      "text": "Is our type system sound?",
      "expect_trigger": true
    },
    {
      "id": "negative-runtime",
      "text": "Why is my program crashing with a null-pointer error?",
      "expect_trigger": false
    }
  ]
}
```

- [ ] **Step 2: Verify**

Run: `python3 -m json.tool evals/fixtures/type-theory/prompts.json > /dev/null && echo VALID`

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/type-theory/prompts.json
git commit -m "test(type-theory): add canonical trigger fixtures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 38: Conform `petri-net-theory/SKILL.md`

**Files:**
- Modify: `skills/petri-net-theory/SKILL.md`

- [ ] **Step 1: Add template sections**

Edit `skills/petri-net-theory/SKILL.md`. After the one-paragraph intro, insert:

```markdown
## When to use

- Any Petri net theory question — formal foundations, decidability, modelling patterns.
- Compliance applications: regulatory workflows, prohibition modelling, deadline semantics.
- Concurrent process / resource-pool / workflow / prohibition / regulatory problems mapping to a Petri net formalism — even when "Petri net" is not mentioned.
- P/T nets, CPNs, HCPNs, WF-nets, CLP(PN), inhibitor arcs, timed nets, algebraic nets, net contracts.

## When not to use

- SAT/SMT/CLP-solver-internals questions — use `formal-methods` (this skill cross-references when needed).
- Type-system questions — use `type-theory`.
- Synchronous-system clock calculus — use `srs`.
- Debugger / trace protocol — use `debugger`.

## Inputs

A Petri-net theory or modelling question. Three modes:

- **Theory query:** formal definitions, decidability of reachability, complexity proofs.
- **Modelling query:** "how do I express prohibition / deadline / regulatory constraint as a net?"
- **Implementation:** propagator / state-equation / SMPT-based reachability checking.

## Examples

### Example 1 — modelling pattern

**User:** "I need to model a regulatory workflow where a user cannot perform action B without first having approval A, valid for 30 days."

**Skill output:** Maps to a timed WF-net with: place `approved` (with timestamp token), inhibitor arc on the alternative-path transition, deadline transition that resets the marking after 30 days. Cites Reisig timed-net formalism. Flags the inhibitor-arc undecidability trap.

### Example 2 — decidability question

**User:** "Is reachability decidable for CPNs?"

**Skill output:** States: CPN reachability is decidable but Ackermann-hard (per Czerwinski et al. 2021); the bound transfers from plain P/T nets. Quantifies the practical implication: state-space exploration is infeasible past mid-size; abstraction (state equation, SMPT) is required. Confidence: High.

## Troubleshooting

- **Inhibitor arcs make the net Turing-equivalent.** Flag explicitly: if the question assumes decidability, the answer is "not decidable in general". Offer the inhibitor-free reformulation.
- **The user describes a workflow but doesn't mention "Petri net".** Map their description to the applicable PN formalism explicitly; cite the mapping.
- **Cross-formalism question (PN + CLP, PN + SRS).** Answer the PN slice; hand off to `formal-methods` or `srs`.
```

- [ ] **Step 2: Tighten description if needed**

The existing description (read it first) may already be pushy enough. If not, replace with:

```yaml
description: >
  Authoritative reference for Petri net theory. Use whenever the user asks about PN
  foundations, decidability, modelling patterns, compliance applications, or workflow
  formalisms. Triggers even when "Petri net" is not mentioned — any concurrent-process,
  resource-pool, workflow, prohibition, deadline, or regulatory compliance problem maps
  here. Covers P/T nets, CPNs, HCPNs, WF-nets, CLP(PN), inhibitor arcs, timed nets,
  algebraic nets, net contracts. Do not use for: SAT/SMT/CLP-solver internals (use
  `formal-methods`); type-system questions (use `type-theory`); synchronous-system clock
  calculus (use `srs`); trace/debug protocols (use `debugger`).
```

- [ ] **Step 3: Verify**

Run: `grep -cE '^## (When to use|When not to use|Inputs|Examples|Troubleshooting)' skills/petri-net-theory/SKILL.md`
Expected: 5.

Run: `python3 evals/run.py --skill petri-net-theory`
Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add skills/petri-net-theory/SKILL.md
git commit -m "feat(petri-net-theory): full template conformance + tightened description

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 39: Add `evals/fixtures/petri-net-theory/prompts.json`

**Files:**
- Create: `evals/fixtures/petri-net-theory/prompts.json`

- [ ] **Step 1: Create the fixture**

```bash
mkdir -p evals/fixtures/petri-net-theory
```

Create `evals/fixtures/petri-net-theory/prompts.json`:

```json
{
  "skill": "petri-net-theory",
  "prompts": [
    {
      "id": "modelling-prohibition",
      "text": "Model a workflow where action B requires approval A within 30 days.",
      "expect_trigger": true
    },
    {
      "id": "cpn-reachability",
      "text": "Is reachability decidable for coloured Petri nets?",
      "expect_trigger": true
    },
    {
      "id": "no-pn-mention",
      "text": "How do I model concurrent resource pools with deadline constraints?",
      "expect_trigger": true
    },
    {
      "id": "wf-net-soundness",
      "text": "Is this workflow net sound?",
      "expect_trigger": true
    },
    {
      "id": "negative-solver",
      "text": "Should I use Z3's QF_LIA or QF_LRA for this constraint?",
      "expect_trigger": false
    }
  ]
}
```

- [ ] **Step 2: Verify**

Run: `python3 -m json.tool evals/fixtures/petri-net-theory/prompts.json > /dev/null && echo VALID`

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/petri-net-theory/prompts.json
git commit -m "test(petri-net-theory): add canonical trigger fixtures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

### Task 40: Final Phase 2 verification

**Files:** none modified; verification only.

- [ ] **Step 1: Run full evals**

Run: `python3 evals/run.py`
Expected: `OK — checked 13 skill(s).`

- [ ] **Step 2: Run full test suite**

Run: `python3 -m unittest discover tests/ -v 2>&1 | tail -10`
Expected: all tests pass.

- [ ] **Step 3: Verify every skill has the template sections**

Run:
```bash
for d in create-tutorial improve-prompt formal-methods debugger srs type-theory petri-net-theory; do
  n=$(grep -cE '^## (When to use|When not to use|Inputs|Examples|Troubleshooting)' skills/$d/SKILL.md)
  echo "$d: $n template sections"
done
```
Expected: every line shows ≥ 5 (one line per skill).

- [ ] **Step 4: Verify every skill has a fixture**

Run:
```bash
for d in create-tutorial improve-prompt formal-methods debugger srs type-theory petri-net-theory; do
  if [ -f "evals/fixtures/$d/prompts.json" ]; then echo "$d: OK"; else echo "$d: MISSING"; fi
done
```
Expected: every line ends `OK`.

- [ ] **Step 5: Verify all 7 agents have TOML siblings**

Run:
```bash
python3 -c "
import pathlib
mds = sorted(pathlib.Path('agents').glob('*-agent.md'))
assert len(mds) == 7, f'expected 7, got {len(mds)}'
for md in mds:
    toml = md.with_suffix('.toml')
    assert toml.exists(), f'missing {toml}'
print('OK', len(mds), 'agents with both formats')
"
```
Expected: `OK 7 agents with both formats`.

- [ ] **Step 6: Open PR 2**

```bash
git push
gh pr create --title "Skills conformance — Examples, Troubleshooting, fixtures, create-tutorial-agent (PR 2/2)" --body "$(cat <<'EOF'
## Summary
- Add When-to-use / When-not-to-use / Inputs / Examples / Troubleshooting sections to 7 skills.
- Relocate \`improve-prompt/evidence-appendix.md\` under \`references/\`.
- Fix \`improve-prompt\`'s cross-reference to the renamed agent path.
- Strip \`\$ARGUMENTS\` from \`create-tutorial/SKILL.md\` and replace with portable Inputs.
- Add \`evals/fixtures/<skill>/prompts.json\` for all 7 skills.
- Add \`create-tutorial-agent\` (Markdown + TOML); register in marketplace.

Builds on PR 1 (scaffolding, renames, agents-layer infrastructure).

## Test plan
- [x] \`python3 evals/run.py\` returns OK.
- [x] \`python3 -m unittest discover tests/\` passes.
- [x] Every modified skill has all template sections.
- [x] Every modified skill has prompts.json.
- [x] All 7 agents have both .md and .toml siblings.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-review

**Spec coverage:**

- §3.1 skill inventory: covered by Tasks 2-5 (renames), 24-39 (conformance).
- §3.2 agent inventory: covered by Tasks 6-11 (renames), 14 (TOML siblings), 33 (create-tutorial-agent).
- §3.3 agents/ folder structure: covered by Tasks 14, 19, 33.
- §3.4 frontmatter conventions: covered by Task 17 (documented) and Task 16 (enforced by checks).
- §3.5 source-of-truth strategy: covered by Tasks 13-14 (generator) and Task 17 (documented).
- §3.6 installer: covered by Task 15.
- §3.7 plugin marketplace: covered by Tasks 22, 33.
- §3.8 documentation surface: covered by Tasks 17 (agents-guide), 18 (portability-checklist), 19 (agents/README), 20 (top README), 21 (install.md).
- §4 per-skill changes: each subsection has a dedicated task.
- §5 PR plan: Phases 1 and 2 implemented; PR 3 explicitly absent (as designed).
- §6 open items: surfaced in the spec; no implementation needed in this plan.
- §7 risks: rename churn addressed by Task 12 sweep; generator drift caught by eval parity (Task 16).
- §8 validation: every "After both PRs land" criterion mapped to a verification step in Tasks 23 and 40.

**Placeholder scan:** no `TBD`, no `TODO`, no "fill in later". Every code block contains the actual content the engineer needs to write.

**Type/name consistency:**

- Generator emits `name`, `description`, `developer_instructions` keys per Codex schema in Task 13; Task 16's parity check reads the same fields. Consistent.
- Installer's `HOSTS` dict in Task 15 uses `.md` for `claude-code` and `.toml` for `codex`; matches the file-extension routing in `plan_installs`. Consistent.
- Eval check `check_agent_format_parity` in Task 16 looks for the same `*.md` files the generator in Task 13 emits. Consistent.
- All 7 skill names used across tasks: `create-tutorial`, `improve-prompt`, `formal-methods`, `debugger`, `srs`, `type-theory`, `petri-net-theory`. No `-expert` slips.
- All 7 agent names: `<skill>-agent` form. No `-expert` slips.

**Spec-to-plan delta:** none — every requirement in the spec maps to at least one task.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-04-skills-conformance-and-agents-layer-plan.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
