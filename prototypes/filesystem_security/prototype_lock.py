from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import sys
from typing import Iterator


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_READ = 0x1
    FILE_SHARE_WRITE = 0x2
    FILE_SHARE_DELETE = 0x4
    OPEN_ALWAYS = 4
    FILE_ATTRIBUTE_NORMAL = 0x80
    LOCKFILE_EXCLUSIVE_LOCK = 0x2
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    class OVERLAPPED(ctypes.Structure):
        _fields_ = [
            ("Internal", ctypes.c_size_t),
            ("InternalHigh", ctypes.c_size_t),
            ("Offset", wintypes.DWORD),
            ("OffsetHigh", wintypes.DWORD),
            ("hEvent", wintypes.HANDLE),
        ]

    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.LockFileEx.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, ctypes.POINTER(OVERLAPPED),
    ]
    kernel32.LockFileEx.restype = wintypes.BOOL
    kernel32.UnlockFileEx.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(OVERLAPPED),
    ]
    kernel32.UnlockFileEx.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    """Cross-process prototype lock stored in owner-controlled state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        handle = kernel32.CreateFileW(
            str(path), GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, None,
        )
        if handle == INVALID_HANDLE_VALUE:
            raise OSError(ctypes.get_last_error(), "CreateFileW(lock) failed")
        overlapped = OVERLAPPED()
        try:
            if not kernel32.LockFileEx(
                handle, LOCKFILE_EXCLUSIVE_LOCK, 0, 1, 0,
                ctypes.byref(overlapped),
            ):
                raise OSError(ctypes.get_last_error(), "LockFileEx failed")
            try:
                yield
            finally:
                if not kernel32.UnlockFileEx(
                    handle, 0, 1, 0, ctypes.byref(overlapped)
                ):
                    raise OSError(ctypes.get_last_error(), "UnlockFileEx failed")
        finally:
            kernel32.CloseHandle(handle)
    else:
        import fcntl

        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
