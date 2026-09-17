from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from .authority import AuthorityDecision, evaluate_authority
from .platform import BackendError, PathStat, StagedWrite, open_native_backend
from .platform.base import NativePathBackend
from .platform.common import validate_relative_path
from .policy import ProjectPolicy, parse_project_policy
from .trust import TrustGrant
from .validation import parse_document, validate_state_pair


ABSENT = "ABSENT"
MAX_MANAGED_BYTES = 8 * 1024 * 1024
JOURNAL_FORMAT = "project-corpus-transaction-v1"
AUDIT_FORMAT = "project-corpus-audit-v1"
PHASES = (
    "PREPARED", "STAGED", "BACKED_UP", "PUBLISHED", "VERIFIED",
    "AUDITED", "COMPLETE", "ROLLED_BACK", "NEEDS_OWNER",
)
TERMINAL_PHASES = frozenset({"COMPLETE", "ROLLED_BACK", "NEEDS_OWNER"})
HASH = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[0-9a-f]{32}$")


class TransactionError(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class SimulatedCrash(BaseException):
    """Test-only process-crash boundary. Production adapters never expose it."""


@dataclass(frozen=True)
class JournalRecord:
    format: str
    transaction_id: str
    project_id: str
    phase: str
    operation: str
    capability: str
    target: str
    stage_id: str
    expected_sha256: str
    old_sha256: str | None
    old_identity: str | None
    new_sha256: str
    new_identity: str | None
    metadata_fingerprint: str | None
    backup_relative: str | None
    audit_relative: str
    audit_sha256: str | None
    started_at: str
    completed_at: str | None
    updated_at: str
    outcome_reason: str | None
    filesystem: str
    root_identity: str
    durability_level: str

    def to_bytes(self) -> bytes:
        return (json.dumps(asdict(self), indent=2, sort_keys=True) + "\n").encode()

    @classmethod
    def from_bytes(cls, content: bytes) -> "JournalRecord":
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransactionError("JOURNAL_PARSE", str(exc)) from exc
        if not isinstance(value, dict) or set(value) != set(cls.__dataclass_fields__):
            raise TransactionError("JOURNAL_SCHEMA", "field set differs")
        try:
            record = cls(**value)
        except TypeError as exc:
            raise TransactionError("JOURNAL_SCHEMA", str(exc)) from exc
        record.validate()
        return record

    def validate(self) -> None:
        string_fields = (
            "format", "transaction_id", "project_id", "phase", "operation",
            "capability", "target", "stage_id", "expected_sha256",
            "new_sha256", "audit_relative", "started_at", "updated_at",
            "filesystem", "root_identity", "durability_level",
        )
        if any(not isinstance(getattr(self, key), str) for key in string_fields):
            raise TransactionError("JOURNAL_SCHEMA", "string field type")
        optional_strings = (
            "old_sha256", "old_identity", "new_identity",
            "metadata_fingerprint", "backup_relative", "audit_sha256",
            "completed_at", "outcome_reason",
        )
        if any(
            value is not None and not isinstance(value, str)
            for value in (getattr(self, key) for key in optional_strings)
        ):
            raise TransactionError("JOURNAL_SCHEMA", "optional field type")
        if self.format != JOURNAL_FORMAT or not ID.fullmatch(self.transaction_id):
            raise TransactionError("JOURNAL_SCHEMA", "format or transaction id")
        if self.phase not in PHASES or self.operation not in {"create", "update"}:
            raise TransactionError("JOURNAL_SCHEMA", "phase or operation")
        if self.capability not in {"state.update", "task.create", "report.create"}:
            raise TransactionError("JOURNAL_SCHEMA", "capability")
        try:
            validate_relative_path(self.target, windows=os.name == "nt")
            validate_relative_path(self.audit_relative, windows=os.name == "nt")
        except ValueError as exc:
            raise TransactionError("JOURNAL_SCHEMA", str(exc)) from exc
        if not ID.fullmatch(self.stage_id) or not HASH.fullmatch(self.new_sha256):
            raise TransactionError("JOURNAL_SCHEMA", "stage id or new hash")
        if self.old_sha256 is not None and not HASH.fullmatch(self.old_sha256):
            raise TransactionError("JOURNAL_SCHEMA", "old hash")
        if self.audit_sha256 is not None and not HASH.fullmatch(self.audit_sha256):
            raise TransactionError("JOURNAL_SCHEMA", "audit hash")
        if self.metadata_fingerprint is not None and not HASH.fullmatch(
            self.metadata_fingerprint
        ):
            raise TransactionError("JOURNAL_SCHEMA", "metadata fingerprint")
        if self.audit_relative != (
            f".project-corpus/audit/{self.transaction_id}.json"
        ):
            raise TransactionError("JOURNAL_SCHEMA", "audit path")
        expected_backup = (
            f"backups/{self.transaction_id}.bin"
            if self.operation == "update" else None
        )
        if self.backup_relative not in {None, expected_backup}:
            raise TransactionError("JOURNAL_SCHEMA", "backup path")
        if self.operation == "create":
            if self.expected_sha256 != ABSENT or self.old_sha256 is not None:
                raise TransactionError("JOURNAL_SCHEMA", "create state")
        elif (
            not HASH.fullmatch(self.expected_sha256) or
            self.old_sha256 != self.expected_sha256
        ):
            raise TransactionError("JOURNAL_SCHEMA", "update state")


@dataclass(frozen=True)
class TransactionResult:
    transaction_id: str
    phase: str
    target: str
    sha256: str | None
    audit_relative: str | None
    reason: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _stage_token(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:32]


def _inside(path: str, scopes: tuple[str, ...]) -> bool:
    for scope in scopes:
        if scope.endswith("/**"):
            prefix = scope[:-3]
            if path.startswith(prefix + "/"):
                return True
        elif fnmatch.fnmatchcase(path, scope):
            return True
    return False


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


class TrustedRuntimeStore:
    """Single-project recovery state rooted in external owner-controlled config."""

    ACTIVE = "journal/active.json"
    LOCK = "locks/writer.lock"

    def __init__(self, root: Path):
        self.root = root
        self.backend = open_native_backend(root)
        try:
            for marker in ("journal/.keep", "backups/.keep", "locks/.keep"):
                self.backend.stat(marker)
        except Exception:
            self.backend.close()
            raise TransactionError(
                "RUNTIME_STORE_NOT_PROVISIONED",
                "owner-controlled journal, backups and locks directories are required",
            )

    def close(self) -> None:
        self.backend.close()

    def writer_lock(self):
        return self.backend.writer_lock(self.LOCK)

    def read_active(self) -> JournalRecord | None:
        if self.backend.stat_optional(self.ACTIVE) is None:
            return None
        return JournalRecord.from_bytes(
            self.backend.read_bytes(self.ACTIVE, max_bytes=1024 * 1024)
        )

    def write_active(self, record: JournalRecord) -> None:
        record.validate()
        content = record.to_bytes()
        current = self.backend.stat_optional(self.ACTIVE)
        stage_id = _stage_token(record.transaction_id, "journal", record.phase)
        self.backend.discard_stage(self.ACTIVE, stage_id)
        staged = self.backend.stage_bytes(
            self.ACTIVE, content, stage_id=stage_id
        )
        try:
            if current is not None:
                self.backend.prepare_replacement(staged)
            result = self.backend.publish(staged, replace=current is not None)
        except Exception:
            self.backend.discard(staged)
            raise
        if result.sha256 != hashlib.sha256(content).hexdigest():
            raise TransactionError("JOURNAL_VERIFY", record.transaction_id)

    def backup(self, record: JournalRecord, content: bytes) -> str:
        relative = f"backups/{record.transaction_id}.bin"
        expected = hashlib.sha256(content).hexdigest()
        current = self.backend.stat_optional(relative)
        if current is not None:
            if current.sha256 != expected:
                raise TransactionError("BACKUP_CONFLICT", record.transaction_id)
            return relative
        stage_id = _stage_token(record.transaction_id, "backup")
        self.backend.discard_stage(relative, stage_id)
        staged = self.backend.stage_bytes(relative, content, stage_id=stage_id)
        try:
            result = self.backend.publish(staged, replace=False)
        except Exception:
            self.backend.discard(staged)
            raise
        if result.sha256 != expected or self.backend.read_bytes(relative) != content:
            raise TransactionError("BACKUP_VERIFY", record.transaction_id)
        return relative

    def verify_backup(self, record: JournalRecord) -> bool:
        if record.operation == "create":
            return record.backup_relative is None
        if record.backup_relative is None or record.old_sha256 is None:
            return False
        stat = self.backend.stat_optional(record.backup_relative)
        return stat is not None and stat.sha256 == record.old_sha256

    def cleanup_stages(self, record: JournalRecord) -> None:
        for phase in PHASES:
            self.backend.discard_stage(
                self.ACTIVE, _stage_token(record.transaction_id, "journal", phase)
            )
        if record.backup_relative:
            self.backend.discard_stage(
                record.backup_relative,
                _stage_token(record.transaction_id, "backup"),
            )


class TransactionEngine:
    def __init__(
        self,
        *,
        trust: TrustGrant,
        runtime_state_root: Path,
        session_capabilities: set[str] | frozenset[str],
        transport: str,
        _fault_after: str | None = None,
    ):
        self.trust = trust
        self.session_capabilities = frozenset(session_capabilities)
        self.transport = transport
        self._fault_after = _fault_after
        self.project = open_native_backend(trust.physical_root)
        self.store: TrustedRuntimeStore | None = None
        try:
            project_path = trust.physical_root.resolve()
            runtime_path = runtime_state_root.resolve()
            common = Path(os.path.commonpath((project_path, runtime_path)))
            if _same_path(common, project_path) or _same_path(common, runtime_path):
                raise TransactionError(
                    "RUNTIME_STATE_NOT_EXTERNAL",
                    "runtime recovery state must be outside the project tree",
                )
            if self.project.filesystem != trust.filesystem:
                raise TransactionError(
                    "TRUST_FILESYSTEM_MISMATCH",
                    f"grant={trust.filesystem} observed={self.project.filesystem}",
                )
            if trust.protocol_version != "2.0":
                raise TransactionError("TRUST_PROTOCOL_VERSION", trust.protocol_version)
            self.store = TrustedRuntimeStore(runtime_state_root)
            self._load_authority()
            try:
                self.project.stat(".project-corpus/audit/.gitkeep")
            except BackendError as exc:
                raise TransactionError(
                    "AUDIT_DIRECTORY_NOT_PROVISIONED", exc.detail
                ) from exc
        except Exception:
            if self.store is not None:
                self.store.close()
            self.project.close()
            raise

    def __enter__(self) -> "TransactionEngine":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self.store is not None:
            self.store.close()
            self.store = None
        self.project.close()

    def _load_authority(self) -> tuple[ProjectPolicy, AuthorityDecision]:
        policy = parse_project_policy(
            self.project.read_bytes(".project-corpus/policy.toml", max_bytes=1024 * 1024)
        )
        decision = evaluate_authority(
            trust=self.trust,
            policy=policy,
            session_capabilities=self.session_capabilities,
            observed_root_identity=self.project.root_identity,
            transport=self.transport,
        )
        self.policy = policy
        self.authority = decision
        return policy, decision

    def _checkpoint(self, phase: str, staged: StagedWrite | None = None) -> None:
        if self._fault_after == phase:
            if staged is not None:
                self.project.abandon(staged)
            raise SimulatedCrash(phase)

    def _validate_request(
        self, capability: str, target: str, content: bytes, operation: str
    ) -> None:
        validate_relative_path(target, windows=os.name == "nt")
        if len(content) > MAX_MANAGED_BYTES:
            raise TransactionError("CONTENT_LIMIT", str(len(content)))
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TransactionError("CONTENT_ENCODING", str(exc)) from exc
        if not self.authority.permits(capability):
            raise TransactionError("CAPABILITY_DENIED", capability)
        if not _inside(target, self.policy.write_scopes):
            raise TransactionError("WRITE_SCOPE_DENIED", target)
        rules = {
            "state.update": ("update", ".project-corpus/state/STATUS.md"),
            "task.create": ("create", ".project-corpus/tasks/"),
            "report.create": ("create", ".project-corpus/reports/"),
        }
        rule = rules.get(capability)
        if rule is None or rule[0] != operation:
            raise TransactionError("CAPABILITY_OPERATION_MISMATCH", capability)
        if rule[1].endswith("/"):
            if not target.startswith(rule[1]) or not target.endswith(".md"):
                raise TransactionError("CAPABILITY_TARGET_MISMATCH", target)
        elif target != rule[1]:
            raise TransactionError("CAPABILITY_TARGET_MISMATCH", target)

        if capability == "state.update":
            project = self.project.read_bytes(".project-corpus/state/PROJECT.md")
            issues = validate_state_pair(project, content)
            if any(item.severity == "ERROR" for item in issues):
                raise TransactionError(
                    "STATE_CONFORMANCE", ",".join(item.code for item in issues)
                )
        else:
            document = parse_document(content, target)
            required = (
                ("Task-ID", "Task-Status") if capability == "task.create"
                else ("Report-ID", "Result")
            )
            if document.metadata.get("Protocol-Version") != "2.0":
                raise TransactionError("ARTIFACT_CONFORMANCE", "Protocol-Version")
            if document.metadata.get("Project-ID") != self.policy.project_id:
                raise TransactionError("ARTIFACT_CONFORMANCE", "Project-ID")
            if any(not document.metadata.get(key) for key in required):
                raise TransactionError("ARTIFACT_CONFORMANCE", "required metadata")
            identity_key = "Task-ID" if capability == "task.create" else "Report-ID"
            if Path(target).stem != document.metadata.get(identity_key):
                raise TransactionError("ARTIFACT_CONFORMANCE", "artifact id/path mismatch")
            sections = (
                {"Objective", "Scope", "Constraints", "Acceptance Criteria"}
                if capability == "task.create"
                else {"Summary", "Evidence", "Limitations"}
            )
            if not sections.issubset(document.sections):
                raise TransactionError("ARTIFACT_CONFORMANCE", "required sections")

    def _stable_current(self, target: str) -> tuple[PathStat | None, bytes | None]:
        before = self.project.stat_optional(target)
        if before is None:
            return None, None
        content = self.project.read_bytes(target, max_bytes=MAX_MANAGED_BYTES)
        after = self.project.stat(target)
        if (
            before.identity != after.identity or before.sha256 != after.sha256 or
            hashlib.sha256(content).hexdigest() != after.sha256
        ):
            raise TransactionError("TARGET_CHANGED_DURING_READ", target)
        return after, content

    def _record_phase(
        self, record: JournalRecord, phase: str, **changes: Any
    ) -> JournalRecord:
        assert self.store is not None
        updated = replace(record, phase=phase, updated_at=_utc_now(), **changes)
        self.store.write_active(updated)
        return updated

    def _audit_bytes(self, record: JournalRecord) -> bytes:
        value = {
            "format": AUDIT_FORMAT,
            "transaction_id": record.transaction_id,
            "project_id": record.project_id,
            "operation": record.operation,
            "capability": record.capability,
            "target": record.target,
            "old_sha256": record.old_sha256,
            "new_sha256": record.new_sha256,
            "old_identity": record.old_identity,
            "new_identity": record.new_identity,
            "metadata_fingerprint": record.metadata_fingerprint,
            "started_at": record.started_at,
            "completed_at": record.completed_at,
            "filesystem": record.filesystem,
            "durability_level": record.durability_level,
            "guarantee_level": "CONTROLLED_TRANSACTION",
        }
        return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()

    def _write_audit(self, record: JournalRecord) -> str:
        content = self._audit_bytes(record)
        expected = hashlib.sha256(content).hexdigest()
        current = self.project.stat_optional(record.audit_relative)
        if current is not None:
            if current.sha256 != expected or self.project.read_bytes(record.audit_relative) != content:
                raise TransactionError("AUDIT_CONFLICT", record.audit_relative)
            return expected
        stage_id = _stage_token(record.transaction_id, "audit")
        self.project.discard_stage(record.audit_relative, stage_id)
        staged = self.project.stage_bytes(
            record.audit_relative, content, stage_id=stage_id
        )
        try:
            result = self.project.publish(staged, replace=False)
        except Exception:
            self.project.discard(staged)
            raise
        if result.sha256 != expected or self.project.read_bytes(record.audit_relative) != content:
            raise TransactionError("AUDIT_VERIFY", record.transaction_id)
        return expected

    def mutate(
        self,
        *,
        capability: str,
        target: str,
        content: bytes,
        expected_sha256: str,
    ) -> TransactionResult:
        if self.store is None:
            raise TransactionError("ENGINE_CLOSED", "transaction engine is closed")
        if not isinstance(capability, str) or not isinstance(target, str):
            raise TransactionError("REQUEST_SCHEMA", "capability and target must be strings")
        if not isinstance(content, bytes) or not isinstance(expected_sha256, str):
            raise TransactionError("REQUEST_SCHEMA", "content bytes and expected hash are required")
        with self.store.writer_lock():
            active = self.store.read_active()
            if active is not None:
                recovered = self._recover_locked(active)
                if recovered.phase == "NEEDS_OWNER":
                    raise TransactionError("RECOVERY_NEEDS_OWNER", recovered.reason or "")

            self._load_authority()
            operation = "create" if expected_sha256 == ABSENT else "update"
            if operation == "update" and not HASH.fullmatch(expected_sha256):
                raise TransactionError("EXPECTED_HASH", "lowercase SHA-256 or ABSENT required")
            self._validate_request(capability, target, content, operation)
            current, old_content = self._stable_current(target)
            if operation == "create" and current is not None:
                raise TransactionError("TARGET_EXISTS", target)
            if operation == "update":
                if current is None:
                    raise TransactionError("TARGET_MISSING", target)
                if current.sha256 != expected_sha256:
                    raise TransactionError("STALE_HASH", target)

            transaction_id = uuid4().hex
            stage_id = uuid4().hex
            now = _utc_now()
            record = JournalRecord(
                JOURNAL_FORMAT, transaction_id, self.policy.project_id,
                "PREPARED", operation, capability, target, stage_id,
                expected_sha256, current.sha256 if current else None,
                current.identity if current else None,
                hashlib.sha256(content).hexdigest(), None, None, None,
                f".project-corpus/audit/{transaction_id}.json", None,
                now, None, now, None, self.project.filesystem,
                self.project.root_identity, self.project.durability_level,
            )
            self.store.write_active(record)
            self._checkpoint("PREPARED")
            staged: StagedWrite | None = None
            try:
                staged = self.project.stage_bytes(target, content, stage_id=stage_id)
                metadata = (
                    self.project.prepare_replacement(staged)
                    if operation == "update" else None
                )
                record = self._record_phase(
                    record, "STAGED", metadata_fingerprint=metadata
                )
                self._checkpoint("STAGED", staged)

                if operation == "update":
                    assert old_content is not None
                    backup = self.store.backup(record, old_content)
                    record = self._record_phase(
                        record, "BACKED_UP", backup_relative=backup
                    )
                else:
                    record = self._record_phase(record, "BACKED_UP")
                self._checkpoint("BACKED_UP", staged)

                latest = self.project.stat_optional(target)
                if operation == "update":
                    assert current is not None
                    if latest is None or latest.sha256 != current.sha256 or latest.identity != current.identity:
                        raise TransactionError("STALE_BEFORE_PUBLISH", target)
                elif latest is not None:
                    raise TransactionError("TARGET_EXISTS", target)

                published = self.project.publish(staged, replace=operation == "update")
                record = self._record_phase(
                    record, "PUBLISHED", new_identity=published.identity
                )
                self._checkpoint("PUBLISHED", staged)

                readback = self.project.read_bytes(target, max_bytes=MAX_MANAGED_BYTES)
                verified = self.project.stat(target)
                published_metadata = self.project.metadata_fingerprint(target)
                if (
                    readback != content or verified.sha256 != record.new_sha256 or
                    (metadata is not None and published_metadata != metadata)
                ):
                    raise TransactionError("READBACK_VERIFY", target)
                record = self._record_phase(
                    record, "VERIFIED", new_identity=verified.identity,
                    metadata_fingerprint=published_metadata, completed_at=_utc_now(),
                )
                self._checkpoint("VERIFIED")

                audit_sha = self._write_audit(record)
                record = self._record_phase(
                    record, "AUDITED", audit_sha256=audit_sha
                )
                self._checkpoint("AUDITED")
                record = self._record_phase(record, "COMPLETE")
                self.store.cleanup_stages(record)
                return TransactionResult(
                    transaction_id, record.phase, target, record.new_sha256,
                    record.audit_relative,
                )
            except Exception as exc:
                if staged is not None and not staged.published:
                    self.project.discard(staged)
                if record.phase in {"PREPARED", "STAGED", "BACKED_UP"}:
                    record = self._record_phase(
                        record, "ROLLED_BACK", outcome_reason=type(exc).__name__
                    )
                if isinstance(exc, TransactionError):
                    raise
                if isinstance(exc, BackendError):
                    raise TransactionError(exc.code, exc.detail) from exc
                raise TransactionError("TRANSACTION_FAILURE", str(exc)) from exc

    def recover(self) -> TransactionResult | None:
        if self.store is None:
            raise TransactionError("ENGINE_CLOSED", "transaction engine is closed")
        with self.store.writer_lock():
            record = self.store.read_active()
            return None if record is None else self._recover_locked(record)

    def _recover_locked(self, record: JournalRecord) -> TransactionResult:
        assert self.store is not None
        if (
            record.project_id != self.policy.project_id or
            record.root_identity != self.project.root_identity or
            record.filesystem != self.project.filesystem
        ):
            raise TransactionError("JOURNAL_TRUST_MISMATCH", record.transaction_id)
        if record.phase in TERMINAL_PHASES:
            return TransactionResult(
                record.transaction_id, record.phase, record.target,
                record.new_sha256 if record.phase == "COMPLETE" else None,
                record.audit_relative if record.phase == "COMPLETE" else None,
                record.outcome_reason,
            )

        current = self.project.stat_optional(record.target)
        old_state = (
            current is None if record.operation == "create"
            else current is not None and current.sha256 == record.old_sha256
        )
        if old_state:
            self.project.discard_stage(record.target, record.stage_id)
            self.store.cleanup_stages(record)
            record = self._record_phase(
                record, "ROLLED_BACK", outcome_reason="PREPUBLICATION_STATE"
            )
            return TransactionResult(
                record.transaction_id, record.phase, record.target, None, None,
                record.outcome_reason,
            )

        if current is not None and current.sha256 == record.new_sha256:
            if not self.store.verify_backup(record):
                record = self._record_phase(
                    record, "NEEDS_OWNER", outcome_reason="BACKUP_MISSING_OR_INVALID"
                )
            else:
                metadata = self.project.metadata_fingerprint(record.target)
                if (
                    record.metadata_fingerprint is not None and
                    metadata != record.metadata_fingerprint
                ):
                    record = self._record_phase(
                        record, "NEEDS_OWNER", outcome_reason="METADATA_MISMATCH"
                    )
                else:
                    record = self._record_phase(
                        record, "VERIFIED", new_identity=current.identity,
                        metadata_fingerprint=metadata,
                        completed_at=record.completed_at or _utc_now(),
                    )
                    try:
                        audit_sha = self._write_audit(record)
                    except TransactionError as exc:
                        if exc.code != "AUDIT_CONFLICT":
                            raise
                        record = self._record_phase(
                            record, "NEEDS_OWNER",
                            outcome_reason="AUDIT_CONFLICT",
                        )
                    else:
                        record = self._record_phase(
                            record, "AUDITED", audit_sha256=audit_sha
                        )
                        record = self._record_phase(record, "COMPLETE")
                        self.store.cleanup_stages(record)
        else:
            observed = "ABSENT" if current is None else current.sha256
            record = self._record_phase(
                record, "NEEDS_OWNER",
                outcome_reason=f"UNEXPECTED_TARGET:{observed}",
            )

        return TransactionResult(
            record.transaction_id, record.phase, record.target,
            record.new_sha256 if record.phase == "COMPLETE" else None,
            record.audit_relative if record.phase == "COMPLETE" else None,
            record.outcome_reason,
        )
