#!/usr/bin/env python3
"""Interactive configuration installer for the developer-diary skill.

Two-scope writer:
    --scope user    -> writes ~/.config/developer-diary/config.yaml
    --scope project -> writes <project_root>/.developer-diary/config.yaml (default
                       when path-typed keys are involved)

Path-typed keys (root_dir, feature_routing_file) are project-only by design:
the diary is a per-project artefact and must not bleed across projects when
the skill itself is installed user-scope.

Stdlib only. Idempotent. Mode 0600 on POSIX.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKILL_NAME = "developer-diary"
ENV_PREFIX = "DEVELOPER_DIARY_"

# NOTE on path-typed keys: their default is empty by design. Returning a
# built-in default for root_dir would mask the "not yet configured" state
# and short-circuit the agent's first-use prompt. The agent treats an empty
# path-typed value as "ask the user, persist via --scope project".
DEFAULTS: dict[str, str] = {
    "root_dir": "",
    "feature_routing_file": "",
    "node_token_limit": "4000",
}

PROMPT_SUGGESTIONS: dict[str, str] = {
    "root_dir": "doc/developer-diary",
    # feature_routing_file stays blank by default — the resolver derives
    # <root_dir>/feature-routing.md when it is unset.
}

PROMPTS: dict[str, str] = {
    "root_dir": "Diary root directory (relative to project root, or absolute)",
    "feature_routing_file": "Feature-routing file path (blank = <root_dir>/feature-routing.md)",
    "node_token_limit": "Soft node-size limit in tokens",
}

# Path-typed keys: refused at the user-config layer.
PATH_KEYS: set[str] = {"root_dir", "feature_routing_file"}


def find_project_root(start: Path | None = None) -> Path | None:
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


def user_config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return Path(os.path.expanduser(base)) / SKILL_NAME / "config.yaml"


def project_config_path(project_root: Path) -> Path:
    return project_root / f".{SKILL_NAME}" / "config.yaml"


def _parse_yaml(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        s = line.split("#", 1)[0].rstrip()
        if not s or ":" not in s:
            continue
        k, _, v = s.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _format_yaml(values: dict[str, str], header_extras: list[str] | None = None) -> str:
    lines = [f"# Configuration for the {SKILL_NAME} skill.",
             f"# Override any value with env var {ENV_PREFIX}<UPPERCASE_KEY>.",
             *(header_extras or []),
             ""]
    for k in DEFAULTS:
        lines.append(f"{k}: {values.get(k, DEFAULTS[k])}")
    return "\n".join(lines) + "\n"


def load_existing(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        return _parse_yaml(path.read_text(encoding="utf-8"))
    except OSError:
        return {}


def resolve(project_values: dict[str, str], user_values: dict[str, str]) -> dict[str, str]:
    """env -> project-local -> user (non-path keys only) -> defaults."""
    out: dict[str, str] = {}
    for k, default in DEFAULTS.items():
        env_v = os.environ.get(f"{ENV_PREFIX}{k.upper()}")
        if env_v:
            out[k] = env_v
        elif k in project_values and project_values[k]:
            out[k] = project_values[k]
        elif k not in PATH_KEYS and k in user_values and user_values[k]:
            out[k] = user_values[k]
        else:
            out[k] = default
    return out


def prompt_for(key: str, current: str) -> str:
    label = PROMPTS.get(key, key)
    suggested = current or PROMPT_SUGGESTIONS.get(key, "")
    while True:
        try:
            ans = input(f"{label} [{suggested}]: ").strip()
        except EOFError:
            return suggested
        if not ans:
            return suggested
        if key == "node_token_limit" and not ans.isdigit():
            print(f"  must be an integer, got: {ans!r}", file=sys.stderr)
            continue
        return ans


def write(path: Path, values: dict[str, str], extras: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _format_yaml(values, extras)
    path.write_text(text, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scope", choices=["user", "project"], default="user")
    p.add_argument("--repair", action="store_true")
    p.add_argument("--print", dest="do_print", action="store_true")
    p.add_argument("--path", action="store_true")
    p.add_argument("--non-interactive", action="store_true")
    for k in DEFAULTS:
        p.add_argument(f"--{k.replace('_', '-')}", dest=k, default=None)
    args = p.parse_args()

    if args.scope == "project":
        proot = find_project_root()
        if proot is None:
            print("error: no project root found at or above the current directory.\n"
                  "Run from inside a project. The developer-diary's root_dir is\n"
                  "project-bound by design — user-scope is not allowed for path keys.",
                  file=sys.stderr)
            return 2
        target = project_config_path(proot)
    else:
        # user scope: warn if a path key was supplied; we'll write it but the
        # resolver will ignore it.
        path_keys_set = [k for k in PATH_KEYS if getattr(args, k, None)]
        if path_keys_set:
            print(
                f"warning: {', '.join(path_keys_set)} are path-typed keys.\n"
                f"  They will be written to user config but the resolver IGNORES\n"
                f"  them at this layer. Use --scope project to actually take effect.",
                file=sys.stderr,
            )
        target = user_config_path()

    if args.path:
        print(target)
        return 0

    if args.do_print:
        proot = find_project_root()
        project_values = (load_existing(project_config_path(proot))
                          if proot else {})
        user_values = load_existing(user_config_path())
        for k, v in resolve(project_values, user_values).items():
            print(f"{k}: {v}")
        return 0

    existing = load_existing(target)
    print(f"Configuring {SKILL_NAME} ({args.scope} scope) at: {target}")
    print("Press Enter to accept the bracketed default for each prompt.\n")

    new_values: dict[str, str] = {}
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

    extras = ([f"# Scope: project."] if args.scope == "project" else [])
    write(target, new_values, extras)
    print(f"\nWrote {target} (mode 0600 on POSIX).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
