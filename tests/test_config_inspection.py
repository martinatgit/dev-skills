"""Exercise configuration inspection from a consuming project's working directory."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = {
    "developer-diary": ("root_dir", "diary", "node_token_limit"),
    "update-todos": ("root_dir", "tasks", "default_expiry_days"),
    "terminology": ("terminology_file", "terms.md", "validation_timeout"),
    "create-tutorial": ("tutorials_dir", "guides", None),
}


class ConfigInspectionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".git").mkdir()
        self.cwd = self.root / "nested" / "consumer"
        self.cwd.mkdir(parents=True)
        self.env = {
            k: v for k, v in os.environ.items()
            if not k.startswith(("DEV_SKILLS_", "DEVELOPER_DIARY_", "UPDATE_TODOS_",
                                 "TERMINOLOGY_", "CREATE_TUTORIAL_"))
        }
        self.env["XDG_CONFIG_HOME"] = str(self.root / "user-config")
        self.env["INSPECTION_DOCS"] = "expanded-docs"

    def write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_script(self, skill, filename, *args):
        result = subprocess.run(
            [sys.executable, "-B", str(REPO_ROOT / "skills" / skill / "scripts" / filename), *args],
            cwd=self.cwd, env={**self.env, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        separator = "=" if filename == "resolve_config.py" else ":"
        return {k: v.strip() for k, _, v in
                (line.partition(separator) for line in result.stdout.splitlines())}

    def snapshot(self):
        return {
            str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in self.root.rglob("*") if p.is_file()
        }

    def assert_inspection(self, skill):
        before = self.snapshot()
        runtime = self.run_script(skill, "resolve_config.py", "--all")
        for scope in ("user", "project"):
            with self.subTest(skill=skill, scope=scope):
                inspected = self.run_script(skill, "configure.py", "--scope", scope, "--print")
                self.assertEqual(inspected, runtime)
        self.assertEqual(self.snapshot(), before, "inspection must not write configuration")
        return runtime

    def test_shared_conventions_and_derived_paths_match_runtime(self):
        self.write(
            self.root / ".agents" / "dev-skills.yaml",
            "schema: dev-skills/v1\ndocs_root: $INSPECTION_DOCS\nskills:\n"
            "  developer-diary:\n    subdir: diary\n    node_token_limit: 321\n"
            "  update-todos:\n    subdir: tasks\n    default_expiry_days: 321\n"
            "  terminology:\n    filename: terms.md\n    validation_timeout: 321\n"
            "  create-tutorial:\n    subdir: guides\n",
        )
        for skill, (path_key, suffix, tunable) in SKILLS.items():
            with self.subTest(skill=skill):
                self.write(self.root / "user-config" / skill / "config.yaml",
                           f"{path_key}: ignored-user-path\n" +
                           (f"{tunable}: 999\n" if tunable else ""))
                runtime = self.assert_inspection(skill)
                self.assertEqual(runtime[path_key], str(Path("expanded-docs") / suffix))
                if tunable:
                    self.assertEqual(runtime[tunable], "321")
                if skill == "developer-diary":
                    self.assertEqual(runtime["feature_routing_file"],
                                     str(Path("expanded-docs") / suffix / "feature-routing.md"))

    def test_environment_project_user_precedence_matches_runtime(self):
        self.write(self.root / ".agents" / "dev-skills.yaml",
                   "schema: dev-skills/v1\ndocs_root: shared-docs\n")
        for skill, (path_key, _, tunable) in SKILLS.items():
            with self.subTest(skill=skill):
                self.write(self.root / f".{skill}" / "config.yaml",
                           f"{path_key}: $INSPECTION_DOCS/project\n")
                self.write(self.root / "user-config" / skill / "config.yaml",
                           f"{path_key}: ignored-user-path\n" +
                           (f"{tunable}: 456\n" if tunable else ""))
                runtime = self.assert_inspection(skill)
                self.assertEqual(runtime[path_key], "expanded-docs/project")
                if tunable:
                    self.assertEqual(runtime[tunable], "456")
                env_key = skill.upper().replace("-", "_") + "_" + path_key.upper()
                self.env[env_key] = "$INSPECTION_DOCS/environment"
                runtime = self.assert_inspection(skill)
                self.assertEqual(runtime[path_key], "expanded-docs/environment")

    def test_unconfigured_inspection_is_read_only(self):
        for skill, (path_key, _, _) in SKILLS.items():
            with self.subTest(skill=skill):
                runtime = self.assert_inspection(skill)
                self.assertEqual(runtime[path_key], "")


if __name__ == "__main__":
    unittest.main()
