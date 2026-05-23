#!/usr/bin/env python3
"""Read or upsert rows in a terminology glossary file.

The glossary lives at the path configured as `terminology_file`. This helper is
the single writer — it preserves everything outside the table verbatim and
guarantees a sorted, de-duplicated table after every write.

Usage:
    python3 scripts/parse_glossary.py --read <file>
        Emit the table as a JSON array of {Term, Abbreviations, Definition,
        Comments on use, Disambiguate from, _line} to stdout.

    python3 scripts/parse_glossary.py --upsert <file> --row <json>
        Insert or merge a single row (passed as a JSON object with the five
        column keys; missing keys default to empty strings). Re-sorts the
        table alphabetically by Term, case-insensitive.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COLUMNS = ("Term", "Abbreviations", "Definition", "Comments on use", "Disambiguate from")
HEADER_LINE = "| " + " | ".join(COLUMNS) + " |"
ALIGN_LINE = "|" + "|".join(["---"] * len(COLUMNS)) + "|"


def _split_row(line):
    # GFM table row, respecting `\|` escape for literal pipes inside a cell.
    cells = []
    cur = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    # GFM rows are bracketed by | … | so the first and last cells are empty.
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def _escape_cell(value):
    # Replace literal newlines with <br> for rendering; escape pipes.
    v = value.replace("\r\n", "\n").replace("\r", "\n")
    v = v.replace("\n", "<br>")
    v = v.replace("|", "\\|")
    return v.strip()


def _unescape_cell(value):
    v = value.replace("<br>", "\n")
    # Note: _split_row already handled \| -> | during parsing.
    return v


def _is_align_line(line):
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return False
    cells = [c.strip() for c in s.strip("|").split("|")]
    if len(cells) != len(COLUMNS):
        return False
    return all(set(c) <= set("-: ") and "---" in c for c in cells)


def _find_table(lines):
    """Return (header_idx, align_idx, body_start, body_end) or None.

    body_end is the index of the first line AFTER the table (exclusive).
    """
    for i, line in enumerate(lines):
        cells = _split_row(line.strip()) if line.strip().startswith("|") else None
        if cells is None or len(cells) != len(COLUMNS):
            continue
        if [c.strip() for c in cells] != list(COLUMNS):
            continue
        # Expect alignment line next.
        if i + 1 >= len(lines) or not _is_align_line(lines[i + 1]):
            continue
        body_start = i + 2
        body_end = body_start
        while body_end < len(lines):
            ln = lines[body_end]
            stripped = ln.strip()
            if not stripped:
                break
            if not (stripped.startswith("|") and stripped.endswith("|")):
                break
            cells2 = _split_row(stripped)
            if len(cells2) != len(COLUMNS):
                break
            body_end += 1
        return i, i + 1, body_start, body_end
    return None


def read_rows(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    found = _find_table(lines)
    if not found:
        return [], lines, None
    _, _, body_start, body_end = found
    rows = []
    for idx in range(body_start, body_end):
        cells = _split_row(lines[idx].strip())
        row = {col: _unescape_cell(cells[i]) for i, col in enumerate(COLUMNS)}
        row["_line"] = idx + 1  # 1-based for human consumption
        rows.append(row)
    return rows, lines, found


def _row_to_md(row):
    cells = [_escape_cell(row.get(col, "")) for col in COLUMNS]
    return "| " + " | ".join(cells) + " |"


def _merge_row(existing, incoming):
    """Strictly-additive merge. Returns (merged_row, conflicts: list[str]).

    - Identical fields: kept.
    - Existing empty + incoming non-empty: take incoming.
    - Both non-empty + identical: keep.
    - Both non-empty + different: record a conflict and keep existing.

    Abbreviations and Disambiguate from are list-typed (comma-separated) and
    are unioned rather than overwritten.
    """
    merged = dict(existing)
    conflicts = []
    list_cols = {"Abbreviations", "Disambiguate from"}
    for col in COLUMNS:
        old = existing.get(col, "").strip()
        new = incoming.get(col, "").strip()
        if not new:
            continue
        if old == new:
            continue
        if not old:
            merged[col] = new
            continue
        if col in list_cols:
            old_items = [s.strip() for s in old.split(",") if s.strip()]
            new_items = [s.strip() for s in new.split(",") if s.strip()]
            seen = set(x.lower() for x in old_items)
            for item in new_items:
                if item.lower() not in seen:
                    old_items.append(item)
                    seen.add(item.lower())
            merged[col] = ", ".join(old_items)
            continue
        conflicts.append(
            "field %r: existing=%r incoming=%r" % (col, old, new)
        )
    return merged, conflicts


def _match_existing(rows, incoming):
    """Return the index of an existing row that matches incoming, or None.

    Match order:
        1. case-insensitive Term equality
        2. abbreviation overlap (incoming term in existing abbreviations,
           or any incoming abbreviation in existing term/abbreviations)
    """
    in_term = incoming.get("Term", "").strip().lower()
    in_abbrevs = {
        s.strip().lower()
        for s in incoming.get("Abbreviations", "").split(",")
        if s.strip()
    }
    for i, row in enumerate(rows):
        if row.get("Term", "").strip().lower() == in_term and in_term:
            return i
    for i, row in enumerate(rows):
        ex_term = row.get("Term", "").strip().lower()
        ex_abbrevs = {
            s.strip().lower()
            for s in row.get("Abbreviations", "").split(",")
            if s.strip()
        }
        if in_term and in_term in ex_abbrevs:
            return i
        if in_abbrevs and (ex_term in in_abbrevs or ex_abbrevs & in_abbrevs):
            return i
    return None


def _sort_rows(rows):
    return sorted(rows, key=lambda r: (r.get("Term", "").lower(), r.get("Term", "")))


def _write_table(lines, found, rows):
    """Write rows back into `lines`, returning the new file text."""
    sorted_rows = _sort_rows(rows)
    body_md = [_row_to_md(r) for r in sorted_rows]
    if found is None:
        # No table found — append the scaffold table at the end.
        new_lines = list(lines)
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append("## Glossary")
        new_lines.append("")
        new_lines.append(HEADER_LINE)
        new_lines.append(ALIGN_LINE)
        new_lines.extend(body_md)
        return "\n".join(new_lines) + "\n"
    header_idx, align_idx, body_start, body_end = found
    new_lines = (
        list(lines[:body_start]) + body_md + list(lines[body_end:])
    )
    # Preserve trailing newline behaviour.
    text = "\n".join(new_lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def upsert(path, incoming):
    rows, lines, found = read_rows(path)
    # Strip the _line annotation before working on the data model.
    for r in rows:
        r.pop("_line", None)
    idx = _match_existing(rows, incoming)
    action = "inserted"
    conflicts = []
    if idx is None:
        rows.append({col: incoming.get(col, "").strip() for col in COLUMNS})
    else:
        merged, conflicts = _merge_row(rows[idx], incoming)
        rows[idx] = merged
        action = "updated"
    text = _write_table(lines, found, rows)
    Path(path).write_text(text, encoding="utf-8")
    return {"action": action, "conflicts": conflicts, "term": incoming.get("Term", "")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--read", metavar="FILE")
    p.add_argument("--upsert", metavar="FILE")
    p.add_argument("--row", metavar="JSON", help="JSON object for --upsert")
    args = p.parse_args()

    if args.read and args.upsert:
        p.error("--read and --upsert are mutually exclusive")
    if args.read:
        try:
            rows, _, _ = read_rows(args.read)
        except FileNotFoundError:
            print("error: file not found: %s" % args.read, file=sys.stderr)
            return 2
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.upsert:
        if not args.row:
            p.error("--upsert requires --row")
        try:
            incoming = json.loads(args.row)
        except json.JSONDecodeError as e:
            print("error: --row is not valid JSON: %s" % e, file=sys.stderr)
            return 2
        if not isinstance(incoming, dict):
            print("error: --row must be a JSON object", file=sys.stderr)
            return 2
        if not Path(args.upsert).exists():
            print(
                "error: glossary file does not exist: %s\n"
                "Create it from the scaffold in SKILL.md first." % args.upsert,
                file=sys.stderr,
            )
            return 2
        result = upsert(args.upsert, incoming)
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    p.error("provide --read or --upsert")


if __name__ == "__main__":
    sys.exit(main())
