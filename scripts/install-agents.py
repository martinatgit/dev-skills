#!/usr/bin/env python3
"""Install dev-skills agents at project scope, or at user scope with -g.

Detect .claude/.codex config directories in the project or home; -a selects
hosts explicitly. Identical files are skipped. --update replaces tracked,
unmodified files; --force backs up differing files before replacement.
Stale managed files are reported and retained. No interactive prompts.
Stdlib only; run from a checkout containing template/scripts/find_project_root.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HOSTS = {
    "claude-code": (Path(".claude") / "agents", ".md"),
    "codex": (Path(".codex") / "agents", ".toml"),
}
MANIFEST = ".dev-skills-install.json"


def detect_hosts(root: Path) -> list[str]:
    """Detect host configuration roots, including fresh agent installations."""
    return [name for name, (sub, _) in HOSTS.items() if (root / sub.parent).is_dir()]


def find_project_root(start: Path) -> Path | None:
    """Use the same canonical project markers as shared configuration."""
    # The installer promises that --dry-run does not modify the checkout.
    # Importing the helper otherwise creates __pycache__ beside the source.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "template" / "scripts"))
    import find_project_root as finder
    return finder.find_project_root(start, finder.DEFAULT_MARKERS)


def check_path(path: Path) -> None:
    """Refuse symlinks and Windows junctions before reading or replacing files."""
    for item in (path, *path.parents):
        if item.is_symlink() or getattr(item, "is_junction", lambda: False)():
            raise ValueError(f"symlink/junction paths are not supported: {item}")


def valid_agent_name(name: str, extension: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name)) and name.endswith(extension)


def read_manifest(target: Path, extension: str) -> dict:
    path = target / MANIFEST
    check_path(path)
    if not path.exists():
        return {"version": 1, "files": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(value, dict) or type(value.get("version")) is not int
                or value["version"] != 1 or not isinstance(value.get("files"), dict)):
            raise ValueError("expected version 1 and a files mapping")
        for name, entry in value["files"].items():
            if (not valid_agent_name(name, extension) or not isinstance(entry, dict)
                    or not isinstance(entry.get("source"), str)
                    or not isinstance(entry.get("sha256"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
                raise ValueError(f"invalid tracked entry: {name!r}")
        return value
    except (ValueError, OSError) as exc:
        raise ValueError(f"invalid manifest {path}: {exc}; repair or move it aside before retrying") from exc


def atomic_write(path: Path, data: bytes) -> None:
    """Replace one file atomically using a private temporary sibling."""
    with tempfile.NamedTemporaryFile(prefix=".dev-skills-write-", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
        except BaseException:
            stream.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def install(args: argparse.Namespace) -> int:
    agents_dir = Path(args.agents_dir).absolute()
    check_path(agents_dir)
    if not agents_dir.is_dir():
        raise ValueError(f"agents dir not found: {agents_dir}")
    sources = [p for p in sorted(agents_dir.iterdir()) if p.suffix in {".md", ".toml"} and p.name != "README.md"]
    for source in sources:
        check_path(source)
        if not source.is_file() or not valid_agent_name(source.name, source.suffix):
            raise ValueError(f"invalid source agent file: {source}")
    selected = set(args.agents) if args.agents else None
    if selected:
        unknown = selected - {p.stem for p in sources}
        if unknown:
            raise ValueError(f"unknown agent name(s): {', '.join(sorted(unknown))}")
    unknown_hosts = set(args.host) - HOSTS.keys()
    if unknown_hosts:
        raise ValueError(f"unknown host(s): {', '.join(sorted(unknown_hosts))}")

    home = Path(args.home).absolute()
    scope = home if args.global_scope else find_project_root(Path.cwd())
    if scope is None:
        raise ValueError("no project root found; pass -g for user scope")
    active = list(dict.fromkeys(args.host or [*detect_hosts(home), *([] if args.global_scope else detect_hosts(scope))]))
    if not active:
        roots = str(home) if args.global_scope else f"{scope} or {home}"
        raise ValueError(f"no .claude/.codex host config roots found under {roots}; pass -a claude-code or -a codex")

    # Preflight every destination and manifest before creating directories or files.
    plans = []
    manifests = {}
    stale = []
    for host in active:
        subdir, extension = HOSTS[host]
        target = scope / subdir
        check_path(target)
        if target.exists() and not target.is_dir():
            raise ValueError(f"target is not a directory: {target}")
        manifest = read_manifest(target, extension)
        manifests[target] = manifest
        current_names = {p.name for p in sources if p.suffix == extension}
        for name in sorted(manifest["files"].keys() - current_names):
            check_path(target / name)
            stale.append(target / name)
        for source in sources:
            if source.suffix != extension or (selected and source.stem not in selected):
                continue
            dest = target / source.name
            check_path(dest)
            if dest.exists() and not dest.is_file():
                raise ValueError(f"destination is not a regular file: {dest}")
            data = source.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            existing = hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else None
            tracked = manifest["files"].get(source.name)
            if existing is None:
                status = "install"
            elif existing == digest:
                status = "unchanged"
            elif args.force:
                status = "backup+replace"
                backup_root = target.parent / ".dev-skills-agent-backups"
                check_path(backup_root)
                if backup_root.exists() and not backup_root.is_dir():
                    raise ValueError(f"backup root is not a directory: {backup_root}")
            elif args.update and tracked and tracked["sha256"] == existing:
                status = "update"
            else:
                status = "conflict"
            plans.append((source, dest, data, digest, status))

    for path in stale:
        print(f"[stale; retained, review manually] {path}")
    for source, dest, _, _, status in plans:
        print(f"{'would ' if args.dry_run else ''}[{status}] {source} -> {dest}")
    if selected and not plans:
        raise ValueError("no selected agent files match the requested hosts")
    if args.dry_run:
        return 0
    conflicts = [dest for _, dest, _, _, status in plans if status == "conflict"]
    if conflicts:
        for path in conflicts:
            print(f"error: destination exists with different content: {path}; use --update for tracked unmodified files or --force to back up and replace", file=sys.stderr)
        return 1

    # Complete all requested backups before replacing any agent files.
    backups = {}
    for _, dest, _, _, status in plans:
        if status == "backup+replace":
            if dest.parent not in backups:
                backup_root = dest.parent.parent / ".dev-skills-agent-backups"
                backup_root.mkdir(parents=True, exist_ok=True)
                backups[dest.parent] = Path(tempfile.mkdtemp(prefix="backup-", dir=backup_root))
            backup = backups[dest.parent] / dest.name
            shutil.copy2(dest, backup)
            print(f"backup {dest} -> {backup}")

    changed_manifests = set()
    for source, dest, data, digest, status in plans:
        if status != "unchanged":
            dest.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(dest, data)
        entry = {"sha256": digest, "source": str(source)}
        # Adopt identical legacy copies without changing the agent file.
        if manifests[dest.parent]["files"].get(dest.name) != entry:
            manifests[dest.parent]["files"][dest.name] = entry
            changed_manifests.add(dest.parent)
    for target in sorted(changed_manifests):
        data = (json.dumps(manifests[target], indent=2, sort_keys=True) + "\n").encode("utf-8")
        atomic_write(target / MANIFEST, data)
    if not plans and not stale:
        print("no agent files matched")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-dir", default=str(Path(__file__).resolve().parent.parent / "agents"))
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--dry-run", action="store_true", help="preview statuses without writes; conflicts are reported with exit 0")
    parser.add_argument("--update", action="store_true", help="replace differing tracked files only when unmodified since installation")
    parser.add_argument("--force", action="store_true", help="back up differing files in <host>/.dev-skills-agent-backups/backup-<unique>/ before replacement")
    parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="install at user scope (under --home)")
    parser.add_argument("-y", "--yes", action="store_true", help="deprecated compatibility no-op; installation never prompts")
    parser.add_argument("-a", "--host", action="append", default=[], help="select an explicit host (claude-code, codex); repeat for both")
    parser.add_argument("--agents", nargs="+", default=None, help="restrict to agent names (stems); unknown names are errors")
    args = parser.parse_args(argv)
    try:
        return install(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
