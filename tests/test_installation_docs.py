"""Validate user-facing installation identifiers against the shipped catalog."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class InstallationDocsTests(unittest.TestCase):
    def test_plugin_install_commands_match_marketplace(self):
        catalog = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        expected = {f"{plugin['name']}@{catalog['name']}" for plugin in catalog["plugins"]}
        for relative in ("README.md", "docs/install.md", "docs/agents-guide.md"):
            with self.subTest(document=relative):
                contents = (ROOT / relative).read_text(encoding="utf-8")
                identifiers = re.findall(r"(?:/plugin|claude plugin) install ([\w-]+@[\w-]+)", contents)
                self.assertTrue(identifiers, "Expected at least one usable plugin install example")
                self.assertLessEqual(set(identifiers), expected)


if __name__ == "__main__":
    unittest.main()
