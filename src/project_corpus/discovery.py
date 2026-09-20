from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Iterable

from .platform import open_native_backend
from .platform.common import validate_relative_path
from .policy import parse_project_policy
from .transactions import MAX_MANAGED_BYTES, path_matches_scopes
from .validation import validate_v2_project


ARTIFACT_TYPES = ("state", "task", "report", "history")
_ARTIFACT_ROOTS = {
    "state": ".project-corpus/state",
    "task": ".project-corpus/tasks",
    "report": ".project-corpus/reports",
    "history": ".project-corpus/history",
}
_AUTHORITY_CLASSES = {
    "state": "CANONICAL_STATE",
    "task": "TASK_INTENT",
    "report": "REPORT_EVIDENCE",
    "history": "HISTORICAL_CONTEXT",
}


class DiscoveryError(ValueError):
    """A bounded, read-only discovery request could not be completed safely."""


@dataclass(frozen=True)
class Artifact:
    path: str
    type: str
    authority_class: str
    content: str


def _require_conformant_root(root: Path) -> None:
    result = validate_v2_project(root)
    if not result.valid:
        codes = sorted({item.code for item in result.issues if item.severity == "ERROR"})
        raise DiscoveryError(f"project is not V2-conformant: {codes}")


def _artifact_paths(backend, read_scopes: tuple[str, ...], types: Iterable[str]) -> tuple[tuple[str, str], ...]:
    selected: list[tuple[str, str]] = []
    for artifact_type in types:
        for path in backend.walk_files(_ARTIFACT_ROOTS[artifact_type]):
            if path.endswith(".md") and path_matches_scopes(path, read_scopes):
                selected.append((path, artifact_type))
    return tuple(sorted(selected))


def _load_artifacts(root: Path, types: tuple[str, ...]) -> tuple[Artifact, ...]:
    _require_conformant_root(root)
    with open_native_backend(root) as backend:
        policy = parse_project_policy(
            backend.read_bytes(".project-corpus/policy.toml", max_bytes=1024 * 1024)
        )
        artifacts = []
        for path, artifact_type in _artifact_paths(backend, policy.read_scopes, types):
            try:
                content = backend.read_bytes(path, max_bytes=MAX_MANAGED_BYTES).decode("utf-8")
            except UnicodeDecodeError as exc:
                raise DiscoveryError(f"artifact is not UTF-8: {path}") from exc
            artifacts.append(Artifact(path, artifact_type, _AUTHORITY_CLASSES[artifact_type], content))
    return tuple(artifacts)


def _artifact_type_for_path(path: str) -> str:
    if not path.endswith(".md"):
        raise DiscoveryError("artifact must be a Markdown file")
    for artifact_type, directory in _ARTIFACT_ROOTS.items():
        if path.startswith(directory + "/"):
            return artifact_type
    raise DiscoveryError("artifact is outside discovery roots")


def show(root: Path | str, artifact: str) -> dict[str, object]:
    """Read one policy-scoped corpus artifact by a portable relative path."""
    if not isinstance(artifact, str):
        raise DiscoveryError("artifact path must be a string")
    try:
        validate_relative_path(artifact, windows=os.name == "nt")
    except ValueError as exc:
        raise DiscoveryError(str(exc)) from exc
    artifact_type = _artifact_type_for_path(artifact)
    root_path = Path(root)
    _require_conformant_root(root_path)
    with open_native_backend(root_path) as backend:
        policy = parse_project_policy(
            backend.read_bytes(".project-corpus/policy.toml", max_bytes=1024 * 1024)
        )
        if not path_matches_scopes(artifact, policy.read_scopes):
            raise DiscoveryError(f"read scope denied: {artifact}")
        try:
            content = backend.read_bytes(artifact, max_bytes=MAX_MANAGED_BYTES).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DiscoveryError(f"artifact is not UTF-8: {artifact}") from exc
    return {
        "path": artifact,
        "type": artifact_type,
        "authority_class": _AUTHORITY_CLASSES[artifact_type],
        "content": content,
    }


def _title(lines: list[str], index: int) -> str:
    for line in reversed(lines[: index + 1]):
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return Path("untitled").stem


def _snippet(line: str, query: str, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", line).strip()
    if len(compact) <= limit:
        return compact
    match = re.search(re.escape(query), compact, flags=re.IGNORECASE)
    if match is None:
        return compact[: limit - 1] + "…"
    body_limit = limit - 2
    start = max(0, match.start() - body_limit // 2)
    end = min(len(compact), start + body_limit)
    start = max(0, end - body_limit)
    prefix = "…" if start else ""
    suffix = "…" if end < len(compact) else ""
    return prefix + compact[start:end] + suffix


def search(root: Path | str, query: str, *, artifact_type: str | None = None, limit: int = 20) -> dict[str, object]:
    """Return a deterministic, non-authoritative local full-text view."""
    if not isinstance(query, str) or not query.strip():
        raise DiscoveryError("query must be non-empty")
    if artifact_type is not None and artifact_type not in ARTIFACT_TYPES:
        raise DiscoveryError(f"unknown artifact type: {artifact_type}")
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise DiscoveryError("limit must be between 1 and 100")
    needle = query.casefold()
    types = (artifact_type,) if artifact_type else ARTIFACT_TYPES
    matches: list[dict[str, object]] = []
    for artifact in _load_artifacts(Path(root), types):
        lines = artifact.content.splitlines()
        for index, line in enumerate(lines):
            score = line.casefold().count(needle)
            if score:
                matches.append({
                    "path": artifact.path,
                    "type": artifact.type,
                    "authority_class": artifact.authority_class,
                    "title": _title(lines, index),
                    "snippet": _snippet(line, query),
                    "line_start": index + 1,
                    "line_end": index + 1,
                    "score": score,
                })
    matches.sort(key=lambda item: (-int(item["score"]), str(item["path"]), int(item["line_start"])))
    return {
        "non_authoritative": True,
        "query": query,
        "results": matches[:limit],
    }


def _timestamp(content: str) -> tuple[str | None, str]:
    for key in ("Created-At", "Created", "Last-Verified-At", "Date"):
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(\S.*?)\s*$", content)
        if match:
            return match.group(1), key
    return None, "unknown"


def timeline(root: Path | str, selector: str) -> dict[str, object]:
    """Return ordered corpus references using only timestamps written in artifacts."""
    if not isinstance(selector, str) or not selector.strip():
        raise DiscoveryError("selector must be non-empty")
    artifacts = _load_artifacts(Path(root), ARTIFACT_TYPES)
    needle = selector.casefold()
    events = []
    for artifact in artifacts:
        if needle not in artifact.path.casefold() and needle not in artifact.content.casefold():
            continue
        timestamp, source = _timestamp(artifact.content)
        lines = artifact.content.splitlines()
        events.append({
            "path": artifact.path,
            "type": artifact.type,
            "authority_class": artifact.authority_class,
            "title": _title(lines, 0),
            "timestamp": timestamp,
            "timestamp_source": source,
        })
    events.sort(key=lambda event: (event["timestamp"] is None, event["timestamp"] or "", event["path"]))
    return {"non_authoritative": True, "selector": selector, "events": events}
