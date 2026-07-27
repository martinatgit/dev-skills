"""Tests for check_registration() in evals/run.py."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN = REPO_ROOT / "evals" / "run.py"


def _skeleton(tmp: Path) -> Path:
    """Copy the parts of the repo evals/run.py reads."""
    for sub in ("evals", "skills", "template"):
        if (REPO_ROOT / sub).is_dir():
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


class RegistrationCheckTests(unittest.TestCase):
    def test_repo_is_fully_registered(self):
        """Every skill on disk is in both the README and the marketplace."""
        result = subprocess.run(
            [sys.executable, str(RUN)], capture_output=True, text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_detects_skill_missing_from_marketplace(self):
        with tempfile.TemporaryDirectory() as td:
            root = _skeleton(Path(td))
            mp = root / ".claude-plugin" / "marketplace.json"
            data = json.loads(mp.read_text(encoding="utf-8"))
            dropped = data["plugins"][0]["skills"].pop()
            mp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = _run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(Path(dropped).name, result.stdout)

    def test_detects_skill_missing_from_readme(self):
        with tempfile.TemporaryDirectory() as td:
            root = _skeleton(Path(td))
            readme = root / "README.md"
            text = readme.read_text(encoding="utf-8")
            readme.write_text(
                text.replace("](skills/terminology/SKILL.md)", "](#)"),
                encoding="utf-8",
            )
            result = _run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("terminology", result.stdout)

    def test_detects_marketplace_entry_without_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = _skeleton(Path(td))
            mp = root / ".claude-plugin" / "marketplace.json"
            data = json.loads(mp.read_text(encoding="utf-8"))
            data["plugins"][0]["skills"].append("./skills/does-not-exist")
            mp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = _run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does-not-exist", result.stdout)


if __name__ == "__main__":
    unittest.main()
