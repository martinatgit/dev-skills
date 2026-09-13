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

    def _make_repo_replica(self, tdp: Path) -> None:
        """Build a minimal repo skeleton good enough for `evals/run.py` to
        pass on an untouched copy: evals/, scripts/, agents/, skills/,
        template/, .claude-plugin/marketplace.json, and README.md.

        README.md must be copied too: check_registration() cross-checks the
        README skills table against skills/ on disk, and an isolated replica
        that omits it fails registration for all 14 skills regardless of
        whatever the test is actually trying to trigger — the test would
        then only be discriminating by accident (via assertIn), not because
        the returncode reflects the fault under test.
        """
        import shutil
        for sub in ("evals", "scripts", "agents", "skills", "template"):
            target = tdp / sub
            if (REPO_ROOT / sub).is_dir():
                shutil.copytree(REPO_ROOT / sub, target)
        (tdp / ".claude-plugin").mkdir()
        (tdp / ".claude-plugin" / "marketplace.json").write_text(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (tdp / "README.md").write_text(
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"), encoding="utf-8",
        )

    def test_detects_missing_toml_sibling(self):
        """If an agent .md exists without a .toml sibling, the check fails."""
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            self._make_repo_replica(tdp)
            # The untouched replica must pass on its own before we break it —
            # otherwise a failure below could come from anything.
            baseline = run(cwd=tdp)
            self.assertEqual(baseline.returncode, 0,
                             f"replica does not pass unmodified:\n{baseline.stdout}\n{baseline.stderr}")

            # Delete one TOML sibling to trigger the check.
            toml = tdp / "agents" / "improve-prompt-agent.toml"
            toml.unlink()
            result = run(cwd=tdp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("improve-prompt-agent", result.stdout + result.stderr)

    def test_detects_orphan_agent_with_no_paired_skill(self):
        """F11: check_agent_skill_pairing() has a real assertion.

        An agents/<name>-agent.md whose implied 'skills/<name>/' does not
        exist must fail the run with a message naming the missing pairing —
        deleting check_agent_skill_pairing() from evals/run.py should make
        this test fail.
        """
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            self._make_repo_replica(tdp)
            (tdp / "agents" / "orphan-agent.md").write_text(
                "---\n"
                "name: orphan-agent\n"
                "description: An agent with no paired skill.\n"
                "---\n\n"
                "You are the `orphan-agent`. Body.\n",
                encoding="utf-8",
            )
            # Generate a matching .toml so the *only* failure signal is the
            # pairing check — otherwise check_agent_format_parity's
            # missing-sibling error would also fail the run, and this test
            # would pass even with check_agent_skill_pairing() deleted.
            gen = subprocess.run(
                [sys.executable, str(tdp / "scripts" / "generate-codex-agents.py"),
                 "--agents-dir", str(tdp / "agents")],
                capture_output=True, text=True, cwd=tdp,
            )
            self.assertEqual(gen.returncode, 0, gen.stderr)

            result = run(cwd=tdp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("skills/orphan/", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
