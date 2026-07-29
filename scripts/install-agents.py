#!/usr/bin/env python3
"""Install dev-skills agents into detected host agent directories.

Per-host file placement:
    Claude Code -> ~/.claude/agents/<name>.md or <project>/.claude/agents/
    Codex CLI   -> ~/.codex/agents/<name>.toml or <project>/.codex/agents/

Cursor, Windsurf, Goose: no file-based agent slot today; skipped silently.

Detection: presence of the target install directory (e.g. ~/.claude/agents/)
indicates the host is installed. The directory must exist; this script does
not create host config directories.

Stdlib only.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HOSTS = {
    # host name -> (subdir under home, agent file extension)
    "claude-code": (Path(".claude") / "agents", ".md"),
    "codex":      (Path(".codex")  / "agents", ".toml"),
}


def detect_hosts(home: Path) -> list[str]:
    """Return list of host names whose target install dir exists under home."""
    return [name for name, (sub, _) in HOSTS.items() if (home / sub).is_dir()]


def find_project_root(start: Path) -> Path | None:
    """Walk up looking for .git, package.json, pyproject.toml, etc."""
    markers = {".git", "package.json", "pyproject.toml", "Cargo.toml", "go.mod"}
    cur = start.resolve()
    while True:
        if any((cur / m).exists() for m in markers):
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def plan_installs(
    agents_dir: Path,
    targets: list[Path],   # one path per host scope+extension combo
    selected_agent_names: set[str] | None,
) -> list[tuple[Path, Path]]:
    """Return list of (source, destination) file pairs."""
    pairs: list[tuple[Path, Path]] = []
    for src in sorted(agents_dir.iterdir()):
        if not src.is_file():
            continue
        if src.name == "README.md":
            continue
        stem = src.stem
        if selected_agent_names is not None and stem not in selected_agent_names:
            continue
        for tgt_dir in targets:
            # Match extension: ".md" -> claude target, ".toml" -> codex target
            if tgt_dir.name == "agents" and (
                (src.suffix == ".md" and tgt_dir.parent.name == ".claude")
                or (src.suffix == ".toml" and tgt_dir.parent.name == ".codex")
            ):
                pairs.append((src, tgt_dir / src.name))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agents-dir",
        default=str(Path(__file__).resolve().parent.parent / "agents"),
    )
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing destination files")
    parser.add_argument("-g", "--global", dest="global_scope", action="store_true",
                        help="install at user scope (under --home)")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="non-interactive; skip confirmations")
    parser.add_argument("-a", "--host", action="append", default=[],
                        help="force a specific host (claude-code, codex)")
    parser.add_argument("--agents", nargs="+", default=None,
                        help="restrict to a subset of agent names (stems)")
    args = parser.parse_args(argv)

    agents_dir = Path(args.agents_dir)
    if not agents_dir.is_dir():
        print(f"error: agents dir not found: {agents_dir}", file=sys.stderr)
        return 2

    home = Path(args.home)
    # Determine scope.
    if args.global_scope:
        scope_root = home
    else:
        proj = find_project_root(Path.cwd())
        if proj is None:
            print("error: no project root found; pass -g for user scope", file=sys.stderr)
            return 2
        scope_root = proj

    # Determine active hosts.
    if args.host:
        unknown = [h for h in args.host if h not in HOSTS]
        if unknown:
            print(f"error: unknown host(s): {unknown}", file=sys.stderr)
            return 2
        active = args.host
    else:
        active = detect_hosts(scope_root if not args.global_scope else home)
        if not active:
            print(
                f"no host agent install dirs found under {home}. "
                "Create .claude/agents/ or .codex/agents/ first, or pass -a.",
                file=sys.stderr,
            )
            return 2

    # Build target dirs.
    targets = [scope_root / HOSTS[h][0] for h in active]

    selected = set(args.agents) if args.agents else None
    pairs = plan_installs(agents_dir, targets, selected)
    if not pairs:
        print("no agent files matched")
        return 0

    # Collisions: destinations that already exist and would need --force.
    collisions = {dst for _src, dst in pairs if dst.exists()} if not args.force else set()

    if args.dry_run:
        # Preview the plan even when some destinations already exist —
        # annotate collisions instead of failing, so `--dry-run` remains
        # usable for a contributor who has already installed once.
        for src, dst in pairs:
            note = "  [collision — exists, needs --force]" if dst in collisions else ""
            print(f"would copy {src} -> {dst}{note}")
        return 0

    if collisions:
        for c in sorted(collisions):
            print(f"error: destination exists (use --force): {c}", file=sys.stderr)
        return 1

    for src, dst in pairs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        print(f"copied {src.name} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
