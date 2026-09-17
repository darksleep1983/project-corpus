from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePath
import re
import sys
import tomllib


class TrustError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class TrustGrant:
    project_id: str
    physical_root: Path
    root_identity: str
    policy_sha256: str
    capability_ceiling: frozenset[str]
    filesystem: str
    transports: frozenset[str]
    approved_at: str
    protocol_version: str


def default_trust_directory(env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    if sys.platform == "win32":
        base = values.get("LOCALAPPDATA")
        if not base:
            raise TrustError("TRUST_CONFIG_HOME", "LOCALAPPDATA is unavailable")
        return Path(base) / "ProjectCorpus" / "trust"
    if sys.platform == "darwin":
        home = values.get("HOME", str(Path.home()))
        return Path(home) / "Library" / "Application Support" / "ProjectCorpus" / "trust"
    base = values.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / "project-corpus" / "trust"
    home = values.get("HOME", str(Path.home()))
    return Path(home) / ".config" / "project-corpus" / "trust"


def grant_path(project_id: str, trust_directory: Path | None = None) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", project_id):
        raise TrustError("TRUST_PROJECT_ID", "invalid project id")
    return (trust_directory or default_trust_directory()) / f"{project_id}.toml"


def runtime_state_path(trust_grant_path: Path, project_id: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", project_id):
        raise TrustError("TRUST_PROJECT_ID", "invalid project id")
    return trust_grant_path.absolute().parent / "runtime" / project_id


def serialize_trust_grant(grant: TrustGrant) -> bytes:
    def quoted(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)

    capabilities = ", ".join(quoted(item) for item in sorted(grant.capability_ceiling))
    transports = ", ".join(quoted(item) for item in sorted(grant.transports))
    text = f'''grant_version = "1"
project_id = {quoted(grant.project_id)}
physical_root = {quoted(str(grant.physical_root))}
root_identity = {quoted(grant.root_identity)}
policy_sha256 = {quoted(grant.policy_sha256)}
capability_ceiling = [{capabilities}]
filesystem = {quoted(grant.filesystem)}
transports = [{transports}]
approved_at = {quoted(grant.approved_at)}
protocol_version = {quoted(grant.protocol_version)}
'''
    return text.encode("utf-8")


def _reject_symlink_ancestors(path: Path) -> None:
    candidate = path.absolute()
    existing: list[Path] = []
    while True:
        existing.append(candidate)
        if candidate.parent == candidate:
            break
        candidate = candidate.parent
    for item in reversed(existing):
        if item.exists() and item.is_symlink():
            raise TrustError("TRUST_SYMLINK", str(item))


def write_trust_grant(path: Path, grant: TrustGrant, *, replace: bool = False) -> None:
    path = path.absolute()
    _reject_symlink_ancestors(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() and not replace:
        raise TrustError("TRUST_EXISTS", str(path))
    if path.is_symlink():
        raise TrustError("TRUST_SYMLINK", str(path))
    temp = path.with_name(f".{path.name}.{os.urandom(8).hex()}.tmp")
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        content = serialize_trust_grant(grant)
        view = memoryview(content)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        staged = load_trust_grant(temp)
        if staged != grant:
            raise TrustError("TRUST_VERIFY", str(temp))
        os.replace(temp, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        loaded = load_trust_grant(path)
        if loaded != grant:
            raise TrustError("TRUST_VERIFY", str(path))
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def provision_runtime_state(path: Path) -> None:
    path = path.absolute()
    _reject_symlink_ancestors(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise TrustError("RUNTIME_STATE_ROOT", str(path))
    for name in ("journal", "backups", "locks"):
        directory = path / name
        _reject_symlink_ancestors(directory)
        directory.mkdir(exist_ok=True, mode=0o700)
        marker = directory / ".keep"
        if marker.is_symlink() or (marker.exists() and not marker.is_file()):
            raise TrustError("RUNTIME_STATE_MARKER", str(marker))
        if not marker.exists():
            descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(descriptor, b"\n")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


def load_trust_grant(path: Path) -> TrustGrant:
    path = path.absolute()
    _reject_symlink_ancestors(path)
    if path.is_symlink():
        raise TrustError("TRUST_SYMLINK", str(path))
    try:
        data = tomllib.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise TrustError("TRUST_LOAD", str(exc)) from exc
    expected = {
        "grant_version", "project_id", "physical_root", "root_identity",
        "policy_sha256", "capability_ceiling", "filesystem", "transports",
        "approved_at", "protocol_version",
    }
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown or missing:
        raise TrustError(
            "TRUST_SCHEMA", f"unknown={sorted(unknown)} missing={sorted(missing)}"
        )
    if data["grant_version"] != "1":
        raise TrustError("TRUST_VERSION", str(data["grant_version"]))
    project_id = data["project_id"]
    if not isinstance(project_id, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9._-]{2,63}", project_id
    ):
        raise TrustError("TRUST_PROJECT_ID", "invalid project id")
    root_value = data["physical_root"]
    if not isinstance(root_value, str):
        raise TrustError("TRUST_ROOT", "physical_root must be a string")
    is_absolute = PurePath(root_value).is_absolute()
    if sys.platform == "win32":
        is_absolute = bool(re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", root_value))
    if not is_absolute:
        raise TrustError("TRUST_ROOT", "physical_root must be absolute")
    for key in (
        "root_identity", "policy_sha256", "filesystem", "approved_at",
        "protocol_version",
    ):
        if not isinstance(data[key], str) or not data[key]:
            raise TrustError("TRUST_SCHEMA", f"{key} must be a non-empty string")
    if not re.fullmatch(r"[0-9a-f]{64}", data["policy_sha256"]):
        raise TrustError("TRUST_POLICY_DIGEST", "expected lowercase SHA-256")
    for key in ("capability_ceiling", "transports"):
        value = data[key]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise TrustError("TRUST_SCHEMA", f"{key} must be an array of strings")
        if len(set(value)) != len(value):
            raise TrustError("TRUST_SCHEMA", f"{key} contains duplicates")
    return TrustGrant(
        project_id=project_id,
        physical_root=Path(root_value),
        root_identity=data["root_identity"],
        policy_sha256=data["policy_sha256"],
        capability_ceiling=frozenset(data["capability_ceiling"]),
        filesystem=data["filesystem"],
        transports=frozenset(data["transports"]),
        approved_at=data["approved_at"],
        protocol_version=data["protocol_version"],
    )
