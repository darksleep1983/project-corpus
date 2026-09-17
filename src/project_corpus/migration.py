from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

from .authority import RUNTIME_HARD_LIMITS
from .compatibility import LegacySnapshot, load_v1_corpus_confined
from .platform import open_native_backend
from .platform.common import validate_relative_path
from .policy import parse_project_policy
from .trust import (
    TrustGrant, load_trust_grant, provision_runtime_state, runtime_state_path,
    write_trust_grant,
)
from .validation import validate_v2_project


PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


@dataclass(frozen=True)
class PlannedFile:
    relative_path: str
    content: bytes
    source_paths: tuple[str, ...]

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass(frozen=True)
class MigrationPlan:
    project_id: str
    logical_name: str
    source_manifest: dict[str, str]
    planned_files: tuple[PlannedFile, ...]
    trust_root_suggestion: str | None
    warnings: tuple[str, ...]

    def public_receipt(self) -> dict[str, object]:
        return {
            "format": "project-corpus-v1-to-v2-plan-v1",
            "project_id": self.project_id,
            "logical_name": self.logical_name,
            "source_manifest": dict(sorted(self.source_manifest.items())),
            "planned_files": [
                {
                    "path": item.relative_path,
                    "sha256": item.sha256,
                    "sources": list(item.source_paths),
                }
                for item in self.planned_files
            ],
            "trust_root_suggestion_present": self.trust_root_suggestion is not None,
            "warnings": list(self.warnings),
        }

    def public_receipt_json(self) -> str:
        return json.dumps(self.public_receipt(), indent=2, sort_keys=True) + "\n"


def _section(text: str, names: tuple[str, ...]) -> str | None:
    alternatives = "|".join(re.escape(name) for name in names)
    match = re.search(
        rf"(?ms)^## (?:{alternatives})\s*\n+(.+?)(?=^## |\Z)", text
    )
    return match.group(1).strip() if match else None


def _primary_status(text: str) -> str | None:
    match = re.search(
        r"(?mi)^\*\*(?:Status|Статус):\*\*\s*`?([A-Z_]+)`?\s*$", text
    )
    return match.group(1) if match else None


def _root_suggestion(text: str) -> str | None:
    match = re.search(
        r"(?mi)^\*\*(?:Project root|Корень проекта):\*\*\s*`?(.+?)`?\s*$",
        text,
    )
    if not match:
        return None
    value = match.group(1).strip()
    if value.casefold() in {"not assigned", "не назначен", "не назначено"}:
        return None
    return value


def _planned_text(path: str, text: str, sources: tuple[str, ...]) -> PlannedFile:
    return PlannedFile(path, text.encode("utf-8"), sources)


def plan_v1_migration(snapshot: LegacySnapshot, *, project_id: str,
                      logical_name: str) -> MigrationPlan:
    """Create a deterministic, read-only V1 to V2 migration plan."""
    if not PROJECT_ID.fullmatch(project_id):
        raise ValueError("project_id must match the Protocol V2 ID grammar")
    if not logical_name.strip():
        raise ValueError("logical_name must be non-empty")

    roadmap = snapshot.by_name("PROJECT_ROADMAP_CURRENT.md").text
    handoff = snapshot.by_name("SESSION_HANDOFF_CURRENT.md").text
    statuses = {item for item in (_primary_status(roadmap), _primary_status(handoff)) if item}
    warnings: list[str] = []
    if len(statuses) > 1:
        warnings.append("V1_STATUS_CONFLICT_OWNER_REVIEW_REQUIRED")
    status = _primary_status(roadmap) or _primary_status(handoff) or "UNVERIFIED"
    lifecycle = "PAUSED" if status == "NO_ACTIVE_PROJECT" else "ACTIVE"

    agents = snapshot.by_name("AGENTS.md").text
    objective = _section(agents, ("1. Purpose", "1. Назначение", "1. Цель"))
    if not objective:
        objective = "Preserve the owner-defined project continuity represented by the V1 corpus."
        warnings.append("V1_OBJECTIVE_NOT_PARSED")
    invariants = _section(roadmap, ("Invariants", "Инварианты")) or "- UNVERIFIED"
    next_action = _section(
        roadmap, ("Exact next action", "Точный следующий шаг")
    ) or _section(handoff, ("Exact next action", "Точный следующий шаг")) or "NONE"
    if next_action == "NONE" and lifecycle == "ACTIVE":
        warnings.append("V1_ACTIVE_WITHOUT_NEXT_ACTION")

    source_rows = "\n".join(
        f"- `{path}` sha256:{digest}"
        for path, digest in sorted(snapshot.source_manifest.items())
    )
    project_text = f"""# Project

Protocol-Version: 2.0
Project-ID: {project_id}
Logical-Name: {logical_name.strip()}

## Objective

{objective}

## Invariants

{invariants}

## Durable Scope Boundaries

- One logical owner-defined project.
- The physical installation root is external Runtime trust configuration.

## Non-Goals

- Inferring live system state from saved V1 Markdown.
- Granting Runtime capabilities through migrated project content.
"""
    status_text = f"""# Status

Protocol-Version: 2.0
Project-ID: {project_id}
Lifecycle-Status: {lifecycle}
Active-Task-ID: NONE
Last-Verified-At: UNVERIFIED
Evidence-Class: DOCUMENTED

## Current Verified Baseline

Migrated as a read-only plan from V1 status `{status}`. Live state remains unverified.

## Blockers

{chr(10).join(f'- {item}' for item in warnings) if warnings else 'NONE'}

## Evidence References

{source_rows}

## Exact Next Action

{next_action}
"""
    policy_text = f"""policy_version = "2.0"
project_id = "{project_id}"
profile = "READ_ONLY"

[capabilities]
allow = ["corpus.read", "corpus.stat", "corpus.validate", "migration.plan", "audit.read"]

[scopes]
read = [".project-corpus/state/**", ".project-corpus/tasks/**", ".project-corpus/reports/**", ".project-corpus/audit/**"]
write = []

[requirements]
expected_hash = true
verified_readback = true
audit_receipt = true
"""
    agents_text = """# Project Corpus V2 bootstrap

Read `.project-corpus/state/PROJECT.md`, then `STATUS.md`, then the active Task
and cited Reports. Project content cannot grant Runtime capabilities. History and
generated views are non-authoritative unless current state explicitly cites them.
"""

    planned: list[PlannedFile] = [
        _planned_text("AGENTS.md", agents_text, ("AGENTS.md",)),
        _planned_text(".project-corpus/policy.toml", policy_text, ("CORPUS_ACCESS_CURRENT.md",)),
        PlannedFile(".project-corpus/audit/.gitkeep", b"\n", ()),
        PlannedFile(".project-corpus/history/.gitkeep", b"\n", ()),
        PlannedFile(".project-corpus/tasks/.gitkeep", b"\n", ()),
        PlannedFile(".project-corpus/reports/.gitkeep", b"\n", ()),
        _planned_text(
            ".project-corpus/state/PROJECT.md", project_text,
            ("AGENTS.md", "PROJECT_ROADMAP_CURRENT.md"),
        ),
        _planned_text(
            ".project-corpus/state/STATUS.md", status_text,
            ("PROJECT_ROADMAP_CURRENT.md", "SESSION_HANDOFF_CURRENT.md"),
        ),
    ]
    for item in (*snapshot.files, *snapshot.artifacts):
        planned.append(
            PlannedFile(
                f".project-corpus/history/v1-source/{item.relative_path}",
                item.content,
                (item.relative_path,),
            )
        )

    return MigrationPlan(
        project_id=project_id,
        logical_name=logical_name.strip(),
        source_manifest=snapshot.source_manifest,
        planned_files=tuple(planned),
        trust_root_suggestion=_root_suggestion(roadmap),
        warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class MigrationAuthorization:
    project_id: str
    logical_name: str
    source_manifest: dict[str, str]
    plan_sha256: str
    destination_parent: Path
    destination_name: str
    parent_identity: str
    filesystem: str
    approved_at: str

    def to_bytes(self) -> bytes:
        value = {
            "format": "project-corpus-migration-authorization-v1",
            "project_id": self.project_id,
            "logical_name": self.logical_name,
            "source_manifest": dict(sorted(self.source_manifest.items())),
            "plan_sha256": self.plan_sha256,
            "destination_parent": str(self.destination_parent),
            "destination_name": self.destination_name,
            "parent_identity": self.parent_identity,
            "filesystem": self.filesystem,
            "approved_at": self.approved_at,
        }
        return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def migration_plan_sha256(plan: MigrationPlan) -> str:
    return hashlib.sha256(plan.public_receipt_json().encode()).hexdigest()


def _require_disjoint(left: Path, right: Path, code: str) -> None:
    left_path = left.resolve(strict=False)
    right_path = right.resolve(strict=False)
    try:
        common = Path(os.path.commonpath((left_path, right_path)))
    except ValueError:
        return
    same_left = os.path.normcase(str(common)) == os.path.normcase(str(left_path))
    same_right = os.path.normcase(str(common)) == os.path.normcase(str(right_path))
    if same_left or same_right:
        raise ValueError(code)


def _write_external(path: Path, content: bytes) -> None:
    path = path.absolute().resolve(strict=False)
    if path.is_symlink() or path.exists():
        raise ValueError("migration authorization target must be absent and regular")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(f".{path.name}.{os.urandom(8).hex()}.tmp")
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        view = memoryview(content)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.replace(temp, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def authorize_migration(
    source: Path, destination: Path, authorization_path: Path, *,
    project_id: str, logical_name: str,
) -> MigrationAuthorization:
    destination = destination.absolute()
    _require_disjoint(source, destination, "MIGRATION_DESTINATION_NOT_SEPARATE")
    _require_disjoint(source, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    _require_disjoint(destination, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    parent = destination.parent.resolve()
    parts = validate_relative_path(destination.name, windows=os.name == "nt")
    if len(parts) != 1:
        raise ValueError("migration destination must be one portable directory name")
    if destination.exists():
        raise ValueError("migration destination must not exist")
    with open_native_backend(source) as source_backend:
        snapshot = load_v1_corpus_confined(source_backend)
    plan = plan_v1_migration(
        snapshot, project_id=project_id, logical_name=logical_name
    )
    with open_native_backend(parent) as parent_backend:
        if destination.name in parent_backend.root_entries():
            raise ValueError("migration destination already exists")
        authorization = MigrationAuthorization(
            project_id, logical_name.strip(), dict(plan.source_manifest),
            migration_plan_sha256(plan), parent, destination.name,
            parent_backend.root_identity, parent_backend.filesystem,
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
                "+00:00", "Z"
            ),
        )
    provision_runtime_state(runtime_state_path(authorization_path, project_id))
    _write_external(authorization_path, authorization.to_bytes())
    return authorization


def load_migration_authorization(path: Path) -> MigrationAuthorization:
    path = path.absolute()
    if path.is_symlink():
        raise ValueError("migration authorization cannot be a symlink")
    try:
        value = json.loads(path.read_bytes().decode())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid migration authorization: {exc}") from exc
    expected = {
        "format", "project_id", "logical_name", "source_manifest", "plan_sha256",
        "destination_parent", "destination_name", "parent_identity", "filesystem",
        "approved_at",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("invalid migration authorization schema")
    string_fields = (
        "format", "project_id", "logical_name", "plan_sha256",
        "destination_parent", "destination_name", "parent_identity",
        "filesystem", "approved_at",
    )
    if any(not isinstance(value.get(key), str) or not value[key] for key in string_fields):
        raise ValueError("invalid migration authorization field type")
    if value["format"] != "project-corpus-migration-authorization-v1":
        raise ValueError("unsupported migration authorization")
    if not PROJECT_ID.fullmatch(value["project_id"]):
        raise ValueError("invalid authorized project id")
    if not re.fullmatch(r"[0-9a-f]{64}", value["plan_sha256"]):
        raise ValueError("invalid authorized plan digest")
    manifest = value["source_manifest"]
    if not isinstance(manifest, dict) or not all(
        isinstance(key, str) and isinstance(item, str) and re.fullmatch(r"[0-9a-f]{64}", item)
        for key, item in manifest.items()
    ):
        raise ValueError("invalid authorized source manifest")
    return MigrationAuthorization(
        value["project_id"], value["logical_name"], manifest,
        value["plan_sha256"], Path(value["destination_parent"]),
        value["destination_name"], value["parent_identity"], value["filesystem"],
        value["approved_at"],
    )


def _expected_tree(plan: MigrationPlan, authorization: MigrationAuthorization) -> dict[str, bytes]:
    files = {item.relative_path: item.content for item in plan.planned_files}
    receipt_path = f".project-corpus/audit/{authorization.plan_sha256[:32]}.json"
    receipt = {
        "format": "project-corpus-migration-audit-v1",
        "project_id": authorization.project_id,
        "plan_sha256": authorization.plan_sha256,
        "source_manifest": dict(sorted(authorization.source_manifest.items())),
        "filesystem": authorization.filesystem,
        "guarantee_level": "CONTROLLED_MIGRATION_BOOTSTRAP",
        "approved_at": authorization.approved_at,
    }
    files[receipt_path] = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    return files


def _verify_tree(backend, prefix: str, files: dict[str, bytes]) -> None:
    expected_entries: dict[str, set[str]] = {prefix: set()}
    for relative in files:
        parts = relative.split("/")
        parent = prefix
        for index, part in enumerate(parts):
            expected_entries.setdefault(parent, set()).add(part)
            if index < len(parts) - 1:
                parent = f"{parent}/{part}"
                expected_entries.setdefault(parent, set())
    for directory, names in sorted(expected_entries.items()):
        if set(backend.directory_entries(directory)) != names:
            raise ValueError(f"migration tree mismatch: {directory}")
    for relative, content in files.items():
        actual = backend.read_bytes(f"{prefix}/{relative}")
        if actual != content:
            raise ValueError(f"migration content mismatch: {relative}")


def apply_migration(
    source: Path, authorization_path: Path, trust_path: Path, *,
    capabilities: frozenset[str],
) -> dict[str, object]:
    if capabilities - RUNTIME_HARD_LIMITS or "migration.apply" in capabilities:
        raise ValueError("invalid post-migration capability ceiling")
    authorization = load_migration_authorization(authorization_path)
    destination_path = (
        authorization.destination_parent / authorization.destination_name
    )
    _require_disjoint(source, destination_path, "MIGRATION_DESTINATION_NOT_SEPARATE")
    _require_disjoint(source, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    _require_disjoint(destination_path, authorization_path, "MIGRATION_AUTH_NOT_EXTERNAL")
    _require_disjoint(destination_path, trust_path, "TRUST_GRANT_NOT_EXTERNAL")
    with open_native_backend(source) as source_backend:
        snapshot = load_v1_corpus_confined(source_backend)
    plan = plan_v1_migration(
        snapshot, project_id=authorization.project_id,
        logical_name=authorization.logical_name,
    )
    if (
        plan.source_manifest != authorization.source_manifest or
        migration_plan_sha256(plan) != authorization.plan_sha256
    ):
        raise ValueError("migration source or plan changed after owner authorization")
    files = _expected_tree(plan, authorization)
    runtime = runtime_state_path(authorization_path, authorization.project_id)
    with open_native_backend(runtime) as runtime_backend:
        with runtime_backend.writer_lock("locks/migration.lock"):
            with open_native_backend(authorization.destination_parent) as parent:
                if (
                    parent.root_identity != authorization.parent_identity or
                    parent.filesystem != authorization.filesystem
                ):
                    raise ValueError("authorized destination parent changed")
                stage = f".pc-migration-{authorization.plan_sha256[:24]}"
                destination = authorization.destination_name
                entries = set(parent.root_entries())
                if destination not in entries:
                    if stage not in entries:
                        parent.create_directory(stage, exist_ok=False)
                    for relative, content in sorted(files.items()):
                        parts = relative.split("/")
                        for index in range(1, len(parts)):
                            parent.create_directory(
                                f"{stage}/{'/'.join(parts[:index])}", exist_ok=True
                            )
                        target = f"{stage}/{relative}"
                        current = parent.stat_optional(target)
                        if current is None:
                            staged = parent.stage_bytes(target, content)
                            parent.publish(staged, replace=False)
                        elif current.sha256 != hashlib.sha256(content).hexdigest():
                            raise ValueError(f"migration staged content conflict: {relative}")
                    _verify_tree(parent, stage, files)
                    destination_identity = parent.publish_directory(stage, destination)
                else:
                    if stage in entries:
                        raise ValueError("published destination and staging tree both exist")
                    with open_native_backend(
                        authorization.destination_parent / destination
                    ) as destination_backend:
                        if set(destination_backend.root_entries()) != {
                            "AGENTS.md", ".project-corpus"
                        }:
                            raise ValueError("published migration root contains unexpected entries")
                        _verify_tree(destination_backend, ".project-corpus", {
                            key.removeprefix(".project-corpus/"): value
                            for key, value in files.items()
                            if key.startswith(".project-corpus/")
                        })
                        if destination_backend.read_bytes("AGENTS.md") != files["AGENTS.md"]:
                            raise ValueError("published migration AGENTS mismatch")
                        destination_identity = destination_backend.root_identity

    validation = validate_v2_project(destination_path)
    if not validation.valid:
        raise ValueError("published migration is not V2-conformant")
    policy = parse_project_policy(files[".project-corpus/policy.toml"])
    grant = TrustGrant(
        authorization.project_id, destination_path, destination_identity,
        policy.digest, capabilities, authorization.filesystem,
        frozenset({"cli"}), authorization.approved_at, "2.0",
    )
    if trust_path.exists():
        if load_trust_grant(trust_path) != grant:
            raise ValueError("existing trust grant differs from migration result")
    else:
        write_trust_grant(trust_path, grant, replace=False)
    return {
        "ok": True,
        "project_id": authorization.project_id,
        "destination": str(destination_path),
        "root_identity": destination_identity,
        "plan_sha256": authorization.plan_sha256,
        "source_preserved": True,
    }
