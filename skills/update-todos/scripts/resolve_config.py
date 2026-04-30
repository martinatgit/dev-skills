#!/usr/bin/env python3
"""Resolve configuration values for the update-todos skill.

Resolution order (first match wins):
    1. Environment variable UPDATE_TODOS_<UPPERCASE_KEY>
    2. <project_root>/.update-todos/config.yaml
    3. ~/.config/update-todos/config.yaml  (only for non-path keys)
    4. Built-in default

The path key (root_dir) is project-only — never read from the user-level
layer. If unresolved, the caller (the agent following an action file) must
prompt the user and persist the answer to project-local config before
continuing.

Usage:
    python3 scripts/resolve_config.py <key>
    python3 scripts/resolve_config.py --all
    python3 scripts/resolve_config.py --project-root
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
    return {k: (expand(v) if k in configure.PATH_KEYS and v else v)
            for k, v in raw.items()}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("key", nargs="?")
    p.add_argument("--all", action="store_true")
    p.add_argument("--project-root", action="store_true")
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
