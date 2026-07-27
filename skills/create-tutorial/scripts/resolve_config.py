#!/usr/bin/env python3
"""Resolve configuration values for the create-tutorial skill.

Resolution order (first match wins):
    1. Environment variable CREATE_TUTORIAL_<UPPERCASE_KEY>
    2. <project_root>/.create-tutorial/config.yaml
    3. <project_root>/.agents/dev-skills.yaml (shared conventions)
    4. ~/.config/create-tutorial/config.yaml  (only for non-path keys)
    5. Built-in default

Path keys (tutorials_dir) are project-only -- never read from the user-level
layer.

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
import read_shared_conventions  # type: ignore  # noqa: E402


def expand(value):
    return os.path.expandvars(os.path.expanduser(value))


def _compose_from_shared(shared, project_root):
    """Return path overrides for create-tutorial derived from the shared file.

    Mapping:
        tutorials_dir <- <docs_root>/skills.create-tutorial.subdir
                         (default subdir = "tutorials")

    `project_root` is unused here but kept for signature parity with the
    other skills' _compose_from_shared helpers.
    """
    if shared is None:
        return {}
    docs_root = shared.get("docs_root", "doc")
    block = (shared.get("skills") or {}).get("create-tutorial", {}) or {}
    subdir = block.get("subdir") or "tutorials"
    return {"tutorials_dir": str(Path(docs_root) / subdir)}


def resolve_all():
    proot = configure.find_project_root()
    project_values = (
        configure.load_existing(configure.project_config_path(proot))
        if proot
        else {}
    )
    user_values = configure.load_existing(configure.user_config_path())
    shared = read_shared_conventions.load(proot) if proot else None
    shared_overrides = _compose_from_shared(shared, proot)

    raw = configure.resolve(project_values, user_values)
    # Layer precedence: env > project-skill > shared > user-skill > default.
    for k in list(raw):
        env_v = os.environ.get(configure.ENV_PREFIX + k.upper())
        if env_v:
            continue  # env wins.
        if k in project_values and project_values[k]:
            continue  # project-skill wins.
        if k in shared_overrides:
            raw[k] = shared_overrides[k]

    resolved = {}
    for k, v in raw.items():
        if k in configure.PATH_KEYS and v:
            resolved[k] = expand(v)
        else:
            resolved[k] = v
    return resolved


def main():
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
            print("%s=%s" % (k, v))
        return 0

    if not args.key:
        p.error("provide a key, or use --all / --project-root")

    if args.key not in resolved:
        print("unknown key: %s" % args.key, file=sys.stderr)
        print("known keys: %s" % ", ".join(resolved), file=sys.stderr)
        return 2

    print(resolved[args.key])
    return 0


if __name__ == "__main__":
    sys.exit(main())
