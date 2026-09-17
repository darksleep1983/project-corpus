from __future__ import annotations

from pathlib import Path
import sys

from .base import BackendError, NativePathBackend


def open_native_backend(root: Path, *, require_qualified: bool = True) -> NativePathBackend:
    if sys.platform == "win32":
        from .windows import WindowsNativeBackend

        return WindowsNativeBackend(root, require_qualified=require_qualified)
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        from .posix import PosixNativeBackend

        return PosixNativeBackend(root, require_qualified=require_qualified)
    raise BackendError("PLATFORM_UNSUPPORTED", sys.platform)
