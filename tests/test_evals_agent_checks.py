"""Tests for the new agent checks in evals/run.py."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN = REPO_ROOT / "evals" / "run.py"


def run(cwd: Path | None = None):
    # When a custom cwd is given (an isolated temp-dir replica), run the
    # run.py that was copied into that temp dir so REPO_ROOT resolves
    # correctly inside the script.
    root = cwd or REPO_ROOT
    script = root / "evals" / "run.py" if cwd else RUN
    return subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True,
        cwd=root,
    )


class AgentChecksTests(unittest.TestCase):
    def test_repo_passes_overall_run(self):
        """The current branch must pass evals/run.py with the new checks active."""
        result = run()
        self.assertEqual(result.returncode, 0,
                         f"evals/run.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("OK", result.stdout)

    def test_detects_missing_toml_sibling(self):
        """If an agent .md exists without a .toml sibling, the check fails."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            # Build a minimal repo skeleton: copy evals/, scripts/, agents/, skills/, template/.
            for sub in ("evals", "scripts", "agents", "skills", "template"):
                target = tdp / sub
                if (REPO_ROOT / sub).is_dir():
                    import shutil
                    shutil.copytree(REPO_ROOT / sub, target)
            (tdp / ".claude-plugin").mkdir()
            (tdp / ".claude-plugin" / "marketplace.json").write_text(
                (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            # Delete one TOML sibling to trigger the check.
            toml = tdp / "agents" / "improve-prompt-agent.toml"
            if toml.exists():
                toml.unlink()
            result = run(cwd=tdp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("improve-prompt-agent", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
