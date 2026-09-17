from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class BackendError(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


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
    def stage_bytes(self, relative: str, content: bytes) -> StagedWrite: ...

    @abstractmethod
    def publish(self, staged: StagedWrite, *, replace: bool) -> PathStat: ...

    @abstractmethod
    def discard(self, staged: StagedWrite) -> None: ...
