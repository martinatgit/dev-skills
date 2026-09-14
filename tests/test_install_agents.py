"""Tests for scripts/install-agents.py."""
import subprocess
import json
import shutil
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

    def test_dry_run_previews_reinstall_without_erroring(self):
        """F12: --dry-run must preview an already-installed set, not fail.

        docs/agents-portability-checklist.md prescribes
        `install-agents.py --dry-run -g` as a pre-PR check; it must succeed
        for a contributor who has already installed once.
        """
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
                 "--dry-run", "-g"],
                cwd=tdp,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".claude/agents/sample-agent.md", result.stdout.replace("\\", "/"))
            # The pre-existing destination is not overwritten by a dry run.
            self.assertEqual(
                (home / ".claude" / "agents" / "sample-agent.md").read_text(encoding="utf-8"),
                "existing",
            )

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


class InstallLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = make_repo_with_agents(Path(self.temp.name))
        self.home = self.root / "home"
        self.project = self.root / "consumer"
        self.project.mkdir()
        (self.project / "AGENTS.md").write_text("project", encoding="utf-8")
        self.target = self.home / ".claude" / "agents"
        self.installed = self.target / "sample-agent.md"
        self.source = self.root / "agents" / "sample-agent.md"

    def install(self, *args, project=False):
        return run(["--agents-dir", str(self.root / "agents"), "--home", str(self.home),
                    *([] if project else ["-g"]), *args], cwd=self.project)

    def first_install(self):
        result = self.install("-a", "claude-code")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_detects_host_config_without_agents_directory(self):
        (self.home / ".claude").mkdir(parents=True)
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.installed.is_file())

    def test_project_scope_detects_home_hosts_using_canonical_root_markers(self):
        (self.home / ".codex").mkdir(parents=True)
        result = self.install(project=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.project / ".codex/agents/sample-agent.toml").is_file())
        self.assertFalse((self.home / ".codex/agents").exists())

    def test_project_detects_project_only_host(self):
        (self.project / ".claude").mkdir()
        result = self.install(project=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.project / ".claude/agents/sample-agent.md").is_file())

    def test_explicit_host_ignores_other_detected_hosts(self):
        (self.home / ".codex").mkdir(parents=True)
        self.first_install()
        self.assertFalse((self.home / ".codex/agents").exists())

    def test_unknown_agent_in_mixed_selection_fails_before_writes(self):
        result = self.install("-a", "claude-code", "--agents", "sample-agent", "typo")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("typo", result.stderr)
        self.assertFalse(self.home.exists())

    def test_identical_reinstall_does_not_rewrite_agent_or_manifest(self):
        self.first_install()
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.target.iterdir()}
        result = self.install("-a", "claude-code")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unchanged", result.stdout)
        after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.target.iterdir()}
        self.assertEqual(before, after)

    def test_update_replaces_tracked_unmodified_file(self):
        self.first_install()
        self.source.write_text("new upstream", encoding="utf-8")
        result = self.install("-a", "claude-code", "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed.read_text(encoding="utf-8"), "new upstream")
        self.assertIn("update", result.stdout)
        self.assertIn(str(self.source), result.stdout)
        self.assertIn(str(self.installed), result.stdout)

    def test_update_refuses_local_change_and_does_not_install_other_files(self):
        self.first_install()
        self.installed.write_text("local edit", encoding="utf-8")
        (self.source.parent / "new-agent.md").write_text("new agent", encoding="utf-8")
        result = self.install("-a", "claude-code", "--update")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.installed.read_text(encoding="utf-8"), "local edit")
        self.assertFalse((self.target / "new-agent.md").exists())

    def test_update_refuses_untracked_different_file(self):
        self.target.mkdir(parents=True)
        self.installed.write_text("untracked", encoding="utf-8")
        result = self.install("-a", "claude-code", "--update")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.installed.read_text(encoding="utf-8"), "untracked")

    def test_identical_legacy_install_is_adopted_for_later_updates(self):
        self.target.mkdir(parents=True)
        self.installed.write_bytes(self.source.read_bytes())
        modified = self.installed.stat().st_mtime_ns
        self.first_install()
        self.assertEqual(self.installed.stat().st_mtime_ns, modified)
        self.source.write_text("upstream change", encoding="utf-8")
        result = self.install("-a", "claude-code", "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed.read_text(encoding="utf-8"), "upstream change")

    def test_regular_install_requires_update_for_changed_managed_file(self):
        self.first_install()
        self.source.write_text("upstream change", encoding="utf-8")
        result = self.install("-a", "claude-code")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.installed.read_text(encoding="utf-8"), SAMPLE_MD)

    def test_force_creates_unique_backups_and_preserves_unrelated_files(self):
        self.first_install()
        unrelated = self.target / "personal.md"
        unrelated.write_text("personal", encoding="utf-8")
        for edit in ("local one", "local two"):
            self.installed.write_text(edit, encoding="utf-8")
            result = self.install("-a", "claude-code", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("backup", result.stdout)
        backups = list((self.target.parent / ".dev-skills-agent-backups").glob("*/sample-agent.md"))
        self.assertEqual({p.read_text(encoding="utf-8") for p in backups}, {"local one", "local two"})
        self.assertFalse(any(p.name.startswith(".dev-skills-backup-") for p in self.target.iterdir()))
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "personal")

    def test_dry_run_force_makes_no_changes_or_backups(self):
        self.first_install()
        self.installed.write_text("local", encoding="utf-8")
        before = {str(p.relative_to(self.target.parent)): p.read_bytes() for p in self.target.parent.rglob("*") if p.is_file()}
        result = self.install("-a", "claude-code", "--force", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("backup", result.stdout)
        after = {str(p.relative_to(self.target.parent)): p.read_bytes() for p in self.target.parent.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.target.parent / ".dev-skills-agent-backups").exists())

    def test_fresh_dry_run_creates_no_target(self):
        result = self.install("-a", "claude-code", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.home.exists())

    def test_project_dry_run_does_not_write_to_source_checkout(self):
        scripts = self.root / "scripts"
        scripts.mkdir()
        copied_script = scripts / "install-agents.py"
        shutil.copyfile(SCRIPT, copied_script)
        template = self.root / "template" / "scripts"
        template.mkdir(parents=True)
        shutil.copyfile(REPO_ROOT / "template/scripts/find_project_root.py", template / "find_project_root.py")
        result = subprocess.run(
            [sys.executable, str(copied_script), "--home", str(self.home), "--dry-run", "-a", "claude-code"],
            capture_output=True, text=True, cwd=self.project,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((template / "__pycache__").exists())
        self.assertFalse((self.project / ".claude").exists())

    def test_stale_managed_files_are_reported_and_retained(self):
        self.first_install()
        self.source.unlink()
        result = self.install("-a", "claude-code", "--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stale", result.stdout)
        self.assertIn("sample-agent.md", result.stdout)
        self.assertTrue(self.installed.exists())

    def test_invalid_manifest_fails_before_writes_even_with_force(self):
        self.target.mkdir(parents=True)
        manifest = self.target / ".dev-skills-install.json"
        for value in ("{bad", "[]", '{"version": true, "files": {}}',
                      '{"version": 1.0, "files": {}}',
                      json.dumps({"version": 1, "files": {"../outside.md": {"sha256": "0" * 64, "source": "x"}}})):
            with self.subTest(value=value):
                manifest.write_text(value, encoding="utf-8")
                result = self.install("-a", "claude-code", "--force")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("manifest", result.stderr)
                self.assertFalse(self.installed.exists())
                self.assertEqual(manifest.read_text(encoding="utf-8"), value)

    def test_symlink_destination_is_refused_even_with_force(self):
        self.target.mkdir(parents=True)
        outside = self.root / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            self.installed.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        result = self.install("-a", "claude-code", "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")

    def test_symlink_manifest_is_refused_even_when_content_is_valid(self):
        self.target.mkdir(parents=True)
        outside = self.root / "manifest.json"
        content = '{"version": 1, "files": {}}'
        outside.write_text(content, encoding="utf-8")
        try:
            (self.target / ".dev-skills-install.json").symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        result = self.install("-a", "claude-code", "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.installed.exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), content)

    def test_symlink_target_directory_is_refused(self):
        self.target.parent.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        try:
            self.target.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        result = self.install("-a", "claude-code", "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_backup_directory_is_refused_before_replacing(self):
        self.first_install()
        self.installed.write_text("local", encoding="utf-8")
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.target.parent / ".dev-skills-agent-backups").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        result = self.install("-a", "claude-code", "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.installed.read_text(encoding="utf-8"), "local")
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
