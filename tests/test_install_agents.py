"""Tests for scripts/install-agents.py."""
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "install-agents.py"

SAMPLE_MD = textwrap.dedent("""\
    ---
    name: sample-agent
    description: A sample agent.
    ---

    Body.
    """)
SAMPLE_TOML = textwrap.dedent('''\
    name = "sample-agent"
    description = "A sample agent."

    developer_instructions = """
    Body.
    """
    ''')


def run(args, cwd):
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def make_repo_with_agents(td: Path) -> Path:
    (td / "agents").mkdir()
    (td / "agents" / "sample-agent.md").write_text(SAMPLE_MD, encoding="utf-8")
    (td / "agents" / "sample-agent.toml").write_text(SAMPLE_TOML, encoding="utf-8")
    return td


class InstallAgentsTests(unittest.TestCase):

    def test_dry_run_lists_targets(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "--dry-run", "-g"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".claude/agents/sample-agent.md", result.stdout.replace("\\", "/"))
            self.assertIn(".codex/agents/sample-agent.toml", result.stdout.replace("\\", "/"))

    def test_install_user_scope(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((home / ".claude" / "agents" / "sample-agent.md").exists())
            self.assertTrue((home / ".codex" / "agents" / "sample-agent.toml").exists())

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".claude" / "agents" / "sample-agent.md").write_text(
                "existing", encoding="utf-8",
            )
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y"],
                cwd=tdp,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exists", result.stderr.lower())
            # File not overwritten
            self.assertEqual(
                (home / ".claude" / "agents" / "sample-agent.md").read_text(encoding="utf-8"),
                "existing",
            )

    def test_force_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".claude" / "agents" / "sample-agent.md").write_text(
                "existing", encoding="utf-8",
            )
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y", "--force"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Body.", (home / ".claude" / "agents" / "sample-agent.md")
                          .read_text(encoding="utf-8"))

    def test_subset_with_agents_flag(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            make_repo_with_agents(tdp)
            (tdp / "agents" / "other-agent.md").write_text(
                SAMPLE_MD.replace("sample-agent", "other-agent"), encoding="utf-8",
            )
            (tdp / "agents" / "other-agent.toml").write_text(
                SAMPLE_TOML.replace("sample-agent", "other-agent"), encoding="utf-8",
            )
            home = tdp / "home"
            (home / ".claude" / "agents").mkdir(parents=True)
            (home / ".codex" / "agents").mkdir(parents=True)

            result = run(
                ["--agents-dir", str(tdp / "agents"), "--home", str(home),
                 "-g", "-y", "--agents", "sample-agent"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((home / ".claude" / "agents" / "sample-agent.md").exists())
            self.assertFalse((home / ".claude" / "agents" / "other-agent.md").exists())


if __name__ == "__main__":
    unittest.main()
