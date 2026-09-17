from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class BackendError(RuntimeError):
    def __init__(self, code: str, detail: str, *, native_code: int | None = None):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.native_code = native_code


@dataclass(frozen=True)
class PathStat:
    relative_path: str
    size: int
    sha256: str
    identity: str


@dataclass
class StagedWrite:
    relative_path: str
    expected_sha256: str
    platform_data: Any
    stage_id: str
    metadata_fingerprint: str | None = None
    published: bool = False


class NativePathBackend(ABC):
    root: Path
    filesystem: str
    root_identity: str
    durability_level: str

    def __enter__(self) -> "NativePathBackend":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def read_bytes(self, relative: str, *, max_bytes: int | None = None) -> bytes: ...

    @abstractmethod
    def stat(self, relative: str) -> PathStat: ...

    @abstractmethod
    def stat_optional(self, relative: str) -> PathStat | None: ...

    @abstractmethod
    def stage_bytes(
        self, relative: str, content: bytes, *, stage_id: str | None = None
    ) -> StagedWrite: ...

    @abstractmethod
    def prepare_replacement(self, staged: StagedWrite) -> str: ...

    @abstractmethod
    def publish(self, staged: StagedWrite, *, replace: bool) -> PathStat: ...

    @abstractmethod
    def discard(self, staged: StagedWrite) -> None: ...

    @abstractmethod
    def abandon(self, staged: StagedWrite) -> None: ...

    @abstractmethod
    def discard_stage(self, relative: str, stage_id: str) -> None: ...

    @abstractmethod
    def metadata_fingerprint(self, relative: str) -> str: ...

    @abstractmethod
    def writer_lock(self, relative: str) -> AbstractContextManager[None]: ...

    @abstractmethod
    def create_directory(self, relative: str, *, exist_ok: bool) -> str: ...

    @abstractmethod
    def directory_entries(self, relative: str) -> tuple[str, ...]: ...

    @abstractmethod
    def publish_directory(self, source: str, target: str) -> str: ...
