#!/usr/bin/env python3
"""Append one JSON object as a single JSONL line to the configured log file.

The orchestrator pipes a JSON object on stdin; this script validates it as
JSON, ensures the parent directory exists, and appends it as one line.

Why a script: the previous orchestrator used `echo '{...}' >> path` via Bash,
which is not portable to PowerShell, restricted shells, or hosts that disallow
shell redirection. Stdlib Python works everywhere Python 3 is installed.

Usage:
    echo '{"agent_id": "...", ...}' | python3 scripts/append_log.py
    python3 scripts/append_log.py --file <path>   # override the log path
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import resolve_config  # type: ignore  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", help="Override the resolved log directory path.")
    p.add_argument("--name", default="cost-log.jsonl",
                   help="Log file name inside log_dir (default: cost-log.jsonl).")
    args = p.parse_args()

    raw = sys.stdin.read().strip()
    if not raw:
        print("error: no JSON on stdin", file=sys.stderr)
        return 2
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: stdin is not valid JSON ({e})", file=sys.stderr)
        return 2

    if args.file:
        target = Path(args.file)
    else:
        log_dir = Path(resolve_config.expand(
            resolve_config.resolve_all()["log_dir"]
        ))
        target = log_dir / args.name

    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    with target.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
