from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from .platform.base import NativePathBackend


V1_CURRENT_FILES = (
    "AGENTS.md",
    "OPERATOR_PROFILE.md",
    "PROJECT_ROADMAP_CURRENT.md",
    "CORPUS_ACCESS_CURRENT.md",
    "LOADER_PROMPT_CURRENT.md",
    "SESSION_HANDOFF_CURRENT.md",
    "SESSION_HANDOFF_FULL_CURRENT.md",
)


class LegacyCorpusError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class LegacyFile:
    relative_path: str
    content: bytes
    sha256: str

    @property
    def text(self) -> str:
        try:
            return self.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LegacyCorpusError(
                "V1_NOT_UTF8", f"{self.relative_path}: {exc}"
            ) from exc


@dataclass(frozen=True)
class LegacySnapshot:
    files: tuple[LegacyFile, ...]
    artifacts: tuple[LegacyFile, ...]
    language: str

    def by_name(self, name: str) -> LegacyFile:
        for item in self.files:
            if item.relative_path == name:
                return item
        raise KeyError(name)

    @property
    def source_manifest(self) -> dict[str, str]:
        return {
            item.relative_path: item.sha256
            for item in (*self.files, *self.artifacts)
        }


def _read_file(path: Path, relative: str) -> LegacyFile:
    data = path.read_bytes()
    item = LegacyFile(relative, data, hashlib.sha256(data).hexdigest())
    item.text
    return item


def _detect_case_collisions(root: Path) -> None:
    names: dict[str, list[str]] = {}
    for path in root.iterdir():
        names.setdefault(path.name.casefold(), []).append(path.name)
    expected = {name.casefold() for name in V1_CURRENT_FILES}
    collisions = {
        key: values for key, values in names.items()
        if key in expected and len(values) > 1
    }
    if collisions:
        detail = "; ".join(f"{key}: {sorted(values)}" for key, values in collisions.items())
        raise LegacyCorpusError("V1_DUPLICATE_CANONICAL_NAME", detail)


def load_v1_corpus(root: Path) -> LegacySnapshot:
    """Fully read a V1 corpus without modifying it."""
    root = root.absolute()
    if not root.is_dir():
        raise LegacyCorpusError("V1_ROOT_NOT_DIRECTORY", str(root))
    _detect_case_collisions(root)
    missing = [name for name in V1_CURRENT_FILES if not (root / name).is_file()]
    if missing:
        raise LegacyCorpusError("V1_MISSING_CURRENT_FILE", ", ".join(missing))

    files = tuple(_read_file(root / name, name) for name in V1_CURRENT_FILES)
    artifacts: list[LegacyFile] = []
    for directory in ("Tasks", "Report"):
        base = root / directory
        if not base.exists():
            continue
        if not base.is_dir():
            raise LegacyCorpusError("V1_ARTIFACT_PATH_NOT_DIRECTORY", directory)
        for path in sorted(item for item in base.rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix()
            artifacts.append(_read_file(path, relative))

    agents = next(item.text for item in files if item.relative_path == "AGENTS.md")
    language = "ru" if re.search(r"(?m)^## \d+\. (?:Назначение|Цель)", agents) else "en"
    return LegacySnapshot(files, tuple(artifacts), language)


def load_v1_corpus_confined(backend: NativePathBackend) -> LegacySnapshot:
    """Read a V1 corpus through an already-qualified confined backend."""
    names: dict[str, list[str]] = {}
    for name in backend.root_entries():
        names.setdefault(name.casefold(), []).append(name)
    collisions = {
        key: values for key, values in names.items()
        if key in {item.casefold() for item in V1_CURRENT_FILES} and len(values) > 1
    }
    if collisions:
        raise LegacyCorpusError("V1_DUPLICATE_CANONICAL_NAME", str(collisions))
    missing = [
        name for name in V1_CURRENT_FILES
        if name not in backend.root_entries()
    ]
    if missing:
        raise LegacyCorpusError("V1_MISSING_CURRENT_FILE", ", ".join(missing))

    def read(relative: str) -> LegacyFile:
        data = backend.read_bytes(relative)
        item = LegacyFile(relative, data, hashlib.sha256(data).hexdigest())
        item.text
        return item

    files = tuple(read(name) for name in V1_CURRENT_FILES)
    artifacts: list[LegacyFile] = []
    top = set(backend.root_entries())
    for directory in ("Tasks", "Report"):
        if directory not in top:
            continue
        for relative in backend.walk_files(directory):
            artifacts.append(read(relative))
    agents = next(item.text for item in files if item.relative_path == "AGENTS.md")
    language = "ru" if re.search(r"(?m)^## \d+\. (?:Назначение|Цель)", agents) else "en"
    return LegacySnapshot(files, tuple(artifacts), language)
