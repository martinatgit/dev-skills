"""Tests for template/scripts/read_shared_conventions.py."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_SCRIPTS = REPO_ROOT / "template" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(TEMPLATE_SCRIPTS))
import read_shared_conventions as rsc  # type: ignore  # noqa: E402


class ResolvePathTest(unittest.TestCase):
    def setUp(self):
        self._saved_env = os.environ.pop("DEV_SKILLS_CONFIG_FILE", None)

    def tearDown(self):
        if self._saved_env is not None:
            os.environ["DEV_SKILLS_CONFIG_FILE"] = self._saved_env

    def test_env_var_wins(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "custom.yaml"
            os.environ["DEV_SKILLS_CONFIG_FILE"] = str(target)
            self.assertEqual(rsc._resolve_path(Path(td)), target)

    def test_default_path(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(
                rsc._resolve_path(Path(td)),
                Path(td) / ".agents" / "dev-skills.yaml",
            )


class LoadTest(unittest.TestCase):
    def setUp(self):
        self._saved_env = os.environ.pop("DEV_SKILLS_CONFIG_FILE", None)
        rsc._WARNED.clear()

    def tearDown(self):
        if self._saved_env is not None:
            os.environ["DEV_SKILLS_CONFIG_FILE"] = self._saved_env
        rsc._WARNED.clear()

    def _load_fixture(self, name):
        os.environ["DEV_SKILLS_CONFIG_FILE"] = str(FIXTURES / name)
        return rsc.load(FIXTURES)

    def test_missing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(rsc.load(Path(td)))

    def test_valid_file_full(self):
        data = self._load_fixture("valid.yaml")
        self.assertEqual(data["docs_root"], "agent-docs")
        self.assertIn("terminology", data["skills"])
        self.assertEqual(data["skills"]["terminology"]["filename"], "terms.md")
        self.assertEqual(
            data["skills"]["developer-diary"]["node_token_limit"], "4000"
        )

    def test_docs_root_only(self):
        data = self._load_fixture("docs_root_only.yaml")
        self.assertEqual(data["docs_root"], "docs")
        self.assertEqual(data["skills"], {})

    def test_no_schema_returns_none(self):
        self.assertIsNone(self._load_fixture("no_schema.yaml"))

    def test_wrong_schema_returns_none(self):
        self.assertIsNone(self._load_fixture("wrong_schema.yaml"))

    def test_malformed_yaml_returns_none(self):
        self.assertIsNone(self._load_fixture("malformed.yaml"))

    def test_warn_once_for_no_schema(self):
        """A foreign file warns once per process, not once per call."""
        import io
        from contextlib import redirect_stderr
        # First call: emits warning.
        buf1 = io.StringIO()
        with redirect_stderr(buf1):
            self.assertIsNone(self._load_fixture("no_schema.yaml"))
        self.assertIn("without dev-skills/v1 schema marker", buf1.getvalue())
        # Second call to the same file: no new warning.
        buf2 = io.StringIO()
        with redirect_stderr(buf2):
            self.assertIsNone(self._load_fixture("no_schema.yaml"))
        self.assertEqual(buf2.getvalue(), "")

    def test_non_utf8_returns_none(self):
        """Soft-refuse contract: binary / non-UTF-8 files do not crash."""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / ".agents" / "dev-skills.yaml"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"\x80\x81\x82 not utf-8 at all\n")
            self.assertIsNone(rsc.load(Path(td)))

    def test_utf8_bom_is_accepted(self):
        """UTF-8 BOM is silently stripped, not treated as a foreign file."""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / ".agents" / "dev-skills.yaml"
            target.parent.mkdir(parents=True)
            target.write_bytes(
                b"\xef\xbb\xbfschema: dev-skills/v1\ndocs_root: agent-docs\n"
            )
            data = rsc.load(Path(td))
            self.assertIsNotNone(data)
            self.assertEqual(data["docs_root"], "agent-docs")


class ParseYamlTest(unittest.TestCase):
    def test_flat_keys(self):
        text = "schema: dev-skills/v1\ndocs_root: agent-docs\n"
        self.assertEqual(
            rsc._parse_yaml(text),
            {"schema": "dev-skills/v1", "docs_root": "agent-docs"},
        )

    def test_nested_one_level(self):
        text = (
            "schema: dev-skills/v1\n"
            "skills:\n"
            "  terminology:\n"
            "    filename: terms.md\n"
        )
        self.assertEqual(
            rsc._parse_yaml(text),
            {
                "schema": "dev-skills/v1",
                "skills": {"terminology": {"filename": "terms.md"}},
            },
        )

    def test_quoted_values(self):
        text = 'schema: "dev-skills/v1"\ndocs_root: \'agent-docs\'\n'
        self.assertEqual(
            rsc._parse_yaml(text)["docs_root"], "agent-docs"
        )

    def test_comments_stripped(self):
        text = "# leading comment\nschema: dev-skills/v1  # trailing\n"
        self.assertEqual(
            rsc._parse_yaml(text), {"schema": "dev-skills/v1"}
        )

    def test_missing_colon_raises(self):
        with self.assertRaises(ValueError):
            rsc._parse_yaml("schema dev-skills/v1\n")

    def test_empty_file(self):
        self.assertEqual(rsc._parse_yaml(""), {})


if __name__ == "__main__":
    unittest.main()
