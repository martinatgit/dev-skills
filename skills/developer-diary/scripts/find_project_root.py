#!/usr/bin/env python3
"""Locate the current project root by walking upward from the cwd.

A directory is treated as a project root if it contains any of these markers:

    VCS directories:    .git, .hg, .svn
    Language manifests: package.json, pyproject.toml, Cargo.toml, go.mod,
                        deno.json, pom.xml, build.gradle, build.gradle.kts,
                        Gemfile, mix.exs
    Agent config dirs:  .agents, .claude, .codex, .cursor, .windsurf
    Agent manifests:    AGENTS.md, CLAUDE.md, CODEX.md

The walk stops at the filesystem root or the user's home directory, whichever
comes first.

Usage:
    python3 scripts/find_project_root.py [--from <path>] [--mark <name> ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_MARKERS = (
    ".git", ".hg", ".svn",
    "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "deno.json",
    "pom.xml", "build.gradle", "build.gradle.kts", "Gemfile", "mix.exs",
    ".agents", ".claude", ".codex", ".cursor", ".windsurf",
    "AGENTS.md", "CLAUDE.md", "CODEX.md",
)


def find_project_root(start: Path, markers: tuple[str, ...]) -> Path | None:
    home = Path.home().resolve()
    cur = start.resolve()
    while True:
        for marker in markers:
            if (cur / marker).exists():
                return cur
        parent = cur.parent
        if parent == cur:
            return None
        if cur == home:
            return None
        cur = parent


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from", dest="start", default=None)
    p.add_argument("--mark", action="append", default=None)
    args = p.parse_args()

    start = Path(args.start) if args.start else Path.cwd()
    markers = tuple(args.mark) if args.mark else DEFAULT_MARKERS

    root = find_project_root(start, markers)
    if root is None:
        print(
            f"no project root found at or above {start}; "
            f"looked for: {', '.join(markers[:6])}, ...",
            file=sys.stderr,
        )
        return 1
    print(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
