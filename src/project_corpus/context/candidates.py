from __future__ import annotations

import re

from .index import IndexedCorpus, _valid_ref
from .schema import CANDIDATE_SCHEMA_VERSION, ContextError

KINDS = {"semantic_fact", "episodic_evidence", "procedural_knowledge", "environment_gotcha", "premise", "resource_reference"}
FIELDS = {"schema_version", "candidate_id", "project_id", "kind", "statement", "source_refs", "created_at", "status"}


def validate_candidate(corpus: IndexedCorpus, candidate: object) -> dict[str, object]:
    if not isinstance(candidate, dict) or set(candidate) != FIELDS:
        raise ContextError("CANDIDATE_SCHEMA", "candidate fields differ from v1")
    if candidate["schema_version"] != CANDIDATE_SCHEMA_VERSION or candidate["status"] != "candidate":
        raise ContextError("CANDIDATE_SCHEMA", "candidate must use v1 and status=candidate")
    if candidate["project_id"] != corpus.project_id:
        raise ContextError("CANDIDATE_PROJECT", "candidate project differs from corpus")
    if not isinstance(candidate["candidate_id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", candidate["candidate_id"]):
        raise ContextError("CANDIDATE_ID", "invalid candidate id")
    if candidate["kind"] not in KINDS:
        raise ContextError("CANDIDATE_KIND", "unknown candidate kind")
    if not isinstance(candidate["statement"], str) or not candidate["statement"].strip() or len(candidate["statement"]) > 4000:
        raise ContextError("CANDIDATE_STATEMENT", "statement must be 1..4000 characters")
    if not isinstance(candidate["created_at"], str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", candidate["created_at"]):
        raise ContextError("CANDIDATE_TIME", "created_at must be RFC3339 UTC seconds")
    refs = candidate["source_refs"]
    if not isinstance(refs, list) or not refs or len(refs) > 32:
        raise ContextError("CANDIDATE_EVIDENCE", "source_refs must contain 1..32 references")
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"source_path", "source_sha256", "line_start"}:
            raise ContextError("CANDIDATE_EVIDENCE", "invalid source reference")
        path = ref["source_path"]
        if not isinstance(path, str) or not _valid_ref(path) or corpus.snapshot.get(path) != ref["source_sha256"]:
            raise ContextError("CANDIDATE_EVIDENCE", "source path/hash is not in current scoped snapshot")
        if not isinstance(ref["line_start"], int) or isinstance(ref["line_start"], bool) or ref["line_start"] < 1:
            raise ContextError("CANDIDATE_EVIDENCE", "invalid source line")
        source = next((item for item in corpus.sources if item.path == path), None)
        if source is None or ref["line_start"] > len(source.content.splitlines()):
            raise ContextError("CANDIDATE_EVIDENCE", "source line is outside referenced artifact")
    return {"ok": True, "candidate_id": candidate["candidate_id"], "project_id": corpus.project_id, "status": "candidate", "non_authoritative": True, "promotion": "EXPLICIT_SUPERVISOR_OR_OWNER_ACTION_REQUIRED"}
