from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import tomllib


class PolicyError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
PROFILES = {"READ_ONLY", "SAFE_EDIT", "MAINTAINER"}
PROFILE_CAPABILITIES = {
    "READ_ONLY": frozenset({
        "corpus.read", "corpus.stat", "corpus.validate", "migration.plan",
        "audit.read", "git.status", "git.diff",
    }),
    "SAFE_EDIT": frozenset({
        "corpus.read", "corpus.stat", "corpus.validate", "migration.plan",
        "state.update", "task.create", "report.create", "audit.read",
        "git.status", "git.diff", "mcp.stdio",
    }),
    "MAINTAINER": frozenset({
        "corpus.read", "corpus.stat", "corpus.validate", "migration.plan",
        "migration.apply", "state.update", "task.create", "report.create",
        "audit.read", "mcp.stdio", "git.status", "git.diff",
    }),
}
TOP_KEYS = {
    "policy_version", "project_id", "profile", "capabilities", "scopes",
    "requirements",
}


@dataclass(frozen=True)
class ProjectPolicy:
    project_id: str
    profile: str
    capabilities: frozenset[str]
    read_scopes: tuple[str, ...]
    write_scopes: tuple[str, ...]
    expected_hash: bool
    verified_readback: bool
    audit_receipt: bool
    digest: str


def _table(data: dict[str, object], name: str, allowed: set[str]) -> dict[str, object]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise PolicyError("POLICY_SCHEMA", f"{name} must be a table")
    unknown = set(value) - allowed
    if unknown:
        raise PolicyError("POLICY_UNKNOWN_KEY", f"{name}: {sorted(unknown)}")
    return value


def _strings(table: dict[str, object], key: str) -> tuple[str, ...]:
    value = table.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PolicyError("POLICY_SCHEMA", f"{key} must be an array of strings")
    if len(set(value)) != len(value):
        raise PolicyError("POLICY_SCHEMA", f"{key} contains duplicates")
    return tuple(value)


def _validate_scope(value: str) -> None:
    if not value or value != value.strip():
        raise PolicyError("POLICY_SCOPE", "scope must be non-empty and trimmed")
    if "\\" in value or ":" in value or value.startswith("/"):
        raise PolicyError("POLICY_SCOPE", f"non-portable scope: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PolicyError("POLICY_SCOPE", f"traversal or empty component: {value!r}")


def parse_project_policy(content: bytes) -> ProjectPolicy:
    try:
        data = tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise PolicyError("POLICY_PARSE", str(exc)) from exc
    unknown = set(data) - TOP_KEYS
    if unknown:
        raise PolicyError("POLICY_UNKNOWN_KEY", str(sorted(unknown)))
    if data.get("policy_version") != "2.0":
        raise PolicyError("POLICY_VERSION", "expected 2.0")
    project_id = data.get("project_id")
    if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id):
        raise PolicyError("POLICY_PROJECT_ID", "invalid project_id")
    profile = data.get("profile")
    if profile not in PROFILES:
        raise PolicyError("POLICY_PROFILE", str(profile))

    capabilities = _table(data, "capabilities", {"allow"})
    allowed = _strings(capabilities, "allow")
    if any(not re.fullmatch(r"[a-z][a-z0-9_.-]*", item) for item in allowed):
        raise PolicyError("POLICY_CAPABILITY", "invalid capability name")
    outside_profile = set(allowed) - PROFILE_CAPABILITIES[profile]
    if outside_profile:
        raise PolicyError(
            "POLICY_PROFILE_CAPABILITY", f"{profile}: {sorted(outside_profile)}"
        )
    scopes = _table(data, "scopes", {"read", "write"})
    read_scopes = _strings(scopes, "read")
    write_scopes = _strings(scopes, "write")
    for item in (*read_scopes, *write_scopes):
        _validate_scope(item)
    requirements = _table(
        data, "requirements", {"expected_hash", "verified_readback", "audit_receipt"}
    )
    values: list[bool] = []
    for key in ("expected_hash", "verified_readback", "audit_receipt"):
        value = requirements.get(key)
        if not isinstance(value, bool):
            raise PolicyError("POLICY_SCHEMA", f"{key} must be boolean")
        values.append(value)
    if write_scopes and not all(values):
        raise PolicyError(
            "POLICY_WRITE_REQUIREMENTS",
            "write scopes require expected hash, readback and audit",
        )
    return ProjectPolicy(
        project_id=project_id,
        profile=profile,
        capabilities=frozenset(allowed),
        read_scopes=read_scopes,
        write_scopes=write_scopes,
        expected_hash=values[0],
        verified_readback=values[1],
        audit_receipt=values[2],
        digest=hashlib.sha256(content).hexdigest(),
    )
