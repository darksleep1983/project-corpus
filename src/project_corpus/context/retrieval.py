from __future__ import annotations

import re

from .index import IndexedCorpus
from .schema import ContextError

WORD = re.compile(r"[^\W_]+", re.UNICODE)
AUTHORITY = {"CANONICAL": 80, "ACTIVE_TASK": 65, "CITED_REPORT": 50, "SCOPED_REPORT": 30, "OTHER_TASK": 15, "HISTORY": 0}
TEMPORAL = {"current": 20, "scoped": 5, "historical": -15, "superseded": -45, "unknown": -5}
STOPWORDS = {"the", "a", "an", "is", "what", "which", "who", "how", "does", "do", "of", "for", "to", "in", "and", "or", "are", "was", "with", "this", "that",
             "что", "как", "какой", "какая", "какие", "где", "кто", "это", "для", "или", "и", "в", "во", "на", "по", "из", "с", "со", "у", "о", "об", "ли", "же", "бы", "есть"}
HISTORICAL_INTENT = ("old", "previous", "past", "historical", "history", "superseded", "стар", "истор", "прошл", "предыдущ", "устар", "замещ")


def words(text: str) -> tuple[str, ...]:
    return tuple(word.casefold() for word in WORD.findall(text))


def _near_duplicate(a: str, b: str) -> bool:
    aa, bb = set(words(a)), set(words(b))
    return bool(aa and bb) and len(aa & bb) / len(aa | bb) >= 0.9


def query_index(corpus: IndexedCorpus, query: str, *, limit: int = 20) -> dict[str, object]:
    if not isinstance(query, str) or not query.strip():
        raise ContextError("QUERY_EMPTY", "query must be non-empty")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        raise ContextError("QUERY_LIMIT", "limit must be 1..100")
    terms = set(words(query)) - STOPWORDS
    if not terms:
        terms = set(words(query))
    historical_requested = any(any(term.startswith(prefix) for prefix in HISTORICAL_INTENT) for term in terms)
    dated = sorted({s.timestamp for s in corpus.sources if s.timestamp and re.match(r"^\d{4}-\d\d-\d\d", s.timestamp)})
    recency = {value: int(10 * (index + 1) / len(dated)) for index, value in enumerate(dated)}
    ranked = []
    for item in corpus.items:
        if item["project_id"] != corpus.project_id:
            continue
        text = str(item["text"])
        tokens = set(words(text + " " + str(item["section"])))
        hits = terms & tokens
        phrase = query.casefold() in text.casefold()
        if not hits and not phrase:
            continue
        reasons = ["lexical_terms:" + ",".join(sorted(hits))] if hits else []
        score = int(100 * len(hits) / len(terms))
        if phrase:
            score += 25
            reasons.append("exact_phrase")
        authority = str(item["authority_class"])
        temporal = str(item["temporal_status"])
        score += AUTHORITY[authority] + TEMPORAL[temporal]
        if historical_requested and temporal in {"historical", "superseded"}:
            score += 70
            reasons.append("historical_query_intent")
        reasons.extend(("authority:" + authority, "temporal:" + temporal, "exact_project_scope"))
        if item["source_path"] == ".project-corpus/state/STATUS.md" and terms & {"status", "state", "lifecycle", "mutable", "baseline", "статус", "состояние", "текущий", "текущая"}:
            score += 50
            reasons.append("canonical_current_state_role")
        if item["source_path"] == ".project-corpus/state/PROJECT.md" and terms & {"stable", "identity", "invariants", "durable", "инварианты", "идентичность", "цель"}:
            score += 50
            reasons.append("canonical_identity_role")
        if item["timestamp"] in recency:
            score += recency[str(item["timestamp"])]
            reasons.append("explicit_timestamp")
        if item["section"]:
            score += 3
            reasons.append("section_provenance")
        result = dict(item)
        result["retrieval_score"] = score
        result["selection_reasons"] = reasons
        result["freshness_requirement"] = "READ_PRIMARY_SOURCE_BEFORE_AUTHORITY_CLAIM"
        ranked.append(result)
    ranked.sort(key=lambda item: (-int(item["retrieval_score"]), str(item["source_path"]), int(item["line_start"])))
    unique: list[dict[str, object]] = []
    for item in ranked:
        if any(_near_duplicate(str(item["text"]), str(old["text"])) for old in unique):
            continue
        unique.append(item)
        if len(unique) >= limit:
            break
    return {"schema_version": "1", "project_id": corpus.project_id, "query": query, "results": unique, "non_authoritative": True}
