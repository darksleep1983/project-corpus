from pathlib import Path
import unittest


class BilingualTemplateTests(unittest.TestCase):
    REQUIRED_FILES = {
        "AGENTS.md",
        "OPERATOR_PROFILE.md",
        "PROJECT_ROADMAP_CURRENT.md",
        "MCP_CONNECTION_CURRENT.md",
        "LOADER_PROMPT_CURRENT.md",
        "SESSION_HANDOFF_CURRENT.md",
        "SESSION_HANDOFF_FULL_CURRENT.md",
    }

    def test_template_file_sets_match(self):
        root = Path(__file__).resolve().parents[1] / "template"
        english = {path.name for path in (root / "en").iterdir() if path.is_file()}
        russian = {path.name for path in (root / "ru").iterdir() if path.is_file()}
        self.assertEqual(english, self.REQUIRED_FILES)
        self.assertEqual(russian, self.REQUIRED_FILES)
        for language in ("en", "ru"):
            self.assertTrue((root / language / "Tasks").is_dir())
            self.assertTrue((root / language / "Report").is_dir())

    def test_protocol_invariants_are_present_in_both_languages(self):
        root = Path(__file__).resolve().parents[1] / "template"
        for language in ("en", "ru"):
            agents = (root / language / "AGENTS.md").read_text(encoding="utf-8")
            for item in self.REQUIRED_FILES:
                self.assertIn(item, agents)
            for invariant in (
                "NO_ACTIVE_PROJECT",
                "REUSABLE_CORPUS_READY",
                "EXPLICIT_OWNER_PROTOCOL_CHANGE",
                "expected_sha256",
                "Tasks/",
                "Report/",
            ):
                self.assertIn(invariant, agents)

            mcp = (root / language / "MCP_CONNECTION_CURRENT.md").read_text(encoding="utf-8")
            self.assertIn("{{CORPUS_ROOT}}", mcp)
            self.assertIn("{{MCP_ROOT}}", mcp)
            self.assertIn("writePolicyVersion>=1.0", mcp)

    def test_user_documentation_has_a_russian_and_english_counterpart(self):
        root = Path(__file__).resolve().parents[1]
        pairs = (
            ("README.md", "README.ru.md"),
            ("PROJECT_INSTRUCTION_TEMPLATE.md", "PROJECT_INSTRUCTION_TEMPLATE.ru.md"),
            ("PUBLISHING_CHECKLIST.md", "PUBLISHING_CHECKLIST_RU.md"),
            ("CHANGELOG.md", "CHANGELOG.ru.md"),
            ("SECURITY.md", "SECURITY.ru.md"),
            ("CONTRIBUTING.md", "CONTRIBUTING.ru.md"),
            ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.ru.md"),
            ("SUPPORT.md", "SUPPORT.ru.md"),
            ("docs/faq.md", "docs/faq.ru.md"),
            ("docs/how-it-works.md", "docs/how-it-works.ru.md"),
            ("docs/security.md", "docs/security.ru.md"),
            ("docs/languages.md", "docs/languages.ru.md"),
            ("docs/uninstall.md", "docs/uninstall.ru.md"),
            ("docs/clients/chatgpt.md", "docs/clients/chatgpt.ru.md"),
            ("docs/clients/claude-code.md", "docs/clients/claude-code.ru.md"),
            ("docs/clients/claude-desktop.md", "docs/clients/claude-desktop.ru.md"),
            ("docs/clients/generic-mcp-client.md", "docs/clients/generic-mcp-client.ru.md"),
        )
        for english, russian in pairs:
            self.assertTrue((root / english).is_file(), english)
            self.assertTrue((root / russian).is_file(), russian)

    def test_support_and_feedback_are_consistent_in_both_languages(self):
        root = Path(__file__).resolve().parents[1]
        wallet = "UQBxFzfzrSZ15nDGIAU2R9FnX2Q_mbF7kyiSCeqGPmRN829P"
        issues = "https://github.com/darksleep1983/project-corpus/issues"

        for support_file in ("SUPPORT.md", "SUPPORT.ru.md"):
            content = (root / support_file).read_text(encoding="utf-8")
            self.assertIn(wallet, content)
            self.assertIn(issues, content)
            self.assertIn("USDT", content)
            self.assertIn("TON", content)

        for readme_file in ("README.md", "README.ru.md"):
            content = (root / readme_file).read_text(encoding="utf-8")
            self.assertIn(issues, content)
