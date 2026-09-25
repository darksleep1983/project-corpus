from __future__ import annotations

from .compiler import compile_bundle
from .index import IndexedCorpus
from .retrieval import query_index
from .schema import ContextError, canonical_json, digest


def evaluate_dataset(corpus: IndexedCorpus, dataset: object) -> dict[str, object]:
    if not isinstance(dataset, dict) or dataset.get("schema_version") != "1" or not isinstance(dataset.get("cases"), list):
        raise ContextError("EVAL_SCHEMA", "expected v1 object with cases array")
    if len(dataset["cases"]) > 1000:
        raise ContextError("EVAL_LIMIT", "too many cases")
    results = []
    for index, case in enumerate(dataset["cases"]):
        if not isinstance(case, dict) or not isinstance(case.get("query"), str):
            raise ContextError("EVAL_SCHEMA", f"invalid case {index}")
        budget = case.get("max_tokens", 1200)
        retrieval = query_index(corpus, case["query"], limit=case.get("retrieval_limit", 20))["results"]
        first = compile_bundle(corpus, case["query"], max_tokens=budget)
        second = compile_bundle(corpus, case["query"], max_tokens=budget)
        items = first["items"]
        paths = {str(item["source_path"]) for item in items}
        classes = {str(item["authority_class"]) for item in items}
        retrieval_paths = [str(item["source_path"]) for item in retrieval]
        expected_paths = set(case.get("expected_source_paths", []))
        expected_classes = set(case.get("expected_authority_classes", []))
        forbidden_paths = set(case.get("forbidden_source_paths", []))
        forbidden_classes = set(case.get("forbidden_authority_classes", []))
        forbidden_scope = set(case.get("forbidden_scope_paths", []))
        text = "\n".join(str(item["text"]) for item in items)
        denominator = len(expected_paths) + len(expected_classes)
        recall = (len(paths & expected_paths) + len(classes & expected_classes)) / denominator if denominator else 1.0
        contamination = (len(paths & forbidden_paths) + len(classes & forbidden_classes)
                         + len(set(retrieval_paths) & set(case.get("forbidden_retrieval_source_paths", []))))
        expected_top = case.get("expected_top_source_path")
        top_ok = expected_top is None or bool(retrieval and retrieval[0]["source_path"] == expected_top)
        top_k = case.get("expected_top_k_paths", [])
        top_k_ok = all(path in retrieval_paths[:case.get("top_k", 5)] for path in top_k)
        source_temporal = case.get("expected_source_temporal", {})
        source_authority = case.get("expected_source_authority", {})
        retrieved_by_path = {str(item["source_path"]): item for item in retrieval}
        source_specific_ok = all(retrieved_by_path.get(path, {}).get("temporal_status") == value for path, value in source_temporal.items()) and all(
            retrieved_by_path.get(path, {}).get("authority_class") == value for path, value in source_authority.items())
        expected_temporal = case.get("expected_temporal_status")
        temporal_ok = expected_temporal is None or bool(retrieval and retrieval[0]["temporal_status"] == expected_temporal)
        contain_ok = all(word in text for word in case.get("must_contain", [])) and all(word not in text for word in case.get("must_not_contain", []))
        isolation = (not forbidden_scope.intersection(corpus.snapshot)
                     and not forbidden_scope.intersection(retrieval_paths)
                     and not forbidden_scope.intersection(paths)
                     and case.get("expected_project_id", corpus.project_id) == corpus.project_id
                     and all(item["project_id"] == corpus.project_id for item in retrieval)) if forbidden_scope or "expected_project_id" in case else None
        budget_ok = (first["budget"]["estimated_tokens"] <= budget
                     and first["serialized_bytes"] == len(canonical_json(first))
                     and first["serialized_bytes"] <= first["budget"]["max_envelope_bytes"])
        repeatable = first["bundle_sha256"] == second["bundle_sha256"]
        expected_snapshot = case.get("expected_snapshot_digest")
        snapshot_ok = (expected_snapshot is None or expected_snapshot == first["source_snapshot_digest"])
        passed = (recall == 1 and contamination == 0 and top_ok and top_k_ok and source_specific_ok
                  and temporal_ok and contain_ok and isolation is not False and budget_ok and repeatable and snapshot_ok)
        results.append({"name": case.get("name", str(index)), "pass": passed, "source_recall": recall,
                        "forbidden_contamination": contamination, "top_source_correct": top_ok,
                        "top_k_correct": top_k_ok, "source_specific_correct": source_specific_ok,
                        "current_historical_correct": temporal_ok, "project_policy_isolation": isolation,
                        "budget_compliant": budget_ok, "deterministic_repeatability": repeatable,
                        "stale_source_detection": snapshot_ok, "must_contain_ok": contain_ok,
                        "bundle_sha256": first["bundle_sha256"]})
    return {"ok": all(result["pass"] for result in results), "project_id": corpus.project_id,
            "case_count": len(results),
            "source_recall_mean": sum(result["source_recall"] for result in results) / len(results) if results else 1.0,
            "forbidden_contamination_rate": sum(result["forbidden_contamination"] > 0 for result in results) / len(results) if results else 0.0,
            "project_policy_isolation_pass_rate": (sum(result["project_policy_isolation"] is True for result in results) /
                                                   sum(result["project_policy_isolation"] is not None for result in results))
            if any(result["project_policy_isolation"] is not None for result in results) else None,
            "results": results, "non_authoritative": True}
