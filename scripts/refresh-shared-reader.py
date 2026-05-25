#!/usr/bin/env python3
"""Refresh the per-skill copies of `read_shared_conventions.py` from the template.

The canonical reader lives at `template/scripts/read_shared_conventions.py`.
This script copies it byte-for-byte into every skill that has a `scripts/`
directory. Run after editing the template; commit the per-skill copies.

`evals/run.py` enforces drift detection (byte-compare each copy against the
template), so forgetting to run this will fail the eval.

Usage:
    python3 scripts/refresh-shared-reader.py
    python3 scripts/refresh-shared-reader.py --repo-root <path>  # for tests
    python3 scripts/refresh-shared-reader.py --check             # dry-run
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def find_skill_script_dirs(skills_root: Path):
    return sorted(p for p in skills_root.glob("*/scripts") if p.is_dir())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parent.parent
    p.add_argument("--repo-root", default=str(default_root))
    p.add_argument("--check", action="store_true",
                   help="Report drift without writing.")
    args = p.parse_args()

    repo_root = Path(args.repo_root).resolve()
    template = repo_root / "template" / "scripts" / "read_shared_conventions.py"
    skills_root = repo_root / "skills"

    if not template.exists():
        print("error: template not found at %s" % template, file=sys.stderr)
        return 2

    canonical = template.read_bytes()
    drift = []
    copied = []
    for scripts_dir in find_skill_script_dirs(skills_root):
        target = scripts_dir / "read_shared_conventions.py"
        if target.exists() and target.read_bytes() == canonical:
            continue
        if args.check:
            drift.append(str(target.relative_to(repo_root)))
        else:
            shutil.copyfile(str(template), str(target))
            copied.append(str(target.relative_to(repo_root)))

    if args.check:
        if drift:
            print("drift detected:", file=sys.stderr)
            for path in drift:
                print("  - " + path, file=sys.stderr)
            print("\nRun: python3 scripts/refresh-shared-reader.py",
                  file=sys.stderr)
            return 1
        print("OK -- no drift.")
        return 0

    if copied:
        for path in copied:
            print("updated " + path)
    else:
        print("OK -- all per-skill copies already match the template.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
