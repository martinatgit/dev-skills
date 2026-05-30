"""Tests for scripts/setup-conventions.py."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "setup-conventions.py"


def _run(*args, cwd, env=None):
    base_env = dict(os.environ)
    # Strip env vars from prior tests that could pollute this one.
    base_env.pop("DEV_SKILLS_CONFIG_FILE", None)
    if env:
        base_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd, env=base_env,
        capture_output=True, text=True, check=False,
    )


class SetupConventionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / ".git").mkdir()  # project-root marker

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_file_non_interactive(self):
        result = _run(
            "--non-interactive", "--docs-root", "agent-docs",
            cwd=self.tmp,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.tmp / ".agents" / "dev-skills.yaml"
        self.assertTrue(target.exists())
        content = target.read_text(encoding="utf-8")
        self.assertIn("schema: dev-skills/v1", content)
        self.assertIn("docs_root: agent-docs", content)

    def test_create_file_with_terminology_filename(self):
        result = _run(
            "--non-interactive", "--docs-root", "agent-docs",
            "--terminology-filename", "terms.md",
            cwd=self.tmp,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        content = (self.tmp / ".agents" / "dev-skills.yaml").read_text(encoding="utf-8")
        self.assertIn("filename: terms.md", content)

    def test_refuses_foreign_file(self):
        target = self.tmp / ".agents" / "dev-skills.yaml"
        target.parent.mkdir()
        target.write_text("some_other_tool: hello\n", encoding="utf-8")
        result = _run(
            "--non-interactive", "--docs-root", "agent-docs",
            cwd=self.tmp,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dev-skills/v1", result.stderr)

    def test_env_var_alternate_path(self):
        alt = self.tmp / ".agents" / "alt-skills.yaml"
        result = _run(
            "--non-interactive", "--docs-root", "agent-docs",
            cwd=self.tmp,
            env={"DEV_SKILLS_CONFIG_FILE": str(alt)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(alt.exists())

    def test_full_round_trip(self):
        """Installer output must round-trip through the canonical reader."""
        result = _run(
            "--non-interactive",
            "--docs-root", "agent-docs",
            "--terminology-filename", "terms.md",
            "--developer-diary-subdir", "diary",
            cwd=self.tmp,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        # Parse via the canonical reader.
        sys.path.insert(0, str(REPO_ROOT / "template" / "scripts"))
        import read_shared_conventions as rsc  # type: ignore
        os.environ["DEV_SKILLS_CONFIG_FILE"] = str(self.tmp / ".agents" / "dev-skills.yaml")
        try:
            parsed = rsc.load(self.tmp)
        finally:
            os.environ.pop("DEV_SKILLS_CONFIG_FILE", None)
        self.assertEqual(parsed["docs_root"], "agent-docs")
        self.assertEqual(parsed["skills"]["terminology"]["filename"], "terms.md")
        self.assertEqual(parsed["skills"]["developer-diary"]["subdir"], "diary")

    def test_rejects_hash_in_docs_root(self):
        result = _run(
            "--non-interactive", "--docs-root", "agent#docs",
            cwd=self.tmp,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden character", result.stderr)

    def test_print_resolves(self):
        target = self.tmp / ".agents" / "dev-skills.yaml"
        target.parent.mkdir()
        target.write_text(
            "schema: dev-skills/v1\ndocs_root: agent-docs\n",
            encoding="utf-8",
        )
        result = _run("--print", cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("docs_root: agent-docs", result.stdout)


if __name__ == "__main__":
    unittest.main()
