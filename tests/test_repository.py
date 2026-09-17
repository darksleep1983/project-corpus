import hashlib
import json
from pathlib import Path
import re
import unittest


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def source_files(self):
        return {
            path.relative_to(self.root).as_posix(): path
            for path in self.root.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
            and path.name != "MANIFEST_SHA256.json"
        }

    def test_v1_templates_and_v2_layers_remain_separate(self):
        self.assertTrue((self.root / "template" / "en" / "AGENTS.md").is_file())
        self.assertTrue((self.root / "template" / "ru" / "AGENTS.md").is_file())
        self.assertTrue((self.root / "protocol" / "v2" / "specification.md").is_file())
        self.assertTrue((self.root / "src" / "project_corpus" / "__init__.py").is_file())
        self.assertTrue((self.root / "pyproject.toml").is_file())

    def test_active_docs_have_no_obsolete_runtime_contract(self):
        active = [
            self.root / "README.md",
            self.root / "README.ru.md",
            self.root / "PROJECT_INSTRUCTION_TEMPLATE.md",
            self.root / "PROJECT_INSTRUCTION_TEMPLATE.ru.md",
            self.root / "docs" / "how-it-works.md",
            self.root / "docs" / "how-it-works.ru.md",
        ]
        active.extend((self.root / "template" / language / "AGENTS.md") for language in ("en", "ru"))

        for path in active:
            text = path.read_text(encoding="utf-8")
            for obsolete in (
                "MCP_CONNECTION_CURRENT.md",
                "{{CORPUS_ROOT}}",
                "{{MCP_ROOT}}",
                "127.0.0.1:8334",
                "install.ps1",
                "start.ps1",
                "PROJECT_CORPUS_ROOT",
            ):
                self.assertNotIn(obsolete, text, f"{path}: {obsolete}")

    def test_manual_mode_protects_protocol_files(self):
        for relative in (
            "PROJECT_INSTRUCTION_TEMPLATE.md",
            "PROJECT_INSTRUCTION_TEMPLATE.ru.md",
            "docs/access/manual.md",
            "docs/access/manual.ru.md",
        ):
            text = (self.root / relative).read_text(encoding="utf-8")
            self.assertIn("AGENTS.md", text)
            self.assertIn("OPERATOR_PROFILE.md", text)
            self.assertIn("MANUAL_SESSION", text)

    def test_internal_markdown_links_resolve(self):
        pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        missing = []
        for path in self.root.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for raw in pattern.findall(text):
                target = raw.strip().split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                target = target.strip("<>")
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    missing.append(f"{path.relative_to(self.root)} -> {raw}")
        self.assertEqual(missing, [])

    def test_repository_manifest(self):
        manifest_path = self.root / "MANIFEST_SHA256.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data["format"], "project-corpus-repository-manifest-v1")

        sources = self.source_files()
        self.assertFalse(any(".git" in Path(relative).parts for relative in sources))
        self.assertEqual(set(data["files"]), set(sources))
        for relative, path in sources.items():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(data["files"][relative], actual, relative)


if __name__ == "__main__":
    unittest.main()
