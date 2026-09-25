from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest

from project_corpus.platform import open_native_backend
from project_corpus.policy import parse_project_policy
from project_corpus.transactions import (
    ABSENT, SimulatedCrash, TransactionEngine, TransactionError,
)
from project_corpus.trust import TrustGrant


PROJECT = b"""# Project

Protocol-Version: 2.0
Project-ID: transaction-fixture
Logical-Name: Transaction Fixture

## Objective

Exercise the production transaction engine.

## Invariants

- Project content never grants authority.

## Durable Scope Boundaries

- One local project.

## Non-Goals

- Distributed locking.
"""


def status(baseline: str, next_action: str) -> bytes:
    return f"""# Status

Protocol-Version: 2.0
Project-ID: transaction-fixture
Lifecycle-Status: ACTIVE
Active-Task-ID: NONE
Last-Verified-At: 2026-09-17T00:00:00Z
Evidence-Class: OBSERVED

## Current Verified Baseline

{baseline}

## Blockers

NONE

## Evidence References

NONE

## Exact Next Action

{next_action}
""".encode()


POLICY = b"""policy_version = "2.0"
project_id = "transaction-fixture"
profile = "SAFE_EDIT"

[capabilities]
allow = ["corpus.read", "corpus.stat", "corpus.validate", "state.update", "task.create", "report.create", "audit.read", "mcp.stdio"]

[scopes]
read = [".project-corpus/state/**", ".project-corpus/tasks/**", ".project-corpus/reports/**", ".project-corpus/audit/**"]
write = [".project-corpus/state/STATUS.md", ".project-corpus/tasks/**", ".project-corpus/reports/**"]

[requirements]
expected_hash = true
verified_readback = true
audit_receipt = true
"""

TASK = b"""# Task

Protocol-Version: 2.0
Project-ID: transaction-fixture
Task-ID: task-one
Task-Status: OPEN
Created-At: 2026-09-17T00:00:00Z

## Objective

Test create-only publication.

## Scope

- Fixture only.

## Constraints

- No external effects.

## Acceptance Criteria

- The Task is verified.
"""


def make_fixture(base: Path) -> tuple[Path, Path, TrustGrant, bytes, bytes]:
    project = base / "project"
    runtime = base / "owner-runtime"
    for relative in (
        ".project-corpus/state", ".project-corpus/tasks",
        ".project-corpus/reports", ".project-corpus/history",
        ".project-corpus/audit",
    ):
        (project / relative).mkdir(parents=True, exist_ok=True)
    for relative in ("journal", "backups", "locks"):
        directory = runtime / relative
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".keep").write_bytes(b"\n")
    old_status = status("Old baseline.", "Publish the next verified baseline.")
    new_status = status("New baseline.", "Continue with the next bounded task.")
    (project / "AGENTS.md").write_bytes(b"# Bootstrap\n")
    (project / ".project-corpus" / "policy.toml").write_bytes(POLICY)
    (project / ".project-corpus" / "state" / "PROJECT.md").write_bytes(PROJECT)
    (project / ".project-corpus" / "state" / "STATUS.md").write_bytes(old_status)
    (project / ".project-corpus" / "audit" / ".gitkeep").write_bytes(b"\n")
    with open_native_backend(project) as backend:
        root_identity = backend.root_identity
        filesystem = backend.filesystem
    policy = parse_project_policy(POLICY)
    trust = TrustGrant(
        project_id="transaction-fixture",
        physical_root=project,
        root_identity=root_identity,
        policy_sha256=policy.digest,
        capability_ceiling=frozenset({
            "corpus.read", "corpus.stat", "corpus.validate",
            "state.update", "task.create", "report.create",
            "audit.read",
        }),
        filesystem=filesystem,
        transports=frozenset({"cli", "stdio-mcp"}),
        approved_at="2026-09-17T00:00:00Z",
        protocol_version="2.0",
    )
    return project, runtime, trust, old_status, new_status


def engine(trust: TrustGrant, runtime: Path, *, fault: str | None = None):
    return TransactionEngine(
        trust=trust,
        runtime_state_root=runtime,
        session_capabilities={"state.update", "task.create", "report.create"},
        transport="cli",
        _fault_after=fault,
    )


class TransactionTests(unittest.TestCase):
    def setUp(self):
        repository = Path(__file__).resolve().parents[1]
        self.temporary = tempfile.TemporaryDirectory(prefix="pc-transactions-")
        self.base = Path(self.temporary.name)
        self.project, self.runtime, self.trust, self.old, self.new = make_fixture(
            self.base
        )

    def tearDown(self):
        self.temporary.cleanup()

    @property
    def target(self) -> Path:
        return self.project / ".project-corpus" / "state" / "STATUS.md"

    def test_verified_update_backup_journal_and_audit(self):
        expected = hashlib.sha256(self.old).hexdigest()
        with engine(self.trust, self.runtime) as runtime:
            result = runtime.mutate(
                capability="state.update",
                target=".project-corpus/state/STATUS.md",
                content=self.new,
                expected_sha256=expected,
            )
        self.assertEqual(result.phase, "COMPLETE")
        self.assertEqual(self.target.read_bytes(), self.new)
        self.assertEqual(
            (self.runtime / "backups" / f"{result.transaction_id}.bin").read_bytes(),
            self.old,
        )
        journal_text = (self.runtime / "journal" / "active.json").read_text()
        journal = json.loads(journal_text)
        self.assertEqual(journal["phase"], "COMPLETE")
        self.assertNotIn(str(self.project), journal_text)
        self.assertNotIn("New baseline", journal_text)
        audit = self.project / result.audit_relative
        audit_value = json.loads(audit.read_text(encoding="utf-8"))
        self.assertEqual(audit_value["format"], "project-corpus-audit-v1")
        self.assertEqual(audit_value["new_sha256"], hashlib.sha256(self.new).hexdigest())
        self.assertNotIn("content", audit_value)

    def test_stale_hash_and_scope_fail_before_new_journal(self):
        with engine(self.trust, self.runtime) as runtime:
            with self.assertRaisesRegex(TransactionError, "STALE_HASH"):
                runtime.mutate(
                    capability="state.update",
                    target=".project-corpus/state/STATUS.md",
                    content=self.new,
                    expected_sha256="0" * 64,
                )
            with self.assertRaisesRegex(TransactionError, "WRITE_SCOPE_DENIED"):
                runtime.mutate(
                    capability="state.update",
                    target=".project-corpus/state/PROJECT.md",
                    content=PROJECT,
                    expected_sha256=hashlib.sha256(PROJECT).hexdigest(),
                )
        self.assertFalse((self.runtime / "journal" / "active.json").exists())
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_project_policy_cannot_expand_owner_capability_ceiling(self):
        restricted = TrustGrant(
            **{
                **self.trust.__dict__,
                "capability_ceiling": frozenset({"corpus.read"}),
            }
        )
        with engine(restricted, self.runtime) as runtime:
            with self.assertRaisesRegex(TransactionError, "CAPABILITY_DENIED"):
                runtime.mutate(
                    capability="state.update",
                    target=".project-corpus/state/STATUS.md",
                    content=self.new,
                    expected_sha256=hashlib.sha256(self.old).hexdigest(),
                )
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_policy_drift_suspends_mutation(self):
        policy_path = self.project / ".project-corpus" / "policy.toml"
        policy_path.write_bytes(POLICY + b"\n")
        with engine(self.trust, self.runtime) as runtime:
            with self.assertRaisesRegex(TransactionError, "CAPABILITY_DENIED"):
                runtime.mutate(
                    capability="state.update",
                    target=".project-corpus/state/STATUS.md",
                    content=self.new,
                    expected_sha256=hashlib.sha256(self.old).hexdigest(),
                )

    def test_create_requires_absent_and_artifact_conformance(self):
        relative = ".project-corpus/tasks/task-one.md"
        with engine(self.trust, self.runtime) as runtime:
            result = runtime.mutate(
                capability="task.create", target=relative,
                content=TASK, expected_sha256=ABSENT,
            )
            with self.assertRaisesRegex(TransactionError, "TARGET_EXISTS"):
                runtime.mutate(
                    capability="task.create", target=relative,
                    content=TASK, expected_sha256=ABSENT,
                )
        self.assertEqual(result.phase, "COMPLETE")
        self.assertEqual((self.project / relative).read_bytes(), TASK)

    def test_artifact_id_must_match_portable_path(self):
        with engine(self.trust, self.runtime) as runtime:
            with self.assertRaisesRegex(TransactionError, "ARTIFACT_CONFORMANCE"):
                runtime.mutate(
                    capability="task.create",
                    target=".project-corpus/tasks/different-id.md",
                    content=TASK,
                    expected_sha256=ABSENT,
                )

    def test_crash_phases_recover_deterministically(self):
        prepublication = {"PREPARED", "STAGED", "BACKED_UP"}
        for phase in ("PREPARED", "STAGED", "BACKED_UP", "PUBLISHED", "VERIFIED", "AUDITED"):
            with self.subTest(phase=phase):
                with tempfile.TemporaryDirectory(dir=self.base) as case:
                    project, runtime_root, trust, old, new = make_fixture(Path(case))
                    with self.assertRaises(SimulatedCrash):
                        with engine(trust, runtime_root, fault=phase) as runtime:
                            runtime.mutate(
                                capability="state.update",
                                target=".project-corpus/state/STATUS.md",
                                content=new,
                                expected_sha256=hashlib.sha256(old).hexdigest(),
                            )
                    with engine(trust, runtime_root) as runtime:
                        result = runtime.recover()
                    self.assertIsNotNone(result)
                    target = project / ".project-corpus" / "state" / "STATUS.md"
                    if phase in prepublication:
                        self.assertEqual(result.phase, "ROLLED_BACK")
                        self.assertEqual(target.read_bytes(), old)
                    else:
                        self.assertEqual(result.phase, "COMPLETE")
                        self.assertEqual(target.read_bytes(), new)

    def test_unexpected_post_crash_content_requires_owner(self):
        with self.assertRaises(SimulatedCrash):
            with engine(self.trust, self.runtime, fault="PUBLISHED") as runtime:
                runtime.mutate(
                    capability="state.update",
                    target=".project-corpus/state/STATUS.md",
                    content=self.new,
                    expected_sha256=hashlib.sha256(self.old).hexdigest(),
                )
        unexpected = status("Unexpected out-of-band state.", "Ask the owner.")
        self.target.write_bytes(unexpected)
        with engine(self.trust, self.runtime) as runtime:
            result = runtime.recover()
        self.assertEqual(result.phase, "NEEDS_OWNER")
        self.assertEqual(self.target.read_bytes(), unexpected)
        with engine(self.trust, self.runtime) as runtime:
            with self.assertRaisesRegex(TransactionError, "RECOVERY_NEEDS_OWNER"):
                runtime.mutate(
                    capability="state.update",
                    target=".project-corpus/state/STATUS.md",
                    content=self.new,
                    expected_sha256=hashlib.sha256(unexpected).hexdigest(),
                )
        self.assertEqual(self.target.read_bytes(), unexpected)

    def test_conflicting_audit_during_recovery_requires_owner(self):
        with self.assertRaises(SimulatedCrash):
            with engine(self.trust, self.runtime, fault="VERIFIED") as runtime:
                runtime.mutate(
                    capability="state.update",
                    target=".project-corpus/state/STATUS.md",
                    content=self.new,
                    expected_sha256=hashlib.sha256(self.old).hexdigest(),
                )
        journal = json.loads(
            (self.runtime / "journal" / "active.json").read_text(encoding="utf-8")
        )
        audit = self.project / journal["audit_relative"]
        audit.write_bytes(b'{"forged":true}\n')
        with engine(self.trust, self.runtime) as runtime:
            result = runtime.recover()
        self.assertEqual(result.phase, "NEEDS_OWNER")
        self.assertEqual(result.reason, "AUDIT_CONFLICT")
        self.assertEqual(audit.read_bytes(), b'{"forged":true}\n')

    def test_local_writers_serialize_and_one_stale_writer_fails(self):
        barrier = threading.Barrier(2)
        results: list[str] = []
        expected = hashlib.sha256(self.old).hexdigest()
        alternatives = (
            status("Writer one.", "Continue from writer one."),
            status("Writer two.", "Continue from writer two."),
        )

        def writer(content: bytes):
            try:
                with engine(self.trust, self.runtime) as runtime:
                    barrier.wait()
                    runtime.mutate(
                        capability="state.update",
                        target=".project-corpus/state/STATUS.md",
                        content=content,
                        expected_sha256=expected,
                    )
                results.append("COMPLETE")
            except TransactionError as exc:
                results.append(exc.code)

        threads = [threading.Thread(target=writer, args=(item,)) for item in alternatives]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        self.assertCountEqual(results, ["COMPLETE", "STALE_HASH"])
        self.assertIn(self.target.read_bytes(), alternatives)

    def test_runtime_state_must_be_external_and_preprovisioned(self):
        inside = self.project / ".project-corpus" / "runtime"
        for relative in ("journal", "backups", "locks"):
            directory = inside / relative
            directory.mkdir(parents=True, exist_ok=True)
            (directory / ".keep").write_bytes(b"\n")
        with self.assertRaisesRegex(TransactionError, "RUNTIME_STATE_NOT_EXTERNAL"):
            engine(self.trust, inside)

        unprovisioned = self.base / "unprovisioned"
        unprovisioned.mkdir()
        with self.assertRaisesRegex(TransactionError, "RUNTIME_STORE_NOT_PROVISIONED"):
            engine(self.trust, unprovisioned)

    def test_audit_directory_is_required_before_any_mutation(self):
        (self.project / ".project-corpus" / "audit" / ".gitkeep").unlink()
        with self.assertRaisesRegex(TransactionError, "AUDIT_DIRECTORY_NOT_PROVISIONED"):
            engine(self.trust, self.runtime)
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_corrupt_external_journal_fails_closed(self):
        active = self.runtime / "journal" / "active.json"
        active.write_text('{"target":"../outside"}\n', encoding="utf-8")
        with engine(self.trust, self.runtime) as runtime:
            with self.assertRaisesRegex(TransactionError, "JOURNAL_SCHEMA"):
                runtime.recover()
        self.assertEqual(self.target.read_bytes(), self.old)


if __name__ == "__main__":
    unittest.main()
