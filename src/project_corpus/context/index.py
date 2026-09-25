from __future__ import annotations

from dataclasses import dataclass
from contextlib import closing
import hashlib
import os
from pathlib import Path
import re
import sqlite3
from typing import Callable

from ..discovery import ARTIFACT_TYPES, Artifact, _AUTHORITY_CLASSES, _artifact_paths, _require_conformant_root
from ..platform import open_native_backend
from ..platform.base import NativePathBackend
from ..platform.base import BackendError
from ..platform.common import validate_relative_path
from ..policy import ProjectPolicy, parse_project_policy
from ..transactions import MAX_MANAGED_BYTES
from .schema import ContextError, INDEX_SCHEMA_VERSION, MAX_INDEX_BYTES, MAX_ITEMS, MAX_SOURCES, MAX_TOTAL_SOURCE_BYTES, digest

ROOTS = (".project-corpus/state/", ".project-corpus/tasks/", ".project-corpus/reports/", ".project-corpus/history/")
RELATION = re.compile(r"(?m)^Supersedes:\s*(\S+)\s*$")
TIMESTAMP = re.compile(r"(?m)^(?:Created-At|Created|Last-Verified-At|Date):\s*(\S+)\s*$")
ACTIVE = re.compile(r"(?m)^Active-Task-ID:\s*(\S+)\s*$")
REPORT_REF = re.compile(r"\.project-corpus/reports/[a-z0-9][a-z0-9._-]*\.md")


@dataclass(frozen=True)
class Source:
    path: str
    source_type: str
    authority_class: str
    sha256: str
    timestamp: str | None
    temporal_status: str
    content: str


@dataclass(frozen=True)
class IndexedCorpus:
    project_id: str
    sources: tuple[Source, ...]
    items: tuple[dict[str, object], ...]
    relations: tuple[tuple[str, str], ...]
    index_schema_version: str = INDEX_SCHEMA_VERSION

    @property
    def snapshot(self) -> dict[str, str]:
        return {source.path: source.sha256 for source in self.sources}


def _valid_ref(path: str) -> bool:
    try:
        validate_relative_path(path, windows=os.name == "nt")
    except ValueError:
        return False
    return path.startswith(ROOTS) and path.endswith(".md")


def valid_relation(source: str, target: str, active_path: str | None) -> bool:
    return (
        _valid_ref(target) and source.startswith(ROOTS[1:]) and
        not target.startswith(ROOTS[0]) and target != active_path and source != target
    )


def cyclic_relations(relations: tuple[tuple[str, str], ...], paths: set[str], active_path: str | None) -> set[tuple[str, str]]:
    edges = {(source, target) for source, target in relations if target in paths and valid_relation(source, target, active_path)}
    adjacency: dict[str, list[str]] = {}
    for source, target in sorted(edges):
        adjacency.setdefault(source, []).append(target)
    cyclic: set[tuple[str, str]] = set()
    for source, target in sorted(edges):
        stack = [target]
        seen: set[str] = set()
        while stack:
            node = stack.pop()
            if node == source:
                cyclic.add((source, target))
                break
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adjacency.get(node, ()))
    return cyclic


def _project_id(artifacts) -> str:
    project = next((a for a in artifacts if a.path == ".project-corpus/state/PROJECT.md"), None)
    if project is None:
        raise ContextError("CONTEXT_SCOPE", "policy must permit canonical PROJECT.md")
    match = re.search(r"(?m)^Project-ID:\s*(\S+)\s*$", project.content)
    if not match:
        raise ContextError("CONTEXT_PROJECT_ID", "PROJECT.md has no Project-ID")
    return match.group(1)


def collect(root: Path | str, *, authorize: Callable[[ProjectPolicy, NativePathBackend], None] | None = None) -> IndexedCorpus:
    root = Path(root)
    _require_conformant_root(root)
    with open_native_backend(root) as backend:
        policy = parse_project_policy(backend.read_bytes(".project-corpus/policy.toml", max_bytes=1024 * 1024))
        if authorize is not None:
            authorize(policy, backend)
        paths = _artifact_paths(backend, policy.read_scopes, ARTIFACT_TYPES)
        if len(paths) > MAX_SOURCES:
            raise ContextError("CONTEXT_LIMIT", "too many scoped sources")
        loaded = []
        total = 0
        for path, source_type in paths:
            raw = backend.read_bytes(path, max_bytes=MAX_MANAGED_BYTES)
            total += len(raw)
            if total > MAX_TOTAL_SOURCE_BYTES:
                raise ContextError("CONTEXT_LIMIT", "scoped sources exceed 64 MiB")
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ContextError("SOURCE_ENCODING", path) from exc
            loaded.append(Artifact(path, source_type, _AUTHORITY_CLASSES[source_type], content))
        artifacts = tuple(loaded)
    project_id = _project_id(artifacts)
    status = next((a for a in artifacts if a.path == ".project-corpus/state/STATUS.md"), None)
    if status is None:
        raise ContextError("CONTEXT_SCOPE", "policy must permit canonical STATUS.md")
    active_match = ACTIVE.search(status.content)
    active = active_match.group(1) if active_match else "NONE"
    active_path = f".project-corpus/tasks/{active}.md" if active != "NONE" else None
    active_doc = next((a for a in artifacts if a.path == active_path), None)
    cited = set(REPORT_REF.findall(status.content))
    if active_doc:
        cited.update(REPORT_REF.findall(active_doc.content))
    paths = {a.path for a in artifacts}
    relations = tuple(sorted((a.path, m.group(1)) for a in artifacts for m in RELATION.finditer(a.content)))
    cycles = cyclic_relations(relations, paths, active_path)
    superseded = {target for source, target in relations if target in paths and valid_relation(source, target, active_path) and (source, target) not in cycles}
    sources: list[Source] = []
    items: list[dict[str, object]] = []
    for artifact in artifacts:
        path = artifact.path
        if path in superseded:
            temporal = "superseded"
        elif path in (".project-corpus/state/PROJECT.md", ".project-corpus/state/STATUS.md", active_path):
            temporal = "current"
        elif artifact.type == "history":
            temporal = "historical"
        elif artifact.type == "task":
            temporal = "historical"
        elif artifact.type == "report":
            status_time = TIMESTAMP.search(status.content)
            report_time = TIMESTAMP.search(artifact.content)
            temporal = "historical" if path not in cited and status_time and report_time and report_time.group(1)[:10] < status_time.group(1)[:10] else "scoped"
        else:
            temporal = "unknown"
        if path.endswith("/PROJECT.md") or path.endswith("/STATUS.md"):
            authority = "CANONICAL"
        elif path == active_path:
            authority = "ACTIVE_TASK"
        elif path in cited:
            authority = "CITED_REPORT"
        elif artifact.type == "report":
            authority = "SCOPED_REPORT"
        elif artifact.type == "history":
            authority = "HISTORY"
        else:
            authority = "OTHER_TASK"
        sha = hashlib.sha256(artifact.content.encode("utf-8")).hexdigest()
        match = TIMESTAMP.search(artifact.content)
        timestamp = match.group(1) if match else None
        sources.append(Source(path, artifact.type, authority, sha, timestamp, temporal, artifact.content))
        section = ""
        section_line = 0
        for number, line in enumerate(artifact.content.splitlines(), 1):
            if line.startswith("#"):
                section = line.lstrip("#").strip()
                section_line = number
            if not line.strip():
                continue
            excerpt = line.strip()[:1200]
            item_id = hashlib.sha256(f"{path}\0{number}\0{excerpt}".encode()).hexdigest()[:20]
            items.append({
                "item_id": item_id, "project_id": project_id, "text": excerpt,
                "source_path": path, "source_sha256": sha, "source_type": artifact.type,
                "authority_class": authority, "temporal_status": temporal,
                "timestamp": timestamp, "section": section, "section_line": section_line, "line_start": number,
                "line_end": number, "non_authoritative": True,
            })
            if len(items) > MAX_ITEMS:
                raise ContextError("CONTEXT_LIMIT", "too many indexed lines")
    return IndexedCorpus(project_id, tuple(sources), tuple(items), relations)


def _index_path(root: Path | str, index: Path | str, *, create: bool) -> Path:
    root_path = Path(root).absolute()
    cache = root_path / ".project-corpus" / "cache"
    given = Path(index)
    if ".." in given.parts:
        raise ContextError("INDEX_PATH", "traversal is forbidden")
    path = given.absolute()
    try:
        validate_relative_path(path.name, windows=True)
    except ValueError as exc:
        raise ContextError("INDEX_PATH", str(exc)) from exc
    if path.suffix != ".sqlite3" or path.name in {"", ".sqlite3"}:
        raise ContextError("INDEX_PATH", "index must be an explicit .sqlite3 file")
    if os.path.normcase(str(path.parent)) != os.path.normcase(str(cache)):
        raise ContextError("INDEX_PATH", "index must be directly under .project-corpus/cache")
    return path


def build_index(root: Path | str, index: Path | str) -> dict[str, object]:
    corpus = collect(root)
    path = _index_path(root, index, create=True)
    relative = f".project-corpus/cache/{path.name}"
    # SQLite never opens a caller-controlled filesystem path. Native confined
    # handles create and publish the serialized database under a pinned root.
    try:
        with closing(sqlite3.connect(":memory:")) as db, db:
            db.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE sources (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, source_type TEXT NOT NULL, authority_class TEXT NOT NULL, temporal_status TEXT NOT NULL, timestamp TEXT)")
            db.execute("CREATE TABLE items (item_id TEXT PRIMARY KEY, source_path TEXT NOT NULL, line_start INTEGER NOT NULL, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE relations (source_path TEXT NOT NULL, target_path TEXT NOT NULL)")
            db.executemany("INSERT INTO meta VALUES (?,?)", (("schema", INDEX_SCHEMA_VERSION), ("project_id", corpus.project_id)))
            db.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?)", ((s.path, s.sha256, s.source_type, s.authority_class, s.temporal_status, s.timestamp) for s in corpus.sources))
            import json
            # Persist provenance only. Source text is read fresh for retrieval, so the
            # derived database never duplicates Corpus content or possible secrets.
            safe_keys = ("item_id", "project_id", "source_path", "source_sha256", "source_type", "authority_class", "temporal_status", "timestamp", "section_line", "line_start", "line_end", "non_authoritative")
            db.executemany("INSERT INTO items VALUES (?,?,?,?)", ((str(i["item_id"]), str(i["source_path"]), int(i["line_start"]), json.dumps({key: i[key] for key in safe_keys}, ensure_ascii=False, sort_keys=True)) for i in corpus.items))
            db.executemany("INSERT INTO relations VALUES (?,?)", corpus.relations)
            content = db.serialize()
        if len(content) > MAX_INDEX_BYTES:
            raise ContextError("CONTEXT_LIMIT", "index exceeds 128 MiB")
        with open_native_backend(Path(root)) as backend:
            backend.create_directory(".project-corpus/cache", exist_ok=True)
            if path.name + ".tmp" in backend.directory_entries(".project-corpus/cache"):
                raise ContextError("INDEX_PATH", "temporary index already exists")
            prior = backend.stat_optional(relative)
            staged = backend.stage_bytes(relative, content)
            try:
                if prior is not None:
                    backend.prepare_replacement(staged)
                backend.publish(staged, replace=prior is not None)
            finally:
                backend.discard(staged)
    except BackendError as exc:
        raise ContextError("INDEX_PATH", f"{exc.code}: {exc.detail}") from exc
    return {"ok": True, "project_id": corpus.project_id, "index_schema_version": INDEX_SCHEMA_VERSION, "source_count": len(corpus.sources), "item_count": len(corpus.items), "source_snapshot_digest": digest(corpus.snapshot), "non_authoritative": True}


def open_index(root: Path | str, index: Path | str, *, verify: bool = True) -> IndexedCorpus:
    path = _index_path(root, index, create=False)
    relative = f".project-corpus/cache/{path.name}"
    try:
        with open_native_backend(Path(root)) as backend:
            saved = backend.stat_optional(relative)
            if saved is None:
                raise ContextError("INDEX_MISSING", str(path))
            if saved.size > MAX_INDEX_BYTES:
                raise ContextError("CONTEXT_LIMIT", "index exceeds 128 MiB")
            content = backend.read_bytes(relative, max_bytes=MAX_INDEX_BYTES)
        with closing(sqlite3.connect(":memory:")) as db:
            db.deserialize(content)
            meta = dict(db.execute("SELECT key,value FROM meta"))
            if meta.get("schema") != INDEX_SCHEMA_VERSION:
                raise ContextError("INDEX_SCHEMA_MISMATCH", str(meta.get("schema")))
            sources = tuple(Source(*row, "") for row in db.execute("SELECT path,source_type,authority_class,sha256,timestamp,temporal_status FROM sources ORDER BY path"))
            import json
            items = tuple(json.loads(row[0]) for row in db.execute("SELECT payload FROM items ORDER BY source_path,line_start"))
            relations = tuple(db.execute("SELECT source_path,target_path FROM relations ORDER BY source_path,target_path"))
    except sqlite3.DatabaseError as exc:
        raise ContextError("INDEX_CORRUPT", str(exc)) from exc
    except BackendError as exc:
        raise ContextError("INDEX_PATH", f"{exc.code}: {exc.detail}") from exc
    corpus = IndexedCorpus(meta.get("project_id", ""), sources, items, relations)
    if verify:
        fresh = collect(root)
        if fresh.project_id != corpus.project_id:
            raise ContextError("INDEX_PROJECT_MISMATCH", "project ID changed")
        if fresh.snapshot != corpus.snapshot:
            raise ContextError("INDEX_STALE", "source files or hashes changed; rebuild index")
        return fresh
    return corpus
