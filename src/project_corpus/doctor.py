from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .compatibility import LegacyCorpusError, load_v1_corpus
from .platform import BackendError, open_native_backend
from .trust import TrustError, load_trust_grant
from .validation import ValidationIssue, validate_v2_project


@dataclass(frozen=True)
class DoctorCheck:
    code: str
    status: str
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    project_format: str
    project_id: str | None
    guarantee_level: str
    checks: tuple[DoctorCheck, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"


def _check_from_issue(issue: ValidationIssue) -> DoctorCheck:
    return DoctorCheck(issue.code, "FAIL" if issue.severity == "ERROR" else "WARN", f"{issue.path}: {issue.detail}")


def doctor(root: Path, *, trust_grant_path: Path | None = None) -> DoctorReport:
    """Read-only diagnosis. This function never upgrades to controlled mode."""
    root = root.absolute()
    v2_marker = root / ".project-corpus" / "state" / "PROJECT.md"
    if v2_marker.exists():
        validation = validate_v2_project(root)
        checks = [_check_from_issue(item) for item in validation.issues]
        if validation.valid:
            checks.append(DoctorCheck("PROTOCOL_V2", "PASS", "required state and policy conform"))
        if trust_grant_path is None:
            checks.append(DoctorCheck(
                "OWNER_TRUST_NOT_EVALUATED", "WARN",
                "direct-folder validation has no external trust grant",
            ))
        else:
            try:
                trust = load_trust_grant(trust_grant_path)
                if validation.project_id != trust.project_id:
                    checks.append(DoctorCheck("PROJECT_ID_MISMATCH", "FAIL", "trust grant differs"))
                if validation.policy and validation.policy.digest != trust.policy_sha256:
                    checks.append(DoctorCheck("POLICY_DRIFT", "FAIL", "owner approval required"))
                if trust.physical_root != root:
                    checks.append(DoctorCheck("TRUST_ROOT_PATH_MISMATCH", "FAIL", "configured root differs"))
                else:
                    try:
                        with open_native_backend(root) as backend:
                            if backend.root_identity != trust.root_identity:
                                checks.append(DoctorCheck(
                                    "ROOT_IDENTITY_MISMATCH", "FAIL",
                                    "external grant differs from opened root identity",
                                ))
                            else:
                                checks.append(DoctorCheck(
                                    "ROOT_IDENTITY", "PASS", backend.root_identity,
                                ))
                            if backend.filesystem != trust.filesystem:
                                checks.append(DoctorCheck(
                                    "FILESYSTEM_MISMATCH", "FAIL",
                                    f"grant={trust.filesystem} observed={backend.filesystem}",
                                ))
                            else:
                                checks.append(DoctorCheck(
                                    "FILESYSTEM_QUALIFIED", "PASS", backend.filesystem,
                                ))
                    except BackendError as exc:
                        checks.append(DoctorCheck(exc.code, "FAIL", exc.detail))
            except TrustError as exc:
                checks.append(DoctorCheck(exc.code, "FAIL", exc.detail))
        ok = not any(item.status == "FAIL" for item in checks)
        return DoctorReport(
            ok, "V2", validation.project_id,
            "DIRECT_FOLDER_OBSERVABLE" if ok else "DIAGNOSTIC_ONLY",
            tuple(checks),
        )

    try:
        snapshot = load_v1_corpus(root)
    except LegacyCorpusError as exc:
        return DoctorReport(
            False, "UNKNOWN", None, "DIAGNOSTIC_ONLY",
            (DoctorCheck(exc.code, "FAIL", exc.detail),),
        )
    return DoctorReport(
        True, "V1", None, "MARKDOWN_COMPATIBLE",
        (
            DoctorCheck("V1_COMPATIBILITY", "PASS", "all seven current files read"),
            DoctorCheck(
                "V1_SOURCE_MANIFEST", "PASS",
                f"{len(snapshot.source_manifest)} files hashed without mutation",
            ),
        ),
    )
