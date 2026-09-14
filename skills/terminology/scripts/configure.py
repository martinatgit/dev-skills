#!/usr/bin/env python3
"""Interactive configuration installer for the terminology skill.

Two-scope writer:
    --scope user    -> writes ~/.config/terminology/config.yaml
    --scope project -> writes <project_root>/.terminology/config.yaml (default
                       when path-typed keys are involved)

Path-typed keys (terminology_file) are project-only by design: the glossary is
a per-project artefact and must not bleed across projects when the skill itself
is installed user-scope.

Stdlib only. Idempotent. Mode 0600 on POSIX.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKILL_NAME = "terminology"
ENV_PREFIX = "TERMINOLOGY_"

# Path-typed keys default to empty by design. An empty value is the signal that
# the agent should run the first-use prompt and persist a project-scoped answer.
DEFAULTS = {
    "terminology_file": "",
    "validation_timeout": "10",
}

PROMPT_SUGGESTIONS = {
    "terminology_file": "doc/terminology.md",
}

PROMPTS = {
    "terminology_file": "Glossary file path (relative to project root, or absolute)",
    "validation_timeout": "Per-source fetch timeout for `validate` (seconds; 0 disables)",
}

# Path-typed keys: refused at the user-config layer.
PATH_KEYS = {"terminology_file"}

# Int-typed keys: validated as digits at prompt time.
INT_KEYS = {"validation_timeout"}


def find_project_root(start=None):
    here = Path(__file__).resolve().parent
    helper = here / "find_project_root.py"
    cmd = [sys.executable, str(helper)]
    if start:
        cmd.extend(["--from", str(start)])
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return Path(out.stdout.strip()) if out.stdout.strip() else None


def user_config_path():
    base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return Path(os.path.expanduser(base)) / SKILL_NAME / "config.yaml"


def project_config_path(project_root):
    return project_root / ("." + SKILL_NAME) / "config.yaml"


def _parse_yaml(text):
    out = {}
    for line in text.splitlines():
        s = line.split("#", 1)[0].rstrip()
        if not s or ":" not in s:
            continue
        k, _, v = s.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _format_yaml(values, header_extras=None):
    lines = [
        "# Configuration for the %s skill." % SKILL_NAME,
        "# Override any value with env var %s<UPPERCASE_KEY>." % ENV_PREFIX,
        *(header_extras or []),
        "",
    ]
    for k in DEFAULTS:
        lines.append("%s: %s" % (k, values.get(k, DEFAULTS[k])))
    return "\n".join(lines) + "\n"


def load_existing(path):
    if not path.exists():
        return {}
    try:
        return _parse_yaml(path.read_text(encoding="utf-8"))
    except OSError:
        return {}


def resolve(project_values, user_values):
    """env -> project-local -> user (non-path keys only) -> defaults."""
    out = {}
    for k, default in DEFAULTS.items():
        env_v = os.environ.get(ENV_PREFIX + k.upper())
        if env_v:
            out[k] = env_v
        elif k in project_values and project_values[k]:
            out[k] = project_values[k]
        elif k not in PATH_KEYS and k in user_values and user_values[k]:
            out[k] = user_values[k]
        else:
            out[k] = default
    return out


def prompt_for(key, current):
    label = PROMPTS.get(key, key)
    suggested = current or PROMPT_SUGGESTIONS.get(key, "")
    while True:
        try:
            ans = input("%s [%s]: " % (label, suggested)).strip()
        except EOFError:
            return suggested
        if not ans:
            return suggested
        if key in INT_KEYS and not ans.isdigit():
            print("  must be a non-negative integer, got: %r" % ans, file=sys.stderr)
            continue
        return ans


def write(path, values, extras=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _format_yaml(values, extras)
    path.write_text(text, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def write_shared_conventions_minimal(project_root: Path, docs_root: str) -> Path:
    """Create a minimal .agents/dev-skills.yaml with schema + docs_root only.

    Refuses to overwrite an existing foreign file (no dev-skills/v1 marker).
    Used by the lazy first-use prompt when the user opts into the shared layer.
    """
    target = project_root / ".agents" / "dev-skills.yaml"
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if "schema: dev-skills/v1" not in existing:
            raise RuntimeError(
                "refusing to overwrite %s: missing schema: dev-skills/v1 marker.\n"
                "Remove the file or set DEV_SKILLS_CONFIG_FILE and re-run."
                % target
            )
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "schema: dev-skills/v1\ndocs_root: %s\n" % docs_root,
        encoding="utf-8",
    )
    return target


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scope", choices=["user", "project"], default="user")
    p.add_argument("--repair", action="store_true")
    p.add_argument("--print", dest="do_print", action="store_true")
    p.add_argument("--path", action="store_true")
    p.add_argument("--non-interactive", action="store_true")
    for k in DEFAULTS:
        p.add_argument("--" + k.replace("_", "-"), dest=k, default=None)
    args = p.parse_args()

    if args.scope == "project":
        proot = find_project_root()
        if proot is None:
            print(
                "error: no project root found at or above the current directory.\n"
                "Run from inside a project. terminology_file is project-bound by\n"
                "design -- user-scope is not allowed for path keys.",
                file=sys.stderr,
            )
            return 2
        target = project_config_path(proot)
    else:
        path_keys_set = [k for k in PATH_KEYS if getattr(args, k, None)]
        if path_keys_set:
            print(
                "warning: %s are path-typed keys.\n"
                "  They will be written to user config but the resolver IGNORES\n"
                "  them at this layer. Use --scope project to actually take effect."
                % ", ".join(path_keys_set),
                file=sys.stderr,
            )
        target = user_config_path()

    if args.path:
        print(target)
        return 0

    if args.do_print:
        # Invoke the runtime CLI in its own module context: it imports configure.
        # Inherit cwd so project discovery starts in the consuming project.
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("resolve_config.py")), "--all"],
            capture_output=True, text=True, check=False,
        )
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                key, _, value = line.partition("=")
                print("%s: %s" % (key, value))
        return result.returncode

    existing = load_existing(target)
    print("Configuring %s (%s scope) at: %s" % (SKILL_NAME, args.scope, target))
    print("Press Enter to accept the bracketed default for each prompt.\n")

    if (
        args.scope == "project"
        and not args.non_interactive
        and not existing.get("terminology_file")
        and not getattr(args, "terminology_file", None)
    ):
        print("\nterminology needs a glossary file path.")
        print("  1. Apply a docs-folder convention to every skill in this project")
        print("     (creates .agents/dev-skills.yaml with docs_root only -- recommended)")
        print("  2. Configure just terminology (creates .terminology/config.yaml)")
        try:
            choice = input("Choice [1/2, default 1]: ").strip() or "1"
        except EOFError:
            choice = "1"
        if choice == "1":
            try:
                docs_root = input("docs_root [doc]: ").strip() or "doc"
            except EOFError:
                docs_root = "doc"
            try:
                shared_path = write_shared_conventions_minimal(proot, docs_root)
                print("\nWrote %s." % shared_path)
                print("terminology will resolve terminology_file to %s/terminology.md"
                      % docs_root)
                return 0
            except RuntimeError as e:
                print("error: %s" % e, file=sys.stderr)
                return 2
        # Choice 2: fall through to per-skill prompt loop below.

    new_values = {}
    for k, default in DEFAULTS.items():
        cli_v = getattr(args, k, None)
        if cli_v is not None:
            new_values[k] = cli_v
            continue
        current = existing.get(k, default)
        if args.repair and existing.get(k):
            new_values[k] = existing[k]
            continue
        if args.non_interactive:
            if not current and k in PROMPT_SUGGESTIONS:
                new_values[k] = PROMPT_SUGGESTIONS[k]
            else:
                new_values[k] = current
            continue
        new_values[k] = prompt_for(k, current)

    extras = ["# Scope: project."] if args.scope == "project" else []
    write(target, new_values, extras)
    print("\nWrote %s (mode 0600 on POSIX)." % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
