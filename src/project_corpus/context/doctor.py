from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import re

from .candidates import validate_candidate
from .index import IndexedCorpus, collect, open_index, valid_relation, cyclic_relations, ACTIVE
from .schema import ContextError, INDEX_SCHEMA_VERSION, digest


def memory_doctor(root: Path | str, *, index: Path | str | None = None, bundle: dict[str, object] | None = None, candidates: list[dict[str, object]] | None = None, corpus: IndexedCorpus | None = None) -> dict[str, object]:
    fresh = corpus if corpus is not None else collect(root)
    issues: list[dict[str, str]] = []

    def issue(code: str, detail: str, severity: str = "WARN") -> None:
        issues.append({"code": code, "detail": detail, "severity": severity})

    if index is not None:
        try:
            saved = open_index(root, index, verify=False)
            if saved.index_schema_version != INDEX_SCHEMA_VERSION:
                issue("INDEX_SCHEMA_MISMATCH", saved.index_schema_version, "FAIL")
            if saved.project_id != fresh.project_id:
                issue("INDEX_PROJECT_MISMATCH", saved.project_id, "FAIL")
            for path, sha in saved.snapshot.items():
                if path not in fresh.snapshot:
                    issue("MISSING_SOURCE", path, "FAIL")
                elif sha != fresh.snapshot[path]:
                    issue("STALE_INDEX", path, "FAIL")
            for path in fresh.snapshot.keys() - saved.snapshot.keys():
                issue("STALE_INDEX", f"new source: {path}", "FAIL")
            for item in saved.items:
                source = next((s for s in saved.sources if s.path == item.get("source_path")), None)
                if source is None or item.get("source_sha256") != source.sha256 or int(item.get("line_start", 0)) < 1:
                    issue("BROKEN_PROVENANCE", str(item.get("item_id")), "FAIL")
                if item.get("temporal_status") == "current" and source and source.path in {t for _, t in saved.relations}:
                    issue("SUPERSEDED_RANKED_CURRENT", source.path, "FAIL")
        except ContextError as exc:
            issue(exc.code, exc.detail, "FAIL")
    normalized = Counter(re.sub(r"\s+", " ", str(i["text"]).casefold()).strip() for i in fresh.items if len(str(i["text"])) > 30)
    for text, count in normalized.items():
        if count > 1:
            issue("DUPLICATE_MEMORY_ITEM", f"{count} copies; text_sha256={hashlib.sha256(text.encode()).hexdigest()}")
    status_text = next(s.content for s in fresh.sources if s.path.endswith("/STATUS.md"))
    active_match = ACTIVE.search(status_text)
    active_path = f".project-corpus/tasks/{active_match.group(1)}.md" if active_match and active_match.group(1) != "NONE" else None
    cycles = cyclic_relations(fresh.relations, set(fresh.snapshot), active_path)
    for source, target in fresh.relations:
        if not valid_relation(source, target, active_path):
            issue("INVALID_TEMPORAL_RELATION", f"{source} -> {target}", "FAIL")
        elif target not in fresh.snapshot:
            issue("ORPHAN_SUPERSESSION", f"{source} -> {target}")
        elif (source, target) in cycles:
            issue("TEMPORAL_CYCLE", f"{source} -> {target}", "FAIL")
    status = next(s for s in fresh.sources if s.path.endswith("/STATUS.md"))
    if len(status.content.encode("utf-8")) > 12000:
        issue("OVERSIZED_STATUS", f"{len(status.content.encode('utf-8'))} bytes")
    for source in fresh.sources:
        if source.source_type not in {"report", "history", "task"}:
            continue
        if re.search(r"\b(currently|right now|today|live|сейчас|сегодня|текущ\w*)\b", source.content, re.IGNORECASE) and "Freshness-Requirement:" not in source.content:
            issue("VOLATILE_WITHOUT_FRESHNESS", source.path)
    if bundle is not None:
        if bundle.get("project_id") != fresh.project_id:
            issue("BUNDLE_PROJECT_MISMATCH", str(bundle.get("project_id")), "FAIL")
        snapshot = bundle.get("selected_source_snapshot")
        if not isinstance(snapshot, dict):
            issue("BUNDLE_SNAPSHOT", "missing selected_source_snapshot", "FAIL")
        else:
            for path, sha in snapshot.items():
                if fresh.snapshot.get(path) != sha:
                    issue("BUNDLE_STALE_SOURCE", str(path), "FAIL")
        if bundle.get("source_snapshot_digest") != digest(fresh.snapshot) or bundle.get("source_count") != len(fresh.snapshot):
            issue("BUNDLE_FULL_SNAPSHOT_MISMATCH", "full scoped source snapshot changed", "FAIL")
    for candidate in candidates or []:
        try:
            validate_candidate(fresh, candidate)
        except ContextError as exc:
            issue("CANDIDATE_WITHOUT_EVIDENCE" if exc.code == "CANDIDATE_EVIDENCE" else exc.code, exc.detail, "FAIL")
    return {"ok": not any(i["severity"] == "FAIL" for i in issues), "project_id": fresh.project_id, "index_schema_version": INDEX_SCHEMA_VERSION, "source_count": len(fresh.sources), "issues": sorted(issues, key=lambda i: (i["code"], i["detail"])), "non_authoritative": True}
