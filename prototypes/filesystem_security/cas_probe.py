from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys

from .prototype_lock import exclusive_lock


class StaleWriteError(RuntimeError):
    pass


def confined_sha256(root: Path, relative: str) -> str:
    digest = hashlib.sha256()
    if sys.platform == "win32":
        from .windows_native import open_confined, read_all

        with open_confined(root, relative) as handle:
            digest.update(read_all(handle))
    else:
        from .posix_native import open_confined

        fd, _ = open_confined(root, relative)
        try:
            while True:
                block = os.read(fd, 1024 * 1024)
                if not block:
                    break
                digest.update(block)
        finally:
            os.close(fd)
    return digest.hexdigest()


def cas_publish(root: Path, relative: str, data: bytes, expected_sha256: str,
                owner_lock: Path) -> str:
    """Prototype managed-writer serialization plus expected-hash check."""
    with exclusive_lock(owner_lock):
        actual = confined_sha256(root, relative)
        if actual != expected_sha256:
            raise StaleWriteError(f"expected {expected_sha256}, observed {actual}")
        if sys.platform == "win32":
            from .windows_native import publish_bytes
        else:
            from .posix_native import publish_bytes
        publish_bytes(root, relative, data, replace=True)
        result = confined_sha256(root, relative)
        intended = hashlib.sha256(data).hexdigest()
        if result != intended:
            raise RuntimeError("readback hash mismatch")
        return result
