"""Tests for scripts/refresh-shared-reader.py."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFRESHER = REPO_ROOT / "scripts" / "refresh-shared-reader.py"


class RefresherTest(unittest.TestCase):
    def _make_fake_repo(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "template" / "scripts").mkdir(parents=True)
        (tmp / "template" / "scripts" / "read_shared_conventions.py").write_text(
            "# canonical template\n", encoding="utf-8"
        )
        (tmp / "skills").mkdir()
        (tmp / "skills" / "alpha" / "scripts").mkdir(parents=True)
        (tmp / "skills" / "beta" / "scripts").mkdir(parents=True)
        (tmp / "skills" / "no-scripts").mkdir()
        return tmp

    def test_copies_into_each_scripts_dir(self):
        tmp = self._make_fake_repo()
        try:
            result = subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            alpha = tmp / "skills" / "alpha" / "scripts" / "read_shared_conventions.py"
            beta = tmp / "skills" / "beta" / "scripts" / "read_shared_conventions.py"
            self.assertEqual(alpha.read_text(encoding="utf-8"), "# canonical template\n")
            self.assertEqual(beta.read_text(encoding="utf-8"), "# canonical template\n")
            # no-scripts skill must NOT have one created.
            self.assertFalse((tmp / "skills" / "no-scripts" / "scripts").exists())
        finally:
            shutil.rmtree(tmp)

    def test_idempotent_no_diff_on_second_run(self):
        tmp = self._make_fake_repo()
        try:
            subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                check=True, capture_output=True,
            )
            target = tmp / "skills" / "alpha" / "scripts" / "read_shared_conventions.py"
            first_mtime = target.stat().st_mtime_ns
            # Touch the template to bump its mtime, then re-run.
            tpl = tmp / "template" / "scripts" / "read_shared_conventions.py"
            tpl.write_text("# canonical template\n", encoding="utf-8")
            subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                check=True, capture_output=True,
            )
            # Byte-for-byte identical; content has not changed.
            self.assertEqual(
                target.read_text(encoding="utf-8"), "# canonical template\n"
            )
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
