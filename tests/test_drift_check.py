"""Tests for the drift check added to evals/run.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals"))
import run  # type: ignore  # noqa: E402


class DriftCheckTest(unittest.TestCase):
    def test_no_drift_today(self):
        """Once Task 2 stamps the per-skill copies, drift must be zero."""
        problems = run.check_stamped_script_drift()
        self.assertEqual(problems, [], "\n".join(problems))

    def test_drift_check_function_exists(self):
        self.assertTrue(callable(getattr(run, "check_stamped_script_drift", None)))


if __name__ == "__main__":
    unittest.main()
