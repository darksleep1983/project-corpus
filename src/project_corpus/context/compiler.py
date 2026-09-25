from __future__ import annotations

import hashlib
import re

from .index import IndexedCorpus
from .retrieval import query_index
from .schema import BUNDLE_SCHEMA_VERSION, RECEIPT_SCHEMA_VERSION, ContextError, canonical_json, digest, token_count, utc_now

MAX_BUNDLE_BYTES = 65536
PROJECT = ".project-corpus/state/PROJECT.md"
STATUS = ".project-corpus/state/STATUS.md"
SECTIONS = {
    "project": (("Objective",), ("Invariants",), ("Durable Scope Boundaries",)),
    "status": (("Current Verified Baseline",), ("Blockers",), ("Exact Next Action",)),
    "task": (("Objective",), ("Prohibited and Out of Scope", "Hard Prohibitions", "Do Not Expand Scope"),
             ("Owner-Controlled Gates", "Launch Authorization Gate"),
             ("Acceptance Criteria", "Supervisor Findings That Must Be Fixed"),
             ("Verification Requirements", "Local Qualification Before Commit")),
}


def _authority_item(source, kind: str, allowance: int) -> dict[str, object]:
    lines = source.content.splitlines()
    metadata = ("Protocol-Version:", "Project-ID:", "Logical-Name:") if kind == "project" else (
        ("Protocol-Version:", "Project-ID:", "Lifecycle-Status:", "Active-Task-ID:", "Last-Verified-At:", "Evidence-Class:")
        if kind == "status" else ("Task-ID:", "Task-Status:", "Created-At:", "Evidence-Class:"))
    selected: list[str] = []
    for prefix in metadata:
        selected.extend(line.strip() for line in lines if line.startswith(prefix))
    section_details: list[tuple[str, str]] = []
    for alternatives in SECTIONS[kind]:
        match = next((i for i, line in enumerate(lines) if any(re.fullmatch(r"##\s+" + re.escape(heading), line.strip(), re.IGNORECASE) for heading in alternatives)), None)
        if match is None:
            continue
        heading = lines[match].lstrip("# ").strip()
        detail = next((line.strip() for line in lines[match + 1:] if line.strip() and not line.startswith("#")), "")
        section_details.append((heading, detail))
    metadata = " | ".join(selected)
    available = allowance * 4 - len(metadata.encode("utf-8")) - sum(len(heading.encode("utf-8")) + 5 for heading, _ in section_details)
    per_section = max(0, available // max(1, len(section_details)))
    for heading, detail in section_details:
        selected.append(f"{heading}: {detail.encode('utf-8')[:per_section].decode('utf-8', errors='ignore')}")
    excerpt = " | ".join(selected)
    if token_count(excerpt) > allowance:
        excerpt = excerpt.encode("utf-8")[:allowance * 4].decode("utf-8", errors="ignore")
    return {
        "item_id": hashlib.sha256((source.path + "\0mandatory").encode()).hexdigest()[:20],
        "text": excerpt, "source_path": source.path, "line_start": 1,
        "line_end": len(lines), "source_sha256": source.sha256,
        "authority_class": source.authority_class, "temporal_status": source.temporal_status,
        "freshness_requirement": "READ_PRIMARY_SOURCE_BEFORE_AUTHORITY_CLAIM",
        "retrieval_score": 10000, "selection_reasons": [f"mandatory_{kind}", "bounded_authority_summary"],
        "section": "", "non_authoritative": True,
    }


def _finalize(bundle: dict[str, object]) -> None:
    bundle["selected_source_snapshot"] = {
        path: bundle["_snapshot"][path] for path in sorted({str(item["source_path"]) for item in bundle["items"]})
    }
    del bundle["_snapshot"]
    bundle["serialized_bytes"] = 0
    bundle["bundle_sha256"] = "0" * 64
    for _ in range(5):
        size = len(canonical_json(bundle))
        if size == bundle["serialized_bytes"]:
            break
        bundle["serialized_bytes"] = size
    bundle["bundle_sha256"] = digest({k: v for k, v in bundle.items() if k not in {"created_at", "bundle_sha256"}})
    bundle["serialized_bytes"] = len(canonical_json(bundle))


def compile_bundle(corpus: IndexedCorpus, query: str, *, max_tokens: int = 1200) -> dict[str, object]:
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or not 80 <= max_tokens <= 20000:
        raise ContextError("BUDGET_INVALID", "max_tokens must be 80..20000")
    sources = {s.path: s for s in corpus.sources}
    for path in (PROJECT, STATUS):
        if path not in sources:
            raise ContextError("CONTEXT_SCOPE", f"missing canonical source: {path}")
    active = next((s for s in corpus.sources if s.authority_class == "ACTIVE_TASK"), None)
    mandatory = [(sources[PROJECT], "project"), (sources[STATUS], "status")]
    if active:
        mandatory.append((active, "task"))
    allowance = max(1, (max_tokens - 8) // len(mandatory))
    chosen = [_authority_item(source, kind, allowance) for source, kind in mandatory]
    used = sum(token_count(str(item["text"])) for item in chosen)
    reads = [{"source_path": source.path, "source_sha256": source.sha256,
              "reason": f"full_primary_{kind}_read_required", "required_sections": [" / ".join(group) for group in SECTIONS[kind]]}
             for source, kind in mandatory]
    snapshot = corpus.snapshot
    bundle: dict[str, object] = {
        "schema_version": BUNDLE_SCHEMA_VERSION, "project_id": corpus.project_id,
        "query": query, "created_at": utc_now(), "index_schema_version": corpus.index_schema_version,
        "source_snapshot_digest": digest(snapshot), "source_count": len(snapshot),
        "mandatory_reads": reads,
        "budget": {"max_tokens": max_tokens, "estimated_tokens": used,
                   "estimator": "utf8_excerpt_bytes_div_4_ceil", "max_envelope_bytes": MAX_BUNDLE_BYTES},
        "items": chosen, "non_authoritative": True, "_snapshot": snapshot,
    }
    _finalize(bundle)
    if bundle["serialized_bytes"] > MAX_BUNDLE_BYTES:
        raise ContextError("BUNDLE_LIMIT", "mandatory authority envelope exceeds bound")
    ranked = query_index(corpus, query, limit=100)["results"]
    historical_requested = any(word in query.casefold() for word in ("old", "previous", "past", "historical", "history", "superseded", "стар", "истор", "прошл", "предыдущ", "устар", "замещ"))
    if not historical_requested and any(item["temporal_status"] == "current" for item in ranked):
        ranked = [item for item in ranked if item["temporal_status"] not in {"historical", "superseded"}]
    seen = {str(item["item_id"]) for item in chosen}
    for item in ranked:
        if item["item_id"] in seen:
            continue
        cost = token_count(str(item["text"]))
        if used + cost > max_tokens:
            continue
        chosen.append(item)
        bundle["_snapshot"] = snapshot
        bundle.pop("selected_source_snapshot", None)
        bundle["budget"]["estimated_tokens"] = used + cost
        _finalize(bundle)
        if bundle["serialized_bytes"] > MAX_BUNDLE_BYTES:
            chosen.pop()
            bundle["_snapshot"] = snapshot
            bundle.pop("selected_source_snapshot", None)
            bundle["budget"]["estimated_tokens"] = used
            _finalize(bundle)
            break
        seen.add(str(item["item_id"]))
        used += cost
        if len(chosen) >= 50:
            break
    return bundle


def make_receipt(bundle: dict[str, object], consumer: str, *, delivered_item_ids: list[str] | None = None) -> dict[str, object]:
    if bundle.get("bundle_sha256") != digest({k: v for k, v in bundle.items() if k not in {"created_at", "bundle_sha256"}}):
        raise ContextError("BUNDLE_HASH", "bundle payload does not match bundle_sha256")
    if bundle.get("serialized_bytes") != len(canonical_json(bundle)):
        raise ContextError("BUNDLE_SIZE", "serialized byte count differs")
    if not isinstance(consumer, str) or not consumer.strip() or len(consumer) > 128:
        raise ContextError("CONSUMER_INVALID", "consumer identifier must be 1..128 characters")
    available = [str(item["item_id"]) for item in bundle["items"]]
    delivered = available if delivered_item_ids is None else delivered_item_ids
    if not isinstance(delivered, list) or len(set(delivered)) != len(delivered) or not all(item in available for item in delivered):
        raise ContextError("RECEIPT_ITEMS", "delivered ids must be unique bundle item ids")
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION, "project_id": bundle["project_id"],
        "bundle_sha256": bundle["bundle_sha256"], "delivered_item_ids": delivered,
        "consumer": consumer, "created_at": utc_now(),
        "source_snapshot_digest": bundle["source_snapshot_digest"],
        "non_authoritative": True,
    }
