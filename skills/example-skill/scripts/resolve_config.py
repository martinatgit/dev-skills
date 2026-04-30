#!/usr/bin/env python3
"""Resolve a single configuration value for the example-skill.

Resolution order (first match wins):
    1. Environment variable EXAMPLE_SKILL_<UPPERCASE_KEY>
    2. <project_root>/.example-skill/config.yaml
    3. ~/.config/example-skill/config.yaml  (only for non-path keys)
    4. Built-in default

Path-typed keys never fall back to the user-level layer — that prevents
project state from leaking across projects when the skill is installed
user-scope but invoked inside different repos.

Usage:
    python3 scripts/resolve_config.py <key>
    python3 scripts/resolve_config.py --all
    python3 scripts/resolve_config.py --project-root   # print detected root
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import configure  # type: ignore  # noqa: E402


def expand(value: str) -> str:
    return os.path.expandvars(os.path.expanduser(value))


def resolve_all() -> dict[str, str]:
    proot = configure.find_project_root()
    project_values = (configure.load_existing(configure.project_config_path(proot))
                      if proot else {})
    user_values = configure.load_existing(configure.user_config_path())
    raw = configure.resolve(project_values, user_values)
    return {k: (expand(v) if k in configure.PATH_KEYS else v)
            for k, v in raw.items()}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("key", nargs="?", help="Config key to resolve.")
    p.add_argument("--all", action="store_true",
                   help="Print every key=value to stdout.")
    p.add_argument("--project-root", action="store_true",
                   help="Print the detected project root, or empty if none.")
    args = p.parse_args()

    if args.project_root:
        proot = configure.find_project_root()
        print(proot if proot else "")
        return 0 if proot else 1

    resolved = resolve_all()

    if args.all:
        for k, v in resolved.items():
            print(f"{k}={v}")
        return 0

    if not args.key:
        p.error("provide a key, or use --all / --project-root")

    if args.key not in resolved:
        print(f"unknown key: {args.key}", file=sys.stderr)
        print(f"known keys: {', '.join(resolved)}", file=sys.stderr)
        return 2

    print(resolved[args.key])
    return 0


if __name__ == "__main__":
    sys.exit(main())
