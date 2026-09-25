from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

INDEX_SCHEMA_VERSION = "1"
BUNDLE_SCHEMA_VERSION = "1"
RECEIPT_SCHEMA_VERSION = "1"
CANDIDATE_SCHEMA_VERSION = "1"
MAX_SOURCES = 2048
MAX_ITEMS = 50000
MAX_TOTAL_SOURCE_BYTES = 64 * 1024 * 1024
MAX_INDEX_BYTES = 128 * 1024 * 1024


class ContextError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def token_count(text: str) -> int:
    # Stable approximation, intentionally independent of a model tokenizer.
    return max(1, (len(text.encode("utf-8")) + 3) // 4)
