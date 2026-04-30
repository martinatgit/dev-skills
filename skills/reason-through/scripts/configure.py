#!/usr/bin/env python3
"""Interactive configuration installer for the reason-through skill.

Two-scope writer:
    --scope user    -> writes ~/.config/reason-through/config.yaml (default)
    --scope project -> writes <project_root>/.reason-through/config.yaml

Stdlib only. Idempotent. Mode 0600 on POSIX.

Usage:
    python3 scripts/configure.py
    python3 scripts/configure.py --scope project
    python3 scripts/configure.py --repair
    python3 scripts/configure.py --print
    python3 scripts/configure.py --path
    python3 scripts/configure.py --non-interactive
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKILL_NAME = "reason-through"
ENV_PREFIX = "REASON_THROUGH_"

DEFAULTS: dict[str, str] = {
    "cache_dir": "~/.cache/reason-through",
    "log_dir": "~/.local/state/reason-through",
    "cache_ttl_seconds": "86400",
    "max_refinement_passes": "3",
    "specialist_model_tier": "fast",
    "orchestrator_model_tier": "strong",
}

PROMPTS: dict[str, str] = {
    "cache_dir": "Directory for cache files",
    "log_dir": "Directory for cost-log.jsonl",
    "cache_ttl_seconds": "Cache TTL in seconds (24h = 86400)",
    "max_refinement_passes": "Max refinement passes (1-3)",
    "specialist_model_tier": "Model tier for specialist agents (fast | default | strong)",
    "orchestrator_model_tier": "Model tier for the orchestrator (fast | default | strong)",
}

# Path-typed keys: reason-through has caches and logs that are inherently
# user-scoped (not project artefacts), so this set is empty. Listed here so
# the file shape stays uniform across skills.
PATH_KEYS: set[str] = set()


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
    while True:
        try:
            ans = input(f"{label} [{current}]: ").strip()
        except EOFError:
            return current
        if not ans:
            return current
        if key.endswith("_seconds") or key == "max_refinement_passes":
            if not ans.isdigit():
                print(f"  must be an integer, got: {ans!r}", file=sys.stderr)
                continue
        if key.endswith("_model_tier") and ans not in ("fast", "default", "strong"):
            print("  must be one of: fast, default, strong", file=sys.stderr)
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
                  "Run from inside a project, or use --scope user.",
                  file=sys.stderr)
            return 2
        target = project_config_path(proot)
    else:
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
            new_values[k] = current
            continue
        new_values[k] = prompt_for(k, current)

    extras = ([f"# Scope: project ({args.scope})."] if args.scope == "project" else [])
    write(target, new_values, extras)
    print(f"\nWrote {target} (mode 0600 on POSIX).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
