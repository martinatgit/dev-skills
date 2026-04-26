#!/usr/bin/env python3
"""
Minimal eval runner skeleton.

Extend this to shell out to each target agent and compare outputs against
fixtures. This stub validates repo structure and prints a summary so that
`python3 evals/run.py` is always a safe first check.

Usage:
    python3 evals/run.py [--skill <skill-name>]
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"


def check_frontmatter(skill_md: Path) -> list[str]:
    """Return a list of problems with a SKILL.md's frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return [f"{skill_md}: missing opening --- frontmatter delimiter"]

    end = text.find("\n---\n", 4)
    if end == -1:
        return [f"{skill_md}: missing closing --- frontmatter delimiter"]

    frontmatter = text[4:end]
    problems: list[str] = []

    if not re.search(r"^name:\s*\S", frontmatter, re.MULTILINE):
        problems.append(f"{skill_md}: frontmatter missing 'name'")
    if not re.search(r"^description:\s*\S", frontmatter, re.MULTILINE):
        problems.append(f"{skill_md}: frontmatter missing 'description'")

    allowed = {"name", "description"}
    for line in frontmatter.splitlines():
        m = re.match(r"^([a-zA-Z_][\w-]*):", line)
        if m and m.group(1) not in allowed:
            problems.append(
                f"{skill_md}: frontmatter contains non-spec key '{m.group(1)}' "
                f"(spec allows only: {', '.join(sorted(allowed))})"
            )
    return problems


def check_marketplace() -> list[str]:
    if not MARKETPLACE.exists():
        return [f"{MARKETPLACE}: missing"]
    try:
        json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{MARKETPLACE}: invalid JSON ({e})"]
    return []


def check_no_placeholders() -> list[str]:
    problems: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "assets" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        if "{{" in text and "}}" in text:
            problems.append(f"{path}: contains unfilled placeholder {{{{...}}}}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", help="Check one skill only (by folder name)")
    args = parser.parse_args()

    all_problems: list[str] = []

    if args.skill:
        skill_md = SKILLS_DIR / args.skill / "SKILL.md"
        if not skill_md.exists():
            print(f"error: no such skill: {args.skill}", file=sys.stderr)
            return 2
        targets = [skill_md]
    else:
        targets = sorted(SKILLS_DIR.glob("*/SKILL.md"))
        all_problems.extend(check_marketplace())
        all_problems.extend(check_no_placeholders())

    for skill_md in targets:
        all_problems.extend(check_frontmatter(skill_md))

    if all_problems:
        print(f"FAIL — {len(all_problems)} problem(s):")
        for p in all_problems:
            print(f"  - {p}")
        return 1

    print(f"OK — checked {len(targets)} skill(s).")
    print()
    print("This runner only validates structure. For real evals:")
    print("  1. Add test prompts under evals/fixtures/<skill-name>/prompts.json")
    print("  2. Extend run.py to invoke each target agent and compare outputs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
