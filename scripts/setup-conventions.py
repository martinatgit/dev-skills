#!/usr/bin/env python3
"""Write the project-scope shared conventions file `.agents/dev-skills.yaml`.

Pre-flight collision check: refuses to overwrite an existing file that lacks
the `schema: dev-skills/v1` marker. Set DEV_SKILLS_CONFIG_FILE to write to an
alternate path.

Usage:
    python3 scripts/setup-conventions.py                                  # interactive
    python3 scripts/setup-conventions.py --non-interactive --docs-root X
    python3 scripts/setup-conventions.py --print
    python3 scripts/setup-conventions.py --repair
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCHEMA_VERSION = "dev-skills/v1"

# Map skill name -> {key_in_yaml: cli_flag_suffix}.
# Path-shaped: subdir / filename. Non-path tunables: passed through.
# Tracks what the installer can write into the per-skill block.
SKILL_SCHEMA = {
    "developer-diary": {
        "subdir": None,
        "node_token_limit": None,
    },
    "update-todos": {
        "subdir": None,
        "default_expiry_days": None,
    },
    "terminology": {
        "filename": None,
        "validation_timeout": None,
    },
    "create-tutorial": {
        "subdir": None,
    },
}


def _find_project_root(start: Path) -> Path:
    here = Path(__file__).resolve().parent
    # find_project_root lives in skills/<any>/scripts/ (any copy works) and in
    # template/scripts/. Use the example-skill copy as the canonical source.
    fpr_path = here.parent / "skills" / "example-skill" / "scripts"
    sys.path.insert(0, str(fpr_path))
    import find_project_root as fpr  # type: ignore
    root = fpr.find_project_root(start, fpr.DEFAULT_MARKERS)
    if root is None:
        print("error: no project root found at or above %s" % start, file=sys.stderr)
        sys.exit(2)
    return root


def _target_path(project_root: Path) -> Path:
    env = os.environ.get("DEV_SKILLS_CONFIG_FILE")
    if env:
        return Path(env)
    return project_root / ".agents" / "dev-skills.yaml"


def _pre_flight(target: Path) -> None:
    if not target.exists():
        return
    text = target.read_text(encoding="utf-8")
    if "schema: dev-skills/v1" not in text:
        print(
            "error: %s exists but is not a dev-skills/v1 file.\n"
            "Either remove it, or set DEV_SKILLS_CONFIG_FILE=<alt-path> and re-run."
            % target,
            file=sys.stderr,
        )
        sys.exit(2)


def _render(docs_root: str, skill_overrides: dict) -> str:
    lines = ["schema: dev-skills/v1", "docs_root: %s" % docs_root, ""]
    if skill_overrides:
        lines.append("skills:")
        for skill in sorted(skill_overrides):
            block = skill_overrides[skill]
            if not block:
                continue
            lines.append("  %s:" % skill)
            for k, v in block.items():
                lines.append("    %s: %s" % (k, v))
    return "\n".join(lines) + "\n"


def _load_existing(target: Path):
    """Load the canonical reader to parse an existing file."""
    if not target.exists():
        return None
    here = Path(__file__).resolve().parent
    template = here.parent / "template" / "scripts"
    sys.path.insert(0, str(template))
    import read_shared_conventions as rsc  # type: ignore
    # Use the target's directory as the project root for the reader.
    return rsc.load(target.parent.parent)


def _print_resolved(target: Path) -> int:
    parsed = _load_existing(target)
    if not parsed:
        print("(no shared conventions file resolved)")
        return 0
    print("docs_root: %s" % parsed.get("docs_root", ""))
    skills = parsed.get("skills", {})
    if skills:
        print("skills:")
        for s in sorted(skills):
            print("  %s:" % s)
            for k, v in skills[s].items():
                print("    %s: %s" % (k, v))
    return 0


def main() -> int:
    epilog = """\
Examples:
    python3 scripts/setup-conventions.py
    python3 scripts/setup-conventions.py --non-interactive --docs-root agent-docs
    python3 scripts/setup-conventions.py --non-interactive --docs-root agent-docs --terminology-filename terms.md
    python3 scripts/setup-conventions.py --print
"""
    parser = argparse.ArgumentParser(
        description="Write the project-scope shared conventions file at "
                    ".agents/dev-skills.yaml.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--docs-root", default=None,
                        help="Set the docs_root (default: doc).")
    parser.add_argument("--print", dest="do_print", action="store_true",
                        help="Print resolved values from existing file and exit.")
    parser.add_argument("--repair", action="store_true",
                        help="Only fill in missing keys; preserve existing values.")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Skip prompts; use --docs-root and per-skill flags.")
    # Per-skill flags. Generated from SKILL_SCHEMA.
    for skill, keys in SKILL_SCHEMA.items():
        for k in keys:
            flag = "--%s-%s" % (skill, k.replace("_", "-"))
            parser.add_argument(
                flag, dest=("%s_%s" % (skill, k)), default=None,
                help="Set %s for %s." % (k, skill),
            )
    args = parser.parse_args()

    proot = _find_project_root(Path.cwd())
    target = _target_path(proot)

    if args.do_print:
        return _print_resolved(target)

    _pre_flight(target)

    # Gather docs_root.
    if args.non_interactive:
        docs_root = args.docs_root or "doc"
    else:
        existing = _load_existing(target)
        existing_docs_root = (existing or {}).get("docs_root", "")
        prompt_default = args.docs_root or existing_docs_root or "doc"
        try:
            ans = input("docs_root [%s]: " % prompt_default).strip()
        except EOFError:
            ans = ""
        docs_root = ans or prompt_default

    # Collect per-skill overrides from CLI flags.
    skill_overrides = {}
    for skill, keys in SKILL_SCHEMA.items():
        block = {}
        for k in keys:
            v = getattr(args, "%s_%s" % (skill, k), None)
            if v is not None:
                block[k] = v
        if block:
            skill_overrides[skill] = block

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_render(docs_root, skill_overrides), encoding="utf-8")
    print("Wrote %s." % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
