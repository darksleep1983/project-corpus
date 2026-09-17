from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .policy import PolicyError, ProjectPolicy, parse_project_policy


PROJECT_METADATA = ("Protocol-Version", "Project-ID", "Logical-Name")
STATUS_METADATA = (
    "Protocol-Version", "Project-ID", "Lifecycle-Status", "Active-Task-ID",
    "Last-Verified-At", "Evidence-Class",
)
PROJECT_SECTIONS = (
    "Objective", "Invariants", "Durable Scope Boundaries", "Non-Goals",
)
STATUS_SECTIONS = (
    "Current Verified Baseline", "Blockers", "Evidence References",
    "Exact Next Action",
)
PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    path: str
    detail: str


@dataclass(frozen=True)
class ParsedDocument:
    metadata: dict[str, str]
    sections: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class ProjectValidation:
    issues: tuple[ValidationIssue, ...]
    project_id: str | None
    policy: ProjectPolicy | None

    @property
    def valid(self) -> bool:
        return not any(item.severity == "ERROR" for item in self.issues)


def parse_document(content: bytes, path: str) -> ParsedDocument:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path} is not UTF-8: {exc}") from exc
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("## "):
            break
        match = re.match(r"^([A-Za-z][A-Za-z0-9-]*):\s*(\S.*)$", line)
        if match:
            key = match.group(1)
            if key in metadata:
                metadata[f"__duplicate__{key}"] = match.group(2)
            else:
                metadata[key] = match.group(2)
    sections = tuple(re.findall(r"^## ([^\r\n]+)\r?$", text, re.MULTILINE))
    return ParsedDocument(metadata, sections, text)


def _document_issues(
    document: ParsedDocument,
    *,
    path: str,
    required_metadata: tuple[str, ...],
    required_sections: tuple[str, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key in required_metadata:
        if key not in document.metadata:
            issues.append(ValidationIssue("MISSING_METADATA", "ERROR", path, key))
    if any(key.startswith("__duplicate__") for key in document.metadata):
        issues.append(ValidationIssue("INVALID_METADATA", "ERROR", path, "duplicate key"))
    for section in required_sections:
        count = document.sections.count(section)
        if count == 0:
            issues.append(ValidationIssue("MISSING_SECTION", "ERROR", path, section))
        elif count > 1:
            issues.append(ValidationIssue("DUPLICATE_SECTION", "ERROR", path, section))
    filtered = tuple(item for item in document.sections if item in required_sections)
    if all(document.sections.count(item) == 1 for item in required_sections):
        if filtered != required_sections:
            issues.append(ValidationIssue("SECTION_ORDER", "ERROR", path, str(filtered)))
    return issues


def validate_state_pair(project_content: bytes, status_content: bytes) -> tuple[ValidationIssue, ...]:
    project_path = ".project-corpus/state/PROJECT.md"
    status_path = ".project-corpus/state/STATUS.md"
    try:
        project = parse_document(project_content, project_path)
        status = parse_document(status_content, status_path)
    except ValueError as exc:
        return (ValidationIssue("INVALID_ENCODING", "ERROR", "state", str(exc)),)
    issues = _document_issues(
        project, path=project_path, required_metadata=PROJECT_METADATA,
        required_sections=PROJECT_SECTIONS,
    )
    issues.extend(_document_issues(
        status, path=status_path, required_metadata=STATUS_METADATA,
        required_sections=STATUS_SECTIONS,
    ))
    if project.metadata.get("Project-ID") != status.metadata.get("Project-ID"):
        issues.append(ValidationIssue(
            "PROJECT_ID_MISMATCH", "ERROR", "state", "PROJECT and STATUS differ"
        ))
    for path, value in (
        (project_path, project.metadata.get("Project-ID")),
        (status_path, status.metadata.get("Project-ID")),
    ):
        if value is not None and not PROJECT_ID.fullmatch(value):
            issues.append(ValidationIssue("INVALID_METADATA", "ERROR", path, "Project-ID"))
    for path, document in ((project_path, project), (status_path, status)):
        if document.metadata.get("Protocol-Version") != "2.0":
            issues.append(ValidationIssue("INVALID_METADATA", "ERROR", path, "Protocol-Version"))
    if any(item in status.sections for item in PROJECT_SECTIONS):
        issues.append(ValidationIssue("ROLE_OVERLAP", "ERROR", status_path, "stable section"))
    if any(item in project.sections for item in STATUS_SECTIONS):
        issues.append(ValidationIssue("ROLE_OVERLAP", "ERROR", project_path, "operational section"))
    root_field = re.compile(
        r"(?im)^(?:Filesystem-Root|Project-Root|Physical-Root):\s*"
        r"(?:[A-Za-z]:[\\/]|\\\\|/)"
    )
    if root_field.search(project.text):
        issues.append(ValidationIssue(
            "PROJECT_ABSOLUTE_ROOT", "ERROR", project_path, "physical root is not portable authority"
        ))
    lifecycle = status.metadata.get("Lifecycle-Status")
    if lifecycle not in {"ACTIVE", "PAUSED", "BLOCKED", "COMPLETE"}:
        issues.append(ValidationIssue("INVALID_METADATA", "ERROR", status_path, "Lifecycle-Status"))
    if status.metadata.get("Evidence-Class") not in {
        "OBSERVED", "DOCUMENTED", "INFERRED", "UNVERIFIED",
    }:
        issues.append(ValidationIssue("INVALID_METADATA", "ERROR", status_path, "Evidence-Class"))
    if lifecycle == "ACTIVE":
        match = re.search(
            r"(?ms)^## Exact Next Action\s*\n+(.+?)(?=^## |\Z)", status.text
        )
        if not match or match.group(1).strip() == "NONE":
            issues.append(ValidationIssue(
                "INVALID_METADATA", "ERROR", status_path, "ACTIVE requires next action"
            ))
    unique = {(item.code, item.severity, item.path, item.detail): item for item in issues}
    return tuple(sorted(unique.values(), key=lambda item: (item.code, item.path, item.detail)))


def validate_v2_project(root: Path) -> ProjectValidation:
    required_files = (
        "AGENTS.md", ".project-corpus/policy.toml",
        ".project-corpus/state/PROJECT.md", ".project-corpus/state/STATUS.md",
    )
    required_dirs = (
        ".project-corpus/tasks", ".project-corpus/reports", ".project-corpus/history",
    )
    issues: list[ValidationIssue] = []
    for relative in required_files:
        path = root / relative
        if not path.is_file():
            issues.append(ValidationIssue("MISSING_REQUIRED_PATH", "ERROR", relative, "file"))
        elif path.is_symlink():
            issues.append(ValidationIssue("REQUIRED_PATH_LINK", "ERROR", relative, "symlink"))
    for relative in required_dirs:
        path = root / relative
        if not path.is_dir():
            issues.append(ValidationIssue("MISSING_REQUIRED_PATH", "ERROR", relative, "directory"))
        elif path.is_symlink():
            issues.append(ValidationIssue("REQUIRED_PATH_LINK", "ERROR", relative, "symlink"))
    if any(item.code == "MISSING_REQUIRED_PATH" for item in issues):
        return ProjectValidation(tuple(issues), None, None)

    project_path = root / ".project-corpus" / "state" / "PROJECT.md"
    status_path = root / ".project-corpus" / "state" / "STATUS.md"
    issues.extend(validate_state_pair(project_path.read_bytes(), status_path.read_bytes()))
    project_id: str | None = None
    try:
        project_id = parse_document(project_path.read_bytes(), str(project_path)).metadata.get("Project-ID")
    except ValueError:
        pass
    policy: ProjectPolicy | None = None
    policy_path = root / ".project-corpus" / "policy.toml"
    try:
        policy = parse_project_policy(policy_path.read_bytes())
        if project_id is not None and policy.project_id != project_id:
            issues.append(ValidationIssue(
                "PROJECT_ID_MISMATCH", "ERROR", ".project-corpus/policy.toml",
                "policy differs from PROJECT",
            ))
    except PolicyError as exc:
        issues.append(ValidationIssue(exc.code, "ERROR", ".project-corpus/policy.toml", exc.detail))
    generated = root / ".project-corpus" / "generated"
    if generated.is_dir():
        for path in sorted(generated.glob("*.md")):
            try:
                prefix = path.read_text(encoding="utf-8")[:512]
            except UnicodeDecodeError:
                prefix = ""
            if "NON_AUTHORITATIVE_VIEW" not in prefix:
                issues.append(ValidationIssue(
                    "GENERATED_VIEW_UNMARKED", "ERROR",
                    path.relative_to(root).as_posix(), "missing marker",
                ))
    return ProjectValidation(tuple(issues), project_id, policy)
