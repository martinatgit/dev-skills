#!/usr/bin/env python3
"""Refresh the per-skill copies of the stamped scripts from the template.

The canonical copies live at `template/scripts/<name>`. This script copies
each byte-for-byte into every skill that ships that script. Run after
editing a template; commit the per-skill copies.

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

STAMPED_SCRIPTS = ("read_shared_conventions.py", "find_project_root.py")


def find_skill_script_dirs(skills_root: Path):
    return sorted(p for p in skills_root.glob("*/scripts") if p.is_dir())


def main() -> int:
    epilog = """\
Examples:
    python3 scripts/refresh-shared-reader.py
    python3 scripts/refresh-shared-reader.py --repo-root <path>  # for tests
    python3 scripts/refresh-shared-reader.py --check             # dry-run
"""
    parser = argparse.ArgumentParser(
        description="Refresh per-skill copies of the stamped scripts "
                    "from the canonical template.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    default_root = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--repo-root", default=str(default_root),
        help="Path to the repo root (default: parent of this script).",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Report drift without writing.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    skills_root = repo_root / "skills"

    drift = []
    copied = []
    missing = []
    for filename in STAMPED_SCRIPTS:
        template = repo_root / "template" / "scripts" / filename
        if not template.exists():
            missing.append(str(template.relative_to(repo_root)))
            continue
        canonical = template.read_bytes()
        for scripts_dir in find_skill_script_dirs(skills_root):
            target = scripts_dir / filename
            if not target.exists():
                continue  # Skill does not ship this helper; not drift.
            if target.read_bytes().replace(b"\r\n", b"\n") == \
                    canonical.replace(b"\r\n", b"\n"):
                continue
            if args.check:
                drift.append(str(target.relative_to(repo_root)))
            else:
                shutil.copyfile(str(template), str(target))
                copied.append(str(target.relative_to(repo_root)))

    if missing:
        print("error: template(s) not found: %s" % ", ".join(missing),
              file=sys.stderr)
        return 2

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
