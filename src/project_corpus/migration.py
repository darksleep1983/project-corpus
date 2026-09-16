from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .compatibility import LegacySnapshot


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
read = [".project-corpus/state/**", ".project-corpus/tasks/**", ".project-corpus/reports/**"]
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
