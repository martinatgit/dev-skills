"""Tests for skills/update-todos/scripts/check_reference_drift.py."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "skills" / "update-todos" / "scripts" / "check_reference_drift.py"


def run(todo_path: Path, cwd: Path | None = None):
    cmd = [sys.executable, str(SCRIPT), "--todo", str(todo_path)]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or todo_path.parent)


TODO_TEMPLATE = """---
id: TODO-20260101-0001
references:
  - path: {ref_path}
    lines: {ref_lines}
    clarified-at-sha: null
    excerpts:
      - lines: {ex_lines}
        text: |
{ex_text}
---

# Test TODO
"""


def write_todo(dir_: Path, ref_path: str, ref_lines: str, ex_lines: str, ex_text: list[str]) -> Path:
    indented = "\n".join("          " + ln for ln in ex_text)
    content = TODO_TEMPLATE.format(
        ref_path=ref_path, ref_lines=ref_lines,
        ex_lines=ex_lines, ex_text=indented,
    )
    todo = dir_ / "TODO-test.md"
    todo.write_text(content, encoding="utf-8")
    return todo


class DriftCheckTests(unittest.TestCase):
    def test_unchanged_excerpt(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "src.txt").write_text("alpha\nbeta\ngamma\ndelta\n", encoding="utf-8")
            todo = write_todo(tdp, "src.txt", "2-3", "2-3", ["beta", "gamma"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: unchanged", result.stdout)

    def test_moved_excerpt(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "src.txt").write_text("inserted\nalpha\nbeta\ngamma\ndelta\n", encoding="utf-8")
            todo = write_todo(tdp, "src.txt", "1-2", "1-2", ["alpha", "beta"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: moved", result.stdout)
            self.assertIn("new-lines: 2-3", result.stdout)

    def test_drifted_excerpt(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "src.txt").write_text(
                "function getData(params) {\n  const x = 1;\n  const result = fetchValue(params);\n  return result;\n}\n",
                encoding="utf-8",
            )
            todo = write_todo(
                tdp, "src.txt", "1-4", "1-4",
                ["function getData(params) {", "  const x = 1;", "  const result = fetchData(params);", "  return result;"],
            )
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: drifted", result.stdout)
            self.assertIn("similarity:", result.stdout)

    def test_gone_excerpt(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "src.txt").write_text("totally different content here\n", encoding="utf-8")
            todo = write_todo(tdp, "src.txt", "1-2", "1-2", ["alpha", "beta"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: gone", result.stdout)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            todo = write_todo(tdp, "does-not-exist.txt", "1-2", "1-2", ["alpha", "beta"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: missing-file", result.stdout)

    def test_ambiguous_match(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "src.txt").write_text(
                "alpha\nbeta\n" * 5,
                encoding="utf-8",
            )
            todo = write_todo(tdp, "src.txt", "5-6", "5-6", ["alpha", "beta"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ambiguous-match:", result.stdout)
            self.assertIn("new-lines: 5-6", result.stdout)

    def test_crlf_normalization(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "src.txt").write_bytes(b"alpha\r\nbeta\r\ngamma\r\n")
            todo = write_todo(tdp, "src.txt", "1-2", "1-2", ["alpha", "beta"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: unchanged", result.stdout)

    def test_trailing_whitespace_normalization(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "src.txt").write_text("alpha   \nbeta\t\n", encoding="utf-8")
            todo = write_todo(tdp, "src.txt", "1-2", "1-2", ["alpha", "beta"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: unchanged", result.stdout)

    def test_diary_reference_existence_only(self):
        """A reference with kind: diary checks existence only; no excerpt match."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "subsystem.md").write_text(
                "# Diary node\n\nFirst entry.\nSecond entry.\n",
                encoding="utf-8",
            )
            todo_text = (
                "---\n"
                "id: TODO-20260101-0001\n"
                "references:\n"
                "  - path: subsystem.md\n"
                "    kind: diary\n"
                "    clarified-at-sha: null\n"
                "---\n\n# Test TODO\n"
            )
            todo = tdp / "TODO-test.md"
            todo.write_text(todo_text, encoding="utf-8")
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("kind: diary", result.stdout)
            self.assertIn("finding: unchanged", result.stdout)
            self.assertNotIn("similarity", result.stdout)
            self.assertNotIn("new-lines", result.stdout)

    def test_rename_detected_excerpt_unchanged(self):
        """A renamed file is detected; excerpt matches at the new path."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            # Init git, commit old file, capture SHA, rename, commit again.
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Test"],
            ):
                subprocess.run(cmd, cwd=tdp, check=True, capture_output=True)
            (tdp / "old.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
            subprocess.run(["git", "add", "old.txt"], cwd=tdp, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tdp, check=True, capture_output=True)
            sha = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=tdp, capture_output=True, text=True, check=True,
            ).stdout.strip()
            subprocess.run(["git", "mv", "old.txt", "new.txt"], cwd=tdp, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "rename"], cwd=tdp, check=True, capture_output=True)

            # TODO references the OLD path with the pre-rename SHA.
            indented = "\n".join("          " + ln for ln in ["alpha", "beta"])
            todo_text = (
                "---\n"
                "id: TODO-rename\n"
                "references:\n"
                "  - path: old.txt\n"
                f"    clarified-at-sha: {sha}\n"
                "    excerpts:\n"
                "      - lines: 1-2\n"
                "        text: |\n"
                f"{indented}\n"
                "---\n\n# Test TODO\n"
            )
            todo = tdp / "TODO-rename-test.md"
            todo.write_text(todo_text, encoding="utf-8")
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("renamed-from: old.txt", result.stdout)
            self.assertIn("path: new.txt", result.stdout)
            self.assertIn("finding: unchanged", result.stdout)

    def test_rename_not_found_falls_back_to_missing_file(self):
        """When the recorded path doesn't exist AND no rename is detected,
        the finding is missing-file (no false renamed-from)."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            # Not in a git repo at all -- rename detection short-circuits.
            todo = write_todo(tdp, "ghost.txt", "1-2", "1-2", ["alpha", "beta"])
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("finding: missing-file", result.stdout)
            self.assertNotIn("renamed-from", result.stdout)

    def test_unreachable_clarified_sha_is_flagged(self):
        """When clarified-at-sha is set but unreachable (rebased away or
        wrong hash), the finding includes sha-unreachable: True."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Test"],
            ):
                subprocess.run(cmd, cwd=tdp, check=True, capture_output=True)
            (tdp / "src.txt").write_text("alpha\nbeta\n", encoding="utf-8")
            subprocess.run(["git", "add", "src.txt"], cwd=tdp, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tdp, check=True, capture_output=True)

            indented = "\n".join("          " + ln for ln in ["alpha", "beta"])
            todo_text = (
                "---\n"
                "id: TODO-unreachable\n"
                "references:\n"
                "  - path: src.txt\n"
                "    clarified-at-sha: deadbee\n"  # not a real SHA
                "    excerpts:\n"
                "      - lines: 1-2\n"
                "        text: |\n"
                f"{indented}\n"
                "---\n\n# Test TODO\n"
            )
            todo = tdp / "TODO-unreach.md"
            todo.write_text(todo_text, encoding="utf-8")
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("sha-unreachable: True", result.stdout)
            self.assertIn("finding: unchanged", result.stdout)

    def test_diary_reference_missing(self):
        """A missing diary reference reports missing-file with kind preserved."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            todo_text = (
                "---\n"
                "id: TODO-20260101-0001\n"
                "references:\n"
                "  - path: gone.md\n"
                "    kind: diary\n"
                "    clarified-at-sha: null\n"
                "---\n\n# Test TODO\n"
            )
            todo = tdp / "TODO-test.md"
            todo.write_text(todo_text, encoding="utf-8")
            result = run(todo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("kind: diary", result.stdout)
            self.assertIn("finding: missing-file", result.stdout)


if __name__ == "__main__":
    unittest.main()
