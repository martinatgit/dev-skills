"""Integration test: create-tutorial resolver consults .agents/dev-skills.yaml."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "create-tutorial" / "scripts"
sys.path.insert(0, str(SCRIPTS))

# Defend against sys.modules collision with other per-skill test files.
for mod_name in ("resolve_config", "configure", "read_shared_conventions"):
    sys.modules.pop(mod_name, None)

import resolve_config  # type: ignore  # noqa: E402


SHARED_YAML = """\
schema: dev-skills/v1
docs_root: agent-docs

skills:
  create-tutorial:
    subdir: lessons
"""


class CreateTutorialSharedTest(unittest.TestCase):
    def setUp(self):
        self._saved = {}
        for k in ("CREATE_TUTORIAL_TUTORIALS_DIR", "DEV_SKILLS_CONFIG_FILE"):
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
            resolved["tutorials_dir"].endswith(os.path.join("agent-docs", "lessons")),
            msg=resolved["tutorials_dir"],
        )

    def test_env_var_overrides_shared(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                shared = Path(td) / ".agents" / "dev-skills.yaml"
                shared.parent.mkdir(parents=True)
                shared.write_text(SHARED_YAML, encoding="utf-8")
                os.environ["DEV_SKILLS_CONFIG_FILE"] = str(shared)
                os.environ["CREATE_TUTORIAL_TUTORIALS_DIR"] = "/explicit/override"
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertEqual(resolved["tutorials_dir"], "/explicit/override")

    def test_no_shared_file_uses_default(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertEqual(resolved["tutorials_dir"], "")

    def test_shared_file_with_default_subdir(self):
        """If skills.create-tutorial block is absent, subdir defaults to 'tutorials'."""
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
            resolved["tutorials_dir"].endswith(os.path.join("docs", "tutorials")),
            msg=resolved["tutorials_dir"],
        )


if __name__ == "__main__":
    unittest.main()
