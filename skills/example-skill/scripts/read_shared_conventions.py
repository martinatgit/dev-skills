#!/usr/bin/env python3
"""Read the project-scope shared conventions file `.agents/dev-skills.yaml`.

This module is the canonical source. The repo-level refresher
(`scripts/refresh-shared-reader.py`) copies it byte-for-byte into every shipped
skill's `scripts/` folder. Skills then run entirely from their own scripts
directory — no cross-skill imports.

The reader validates a mandatory `schema: dev-skills/v1` discriminator at the
top of the file. Files missing the marker, with a wrong marker, or with parse
errors are skipped silently (with a single stderr warning per process), so the
shared layer fails open: a skill never refuses to run because a foreign file
appeared. Use the `DEV_SKILLS_CONFIG_FILE` env var to override the default path.

The parser supports a tightly-constrained YAML subset: top-level scalar keys
plus a one-level-nested map (the `skills:` block, with one map per skill name,
each containing scalar leaves). No lists. No anchors. No multi-line strings.
The `#` character is always treated as a comment delimiter, even inside quoted
values; do not put `#` inside any value in the schema.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SCHEMA_VERSION = "dev-skills/v1"
DEFAULT_DOCS_ROOT = "doc"

# Module-level set to make warnings idempotent within a single process.
_WARNED: set = set()


def _warn_once(msg: str) -> None:
    if msg in _WARNED:
        return
    _WARNED.add(msg)
    print(msg, file=sys.stderr)


def _resolve_path(project_root: Path) -> Path:
    """Return the path to read. Env var wins; default is .agents/dev-skills.yaml."""
    env = os.environ.get("DEV_SKILLS_CONFIG_FILE")
    if env:
        return Path(env)
    return Path(project_root) / ".agents" / "dev-skills.yaml"


def _parse_yaml(text: str):
    """Parse the constrained YAML subset documented at module level."""
    parsed = []
    for raw in text.splitlines():
        stripped = raw.split("#", 1)[0].rstrip()
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip())
        content = stripped.strip()
        if ":" not in content:
            raise ValueError("line missing ':': %r" % raw)
        key, _, value = content.partition(":")
        parsed.append((indent, key.strip(), value.strip().strip('"').strip("'")))

    root: dict = {}
    stack = [(-1, root)]
    i = 0
    while i < len(parsed):
        indent, key, value = parsed[i]
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value:
            parent[key] = value
        else:
            # Empty value — could be a nested map header. Peek ahead.
            if i + 1 < len(parsed) and parsed[i + 1][0] > indent:
                child: dict = {}
                parent[key] = child
                stack.append((indent, child))
            else:
                parent[key] = ""
        i += 1
    return root


def load(project_root):
    """Return parsed conventions, or None if the file is missing/foreign/malformed.

    Args:
        project_root: Path to the project root. The file is resolved as
            DEV_SKILLS_CONFIG_FILE env var if set, else
            <project_root>/.agents/dev-skills.yaml.

    Returns:
        dict with keys 'docs_root' (str) and 'skills' (dict of skill_name -> dict),
        or None if the file does not exist, lacks the schema discriminator, or
        fails to parse.
    """
    path = _resolve_path(Path(project_root))
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        _warn_once("could not read %s: %s" % (path, e))
        return None
    except UnicodeDecodeError as e:
        _warn_once("could not decode %s as UTF-8: %s; ignoring" % (path, e))
        return None
    try:
        data = _parse_yaml(raw)
    except ValueError as e:
        _warn_once("could not parse %s: %s; ignoring" % (path, e))
        return None
    if data.get("schema") != SCHEMA_VERSION:
        _warn_once(
            "found %s without %s schema marker; ignoring" % (path, SCHEMA_VERSION)
        )
        return None
    skills = data.get("skills") or {}
    if not isinstance(skills, dict):
        _warn_once("skills: block in %s is not a map; ignoring" % path)
        skills = {}
    return {
        "docs_root": data.get("docs_root") or DEFAULT_DOCS_ROOT,
        "skills": skills,
    }
