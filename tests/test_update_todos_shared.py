"""Integration test: update-todos resolver consults .agents/dev-skills.yaml."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "update-todos" / "scripts"
sys.path.insert(0, str(SCRIPTS))
# Drop any cached `resolve_config` / `configure` / `read_shared_conventions`
# modules from another skill's scripts dir loaded earlier in this test run,
# so our import resolves against update-todos's scripts (sys.path lookups
# read sys.modules first).
for _mod in ("resolve_config", "configure", "read_shared_conventions"):
    sys.modules.pop(_mod, None)
import resolve_config  # type: ignore  # noqa: E402


SHARED_YAML = """\
schema: dev-skills/v1
docs_root: agent-docs

skills:
  update-todos:
    subdir: tasks
"""


class UpdateTodosSharedTest(unittest.TestCase):
    def setUp(self):
        self._saved = {}
        for k in ("UPDATE_TODOS_ROOT_DIR", "DEV_SKILLS_CONFIG_FILE"):
            self._saved[k] = os.environ.pop(k, None)
        self._cwd = os.getcwd()

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        os.chdir(self._cwd)

    def test_shared_file_wins(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                shared = Path(td) / ".agents" / "dev-skills.yaml"
                shared.parent.mkdir(parents=True)
                shared.write_text(SHARED_YAML, encoding="utf-8")
                os.environ["DEV_SKILLS_CONFIG_FILE"] = str(shared)
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertTrue(
            resolved["root_dir"].endswith(os.path.join("agent-docs", "tasks")),
            msg=resolved["root_dir"],
        )

    def test_env_var_overrides_shared(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                shared = Path(td) / ".agents" / "dev-skills.yaml"
                shared.parent.mkdir(parents=True)
                shared.write_text(SHARED_YAML, encoding="utf-8")
                os.environ["DEV_SKILLS_CONFIG_FILE"] = str(shared)
                os.environ["UPDATE_TODOS_ROOT_DIR"] = "/explicit/override"
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertEqual(resolved["root_dir"], "/explicit/override")

    def test_no_shared_file_uses_default(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertEqual(resolved["root_dir"], "")

    def test_shared_file_with_default_subdir(self):
        """If skills.update-todos block is absent, subdir defaults to 'TODOs'."""
        minimal_yaml = "schema: dev-skills/v1\ndocs_root: docs\n"
        with tempfile.TemporaryDirectory() as td:
            try:
                shared = Path(td) / ".agents" / "dev-skills.yaml"
                shared.parent.mkdir(parents=True)
                shared.write_text(minimal_yaml, encoding="utf-8")
                os.environ["DEV_SKILLS_CONFIG_FILE"] = str(shared)
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertTrue(
            resolved["root_dir"].endswith(os.path.join("docs", "TODOs")),
            msg=resolved["root_dir"],
        )

    def test_shared_default_expiry_days_flows_through(self):
        """default_expiry_days in the shared file should override user-config default."""
        shared_yaml = (
            "schema: dev-skills/v1\n"
            "docs_root: agent-docs\n"
            "\n"
            "skills:\n"
            "  update-todos:\n"
            "    subdir: tasks\n"
            "    default_expiry_days: 42\n"
        )
        with tempfile.TemporaryDirectory() as td:
            try:
                shared = Path(td) / ".agents" / "dev-skills.yaml"
                shared.parent.mkdir(parents=True)
                shared.write_text(shared_yaml, encoding="utf-8")
                os.environ["DEV_SKILLS_CONFIG_FILE"] = str(shared)
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertEqual(resolved.get("default_expiry_days"), "42")

    def test_shared_deprecated_keys_are_ignored(self):
        """Deprecated keys in the shared file should not affect resolution."""
        shared_yaml = (
            "schema: dev-skills/v1\n"
            "docs_root: agent-docs\n"
            "\n"
            "skills:\n"
            "  update-todos:\n"
            "    subdir: tasks\n"
            "    inbox_wip_limit: 999\n"
            "    active_wip_limit: 999\n"
        )
        with tempfile.TemporaryDirectory() as td:
            try:
                shared = Path(td) / ".agents" / "dev-skills.yaml"
                shared.parent.mkdir(parents=True)
                shared.write_text(shared_yaml, encoding="utf-8")
                os.environ["DEV_SKILLS_CONFIG_FILE"] = str(shared)
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertNotIn("inbox_wip_limit", resolved)
        self.assertNotIn("active_wip_limit", resolved)


if __name__ == "__main__":
    unittest.main()
