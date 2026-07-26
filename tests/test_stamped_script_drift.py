"""Tests for the generalised stamped-script drift check."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAMPED = ("read_shared_conventions.py", "find_project_root.py")


def _skeleton(tmp: Path) -> Path:
    for sub in ("evals", "skills", "template"):
        shutil.copytree(REPO_ROOT / sub, tmp / sub)
    (tmp / ".claude-plugin").mkdir()
    shutil.copyfile(
        REPO_ROOT / ".claude-plugin" / "marketplace.json",
        tmp / ".claude-plugin" / "marketplace.json",
    )
    shutil.copyfile(REPO_ROOT / "README.md", tmp / "README.md")
    return tmp


def _run(cwd: Path):
    return subprocess.run(
        [sys.executable, str(cwd / "evals" / "run.py")],
        capture_output=True, text=True, cwd=cwd,
    )


class StampedScriptDriftTests(unittest.TestCase):
    def test_repo_has_no_drift(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "evals" / "run.py")],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_stamped_script_is_identical_across_skills(self):
        """The invariant itself, independent of evals/run.py."""
        for filename in STAMPED:
            canonical = (REPO_ROOT / "template" / "scripts" / filename)
            expected = canonical.read_bytes().replace(b"\r\n", b"\n")
            copies = sorted(
                (REPO_ROOT / "skills").glob("*/scripts/" + filename))
            self.assertGreater(len(copies), 0, f"no copies of {filename}")
            for copy in copies:
                self.assertEqual(
                    copy.read_bytes().replace(b"\r\n", b"\n"), expected,
                    f"{copy} differs from {canonical}",
                )

    def test_detects_forked_find_project_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = _skeleton(Path(td))
            target = root / "skills" / "terminology" / "scripts" / \
                "find_project_root.py"
            target.write_text(
                target.read_text(encoding="utf-8") + "\n# local fork\n",
                encoding="utf-8",
            )
            result = _run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("find_project_root.py", result.stdout)

    def test_crlf_copy_is_not_drift(self):
        """A CRLF checkout must not be reported as drift."""
        with tempfile.TemporaryDirectory() as td:
            root = _skeleton(Path(td))
            target = root / "skills" / "example-skill" / "scripts" / \
                "find_project_root.py"
            data = target.read_bytes().replace(b"\r\n", b"\n")
            target.write_bytes(data.replace(b"\n", b"\r\n"))
            result = _run(root)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
