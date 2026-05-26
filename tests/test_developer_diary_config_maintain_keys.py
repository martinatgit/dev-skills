"""Tests for the maintain-action config keys in developer-diary."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "developer-diary" / "scripts"
CONFIGURE = SCRIPTS / "configure.py"  # used by upcoming TodosCouplingTests
RESOLVE = SCRIPTS / "resolve_config.py"


def run(script, *args, env=None, cwd=None):
    cmd = [sys.executable, str(script), *args]
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=full_env, cwd=cwd)


class MaintainKeyDefaultsTests(unittest.TestCase):
    def test_three_new_keys_default_to_empty(self):
        with tempfile.TemporaryDirectory() as td:
            env = {
                "HOME": td,
                "XDG_CONFIG_HOME": str(Path(td) / "config"),
            }
            result = run(RESOLVE, "--all", env=env, cwd=td)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("requirements_dir=", result.stdout)
            self.assertIn("todos_inbox_dir=", result.stdout)
            self.assertIn("todos_archive_dir=", result.stdout)
            for line in result.stdout.splitlines():
                k, _, v = line.partition("=")
                if k in {"requirements_dir", "todos_inbox_dir", "todos_archive_dir"}:
                    self.assertEqual(v, "", f"{k} should default to empty, got {v!r}")


class TodosCouplingTests(unittest.TestCase):
    def _project_root(self, td):
        # configure.py with --scope project needs a project marker.
        # find_project_root.py looks for .git, package.json, etc.
        proot = Path(td) / "proj"
        proot.mkdir()
        (proot / ".git").mkdir()
        return proot

    def test_inbox_without_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            proot = self._project_root(td)
            env = {"HOME": td, "XDG_CONFIG_HOME": str(Path(td) / "config")}
            result = run(
                CONFIGURE,
                "--scope", "project",
                "--non-interactive",
                "--root-dir", "doc/developer-diary",
                "--todos-inbox-dir", "doc/TODOs/inbox",
                # deliberately omit --todos-archive-dir
                env=env,
                cwd=proot,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("todos_archive_dir", result.stderr)

    def test_archive_without_inbox_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            proot = self._project_root(td)
            env = {"HOME": td, "XDG_CONFIG_HOME": str(Path(td) / "config")}
            result = run(
                CONFIGURE,
                "--scope", "project",
                "--non-interactive",
                "--root-dir", "doc/developer-diary",
                "--todos-archive-dir", "doc/TODOs/archive",
                env=env,
                cwd=proot,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("todos_inbox_dir", result.stderr)

    def test_both_set_is_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            proot = self._project_root(td)
            env = {"HOME": td, "XDG_CONFIG_HOME": str(Path(td) / "config")}
            result = run(
                CONFIGURE,
                "--scope", "project",
                "--non-interactive",
                "--root-dir", "doc/developer-diary",
                "--todos-inbox-dir", "doc/TODOs/inbox",
                "--todos-archive-dir", "doc/TODOs/archive",
                env=env,
                cwd=proot,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_neither_set_is_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            proot = self._project_root(td)
            env = {"HOME": td, "XDG_CONFIG_HOME": str(Path(td) / "config")}
            result = run(
                CONFIGURE,
                "--scope", "project",
                "--non-interactive",
                "--root-dir", "doc/developer-diary",
                env=env,
                cwd=proot,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
