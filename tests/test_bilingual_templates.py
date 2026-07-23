from pathlib import Path
import unittest


class BilingualTemplateTests(unittest.TestCase):
    REQUIRED_FILES = {
        "AGENTS.md",
        "OPERATOR_PROFILE.md",
        "PROJECT_ROADMAP_CURRENT.md",
        "CORPUS_ACCESS_CURRENT.md",
        "LOADER_PROMPT_CURRENT.md",
        "SESSION_HANDOFF_CURRENT.md",
        "SESSION_HANDOFF_FULL_CURRENT.md",
    }

    MODES = ("DIRECT_FOLDER", "OWNER_MCP", "MANUAL_SESSION")

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_template_file_sets_match(self):
        template = self.root / "template"
        for language in ("en", "ru"):
            files = {path.name for path in (template / language).iterdir() if path.is_file()}
            self.assertEqual(files, self.REQUIRED_FILES)
            self.assertTrue((template / language / "Tasks").is_dir())
            self.assertTrue((template / language / "Report").is_dir())

    def test_protocol_invariants_are_present_in_both_languages(self):
        for language in ("en", "ru"):
            base = self.root / "template" / language
            agents = (base / "AGENTS.md").read_text(encoding="utf-8")
            access = (base / "CORPUS_ACCESS_CURRENT.md").read_text(encoding="utf-8")

            for item in self.REQUIRED_FILES:
                self.assertIn(item, agents)
            for invariant in (
                "NO_ACTIVE_PROJECT",
                "REUSABLE_CORPUS_READY",
                "Tasks/",
                "Report/",
                "AGENTS.md",
                "OPERATOR_PROFILE.md",
            ):
                self.assertIn(invariant, agents)
            for mode in self.MODES:
                self.assertIn(mode, agents)
                self.assertIn(mode, access)

            self.assertNotIn("MCP_CONNECTION_CURRENT.md", agents)
            self.assertNotIn("{{CORPUS_ROOT}}", agents)
            self.assertNotIn("{{MCP_ROOT}}", agents)

    def test_user_documentation_has_language_pairs(self):
        pairs = (
            ("README.md", "README.ru.md"),
            ("PROJECT_INSTRUCTION_TEMPLATE.md", "PROJECT_INSTRUCTION_TEMPLATE.ru.md"),
            ("PUBLISHING_CHECKLIST.md", "PUBLISHING_CHECKLIST_RU.md"),
            ("CHANGELOG.md", "CHANGELOG.ru.md"),
            ("SECURITY.md", "SECURITY.ru.md"),
            ("CONTRIBUTING.md", "CONTRIBUTING.ru.md"),
            ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.ru.md"),
            ("SUPPORT.md", "SUPPORT.ru.md"),
            ("REPOSITORY_METADATA.md", "REPOSITORY_METADATA.ru.md"),
            ("docs/faq.md", "docs/faq.ru.md"),
            ("docs/how-it-works.md", "docs/how-it-works.ru.md"),
            ("docs/security.md", "docs/security.ru.md"),
            ("docs/languages.md", "docs/languages.ru.md"),
            ("docs/uninstall.md", "docs/uninstall.ru.md"),
            ("docs/access/direct-folder.md", "docs/access/direct-folder.ru.md"),
            ("docs/access/own-mcp.md", "docs/access/own-mcp.ru.md"),
            ("docs/access/manual.md", "docs/access/manual.ru.md"),
            ("docs/clients/chatgpt.md", "docs/clients/chatgpt.ru.md"),
            ("docs/clients/codex.md", "docs/clients/codex.ru.md"),
            ("docs/clients/claude-code.md", "docs/clients/claude-code.ru.md"),
            ("docs/clients/claude-desktop.md", "docs/clients/claude-desktop.ru.md"),
            ("docs/clients/other-clients.md", "docs/clients/other-clients.ru.md"),
        )
        for english, russian in pairs:
            self.assertTrue((self.root / english).is_file(), english)
            self.assertTrue((self.root / russian).is_file(), russian)

    def test_support_and_feedback_are_consistent(self):
        wallet = "UQBxFzfzrSZ15nDGIAU2R9FnX2Q_mbF7kyiSCeqGPmRN829P"
        issues = "https://github.com/darksleep1983/project-corpus/issues"

        for support_file in ("SUPPORT.md", "SUPPORT.ru.md"):
            content = (self.root / support_file).read_text(encoding="utf-8")
            self.assertIn(wallet, content)
            self.assertIn(issues, content)
            self.assertIn("USDT", content)
            self.assertIn("TON", content)

        for readme_file in ("README.md", "README.ru.md"):
            content = (self.root / readme_file).read_text(encoding="utf-8")
            self.assertIn(issues, content)


if __name__ == "__main__":
    unittest.main()
