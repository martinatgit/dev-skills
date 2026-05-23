"""Tests for tier-key config and WIP-key deprecation in update-todos."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "update-todos" / "scripts"
CONFIGURE = SCRIPTS / "configure.py"
RESOLVE = SCRIPTS / "resolve_config.py"


def run(script, *args, env=None, cwd=None):
    cmd = [sys.executable, str(script), *args]
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=full_env, cwd=cwd)


class TierKeysTests(unittest.TestCase):
    def test_new_tier_keys_have_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"HOME": td, "XDG_CONFIG_HOME": str(Path(td) / "config")}
            result = run(RESOLVE, "--all", env=env, cwd=td)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("health_tier_healthy_max=20", result.stdout)
            self.assertIn("health_tier_guidance_max=60", result.stdout)
            self.assertIn("health_tier_strong_threshold=60", result.stdout)
            self.assertIn("auto_maintenance_on_resolve=false", result.stdout)

    def test_env_var_overrides_tier(self):
        with tempfile.TemporaryDirectory() as td:
            env = {
                "HOME": td,
                "XDG_CONFIG_HOME": str(Path(td) / "config"),
                "UPDATE_TODOS_HEALTH_TIER_HEALTHY_MAX": "10",
            }
            result = run(RESOLVE, "health_tier_healthy_max", env=env, cwd=td)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("10", result.stdout)

    def test_deprecated_wip_key_emits_warning(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"HOME": td, "XDG_CONFIG_HOME": str(Path(td) / "config")}
            result = run(
                CONFIGURE, "--scope", "user", "--non-interactive",
                "--inbox-wip-limit", "30",
                env=env, cwd=td,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("deprecated", result.stderr.lower())
            written = (Path(td) / "config" / "update-todos" / "config.yaml").read_text(encoding="utf-8")
            self.assertIn("health_tier_guidance_max: 30", written)
            self.assertNotIn("inbox_wip_limit:", written)


if __name__ == "__main__":
    unittest.main()
