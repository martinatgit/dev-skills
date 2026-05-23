#!/usr/bin/env python3
"""Phase 1 drift detector for the update-todos maintenance mode.

Reads a TODO markdown file (with YAML frontmatter), for each reference[]
opens the cited file, normalizes both sides (LF endings, per-line rstrip),
and produces a finding per excerpt:

    unchanged | moved | drifted | gone | missing-file

Multi-match candidates are disambiguated by numeric closeness to the
originally recorded line range; ambiguity is surfaced via an
`ambiguous-match: <N>` field on the finding.

Output: YAML fragment to stdout, one block per reference. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

JACCARD_THRESHOLD = 0.85
SIMILARITY_WINDOW_PAD = 2

_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    m = _FRONT_RE.match(text)
    if not m:
        return {}
    return _parse_yaml(m.group(1))


def _parse_yaml(text: str) -> dict:
    """Tiny YAML-ish parser sufficient for TODO frontmatter."""
    root: dict = {}
    stack = [(0, root)]
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.split("#", 1)[0].rstrip()
        if not stripped.strip():
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent < stack[-1][0]:
            stack.pop()
        parent_indent, parent = stack[-1]
        body = raw[indent:]
        if body.startswith("- "):
            entry_body = body[2:].strip()
            if isinstance(parent, list):
                lst = parent
            else:
                last_key = next(reversed(parent))
                if not isinstance(parent[last_key], list):
                    parent[last_key] = []
                lst = parent[last_key]
            if ":" in entry_body:
                entry: dict = {}
                k, _, v = entry_body.partition(":")
                v = v.strip()
                if v == "|":
                    block, consumed = _read_block_scalar(lines, i + 1, indent + 4)
                    entry[k.strip()] = block
                    i += consumed
                elif v:
                    entry[k.strip()] = _coerce(v)
                else:
                    entry[k.strip()] = None
                lst.append(entry)
                stack.append((indent + 2, entry))
            else:
                lst.append(_coerce(entry_body))
            i += 1
            continue
        if ":" in body:
            k, _, v = body.partition(":")
            v = v.strip()
            if v == "":
                parent[k.strip()] = None
                i += 1
                stack.append((indent + 2, parent))
                continue
            if v == "|":
                block, consumed = _read_block_scalar(lines, i + 1, indent + 2)
                parent[k.strip()] = block
                i += consumed + 1
                continue
            parent[k.strip()] = _coerce(v)
            i += 1
            continue
        i += 1
    return root


def _read_block_scalar(lines: list[str], start: int, base_indent: int) -> tuple[str, int]:
    out_lines: list[str] = []
    j = start
    while j < len(lines):
        ln = lines[j]
        if ln.strip() == "":
            out_lines.append("")
            j += 1
            continue
        if (len(ln) - len(ln.lstrip(" "))) < base_indent:
            break
        out_lines.append(ln[base_indent:])
        j += 1
    return "\n".join(out_lines), j - start


def _coerce(v: str):
    v = v.strip().strip('"').strip("'")
    if v == "null":
        return None
    if v == "true":
        return True
    if v == "false":
        return False
    return v


def normalize(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def tokenize(text: str) -> list[str]:
    text = text.lower().replace("\n", " ").replace("\t", " ")
    toks: list[str] = []
    buf: list[str] = []
    for ch in text:
        if ch.isalnum() or ch == "_":
            buf.append(ch)
        else:
            if buf:
                toks.append("".join(buf))
                buf = []
            if not ch.isspace():
                toks.append(ch)
    if buf:
        toks.append("".join(buf))
    return toks


def jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def find_exact_matches(needle: list[str], haystack: list[str]) -> list[int]:
    n = len(needle)
    if n == 0:
        return []
    hits: list[int] = []
    for i in range(len(haystack) - n + 1):
        if haystack[i:i + n] == needle:
            hits.append(i + 1)
    return hits


def find_similar_matches(needle: list[str], haystack: list[str], threshold: float) -> list[tuple[int, float]]:
    n = len(needle)
    if n == 0:
        return []
    needle_toks = tokenize("\n".join(needle))
    windows: list[tuple[int, float]] = []
    for delta in range(-SIMILARITY_WINDOW_PAD, SIMILARITY_WINDOW_PAD + 1):
        size = max(1, n + delta)
        for i in range(len(haystack) - size + 1):
            window = haystack[i:i + size]
            sim = jaccard(needle_toks, tokenize("\n".join(window)))
            if sim >= threshold:
                windows.append((i + 1, sim))
    best: dict[int, float] = {}
    for start, sim in windows:
        if sim > best.get(start, 0.0):
            best[start] = sim
    return sorted(best.items())


def closest_to(target_start: int, candidates: list[int]) -> int:
    return min(candidates, key=lambda c: (abs(c - target_start), c))


def find_rename_target(old_path: str, cwd: Path, since_sha: str | None) -> str | None:
    """If old_path was renamed in git history (optionally since `since_sha`),
    return the most-recent new path. None if no rename event found, or git
    is unavailable, or the SHA is unreachable.

    Uses `git log --diff-filter=R --name-status` scoped to the file. The
    output's R lines have format `R<similarity>\\t<old>\\t<new>`. Git walks
    history newest-first, so the FIRST R line we encounter whose <old>
    matches our recorded path is the most-recent rename.
    """
    # Confirm we're in a worktree.
    try:
        ws = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        if ws.returncode != 0 or ws.stdout.strip() != "true":
            return None
    except OSError:
        return None

    # If since_sha is set, verify it's reachable; otherwise omit the range
    # (search all history).
    rev_range: str | None = None
    if since_sha:
        check = subprocess.run(
            ["git", "cat-file", "-e", since_sha],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        if check.returncode == 0:
            rev_range = f"{since_sha}..HEAD"

    # Don't restrict via -- <path>: git's pathspec filter does not always
    # surface renames whose old-side matches a deleted file. Dump all rename
    # events in the (optional) revision range and filter in Python.
    cmd = ["git", "log", "--diff-filter=R", "--name-status", "--format="]
    if rev_range:
        cmd.append(rev_range)

    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError:
        return None
    if out.returncode != 0:
        return None

    # Try matching the exact recorded path first; if not found, also accept
    # paths that end with the same basename (covers cases where the recorded
    # path was relative to a different directory than git's repo root).
    basename = old_path.rsplit("/", 1)[-1]
    fallback: str | None = None
    for line in out.stdout.splitlines():
        if not line.startswith("R"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        if parts[1] == old_path:
            return parts[2]
        if fallback is None and parts[1].rsplit("/", 1)[-1] == basename:
            fallback = parts[2]
    return fallback


def sha_reachable(sha: str, cwd: Path) -> bool:
    """True if the given SHA exists in the local repo. False otherwise."""
    if not sha or sha == "null":
        return False
    try:
        out = subprocess.run(
            ["git", "cat-file", "-e", sha],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        return out.returncode == 0
    except OSError:
        return False


def check_reference(ref: dict, todo_dir: Path) -> dict:
    path_str = ref.get("path", "")
    file_path = (todo_dir / path_str).resolve() if not Path(path_str).is_absolute() else Path(path_str)
    out: dict = {"path": path_str}

    if ref.get("kind") == "diary":
        # Diary-node references are append-only by contract. Drift detection
        # is meaningless; we only verify existence.
        out["kind"] = "diary"
        out["finding"] = "unchanged" if file_path.exists() else "missing-file"
        return out

    clarified_sha = ref.get("clarified-at-sha")
    if isinstance(clarified_sha, str) and clarified_sha and clarified_sha != "null":
        if not sha_reachable(clarified_sha, todo_dir):
            out["sha-unreachable"] = True

    if not file_path.exists():
        # Try to detect a rename so we don't false-positive to `obsolete`.
        new_path = find_rename_target(
            path_str, todo_dir,
            clarified_sha if isinstance(clarified_sha, str) else None,
        )
        if new_path:
            new_file = (todo_dir / new_path).resolve() if not Path(new_path).is_absolute() else Path(new_path)
            if new_file.exists():
                out["renamed-from"] = path_str
                out["path"] = new_path
                file_path = new_file
            else:
                out["finding"] = "missing-file"
                return out
        else:
            out["finding"] = "missing-file"
            return out

    file_lines = normalize(file_path.read_text(encoding="utf-8", errors="replace"))

    excerpts = ref.get("excerpts") or []
    if not excerpts:
        out["finding"] = "no-excerpt"
        out["note"] = "reference has no excerpts to compare against"
        return out

    findings = []
    for ex in excerpts:
        ex_text = ex.get("text", "") if isinstance(ex, dict) else ""
        ex_lines_spec = str(ex.get("lines", "")) if isinstance(ex, dict) else ""
        orig_start = int(ex_lines_spec.partition("-")[0] or "1")
        needle = normalize(ex_text)

        exact = find_exact_matches(needle, file_lines)
        finding: dict
        if exact:
            chosen = closest_to(orig_start, exact)
            end = chosen + len(needle) - 1
            if len(exact) > 1:
                # Ambiguous matches: always report new-lines to show where we found it
                if chosen == orig_start:
                    finding = {"finding": "unchanged", "new-lines": f"{chosen}-{end}"}
                else:
                    finding = {"finding": "moved", "new-lines": f"{chosen}-{end}"}
                finding["ambiguous-match"] = len(exact)
            else:
                # Single exact match
                if chosen == orig_start:
                    finding = {"finding": "unchanged", "lines": ex_lines_spec}
                else:
                    finding = {"finding": "moved", "new-lines": f"{chosen}-{end}"}
        else:
            sim = find_similar_matches(needle, file_lines, JACCARD_THRESHOLD)
            if sim:
                starts = [s for s, _ in sim]
                chosen = closest_to(orig_start, starts)
                chosen_sim = next(s for st, s in sim if st == chosen)
                end = chosen + len(needle) - 1
                finding = {
                    "finding": "drifted",
                    "new-lines": f"{chosen}-{end}",
                    "similarity": round(chosen_sim, 2),
                }
                if len(sim) > 1:
                    finding["ambiguous-match"] = len(sim)
            else:
                finding = {"finding": "gone", "lines": ex_lines_spec}
        findings.append(finding)

    if len(findings) == 1:
        out.update(findings[0])
    else:
        out["findings"] = findings
    return out


def dict_to_inline(d: dict) -> str:
    return ", ".join(f"{k}: {v}" for k, v in d.items())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--todo", required=True, help="Path to the TODO markdown file")
    args = p.parse_args()

    todo_path = Path(args.todo)
    if not todo_path.exists():
        print(f"error: {todo_path}: not found", file=sys.stderr)
        return 2
    text = todo_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    refs = fm.get("references") or []

    for ref in refs:
        result = check_reference(ref, todo_path.parent)
        print(f"- path: {result['path']}")
        for k, v in result.items():
            if k == "path":
                continue
            if isinstance(v, list):
                print(f"  {k}:")
                for item in v:
                    print(f"    - {dict_to_inline(item)}")
            else:
                print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
