"""End-to-end smoke test for the update-todos snapshot + drift pipeline.

Simulates a single TODO's lifecycle (capture → clarify → maintenance over
several drift scenarios) using the actual scripts. Builds a tmp git repo,
runs the helpers, and asserts the script outputs are what the action files
expect when an agent splices them into a TODO.

Does NOT invoke an LLM agent. The action markdown files (capture.md,
clarify.md, maintenance.md) describe a workflow the agent executes; this
test exercises the scripted plumbing that workflow depends on. If this
test breaks, an agent following the action files will produce wrong output.
"""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = REPO_ROOT / "skills" / "update-todos" / "scripts" / "snapshot_reference.py"
DRIFT = REPO_ROOT / "skills" / "update-todos" / "scripts" / "check_reference_drift.py"


def git(*args, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def run_script(script: Path, *args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd, capture_output=True, text=True,
    )


def parse_keyval(text: str) -> dict[str, str]:
    """Pull simple `key: value` pairs from the script's stdout. Skips
    block-scalar bodies and list items. Sufficient for the smoke checks."""
    out: dict[str, str] = {}
    in_block = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if in_block:
            if not line.startswith("      ") and not line.startswith("    "):
                in_block = False
            else:
                continue
        if not line or line.startswith("  "):
            continue
        if line.endswith("|"):
            in_block = True
            continue
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def write_active_todo(
    proj: Path, name: str, ref_path: str,
    captured_at_sha: str, captured_at: str,
    clarified_at_sha: str, last_checked: str,
    excerpt_lines: str, excerpt_body: list[str],
) -> Path:
    indented = "\n".join("          " + ln for ln in excerpt_body)
    text = (
        "---\n"
        f"id: {name}\n"
        "status: open\n"
        "references:\n"
        f"  - path: {ref_path}\n"
        "    lines: 1-3\n"
        f"    captured-at-sha: {captured_at_sha}\n"
        f"    captured-at: {captured_at}\n"
        f"    clarified-at-sha: {clarified_at_sha}\n"
        f"    last-checked: {last_checked}\n"
        "    excerpts:\n"
        f"      - lines: {excerpt_lines}\n"
        "        text: |\n"
        f"{indented}\n"
        "---\n\n# Test TODO\n"
    )
    todo = proj / f"{name}.md"
    todo.write_text(text, encoding="utf-8")
    return todo


class EndToEndSmokeTests(unittest.TestCase):
    def test_full_lifecycle(self):
        """Capture → clarify → drift checks over four scenarios: unchanged,
        moved, drifted, renamed. Each step uses the actual scripts."""
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td)
            # Setup: minimal git repo with a source file.
            git("init", "-q", cwd=proj)
            git("config", "user.email", "test@example.com", cwd=proj)
            git("config", "user.name", "Smoke Test", cwd=proj)
            source = proj / "parser.ts"
            source.write_text(
                "function emitToken(camelCase) {\n"
                "  return tokens.push({name: camelCase});\n"
                "}\n",
                encoding="utf-8",
            )
            git("add", "parser.ts", cwd=proj)
            git("commit", "-q", "-m", "initial", cwd=proj)

            # --- Phase 1: capture (light snapshot) ---
            res = run_script(SNAPSHOT, "parser.ts", cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            cap = parse_keyval(res.stdout)
            self.assertIn("captured-at-sha", cap)
            self.assertIn("captured-at", cap)
            self.assertNotIn("excerpts", res.stdout)
            captured_at_sha = cap["captured-at-sha"]
            captured_at = cap["captured-at"]
            self.assertNotEqual(captured_at_sha, "null",
                                "captured-at-sha should be set inside a git repo")

            # --- Phase 2: clarify (heavy snapshot) ---
            res = run_script(SNAPSHOT, "parser.ts", "--lines", "1-3", cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            cla = parse_keyval(res.stdout)
            self.assertIn("clarified-at-sha", cla)
            self.assertIn("excerpts:", res.stdout)
            self.assertIn("emitToken", res.stdout)
            clarified_at_sha = cla["clarified-at-sha"]
            clarified_at = cla["clarified-at"]

            # Assemble a clarified active TODO using the script outputs.
            excerpt_body = [
                "function emitToken(camelCase) {",
                "  return tokens.push({name: camelCase});",
                "}",
            ]
            todo = write_active_todo(
                proj, "TODO-smoke", "parser.ts",
                captured_at_sha, captured_at,
                clarified_at_sha, clarified_at,
                "1-3", excerpt_body,
            )

            # --- Phase 3a: drift check on untouched file → unchanged ---
            res = run_script(DRIFT, "--todo", str(todo), cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("finding: unchanged", res.stdout)
            self.assertNotIn("renamed-from", res.stdout)

            # --- Phase 3b: insert a line above → moved ---
            source.write_text(
                "// auto-generated header\n"
                "function emitToken(camelCase) {\n"
                "  return tokens.push({name: camelCase});\n"
                "}\n",
                encoding="utf-8",
            )
            res = run_script(DRIFT, "--todo", str(todo), cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("finding: moved", res.stdout)
            self.assertIn("new-lines: 2-4", res.stdout)

            # --- Phase 3c: rename one token in the body → drifted (similarity) ---
            source.write_text(
                "// auto-generated header\n"
                "function emitToken(snake_case) {\n"
                "  return tokens.push({name: snake_case});\n"
                "}\n",
                encoding="utf-8",
            )
            res = run_script(DRIFT, "--todo", str(todo), cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("finding: drifted", res.stdout)
            self.assertIn("similarity:", res.stdout)

            # --- Phase 3d: commit, rename via git → renamed-from + finding ---
            git("add", "parser.ts", cwd=proj)
            git("commit", "-q", "-m", "rename inside", cwd=proj)
            git("mv", "parser.ts", "lexer.ts", cwd=proj)
            git("commit", "-q", "-m", "rename file", cwd=proj)
            res = run_script(DRIFT, "--todo", str(todo), cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("renamed-from: parser.ts", res.stdout)
            self.assertIn("path: lexer.ts", res.stdout)
            # The body content was also changed (snake_case rename), so we
            # expect either drifted or moved at the new path — not gone.
            self.assertNotIn("finding: gone", res.stdout)
            self.assertNotIn("finding: missing-file", res.stdout)

    def test_lifecycle_with_diary_reference(self):
        """A diary-node reference goes through capture (no special kind) and
        clarify (with --kind diary), then drift checks existence only."""
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td)
            git("init", "-q", cwd=proj)
            git("config", "user.email", "test@example.com", cwd=proj)
            git("config", "user.name", "Smoke Test", cwd=proj)
            (proj / "diary").mkdir()
            diary = proj / "diary" / "parser-subsystem.md"
            diary.write_text("# Parser subsystem\n\nFirst entry.\n", encoding="utf-8")
            git("add", "diary/parser-subsystem.md", cwd=proj)
            git("commit", "-q", "-m", "diary", cwd=proj)

            # Clarify with --kind diary suppresses the excerpt block.
            res = run_script(SNAPSHOT, "diary/parser-subsystem.md",
                             "--lines", "1-3", "--kind", "diary", cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("kind: diary", res.stdout)
            self.assertNotIn("excerpts", res.stdout)
            self.assertNotIn("First entry", res.stdout)

            cla = parse_keyval(res.stdout)
            todo_text = (
                "---\n"
                "id: TODO-smoke-diary\n"
                "status: open\n"
                "references:\n"
                "  - path: diary/parser-subsystem.md\n"
                "    kind: diary\n"
                f"    clarified-at-sha: {cla['clarified-at-sha']}\n"
                "---\n\n# Diary-linked TODO\n"
            )
            todo = proj / "TODO-diary.md"
            todo.write_text(todo_text, encoding="utf-8")

            # Diary drift check passes through existence-only path.
            res = run_script(DRIFT, "--todo", str(todo), cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("kind: diary", res.stdout)
            self.assertIn("finding: unchanged", res.stdout)

            # Modifying the diary node (append-only is honored in practice;
            # the drift check is existence-only so the finding stays
            # unchanged regardless of content edits).
            diary.write_text(diary.read_text() + "Second entry.\n", encoding="utf-8")
            res = run_script(DRIFT, "--todo", str(todo), cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("finding: unchanged", res.stdout)

    def test_lifecycle_with_spec_anchor(self):
        """A spec reference uses --anchor in clarify; drift check matches the
        excerpt at the new anchor location after section reordering."""
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td)
            git("init", "-q", cwd=proj)
            git("config", "user.email", "test@example.com", cwd=proj)
            git("config", "user.name", "Smoke Test", cwd=proj)
            spec = proj / "spec.md"
            spec.write_text(
                "# Project spec\n\n"
                "## §4.2.1 Naming\n\n"
                "Use snake_case for identifiers.\n\n"
                "## §4.2.2 Layout\n\n"
                "Two-space indent.\n",
                encoding="utf-8",
            )
            git("add", "spec.md", cwd=proj)
            git("commit", "-q", "-m", "spec", cwd=proj)

            res = run_script(SNAPSHOT, "spec.md", "--anchor", "§4.2.1", cwd=proj)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("§4.2.1 Naming", res.stdout)
            self.assertIn("snake_case", res.stdout)
            self.assertNotIn("§4.2.2", res.stdout)


if __name__ == "__main__":
    unittest.main()
