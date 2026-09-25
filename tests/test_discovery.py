from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from project_corpus.discovery import DiscoveryError, search, show, timeline
from tests.test_transactions import make_fixture


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        repository = Path(__file__).resolve().parents[1]
        self.temporary = tempfile.TemporaryDirectory(prefix="pc-discovery-")
        self.base = Path(self.temporary.name)
        self.project, _, _, _, _ = make_fixture(self.base)
        tasks = self.project / ".project-corpus" / "tasks"
        tasks.joinpath("task-russian.md").write_text(
            "# Russian discovery task\n\n"
            "Task-ID: task-russian\n"
            "Created-At: 2026-09-18T10:00:00Z\n\n"
            "## Objective\n\n"
            "Проверить поиск и порядок результатов.\n",
            encoding="utf-8",
        )
        (self.project / ".project-corpus" / "reports" / "report-russian.md").write_text(
            "# Evidence report\n\nReport-ID: report-russian\nCreated: 2026-09-19T10:00:00Z\n\n"
            "## Summary\n\nПоиск подтверждён.\n",
            encoding="utf-8",
        )
        (self.project / ".project-corpus" / "history" / "old.md").write_text(
            "# Old history\n\n## Note\n\nПоиск без даты.\n", encoding="utf-8"
        )
        policy = self.project / ".project-corpus" / "policy.toml"
        policy.write_text(
            policy.read_text(encoding="utf-8").replace(
                '".project-corpus/audit/**"]',
                '".project-corpus/audit/**", ".project-corpus/history/**"]',
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_search_returns_deterministic_source_aware_russian_result(self):
        results = search(self.project, "поиск", artifact_type="task")

        self.assertTrue(results["non_authoritative"])
        self.assertEqual(results["query"], "поиск")
        self.assertEqual(len(results["results"]), 1)
        result = results["results"][0]
        self.assertEqual(result["path"], ".project-corpus/tasks/task-russian.md")
        self.assertEqual(result["type"], "task")
        self.assertEqual(result["authority_class"], "TASK_INTENT")
        self.assertEqual(result["title"], "Objective")
        self.assertEqual(result["line_start"], 8)
        self.assertEqual(result["line_end"], 8)
        self.assertIn("поиск", result["snippet"])

    def test_search_keeps_a_distant_match_in_its_bounded_snippet(self):
        task = self.project / ".project-corpus" / "tasks" / "task-long.md"
        task.write_text("# Long task\n\n" + "x" * 1000 + " needle " + "y" * 1000 + "\n", encoding="utf-8")

        result = search(self.project, "needle", artifact_type="task")

        match = next(item for item in result["results"] if item["path"].endswith("task-long.md"))
        self.assertLessEqual(len(match["snippet"]), 240)
        self.assertIn("needle", match["snippet"])
        self.assertEqual((match["line_start"], match["line_end"]), (3, 3))

    def test_search_honors_scope_filter_and_no_match_type_and_limit_contracts(self):
        policy = self.project / ".project-corpus" / "policy.toml"
        policy.write_text(
            policy.read_text(encoding="utf-8").replace('".project-corpus/tasks/**", ', ""),
            encoding="utf-8",
        )

        self.assertEqual(search(self.project, "поиск", artifact_type="task")["results"], [])
        self.assertEqual(search(self.project, "missing")["results"], [])
        self.assertEqual(search(self.project, "поиск", artifact_type="report")["results"][0]["type"], "report")
        with self.assertRaisesRegex(DiscoveryError, "between 1 and 100"):
            search(self.project, "поиск", limit=0)
        with self.assertRaisesRegex(DiscoveryError, "between 1 and 100"):
            search(self.project, "поиск", limit=101)

    def test_search_applies_a_positive_result_limit_deterministically(self):
        report = self.project / ".project-corpus" / "reports" / "report-second.md"
        report.write_text("# Second report\n\nneedle\n", encoding="utf-8")
        first = self.project / ".project-corpus" / "reports" / "report-first.md"
        first.write_text("# First report\n\nneedle\n", encoding="utf-8")

        result = search(self.project, "needle", artifact_type="report", limit=1)

        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["path"], ".project-corpus/reports/report-first.md")

    def test_show_denies_out_of_scope_and_non_utf8_artifacts(self):
        task = self.project / ".project-corpus" / "tasks" / "task-binary.md"
        task.write_bytes(b"# Invalid\n\xff\n")
        with self.assertRaisesRegex(DiscoveryError, "not UTF-8"):
            search(self.project, "invalid", artifact_type="task")
        with self.assertRaisesRegex(DiscoveryError, "not UTF-8"):
            show(self.project, ".project-corpus/tasks/task-binary.md")

        policy = self.project / ".project-corpus" / "policy.toml"
        policy.write_text(
            policy.read_text(encoding="utf-8").replace('".project-corpus/tasks/**", ', ""),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(DiscoveryError, "read scope denied"):
            show(self.project, ".project-corpus/tasks/task-russian.md")

    def test_show_returns_scoped_artifact_and_rejects_traversal(self):
        artifact = show(self.project, ".project-corpus/tasks/task-russian.md")

        self.assertEqual(artifact["type"], "task")
        self.assertEqual(artifact["authority_class"], "TASK_INTENT")
        self.assertIn("Проверить поиск", artifact["content"])
        with self.assertRaises(DiscoveryError):
            show(self.project, "../AGENTS.md")
        for invalid in (
            "/etc/passwd",
            "C:/Windows/system32",
            "\\\\?\\C:\\Windows\\system32",
            ".project-corpus/tasks/task-russian.md:ads",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(DiscoveryError):
                show(self.project, invalid)

    def test_timeline_uses_documented_timestamps_and_marks_unknown(self):
        result = timeline(self.project, "поиск")

        self.assertTrue(result["non_authoritative"])
        self.assertEqual(
            [event["path"] for event in result["events"]],
            [
                ".project-corpus/tasks/task-russian.md",
                ".project-corpus/reports/report-russian.md",
                ".project-corpus/history/old.md",
            ],
        )
        self.assertEqual(result["events"][0]["timestamp_source"], "Created-At")
        self.assertEqual(result["events"][2]["timestamp_source"], "unknown")
        self.assertIsNone(result["events"][2]["timestamp"])


if __name__ == "__main__":
    unittest.main()
