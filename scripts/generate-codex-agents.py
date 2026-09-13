#!/usr/bin/env python3
"""Generate Codex CLI TOML agents from Claude Code Markdown agents.

Reads each agents/<name>.md, extracts YAML frontmatter and Markdown body,
and emits a TOML file with the same basename: agents/<name>.toml.

Mapping:
    frontmatter name        -> toml name
    frontmatter description -> toml description
    body                    -> toml developer_instructions (multi-line)
    frontmatter skills      -> [skills.config] block (if present)
    frontmatter tools       -> dropped (Codex has its own tool model)
    frontmatter model       -> dropped (Claude Code model tiers like "opus"
                               are not Codex model IDs; map explicitly in
                               docs/agents-guide.md if a mapping is ever needed)

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
        # A YAML block-sequence item ("- foo"), at any indent (including
        # column 0 — valid YAML for a sequence directly under its key).
        list_m = re.match(r"^\s*-\s+(.*)$", raw)
        if list_m:
            if current_list is None:
                raise ValueError(f"list item without key context: {raw!r}")
            current_list.append(list_m.group(1).strip())
            continue
        m = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", raw)
        if m:
            key, value = m.group(1), m.group(2).strip()
            current_key = key
            current_list = None
            if value and value[0] in ">|":
                # Folded (>) or literal (|) block scalar. Chomping/indentation
                # indicators (-, +, digits) may follow the indicator character
                # itself; ignore them and accumulate from continuation lines.
                fm[key] = ""
            elif value == "":
                fm[key] = []
                current_list = fm[key]
            else:
                fm[key] = value
            continue
        # Not a key line and not a list item: only valid as a continuation
        # of an in-progress folded/literal scalar value.
        if current_key is not None and isinstance(fm.get(current_key), str):
            fm[current_key] = (fm[current_key] + " " + raw.strip()).strip()
            continue
        raise ValueError(f"unrecognised frontmatter line: {raw!r}")
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
    # frontmatter `model` (a Claude Code model tier like "opus") is
    # deliberately dropped here, same as `tools` above it in the docstring:
    # Codex has its own model IDs and a Claude tier is meaningless there.
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
    """Convert one agent .md to its .toml. Raises ValueError on any parse
    or emission failure — the caller must count that as a failed file, not
    a silent skip (a stale .toml must not survive a bad source file)."""
    text = md_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
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
