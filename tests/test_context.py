from __future__ import annotations

from dataclasses import replace
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from project_corpus.context import build_index, open_index, query_index, compile_bundle, make_receipt, memory_doctor, evaluate_dataset, validate_candidate
from project_corpus.context.index import collect, Source
from project_corpus.context.schema import ContextError, canonical_json, digest
from project_corpus.cli import main
from project_corpus.mcp_stdio import McpRuntime, StdioMcpServer
from project_corpus.policy import parse_project_policy
from project_corpus.trust import write_trust_grant
from tests.test_transactions import make_fixture


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pc-context-")
        self.base = Path(self.temp.name)
        self.root, _, self.trust, _, _ = make_fixture(self.base)
        self.index = self.root / ".project-corpus/cache/context.sqlite3"
        policy = self.root / ".project-corpus/policy.toml"
        policy.write_text(policy.read_text(encoding="utf-8").replace('"corpus.validate",', '"corpus.validate", "corpus.context",').replace('".project-corpus/audit/**"]', '".project-corpus/audit/**", ".project-corpus/history/**"]'), encoding="utf-8")
        status = self.root / ".project-corpus/state/STATUS.md"
        status.write_text(status.read_text(encoding="utf-8").replace("Active-Task-ID: NONE", "Active-Task-ID: current-task").replace("Old baseline.", "Current color is blue."), encoding="utf-8")
        (self.root / ".project-corpus/tasks/current-task.md").write_text("# Current task\n\nTask-ID: current-task\nCreated-At: 2026-09-17T00:00:00Z\n\n## Objective\n\nVerify blue color.\n", encoding="utf-8")
        self.old = ".project-corpus/reports/old-report.md"
        (self.root / self.old).write_text("# Old report\n\nDate: 2026-09-16\n\n## Result\n\nThe color is red.\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def build(self):
        build_index(self.root, self.index)
        return open_index(self.root, self.index)

    def test_current_outranks_old_and_old_remains_discoverable(self):
        result = query_index(self.build(), "color", limit=20)["results"]
        self.assertEqual(result[0]["source_path"], ".project-corpus/state/STATUS.md")
        old = next(item for item in result if item["source_path"] == self.old)
        self.assertEqual(old["temporal_status"], "historical")
        self.assertTrue(all(item["non_authoritative"] for item in result))

    def test_active_task_outranks_irrelevant_report(self):
        (self.root / ".project-corpus/reports/other.md").write_text("# Color report\n\nDate: 2026-09-17\n\nColor table.\n", encoding="utf-8")
        result = query_index(self.build(), "color", limit=20)["results"]
        active = next(i for i, item in enumerate(result) if item["authority_class"] == "ACTIVE_TASK")
        other = next(i for i, item in enumerate(result) if item["source_path"].endswith("other.md"))
        self.assertLess(active, other)

    def test_explicit_supersession_and_no_guessed_link(self):
        corpus = self.build()
        self.assertEqual(next(s.temporal_status for s in corpus.sources if s.path == self.old), "historical")
        (self.root / ".project-corpus/tasks/current-task.md").write_text("# Current task\n\nSupersedes: " + self.old + "\n\nVerify blue color.\n", encoding="utf-8")
        corpus = self.build()
        self.assertEqual(next(s.temporal_status for s in corpus.sources if s.path == self.old), "superseded")
        self.assertIn(self.old, [item["source_path"] for item in query_index(corpus, "red", limit=20)["results"]])

    def test_cross_project_and_policy_scope_deny(self):
        sibling = self.base / "other-project"
        sibling.mkdir()
        (sibling / "secret.md").write_text("foreignneedle", encoding="utf-8")
        self.assertEqual(query_index(self.build(), "foreignneedle")["results"], [])
        policy = self.root / ".project-corpus/policy.toml"
        policy.write_text(policy.read_text(encoding="utf-8").replace('".project-corpus/reports/**", ', ""), encoding="utf-8")
        restricted = collect(self.root)
        self.assertEqual([s for s in restricted.sources if s.source_type == "report"], [])
        isolation = evaluate_dataset(restricted, {"schema_version": "1", "cases": [{
            "query": "color", "forbidden_scope_paths": [self.old, "other-project/secret.md"],
            "expected_project_id": restricted.project_id}]})
        self.assertTrue(isolation["ok"], isolation)

    def test_stale_index_and_bundle_hash_change(self):
        corpus = self.build()
        old_hash = compile_bundle(corpus, "color")["bundle_sha256"]
        report = self.root / self.old
        report.write_text(report.read_text(encoding="utf-8") + "New evidence.\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextError, "INDEX_STALE"):
            open_index(self.root, self.index)
        codes = {item["code"] for item in memory_doctor(self.root, index=self.index)["issues"]}
        self.assertIn("STALE_INDEX", codes)
        self.assertNotEqual(old_hash, compile_bundle(self.build(), "color")["bundle_sha256"])

    def test_deterministic_bundle_budget_and_receipt(self):
        corpus = self.build()
        first = compile_bundle(corpus, "color", max_tokens=80)
        second = compile_bundle(corpus, "color", max_tokens=80)
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])
        self.assertLessEqual(first["budget"]["estimated_tokens"], 80)
        self.assertEqual([item["source_path"] for item in first["items"][:2]], [".project-corpus/state/PROJECT.md", ".project-corpus/state/STATUS.md"])
        receipt = make_receipt(first, "fixture-consumer")
        self.assertEqual(receipt["bundle_sha256"], first["bundle_sha256"])
        self.assertTrue(receipt["non_authoritative"])
        self.assertEqual(receipt["source_snapshot_digest"], first["source_snapshot_digest"])
        self.assertEqual(first["serialized_bytes"], len(canonical_json(first)))
        self.assertEqual(set(first["selected_source_snapshot"]), {item["source_path"] for item in first["items"]})
        self.assertEqual(len(first["mandatory_reads"]), 3)

    def test_near_limit_source_count_keeps_whole_bundle_bounded(self):
        corpus = collect(self.root)
        additions = tuple(Source(f".project-corpus/history/synthetic-{i:04}.md", "history", "HISTORY", f"{i:064x}", None, "historical", "") for i in range(2048 - len(corpus.sources)))
        large = replace(corpus, sources=corpus.sources + additions)
        bundle = compile_bundle(large, "color", max_tokens=20000)
        self.assertEqual(bundle["source_count"], 2048)
        self.assertLess(len(bundle["selected_source_snapshot"]), 100)
        self.assertLessEqual(bundle["serialized_bytes"], 65536)
        self.assertEqual(bundle["serialized_bytes"], len(canonical_json(bundle)))
        changed = replace(large, sources=large.sources[:-1] + (replace(large.sources[-1], sha256="f" * 64),))
        changed_bundle = compile_bundle(changed, "color", max_tokens=20000)
        self.assertNotEqual(bundle["source_snapshot_digest"], changed_bundle["source_snapshot_digest"])
        self.assertNotEqual(bundle["bundle_sha256"], changed_bundle["bundle_sha256"])
        self.assertIn("BUNDLE_FULL_SNAPSHOT_MISMATCH", {issue["code"] for issue in memory_doctor(self.root, corpus=large, bundle=changed_bundle)["issues"]})

    def test_cache_directory_link_escape_rejected(self):
        outside = self.base / "outside-cache"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("outside", encoding="utf-8")
        link = self.root / ".project-corpus/cache"
        if link.exists():
            link.rmdir()
        if sys.platform == "win32":
            result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
            if result.returncode:
                self.skipTest("junction creation unavailable")
        else:
            os.symlink(outside, link)
        try:
            with self.assertRaisesRegex(ContextError, "INDEX_PATH"):
                build_index(self.root, self.index)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "outside")
            self.assertFalse((outside / self.index.name).exists())
        finally:
            if sys.platform == "win32":
                link.rmdir()
            else:
                link.unlink()

    def test_index_and_temp_link_escape_rejected(self):
        cache = self.root / ".project-corpus/cache"
        cache.mkdir()
        outside = self.base / "outside.sqlite3"
        outside.write_bytes(b"outside")
        try:
            os.symlink(outside, self.index)
        except OSError:
            self.skipTest("file symlink creation unavailable")
        with self.assertRaisesRegex(ContextError, "INDEX_PATH"):
            build_index(self.root, self.index)
        self.assertEqual(outside.read_bytes(), b"outside")
        self.index.unlink()
        temp = self.index.with_name(self.index.name + ".tmp")
        os.symlink(outside, temp)
        try:
            with self.assertRaisesRegex(ContextError, "INDEX_PATH"):
                build_index(self.root, self.index)
            self.assertEqual(outside.read_bytes(), b"outside")
        finally:
            temp.unlink()

    def test_temporal_cycles_orphans_and_acyclic_chain(self):
        first = self.root / ".project-corpus/reports/a.md"
        second = self.root / ".project-corpus/reports/b.md"
        third = self.root / ".project-corpus/reports/c.md"
        a, b, c = (f".project-corpus/reports/{name}.md" for name in ("a", "b", "c"))
        first.write_text(f"# A\nSupersedes: {b}\n", encoding="utf-8")
        second.write_text(f"# B\nSupersedes: {c}\n", encoding="utf-8")
        third.write_text("# C\n", encoding="utf-8")
        self.assertNotIn("TEMPORAL_CYCLE", {issue["code"] for issue in memory_doctor(self.root)["issues"]})
        self.assertEqual(next(s.temporal_status for s in collect(self.root).sources if s.path == c), "superseded")
        third.write_text(f"# C\nSupersedes: {a}\n", encoding="utf-8")
        self.assertIn("TEMPORAL_CYCLE", {issue["code"] for issue in memory_doctor(self.root)["issues"]})
        self.assertNotEqual(next(s.temporal_status for s in collect(self.root).sources if s.path == a), "superseded")
        second.write_text(f"# B\nSupersedes: {a}\n", encoding="utf-8")
        third.write_text("# C\n", encoding="utf-8")
        self.assertIn("TEMPORAL_CYCLE", {issue["code"] for issue in memory_doctor(self.root)["issues"]})
        first.write_text(f"# A\nSupersedes: {a}\n", encoding="utf-8")
        self.assertIn("INVALID_TEMPORAL_RELATION", {issue["code"] for issue in memory_doctor(self.root)["issues"]})
        first.write_text("# A\nSupersedes: .project-corpus/reports/missing.md\n", encoding="utf-8")
        self.assertIn("ORPHAN_SUPERSESSION", {issue["code"] for issue in memory_doctor(self.root)["issues"]})

    def test_russian_retrieval_and_volatile_wording(self):
        status = self.root / ".project-corpus/state/STATUS.md"
        status.write_text(status.read_text(encoding="utf-8") + "\nТекущее состояние: синий цвет.\n", encoding="utf-8")
        self.old_path = self.root / self.old
        self.old_path.write_text(self.old_path.read_text(encoding="utf-8") + "\nИсторический цвет был красный. Сейчас неизвестно.\n", encoding="utf-8")
        corpus = collect(self.root)
        self.assertEqual(query_index(corpus, "какое текущее состояние цвет")["results"][0]["source_path"], ".project-corpus/state/STATUS.md")
        self.assertTrue(any(item["source_path"] == self.old for item in query_index(corpus, "исторический красный цвет")["results"]))
        self.assertIn("VOLATILE_WITHOUT_FRESHNESS", {issue["code"] for issue in memory_doctor(self.root)["issues"]})

    def test_eval_top_source_and_source_specific_expectations(self):
        corpus = collect(self.root)
        case = {"query": "color", "expected_top_source_path": ".project-corpus/state/STATUS.md",
                "expected_top_k_paths": [".project-corpus/state/STATUS.md"],
                "expected_source_temporal": {self.old: "historical"},
                "expected_source_authority": {self.old: "SCOPED_REPORT"},
                "forbidden_scope_paths": ["other-project/secret.md"],
                "expected_project_id": corpus.project_id, "max_tokens": 500}
        good = evaluate_dataset(corpus, {"schema_version": "1", "cases": [case]})
        self.assertTrue(good["ok"], good)
        case["expected_source_temporal"] = {self.old: "current"}
        self.assertFalse(evaluate_dataset(corpus, {"schema_version": "1", "cases": [case]})["ok"])

    def test_rebuild_delete_recreate_and_no_raw_source_text(self):
        self.build()
        data = self.index.read_bytes()
        self.assertNotIn(b"Current color is blue", data)
        self.build()
        self.assertEqual(self.index.read_bytes(), data)
        self.index.unlink()
        self.assertFalse(self.index.exists())
        self.assertEqual(self.build().project_id, "transaction-fixture")
        self.assertEqual(self.index.read_bytes(), data)

    def test_doctor_detects_selected_and_full_snapshot_staleness(self):
        corpus = self.build()
        bundle = compile_bundle(corpus, "color")
        status = self.root / ".project-corpus/state/STATUS.md"
        status.write_text(status.read_text(encoding="utf-8") + "\nnew status evidence\n", encoding="utf-8")
        codes = {issue["code"] for issue in memory_doctor(self.root, bundle=bundle)["issues"]}
        self.assertIn("BUNDLE_STALE_SOURCE", codes)
        self.assertIn("BUNDLE_FULL_SNAPSHOT_MISMATCH", codes)

    def test_index_path_escape_and_bad_relations(self):
        with self.assertRaisesRegex(ContextError, "INDEX_PATH"):
            build_index(self.root, self.base / "outside.sqlite3")
        with self.assertRaisesRegex(ContextError, "INDEX_PATH"):
            build_index(self.root, self.root / ".project-corpus/cache/../cache/context.sqlite3")
        task = self.root / ".project-corpus/tasks/current-task.md"
        task.write_text(task.read_text(encoding="utf-8") + "Supersedes: ../outside.md\n", encoding="utf-8")
        codes = {item["code"] for item in memory_doctor(self.root)["issues"]}
        self.assertIn("INVALID_TEMPORAL_RELATION", codes)
        task.write_text("# Current task\n\nSupersedes: .project-corpus/state/STATUS.md\n", encoding="utf-8")
        corpus = collect(self.root)
        self.assertEqual(next(s.temporal_status for s in corpus.sources if s.path.endswith("/STATUS.md")), "current")
        self.assertIn("INVALID_TEMPORAL_RELATION", {item["code"] for item in memory_doctor(self.root)["issues"]})

    def test_candidate_requires_evidence_and_never_promotes(self):
        corpus = self.build()
        candidate = {"schema_version": "1", "candidate_id": "candidate-one", "project_id": corpus.project_id, "kind": "semantic_fact", "statement": "Blue is current.", "source_refs": [{"source_path": ".project-corpus/state/STATUS.md", "source_sha256": corpus.snapshot[".project-corpus/state/STATUS.md"], "line_start": 12}], "created_at": "2026-09-25T00:00:00Z", "status": "candidate"}
        before = (self.root / ".project-corpus/state/STATUS.md").read_bytes()
        self.assertTrue(validate_candidate(corpus, candidate)["ok"])
        self.assertEqual(before, (self.root / ".project-corpus/state/STATUS.md").read_bytes())
        candidate["source_refs"] = []
        self.assertIn("CANDIDATE_WITHOUT_EVIDENCE", {item["code"] for item in memory_doctor(self.root, candidates=[candidate])["issues"]})

    def test_eval_metrics(self):
        corpus = self.build()
        dataset = {"schema_version": "1", "cases": [{"name": "current-color", "query": "color", "expected_source_paths": [".project-corpus/state/STATUS.md"], "forbidden_source_paths": ["other-project/secret.md"], "expected_temporal_status": "current", "must_contain": ["blue"], "max_tokens": 300}]}
        result = evaluate_dataset(corpus, dataset)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["results"][0]["deterministic_repeatability"])

    def test_mcp_success_denial_and_strict_arguments(self):
        policy = parse_project_policy((self.root / ".project-corpus/policy.toml").read_bytes())
        grant = replace(self.trust, policy_sha256=policy.digest, capability_ceiling=self.trust.capability_ceiling | {"mcp.stdio", "corpus.context"})
        trust_path = self.base / "owner" / "grant.toml"
        write_trust_grant(trust_path, grant)
        runtime = McpRuntime(trust_path, frozenset({"mcp.stdio", "corpus.context"}))
        listed = {item["name"] for item in runtime.listed_tools()}
        self.assertIn("corpus.context_bundle", listed)
        self.assertTrue(runtime.call("corpus.context_query", {"query": "color", "limit": 5})["results"])
        self.assertTrue(runtime.call("corpus.context_bundle", {"query": "color", "max_tokens": 300})["non_authoritative"])
        self.assertTrue(runtime.call("corpus.context_doctor", {})["ok"])
        with self.assertRaises(ValueError):
            runtime.call("corpus.context_query", {"query": "color", "limit": 5, "path": "../outside"})
        denied = McpRuntime(trust_path, frozenset({"mcp.stdio"}))
        with self.assertRaises(PermissionError):
            denied.call("corpus.context_query", {"query": "color", "limit": 5})
        server = StdioMcpServer(runtime)
        server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})
        server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        result = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "corpus.context_query", "arguments": {"query": "color", "limit": 5}}})
        self.assertFalse(result["result"]["isError"])
        result = server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "corpus.context_query", "arguments": {"query": "color", "limit": 5, "path": "../outside"}}})
        self.assertTrue(result["result"]["isError"])

    def test_cli_build_query_bundle_doctor_eval_candidate_and_denial(self):
        def invoke(*args):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(["context", *map(str, args)])
            return code, json.loads(out.getvalue() if code == 0 else err.getvalue())

        self.assertEqual(invoke("build", self.root, "--index", self.index)[0], 0)
        self.assertEqual(invoke("query", self.root, "color", "--index", self.index)[1]["results"][0]["source_path"], ".project-corpus/state/STATUS.md")
        self.assertTrue(invoke("bundle", self.root, "color", "--index", self.index, "--max-tokens", 250)[1]["bundle_sha256"])
        self.assertTrue(invoke("doctor", self.root, "--index", self.index)[1]["ok"])
        dataset = self.root / "eval.json"
        dataset.write_text(json.dumps({"schema_version": "1", "cases": [{"query": "color", "expected_source_paths": [".project-corpus/state/STATUS.md"]}]}), encoding="utf-8")
        self.assertTrue(invoke("eval", self.root, "--index", self.index, "--dataset", dataset)[1]["ok"])
        corpus = open_index(self.root, self.index)
        candidate = self.root / "candidate.json"
        candidate.write_text(json.dumps({"schema_version": "1", "candidate_id": "candidate-one", "project_id": corpus.project_id, "kind": "semantic_fact", "statement": "Blue.", "source_refs": [{"source_path": ".project-corpus/state/STATUS.md", "source_sha256": corpus.snapshot[".project-corpus/state/STATUS.md"], "line_start": 12}], "created_at": "2026-09-25T00:00:00Z", "status": "candidate"}), encoding="utf-8")
        self.assertTrue(invoke("candidate-validate", self.root, "--input", candidate)[1]["ok"])
        code, error = invoke("eval", self.root, "--index", self.index, "--dataset", self.base / "outside.json")
        self.assertEqual((code, error["error"]), (2, "CONTEXT_INPUT_PATH"))


if __name__ == "__main__":
    unittest.main()
