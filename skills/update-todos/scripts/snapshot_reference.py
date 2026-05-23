#!/usr/bin/env python3
"""Snapshot a file reference for the update-todos skill.

Two modes driven by --lines:
    snapshot_reference.py <path>                  # lightweight
    snapshot_reference.py <path> --lines N-M      # heavy

Emits a YAML fragment to stdout suitable for splicing into a TODO file's
references[] entry. Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import subprocess
import sys
from pathlib import Path

EXCERPT_HARD_LIMIT = 50
NULL_BYTE_PROBE_BYTES = 8192


def parse_lines(spec: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec)
    if not m:
        raise ValueError(f"invalid --lines value: {spec!r}; expected N or N-M")
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else start
    if start < 1 or end < start:
        raise ValueError(f"invalid --lines range: {spec!r}; need 1 <= start <= end")
    return start, end


def is_binary(path: Path) -> bool:
    try:
        chunk = path.open("rb").read(NULL_BYTE_PROBE_BYTES)
    except OSError:
        return False
    return b"\x00" in chunk


def git_short_head(cwd: Path) -> str | None:
    try:
        ws = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        if ws.returncode != 0 or ws.stdout.strip() != "true":
            return None
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip() or None
    except OSError:
        return None


def read_excerpt(path: Path, start: int, end: int) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    all_lines = text.splitlines()
    if start > len(all_lines):
        raise ValueError(f"start line {start} exceeds file length {len(all_lines)}")
    if end > len(all_lines):
        end = len(all_lines)
    return all_lines[start - 1:end]


def heading_level(line: str) -> int:
    """Return 1 for '# x', 2 for '## x', etc. 0 if not a markdown heading."""
    s = line.lstrip()
    if not s.startswith("#"):
        return 0
    count = 0
    for ch in s:
        if ch == "#":
            count += 1
        else:
            break
    if count == 0 or count > 6:
        return 0
    if len(s) > count and s[count] != " ":
        return 0
    return count


def find_anchor_section(path: Path, anchor: str) -> tuple[int, int] | None:
    """Find a markdown heading containing the anchor substring (case-sensitive).
    Return (start_line, end_line) 1-indexed inclusive. End is the line BEFORE
    the next heading of same-or-higher level, OR start + EXCERPT_HARD_LIMIT - 1,
    whichever comes first. None if no matching heading found."""
    text = path.read_text(encoding="utf-8", errors="replace")
    all_lines = text.splitlines()
    for i, ln in enumerate(all_lines):
        lvl = heading_level(ln)
        if lvl and anchor in ln:
            start = i + 1
            max_end = min(start + EXCERPT_HARD_LIMIT - 1, len(all_lines))
            for j in range(i + 1, len(all_lines)):
                jl = heading_level(all_lines[j])
                if jl and jl <= lvl:
                    return (start, min(j, max_end))
            return (start, max_end)
    return None


def emit_yaml_block(lines: list[str], indent: str = "    ") -> str:
    body = "\n".join(f"{indent}  {ln}" for ln in lines) if lines else ""
    return f"{indent}text: |\n{body}\n" if lines else f"{indent}text: |\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", help="File path (absolute, or relative to cwd)")
    p.add_argument("--lines", help="Line range as N or N-M (heavy mode)")
    p.add_argument("--anchor",
                   help="Spec anchor (e.g. '§4.2.1'). When provided in heavy mode "
                        "and --lines is omitted, the excerpt is auto-derived from "
                        "the matching markdown heading through the next same-or-"
                        "higher-level heading (capped at the 50-line hard limit).")
    p.add_argument("--kind", choices=["code", "spec", "diary"], default="code",
                   help="Reference kind. 'diary' suppresses excerpt extraction in "
                        "heavy mode (diary nodes are append-only; drift detection "
                        "against them is meaningless). 'spec' and 'code' both "
                        "produce excerpts.")
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"error: {path}: file not found", file=sys.stderr)
        return 2

    today = _dt.date.today().isoformat()
    sha = git_short_head(path.parent if path.is_absolute() else Path.cwd())
    sha_line = f"captured-at-sha: {sha or 'null'}"
    unavailable_line = "" if sha else "git-unavailable: true\n"

    if args.lines is None and not args.anchor:
        out = f"{sha_line}\ncaptured-at: {today}\n{unavailable_line}"
        sys.stdout.write(out)
        return 0

    if args.kind == "diary":
        # Diary nodes are append-only by contract. Heavy mode for a diary
        # reference records the SHA only; no excerpt is extracted (drift
        # detection against append-only files is meaningless).
        out = (
            f"clarified-at-sha: {sha or 'null'}\n"
            f"clarified-at: {today}\n"
            f"kind: diary\n"
        )
        if not sha:
            out += "git-unavailable: true\n"
        sys.stdout.write(out)
        return 0

    if args.lines is None and args.anchor:
        # Anchor-only heavy mode: derive line range from the matching heading.
        if is_binary(path):
            print(f"error: anchor extraction not supported on binary file: {path}",
                  file=sys.stderr)
            return 2
        match = find_anchor_section(path, args.anchor)
        if match is None:
            print(f"error: anchor {args.anchor!r} not found in {path}",
                  file=sys.stderr)
            return 2
        start, end = match
    else:
        try:
            start, end = parse_lines(args.lines)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    span = end - start + 1
    if span > EXCERPT_HARD_LIMIT:
        print(
            f"error: excerpt span {span} exceeds hard limit of {EXCERPT_HARD_LIMIT} lines. "
            f"Narrow the reference's `lines` field or split into multiple references.",
            file=sys.stderr,
        )
        return 2

    if is_binary(path):
        out = (
            f"clarified-at-sha: {sha or 'null'}\n"
            f"clarified-at: {today}\n"
            f"binary: true\n"
            f"excerpts: []\n"
        )
        if not sha:
            out += "git-unavailable: true\n"
        sys.stdout.write(out)
        return 0

    try:
        lines = read_excerpt(path, start, end)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = (
        f"clarified-at-sha: {sha or 'null'}\n"
        f"clarified-at: {today}\n"
        f"excerpts:\n"
        f"  - lines: {start}-{end}\n"
        + emit_yaml_block(lines, indent="    ")
    )
    if not sha:
        out += "git-unavailable: true\n"
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
