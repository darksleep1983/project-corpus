from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from project_corpus.cli import main
from tests.test_transactions import make_fixture


def invoke(arguments: list[str]) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    content = stdout.getvalue() if code == 0 else stderr.getvalue()
    return code, json.loads(content)


class CliTests(unittest.TestCase):
    def setUp(self):
        repository = Path(__file__).resolve().parents[1]
        self.temporary = tempfile.TemporaryDirectory(dir=repository)
        self.base = Path(self.temporary.name)
        self.project, _, _, self.old, self.new = make_fixture(self.base)
        self.trust = self.base / "owner-config" / "trust" / "fixture.toml"

    def tearDown(self):
        self.temporary.cleanup()

    def create_trust(self) -> dict[str, object]:
        arguments = [
            "trust", "create", str(self.project), "--trust", str(self.trust),
        ]
        for capability in (
            "corpus.read", "corpus.stat", "corpus.validate", "state.update",
            "task.create", "report.create", "audit.read",
        ):
            arguments.extend(("--allow", capability))
        code, value = invoke(arguments)
        self.assertEqual(code, 0, value)
        return value

    def test_controlled_cli_update_read_stat_and_audit(self):
        trust_receipt = self.create_trust()
        self.assertNotIn(str(self.project), json.dumps(trust_receipt))
        code, initialized = invoke(["runtime", "init", "--trust", str(self.trust)])
        self.assertEqual(code, 0, initialized)

        replacement = self.base / "replacement-status.md"
        replacement.write_bytes(self.new)
        code, result = invoke([
            "state", "update", "--trust", str(self.trust),
            "--input", str(replacement),
            "--expected-sha256", hashlib.sha256(self.old).hexdigest(),
        ])
        self.assertEqual(code, 0, result)
        self.assertEqual(result["phase"], "COMPLETE")

        code, read = invoke([
            "read", "--trust", str(self.trust),
            "--path", ".project-corpus/state/STATUS.md",
        ])
        self.assertEqual(code, 0, read)
        self.assertEqual(read["content"].encode(), self.new)
        code, stat = invoke([
            "stat", "--trust", str(self.trust),
            "--path", ".project-corpus/state/STATUS.md",
        ])
        self.assertEqual(code, 0, stat)
        self.assertEqual(stat["stat"]["sha256"], hashlib.sha256(self.new).hexdigest())

        code, audit = invoke([
            "audit-read", "--trust", str(self.trust),
            "--transaction-id", result["transaction_id"],
        ])
        self.assertEqual(code, 0, audit)
        receipt = json.loads(audit["content"])
        self.assertEqual(receipt["transaction_id"], result["transaction_id"])

    def test_cli_fails_closed_before_runtime_provisioning(self):
        self.create_trust()
        replacement = self.base / "replacement-status.md"
        replacement.write_bytes(self.new)
        code, error = invoke([
            "state", "update", "--trust", str(self.trust),
            "--input", str(replacement),
            "--expected-sha256", hashlib.sha256(self.old).hexdigest(),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(error["error"], "RUNTIME_STORE_NOT_PROVISIONED")
        target = self.project / ".project-corpus" / "state" / "STATUS.md"
        self.assertEqual(target.read_bytes(), self.old)

    def test_cli_rejects_ungranted_capability_and_scope(self):
        code, _ = invoke([
            "trust", "create", str(self.project), "--trust", str(self.trust),
            "--allow", "corpus.read",
        ])
        self.assertEqual(code, 0)
        code, _ = invoke(["runtime", "init", "--trust", str(self.trust)])
        self.assertEqual(code, 0)
        replacement = self.base / "replacement-status.md"
        replacement.write_bytes(self.new)
        code, error = invoke([
            "state", "update", "--trust", str(self.trust),
            "--input", str(replacement),
            "--expected-sha256", hashlib.sha256(self.old).hexdigest(),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(error["error"], "CAPABILITY_DENIED")

        code, error = invoke([
            "read", "--trust", str(self.trust), "--path", "AGENTS.md",
        ])
        self.assertEqual(code, 2)
        self.assertEqual(error["error"], "PermissionError")

    def test_doctor_verifies_native_trust_without_claiming_operation(self):
        self.create_trust()
        code, report = invoke([
            "doctor", str(self.project), "--trust", str(self.trust),
        ])
        self.assertEqual(code, 0, report)
        self.assertTrue(report["ok"])
        self.assertEqual(report["guarantee_level"], "DIRECT_FOLDER_OBSERVABLE")
        codes = {item["code"] for item in report["checks"]}
        self.assertIn("ROOT_IDENTITY", codes)
        self.assertIn("FILESYSTEM_QUALIFIED", codes)

    def test_policy_change_requires_explicit_owner_approval(self):
        self.create_trust()
        policy = self.project / ".project-corpus" / "policy.toml"
        policy.write_bytes(policy.read_bytes() + b"\n")
        code, initialization = invoke([
            "runtime", "init", "--trust", str(self.trust),
        ])
        self.assertEqual(code, 2)
        self.assertIn("policy digest changed", initialization["detail"])
        code, before = invoke([
            "doctor", str(self.project), "--trust", str(self.trust),
        ])
        self.assertEqual(code, 0)
        self.assertFalse(before["ok"])
        self.assertIn("POLICY_DRIFT", {item["code"] for item in before["checks"]})

        code, approval = invoke([
            "trust", "approve-policy", "--trust", str(self.trust),
        ])
        self.assertEqual(code, 0, approval)
        code, after = invoke([
            "doctor", str(self.project), "--trust", str(self.trust),
        ])
        self.assertEqual(code, 0)
        self.assertTrue(after["ok"])

    def test_validate_and_migration_plan_are_read_only(self):
        code, validation = invoke(["validate", str(self.project)])
        self.assertEqual(code, 0)
        self.assertTrue(validation["ok"])

        repository = Path(__file__).resolve().parents[1]
        source = repository / "template" / "en"
        before = {
            path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source.rglob("*") if path.is_file()
        }
        code, plan = invoke([
            "migration", "plan", str(source),
            "--project-id", "cli-migration", "--logical-name", "CLI Migration",
        ])
        self.assertEqual(code, 0, plan)
        after = {
            path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(plan["project_id"], "cli-migration")

    def test_trust_and_runtime_state_must_be_external(self):
        inside = self.project / ".project-corpus" / "owner" / "grant.toml"
        code, error = invoke([
            "trust", "create", str(self.project), "--trust", str(inside),
            "--allow", "corpus.read",
        ])
        self.assertEqual(code, 2)
        self.assertIn("TRUST_GRANT_NOT_EXTERNAL", error["detail"])
        self.assertFalse(inside.exists())

        self.create_trust()
        original = self.trust.read_text(encoding="utf-8")
        embedded = self.project / ".project-corpus" / "grant.toml"
        embedded.write_text(original, encoding="utf-8")
        code, error = invoke(["runtime", "init", "--trust", str(embedded)])
        self.assertEqual(code, 2)
        self.assertIn("TRUST_GRANT_NOT_EXTERNAL", error["detail"])

    def test_trust_create_rejects_nonconformant_project(self):
        project = self.project / ".project-corpus" / "state" / "PROJECT.md"
        project.write_text(
            project.read_text(encoding="utf-8").replace(
                "Project-ID: fixture-project", "Project-ID: different-project"
            ),
            encoding="utf-8",
        )
        code, error = invoke([
            "trust", "create", str(self.project), "--trust", str(self.trust),
            "--allow", "corpus.read",
        ])
        self.assertEqual(code, 2)
        self.assertIn("not V2-conformant", error["detail"])
        self.assertFalse(self.trust.exists())


if __name__ == "__main__":
    unittest.main()
