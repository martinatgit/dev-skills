"""Tests for scripts/refresh-shared-reader.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFRESHER = REPO_ROOT / "scripts" / "refresh-shared-reader.py"


class RefresherTest(unittest.TestCase):
    def _populate_fake_repo(self, tmp: Path) -> Path:
        (tmp / "template" / "scripts").mkdir(parents=True)
        (tmp / "template" / "scripts" / "read_shared_conventions.py").write_text(
            "# canonical template\n", encoding="utf-8"
        )
        (tmp / "template" / "scripts" / "find_project_root.py").write_text(
            "# canonical find_project_root\n", encoding="utf-8"
        )
        (tmp / "skills").mkdir()
        # alpha/beta already ship stale copies of both stamped scripts: the
        # refresher updates existing copies but does not invent new ones.
        for skill in ("alpha", "beta"):
            scripts_dir = tmp / "skills" / skill / "scripts"
            scripts_dir.mkdir(parents=True)
            (scripts_dir / "read_shared_conventions.py").write_text(
                "# stale\n", encoding="utf-8"
            )
            (scripts_dir / "find_project_root.py").write_text(
                "# stale\n", encoding="utf-8"
            )
        (tmp / "skills" / "no-scripts").mkdir()
        # gamma ships only one of the two stamped scripts.
        gamma_scripts = tmp / "skills" / "gamma" / "scripts"
        gamma_scripts.mkdir(parents=True)
        (gamma_scripts / "read_shared_conventions.py").write_text(
            "# stale\n", encoding="utf-8"
        )
        return tmp

    def test_copies_into_each_scripts_dir(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = self._populate_fake_repo(Path(td))
            result = subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for skill in ("alpha", "beta"):
                reader = tmp / "skills" / skill / "scripts" / "read_shared_conventions.py"
                finder = tmp / "skills" / skill / "scripts" / "find_project_root.py"
                self.assertEqual(
                    reader.read_text(encoding="utf-8"), "# canonical template\n"
                )
                self.assertEqual(
                    finder.read_text(encoding="utf-8"), "# canonical find_project_root\n"
                )
            self.assertFalse((tmp / "skills" / "no-scripts" / "scripts").exists())

    def test_skill_with_only_one_stamped_script_is_not_given_the_other(self):
        """A skill that ships one stamped script but not the other keeps it
        that way: the refresher must not invent files a skill never asked for."""
        with tempfile.TemporaryDirectory() as td:
            tmp = self._populate_fake_repo(Path(td))
            result = subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            gamma_scripts = tmp / "skills" / "gamma" / "scripts"
            self.assertEqual(
                (gamma_scripts / "read_shared_conventions.py").read_text(encoding="utf-8"),
                "# canonical template\n",
            )
            self.assertFalse((gamma_scripts / "find_project_root.py").exists())

    def test_idempotent_no_diff_on_second_run(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = self._populate_fake_repo(Path(td))
            subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                check=True, capture_output=True,
            )
            target = tmp / "skills" / "alpha" / "scripts" / "read_shared_conventions.py"
            first_mtime = target.stat().st_mtime_ns
            # Touch the template to bump its mtime, then re-run. The refresher
            # must NOT touch the target because content is unchanged.
            tpl = tmp / "template" / "scripts" / "read_shared_conventions.py"
            tpl.write_text("# canonical template\n", encoding="utf-8")
            subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                check=True, capture_output=True,
            )
            self.assertEqual(
                target.read_text(encoding="utf-8"), "# canonical template\n"
            )
            # Real idempotency claim: target file unchanged.
            self.assertEqual(target.stat().st_mtime_ns, first_mtime)


if __name__ == "__main__":
    unittest.main()
