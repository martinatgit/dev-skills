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
        (tmp / "skills").mkdir()
        (tmp / "skills" / "alpha" / "scripts").mkdir(parents=True)
        (tmp / "skills" / "beta" / "scripts").mkdir(parents=True)
        (tmp / "skills" / "no-scripts").mkdir()
        return tmp

    def test_copies_into_each_scripts_dir(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = self._populate_fake_repo(Path(td))
            result = subprocess.run(
                [sys.executable, str(REFRESHER), "--repo-root", str(tmp)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            alpha = tmp / "skills" / "alpha" / "scripts" / "read_shared_conventions.py"
            beta = tmp / "skills" / "beta" / "scripts" / "read_shared_conventions.py"
            self.assertEqual(alpha.read_text(encoding="utf-8"), "# canonical template\n")
            self.assertEqual(beta.read_text(encoding="utf-8"), "# canonical template\n")
            self.assertFalse((tmp / "skills" / "no-scripts" / "scripts").exists())

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
