#!/usr/bin/env python3
"""Write the project-scope shared conventions file `.agents/dev-skills.yaml`.

Pre-flight collision check: refuses to overwrite an existing file that lacks
the `schema: dev-skills/v1` marker. Set DEV_SKILLS_CONFIG_FILE to write to an
alternate path.

Reruns preserve the parsed docs_root and per-skill scalar values, including
keys without CLI flags. Explicit flags replace only their named values.
Rewriting normalizes ordering/formatting and does not retain comments or
unsupported top-level fields (the canonical reader does not expose them).

Usage:
    python3 scripts/setup-conventions.py                                  # interactive
    python3 scripts/setup-conventions.py --non-interactive --docs-root X
    python3 scripts/setup-conventions.py --print

(--repair is a v2 candidate; not implemented in v1.)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCHEMA_VERSION = "dev-skills/v1"

_INVALID_VALUE_CHARS = ("#", "\n", "\r")


def _validate_scalar(label: str, value: str) -> None:
    """Reject values that would not round-trip through the canonical reader."""
    for ch in _INVALID_VALUE_CHARS:
        if ch in value:
            print(
                "error: %s value %r contains forbidden character %r.\n"
                "The shared-conventions YAML subset rejects '#', '\\n', '\\r' "
                "in values (they break the reader's comment / line handling)."
                % (label, value, ch),
                file=sys.stderr,
            )
            sys.exit(2)

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
    template = here.parent / "template" / "scripts"
    sys.path.insert(0, str(template))
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
    """Refuse to overwrite a file that does not parse as dev-skills/v1."""
    if not target.exists():
        return
    parsed = _load_existing(target)
    if parsed is None:
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
    """Use the canonical reader to parse `target` directly (no project_root)."""
    if not target.exists():
        return None
    here = Path(__file__).resolve().parent
    template = here.parent / "template" / "scripts"
    sys.path.insert(0, str(template))
    import read_shared_conventions as rsc  # type: ignore
    # Set the env var to point at `target` so the reader uses it verbatim,
    # then restore. This makes _load_existing path-explicit and removes the
    # accidental reliance on target.parent.parent.
    saved = os.environ.get("DEV_SKILLS_CONFIG_FILE")
    os.environ["DEV_SKILLS_CONFIG_FILE"] = str(target)
    try:
        return rsc.load(target.parent)  # second arg is irrelevant when env set
    finally:
        if saved is None:
            os.environ.pop("DEV_SKILLS_CONFIG_FILE", None)
        else:
            os.environ["DEV_SKILLS_CONFIG_FILE"] = saved


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
                        help="Set docs_root (default: existing value, then doc).")
    parser.add_argument("--print", dest="do_print", action="store_true",
                        help="Print resolved values from existing file and exit.")
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
    existing = _load_existing(target) or {}

    # Gather docs_root.
    prompt_default = args.docs_root if args.docs_root is not None else existing.get("docs_root", "doc")
    if args.non_interactive:
        docs_root = prompt_default
    else:
        try:
            ans = input("docs_root [%s]: " % prompt_default).strip()
        except EOFError:
            ans = ""
        docs_root = ans or prompt_default

    _validate_scalar("docs_root", docs_root)

    # Preserve every parsed per-skill key, including keys without CLI flags.
    skill_overrides = {
        skill: dict(block) for skill, block in existing.get("skills", {}).items()
    }
    for skill, keys in SKILL_SCHEMA.items():
        for k in keys:
            v = getattr(args, "%s_%s" % (skill, k), None)
            if v is not None:
                skill_overrides.setdefault(skill, {})[k] = v

    for skill, block in skill_overrides.items():
        for k, v in block.items():
            _validate_scalar("%s.%s" % (skill, k), v)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_render(docs_root, skill_overrides), encoding="utf-8")
    print("Wrote %s." % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
