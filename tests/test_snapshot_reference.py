"""Tests for skills/update-todos/scripts/snapshot_reference.py."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "skills" / "update-todos" / "scripts" / "snapshot_reference.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "snapshot"


def run(*args, cwd=None):
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or REPO_ROOT)


class SnapshotReferenceTests(unittest.TestCase):
    def test_lightweight_mode_emits_captured_at_only(self):
        result = run(str(FIXTURES / "sample.txt"))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        self.assertIn("captured-at-sha:", out)
        self.assertIn("captured-at:", out)
        self.assertNotIn("excerpts:", out)
        self.assertNotIn("clarified-at-sha:", out)

    def test_heavy_mode_emits_excerpt_and_clarified_sha(self):
        result = run(str(FIXTURES / "sample.txt"), "--lines", "3-5")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        self.assertIn("clarified-at-sha:", out)
        self.assertIn("excerpts:", out)
        self.assertIn("line 3", out)
        self.assertIn("line 4", out)
        self.assertIn("line 5", out)
        self.assertNotIn("line 2", out)
        self.assertNotIn("line 6", out)

    def test_lines_format_validation(self):
        result = run(str(FIXTURES / "sample.txt"), "--lines", "5-3")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid", result.stderr.lower())

    def test_50_line_hard_refuse(self):
        result = run(str(FIXTURES / "big.txt"), "--lines", "1-55")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("50", result.stderr)

    def test_missing_file(self):
        result = run(str(FIXTURES / "does-not-exist.txt"), "--lines", "1-3")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr.lower())

    def test_binary_file_detection(self):
        result = run(str(FIXTURES / "binary.bin"), "--lines", "1-3")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        self.assertIn("binary: true", out)
        self.assertNotIn("line", out)

    def test_git_unavailable_flag(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "loose.txt"
            target.write_text("a\nb\nc\n", encoding="utf-8")
            result = run(str(target), cwd=td)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("captured-at-sha: null", result.stdout)
            self.assertIn("git-unavailable: true", result.stdout)


if __name__ == "__main__":
    unittest.main()
