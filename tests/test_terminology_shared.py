"""Integration test: terminology resolver consults .agents/dev-skills.yaml."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "skills" / "terminology" / "scripts"
sys.path.insert(0, str(SCRIPTS))

# Defend against sys.modules collision with other per-skill test files.
for mod_name in ("resolve_config", "configure", "read_shared_conventions"):
    sys.modules.pop(mod_name, None)

import resolve_config  # type: ignore  # noqa: E402


SHARED_YAML = """\
schema: dev-skills/v1
docs_root: agent-docs

skills:
  terminology:
    filename: terms.md
"""


class TerminologySharedTest(unittest.TestCase):
    def setUp(self):
        self._saved = {}
        for k in ("TERMINOLOGY_TERMINOLOGY_FILE", "DEV_SKILLS_CONFIG_FILE"):
            self._saved[k] = os.environ.pop(k, None)
        self._cwd = os.getcwd()

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        os.chdir(self._cwd)

    def test_shared_file_renames_terminology_file(self):
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
            resolved["terminology_file"].endswith(os.path.join("agent-docs", "terms.md")),
            msg=resolved["terminology_file"],
        )

    def test_env_var_overrides_shared(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                shared = Path(td) / ".agents" / "dev-skills.yaml"
                shared.parent.mkdir(parents=True)
                shared.write_text(SHARED_YAML, encoding="utf-8")
                os.environ["DEV_SKILLS_CONFIG_FILE"] = str(shared)
                os.environ["TERMINOLOGY_TERMINOLOGY_FILE"] = "/explicit/override.md"
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertEqual(resolved["terminology_file"], "/explicit/override.md")

    def test_no_shared_file_uses_default(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                (Path(td) / ".git").mkdir()
                os.chdir(td)
                resolved = resolve_config.resolve_all()
            finally:
                os.chdir(self._cwd)
        self.assertEqual(resolved["terminology_file"], "")

    def test_shared_file_with_default_filename(self):
        """If skills.terminology block is absent, filename defaults to 'terminology.md'."""
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
            resolved["terminology_file"].endswith(os.path.join("docs", "terminology.md")),
            msg=resolved["terminology_file"],
        )


if __name__ == "__main__":
    unittest.main()
