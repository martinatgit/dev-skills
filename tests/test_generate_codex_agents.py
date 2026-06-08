"""Tests for scripts/generate-codex-agents.py."""
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "generate-codex-agents.py"

SAMPLE_MD = textwrap.dedent("""\
    ---
    name: sample-agent
    description: >
      A sample agent. Triggers on "sample me" and similar.
    tools: Read, Grep
    model: opus
    skills:
      - sample-skill
    ---

    You are the `sample-agent`. Do sample things.

    ## Workflow

    1. Read.
    2. Think.
    3. Emit.
    """)


def run(args, cwd):
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


class GenerateCodexAgentsTests(unittest.TestCase):

    def test_generates_toml_from_md(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")

            result = run(["--agents-dir", str(agents)], cwd=tdp)
            self.assertEqual(result.returncode, 0, result.stderr)

            toml_path = agents / "sample-agent.toml"
            self.assertTrue(toml_path.exists())
            toml_text = toml_path.read_text(encoding="utf-8")

            self.assertIn('name = "sample-agent"', toml_text)
            self.assertIn("A sample agent", toml_text)
            self.assertIn("developer_instructions", toml_text)
            self.assertIn("You are the `sample-agent`", toml_text)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")

            result = run(["--agents-dir", str(agents), "--dry-run"], cwd=tdp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((agents / "sample-agent.toml").exists())

    def test_round_trip_preserves_name_and_description(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")

            run(["--agents-dir", str(agents)], cwd=tdp)
            toml_text = (agents / "sample-agent.toml").read_text(encoding="utf-8")

            # Extract name and description by simple TOML key lookup.
            name_line = next(ln for ln in toml_text.splitlines() if ln.startswith("name "))
            desc_line = next(ln for ln in toml_text.splitlines() if ln.startswith("description "))
            self.assertIn('"sample-agent"', name_line)
            self.assertIn("A sample agent", desc_line)

    def test_missing_required_field_fails(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "broken-agent.md").write_text(
                "---\ndescription: no name field\n---\n\nBody.\n",
                encoding="utf-8",
            )
            result = run(["--agents-dir", str(agents)], cwd=tdp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("name", result.stderr.lower())

    def test_skips_non_md_files(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            agents = tdp / "agents"
            agents.mkdir()
            (agents / "README.md").write_text(
                "# Agents README — not an agent.\n", encoding="utf-8",
            )
            (agents / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")
            result = run(["--agents-dir", str(agents)], cwd=tdp)
            self.assertEqual(result.returncode, 0, result.stderr)
            # README is not a valid agent: it has no frontmatter. Generator
            # must skip it without erroring.
            self.assertFalse((agents / "README.toml").exists())


if __name__ == "__main__":
    unittest.main()
