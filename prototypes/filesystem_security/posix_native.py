from __future__ import annotations

import ctypes
from dataclasses import dataclass
import errno
import os
from pathlib import Path
import platform
import stat
import unicodedata
from uuid import uuid4

from .common import PrototypePathError, validate_relative_path


class NativeProbeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProbeResult:
    backend: str
    path: str


def _portable_collision(parent_fd: int, target: str) -> None:
    key = unicodedata.normalize("NFC", target).casefold()
    for existing in os.listdir(parent_fd):
        if existing == target:
            continue
        if unicodedata.normalize("NFC", existing).casefold() == key:
            raise FileExistsError(
                errno.EEXIST, "portable case/Unicode collision", target
            )


def _openat2(root_fd: int, relative: str, flags: int) -> int:
    class OPEN_HOW(ctypes.Structure):
        _fields_ = [("flags", ctypes.c_ulonglong), ("mode", ctypes.c_ulonglong),
                    ("resolve", ctypes.c_ulonglong)]

    # Linux assigns openat2 syscall number 437 on the architectures exercised by
    # the V2 CI matrix.  Unsupported kernels fail closed and use the component
    # walk below only after that walk passes its own adversarial tests.
    SYS_OPENAT2 = 437
    RESOLVE_NO_XDEV = 0x01
    RESOLVE_NO_MAGICLINKS = 0x02
    RESOLVE_NO_SYMLINKS = 0x04
    RESOLVE_BENEATH = 0x08
    how = OPEN_HOW(
        flags | getattr(os, "O_CLOEXEC", 0), 0,
        RESOLVE_NO_XDEV | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS | RESOLVE_BENEATH,
    )
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.syscall(
        SYS_OPENAT2, root_fd, relative.encode(), ctypes.byref(how), ctypes.sizeof(how)
    )
    if fd < 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), relative)
    return fd


def _component_walk(root_fd: int, parts: tuple[str, ...], *, final_flags: int) -> int:
    current = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
                getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
                dir_fd=current,
            )
            os.close(current)
            current = next_fd
        nofollow_any = getattr(os, "O_NOFOLLOW_ANY", 0)
        fd = os.open(
            parts[-1], final_flags | getattr(os, "O_NOFOLLOW", 0) |
            nofollow_any | getattr(os, "O_CLOEXEC", 0), dir_fd=current,
        )
        return fd
    finally:
        os.close(current)


def open_confined(root: Path, relative: str, *, force_fallback: bool = False) -> tuple[int, ProbeResult]:
    parts = validate_relative_path(relative, windows=False)
    root_fd = os.open(
        root,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
        getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        if platform.system() == "Linux" and not force_fallback:
            try:
                fd = _openat2(root_fd, "/".join(parts), flags)
                backend = "openat2"
            except OSError as exc:
                if exc.errno not in {errno.ENOSYS, errno.EINVAL}:
                    raise
                fd = _component_walk(root_fd, parts, final_flags=flags)
                backend = "openat-component-walk"
        else:
            fd = _component_walk(root_fd, parts, final_flags=flags)
            backend = "openat-component-walk"
        mode = os.fstat(fd).st_mode
        if not stat.S_ISREG(mode):
            os.close(fd)
            raise NativeProbeError("target is not a regular file")
        return fd, ProbeResult(backend, "/".join(parts))
    finally:
        os.close(root_fd)


def publish_bytes(root: Path, relative: str, data: bytes, *, replace: bool) -> None:
    parts = validate_relative_path(relative, windows=False)
    if len(parts) < 2:
        raise PrototypePathError("prototype publish requires a child directory")
    root_fd = os.open(
        root,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
        getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    parent_fd = None
    temp_fd = None
    temp_name = f".pc-probe-{uuid4().hex}.tmp"
    try:
        parent_parts = parts[:-1]
        parent_fd = os.dup(root_fd)
        for part in parent_parts:
            next_fd = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
                getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_fd,
            )
            os.close(parent_fd)
            parent_fd = next_fd
        _portable_collision(parent_fd, parts[-1])
        temp_fd = os.open(
            temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
            getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd,
        )
        view = memoryview(data)
        while view:
            view = view[os.write(temp_fd, view):]
        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = None
        target = parts[-1]
        if not replace:
            # Hard-link publication provides create-if-absent semantics.  The
            # temporary name is removed only after the target link exists.
            os.link(temp_name, target, src_dir_fd=parent_fd, dst_dir_fd=parent_fd,
                    follow_symlinks=False)
            os.unlink(temp_name, dir_fd=parent_fd)
        else:
            os.replace(temp_name, target, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally:
        if temp_fd is not None:
            os.close(temp_fd)
        if parent_fd is not None:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            os.close(parent_fd)
        os.close(root_fd)
