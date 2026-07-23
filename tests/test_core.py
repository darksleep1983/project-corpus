from pathlib import Path
import tempfile
import unittest

from project_corpus_mcp.core import CorpusConfig, CorpusError, CorpusStore


class CorpusStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "Corpus"
        self.mcp_root = base / "mcp"
        (self.root / "Tasks").mkdir(parents=True)
        (self.root / "Report").mkdir()
        for name in (
            "AGENTS.md", "OPERATOR_PROFILE.md", "PROJECT_ROADMAP_CURRENT.md",
            "MCP_CONNECTION_CURRENT.md", "LOADER_PROMPT_CURRENT.md",
            "SESSION_HANDOFF_CURRENT.md", "SESSION_HANDOFF_FULL_CURRENT.md",
        ):
            (self.root / name).write_text(f"# {name}\n", encoding="utf-8")
        self.store = CorpusStore(CorpusConfig(self.root, self.mcp_root))

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_update(self):
        created = self.store.write(
            path="Tasks/TEST__TASK.md", content="# Task\n", operation="create"
        )
        self.assertEqual(created["operation"], "create")
        old_sha = created["newSha256"]
        updated = self.store.write(
            path="Tasks/TEST__TASK.md", content="# Updated\n", operation="update",
            expected_sha256=old_sha,
        )
        self.assertEqual(updated["oldSha256"], old_sha)
        self.assertEqual(updated["newSha256"], updated["readbackSha256"])
        self.assertTrue(Path(updated["backupPath"]).is_file())

    def test_stale_sha_blocked(self):
        path = self.root / "PROJECT_ROADMAP_CURRENT.md"
        before = path.read_bytes()
        with self.assertRaisesRegex(CorpusError, "STALE_EXPECTED_SHA256"):
            self.store.write(
                path=path.name, content="changed", operation="update",
                expected_sha256="0" * 64,
            )
        self.assertEqual(path.read_bytes(), before)

    def test_agents_requires_authorization(self):
        old = self.store.stat("AGENTS.md")["sha256"]
        with self.assertRaises(CorpusError):
            self.store.write(
                path="AGENTS.md", content="# new", operation="update",
                expected_sha256=old,
            )
        result = self.store.write(
            path="AGENTS.md", content="# new", operation="update",
            expected_sha256=old,
            authorization="EXPLICIT_OWNER_PROTOCOL_CHANGE",
        )
        self.assertEqual(result["newSha256"], result["readbackSha256"])

    def test_profile_is_hard_denied(self):
        old = self.store.stat("OPERATOR_PROFILE.md")["sha256"]
        with self.assertRaises(CorpusError):
            self.store.write(
                path="OPERATOR_PROFILE.md", content="x", operation="update",
                expected_sha256=old,
            )

    def test_path_escape_blocked(self):
        for value in ("../x", "/tmp/x", "C:/x", "Tasks/nested/x.md"):
            with self.assertRaises(CorpusError, msg=value):
                self.store.write(path=value, content="x", operation="create")

    def test_mcp_root_must_be_outside_corpus(self):
        with self.assertRaises(CorpusError):
            CorpusStore(CorpusConfig(self.root, self.root / "mcp-state"))

    def test_write_size_limit(self):
        with self.assertRaises(CorpusError):
            self.store.write(
                path="Tasks/LARGE__TASK.md", content="x" * 5_000_001, operation="create"
            )

    def test_read_many_path_limit(self):
        with self.assertRaises(CorpusError):
            self.store.read_many(["AGENTS.md"] * 51)


if __name__ == "__main__":
    unittest.main()
