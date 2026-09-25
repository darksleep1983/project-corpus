"""Optional, non-authoritative Context Intelligence for Protocol V2 corpora."""

from .index import build_index, open_index
from .retrieval import query_index
from .compiler import compile_bundle, make_receipt
from .doctor import memory_doctor
from .eval import evaluate_dataset
from .candidates import validate_candidate

__all__ = [
    "build_index", "open_index", "query_index", "compile_bundle", "make_receipt",
    "memory_doctor", "evaluate_dataset", "validate_candidate",
]
