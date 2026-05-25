"""Tests for the maintain-action config keys in developer-diary."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "developer-diary" / "scripts"
CONFIGURE = SCRIPTS / "configure.py"
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


if __name__ == "__main__":
    unittest.main()
