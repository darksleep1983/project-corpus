from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import sys
from uuid import uuid4

from .common import PrototypePathError, validate_relative_path


if sys.platform == "win32":
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")

    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_SHARE_READ = 0x1
    FILE_SHARE_WRITE = 0x2
    FILE_SHARE_DELETE = 0x4
    SHARE_ALL = FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    DELETE = 0x00010000
    SYNCHRONIZE = 0x00100000
    FILE_READ_ATTRIBUTES = 0x80
    FILE_LIST_DIRECTORY = 0x1
    FILE_OPEN = 0x1
    FILE_CREATE = 0x2
    FILE_DIRECTORY_FILE = 0x1
    FILE_SYNCHRONOUS_IO_NONALERT = 0x20
    FILE_NON_DIRECTORY_FILE = 0x40
    FILE_OPEN_REPARSE_POINT = 0x00200000
    OBJ_CASE_INSENSITIVE = 0x40
    FileAttributeTagInfo = 9
    FileIdInfo = 18
    FileRenameInformation = 10
    FileDispositionInformation = 13

    class UNICODE_STRING(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        ]

    class OBJECT_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UNICODE_STRING)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        ]

    class IO_STATUS_BLOCK(ctypes.Structure):
        _fields_ = [("Status", ctypes.c_long), ("Information", ctypes.c_size_t)]

    class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
        _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]

    class FILE_ID_128(ctypes.Structure):
        _fields_ = [("Identifier", ctypes.c_ubyte * 16)]

    class FILE_ID_INFO(ctypes.Structure):
        _fields_ = [("VolumeSerialNumber", ctypes.c_ulonglong), ("FileId", FILE_ID_128)]

    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
    ]
    kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel32.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
    ]
    kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel32.WriteFile.argtypes = [
        wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    kernel32.WriteFile.restype = wintypes.BOOL
    kernel32.ReadFile.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    kernel32.FlushFileBuffers.restype = wintypes.BOOL
    advapi32.GetFileSecurityW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.GetFileSecurityW.restype = wintypes.BOOL
    ntdll.NtCreateFile.argtypes = [
        ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
        ctypes.POINTER(OBJECT_ATTRIBUTES), ctypes.POINTER(IO_STATUS_BLOCK),
        ctypes.c_void_p, wintypes.ULONG, wintypes.ULONG, wintypes.ULONG,
        wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG,
    ]
    ntdll.NtCreateFile.restype = ctypes.c_long
    ntdll.NtSetInformationFile.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(IO_STATUS_BLOCK), ctypes.c_void_p,
        wintypes.ULONG, ctypes.c_int,
    ]
    ntdll.NtSetInformationFile.restype = ctypes.c_long
    ntdll.RtlNtStatusToDosError.argtypes = [ctypes.c_long]
    ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG


class NativeProbeError(RuntimeError):
    pass


@dataclass(frozen=True)
class FileIdentity:
    volume_serial: int
    file_id: bytes


class Handle:
    def __init__(self, value: int):
        self.value = value

    def close(self) -> None:
        if self.value not in (None, 0, INVALID_HANDLE_VALUE if sys.platform == "win32" else -1):
            kernel32.CloseHandle(self.value)
            self.value = 0

    def __enter__(self) -> "Handle":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _win_error(message: str) -> NativeProbeError:
    return NativeProbeError(f"{message}: {ctypes.WinError(ctypes.get_last_error())}")


def _open_root(path: Path) -> Handle:
    handle = kernel32.CreateFileW(
        str(path), FILE_READ_ATTRIBUTES | FILE_LIST_DIRECTORY | SYNCHRONIZE,
        SHARE_ALL, None, OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise _win_error("CreateFileW(root) failed")
    result = Handle(handle)
    if is_reparse(result):
        result.close()
        raise NativeProbeError("root must not be a reparse point")
    return result


def _nt_open_relative(parent: Handle, name: str, *, directory: bool,
                      create: bool = False) -> Handle:
    buffer = ctypes.create_unicode_buffer(name)
    encoded_length = len(name.encode("utf-16-le"))
    unicode_name = UNICODE_STRING(encoded_length, encoded_length, ctypes.cast(buffer, wintypes.LPWSTR))
    attrs = OBJECT_ATTRIBUTES(
        ctypes.sizeof(OBJECT_ATTRIBUTES), parent.value, ctypes.pointer(unicode_name),
        OBJ_CASE_INSENSITIVE, None, None,
    )
    iosb = IO_STATUS_BLOCK()
    output = wintypes.HANDLE()
    access = FILE_READ_ATTRIBUTES | SYNCHRONIZE
    options = FILE_SYNCHRONOUS_IO_NONALERT | FILE_OPEN_REPARSE_POINT
    if directory:
        access |= FILE_LIST_DIRECTORY
        options |= FILE_DIRECTORY_FILE
    else:
        options |= FILE_NON_DIRECTORY_FILE
        access |= GENERIC_READ
        if create:
            access |= GENERIC_WRITE | DELETE
    status = ntdll.NtCreateFile(
        ctypes.byref(output), access, ctypes.byref(attrs), ctypes.byref(iosb),
        None, FILE_ATTRIBUTE_NORMAL, SHARE_ALL, FILE_CREATE if create else FILE_OPEN,
        options, None, 0,
    )
    if status < 0:
        code = ntdll.RtlNtStatusToDosError(status)
        raise NativeProbeError(f"NtCreateFile({name!r}) failed: WinError {code}")
    return Handle(output.value)


def is_reparse(handle: Handle) -> bool:
    info = FILE_ATTRIBUTE_TAG_INFO()
    if not kernel32.GetFileInformationByHandleEx(
        handle.value, FileAttributeTagInfo, ctypes.byref(info), ctypes.sizeof(info)
    ):
        raise _win_error("GetFileInformationByHandleEx(FileAttributeTagInfo) failed")
    return bool(info.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)


def identity(handle: Handle) -> FileIdentity:
    info = FILE_ID_INFO()
    if not kernel32.GetFileInformationByHandleEx(
        handle.value, FileIdInfo, ctypes.byref(info), ctypes.sizeof(info)
    ):
        raise _win_error("GetFileInformationByHandleEx(FileIdInfo) failed")
    return FileIdentity(info.VolumeSerialNumber, bytes(info.FileId.Identifier))


def final_path(handle: Handle) -> str:
    size = kernel32.GetFinalPathNameByHandleW(handle.value, None, 0, 0)
    if not size:
        raise _win_error("GetFinalPathNameByHandleW(size) failed")
    buffer = ctypes.create_unicode_buffer(size + 1)
    written = kernel32.GetFinalPathNameByHandleW(handle.value, buffer, len(buffer), 0)
    if not written or written >= len(buffer):
        raise _win_error("GetFinalPathNameByHandleW(path) failed")
    return buffer.value


def security_descriptor(path: Path) -> bytes:
    """Return owner/group/DACL metadata for replacement observations."""
    OWNER_SECURITY_INFORMATION = 0x00000001
    GROUP_SECURITY_INFORMATION = 0x00000002
    DACL_SECURITY_INFORMATION = 0x00000004
    requested = (
        OWNER_SECURITY_INFORMATION | GROUP_SECURITY_INFORMATION |
        DACL_SECURITY_INFORMATION
    )
    needed = wintypes.DWORD()
    advapi32.GetFileSecurityW(str(path), requested, None, 0, ctypes.byref(needed))
    if not needed.value:
        raise _win_error("GetFileSecurityW(size) failed")
    buffer = ctypes.create_string_buffer(needed.value)
    if not advapi32.GetFileSecurityW(
        str(path), requested, buffer, len(buffer), ctypes.byref(needed)
    ):
        raise _win_error("GetFileSecurityW(descriptor) failed")
    return buffer.raw[:needed.value]


def open_without_delete_share(path: Path) -> Handle:
    """Hold a file so replacement failure semantics can be measured."""
    handle = kernel32.CreateFileW(
        str(path), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, None,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise _win_error("CreateFileW(no-delete-share) failed")
    return Handle(handle)


def directory_flush_observation(path: Path) -> tuple[bool, int]:
    """Observe, without claiming, whether this filesystem accepts dir flush."""
    handle = kernel32.CreateFileW(
        str(path), GENERIC_READ, SHARE_ALL, None, OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise _win_error("CreateFileW(directory flush probe) failed")
    with Handle(handle) as opened:
        ctypes.set_last_error(0)
        accepted = bool(kernel32.FlushFileBuffers(opened.value))
        return accepted, 0 if accepted else ctypes.get_last_error()


def open_confined(root: Path, relative: str, *, directory: bool = False) -> Handle:
    parts = validate_relative_path(relative, windows=True)
    current = _open_root(root)
    try:
        for index, part in enumerate(parts):
            next_handle = _nt_open_relative(
                current, part, directory=(directory or index < len(parts) - 1)
            )
            if is_reparse(next_handle):
                next_handle.close()
                raise NativeProbeError("reparse point traversal is forbidden")
            current.close()
            current = next_handle
        return current
    except Exception:
        current.close()
        raise


def _write_all(handle: Handle, data: bytes) -> None:
    buffer = ctypes.create_string_buffer(data)
    written = wintypes.DWORD()
    if not kernel32.WriteFile(handle.value, buffer, len(data), ctypes.byref(written), None):
        raise _win_error("WriteFile failed")
    if written.value != len(data):
        raise NativeProbeError("short WriteFile")
    if not kernel32.FlushFileBuffers(handle.value):
        raise _win_error("FlushFileBuffers failed")


def read_all(handle: Handle) -> bytes:
    chunks: list[bytes] = []
    while True:
        buffer = ctypes.create_string_buffer(1024 * 1024)
        read = wintypes.DWORD()
        if not kernel32.ReadFile(
            handle.value, buffer, len(buffer), ctypes.byref(read), None
        ):
            raise _win_error("ReadFile failed")
        if not read.value:
            return b"".join(chunks)
        chunks.append(buffer.raw[:read.value])


def _rename_relative(handle: Handle, parent: Handle, name: str, *, replace: bool) -> None:
    class FILE_RENAME_INFO_BUFFER(ctypes.Structure):
        _fields_ = [
            ("ReplaceIfExists", wintypes.BOOLEAN),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * len(name)),
        ]

    info = FILE_RENAME_INFO_BUFFER()
    info.ReplaceIfExists = 1 if replace else 0
    info.RootDirectory = parent.value
    info.FileNameLength = len(name.encode("utf-16-le"))
    info.FileName = name
    # ctypes rounds Structure size up to pointer alignment. Windows expects the
    # variable-length record size, not that trailing ABI padding.
    record_size = FILE_RENAME_INFO_BUFFER.FileName.offset + info.FileNameLength
    iosb = IO_STATUS_BLOCK()
    status = ntdll.NtSetInformationFile(
        handle.value, ctypes.byref(iosb), ctypes.byref(info), record_size,
        FileRenameInformation,
    )
    if status < 0:
        code = ntdll.RtlNtStatusToDosError(status)
        raise NativeProbeError(
            f"NtSetInformationFile(FileRenameInformation) failed: WinError {code}"
        )


def _mark_delete(handle: Handle) -> None:
    class FILE_DISPOSITION_INFORMATION(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

    info = FILE_DISPOSITION_INFORMATION(1)
    iosb = IO_STATUS_BLOCK()
    status = ntdll.NtSetInformationFile(
        handle.value, ctypes.byref(iosb), ctypes.byref(info), ctypes.sizeof(info),
        FileDispositionInformation,
    )
    if status < 0:
        code = ntdll.RtlNtStatusToDosError(status)
        raise NativeProbeError(
            f"NtSetInformationFile(FileDispositionInformation) failed: WinError {code}"
        )


def publish_bytes(root: Path, relative: str, data: bytes, *, replace: bool) -> str:
    """Prototype handle-relative publish, deliberately not a Runtime API."""
    parts = validate_relative_path(relative, windows=True)
    if len(parts) < 2:
        raise PrototypePathError("prototype publish requires a child directory")
    parent_rel = "/".join(parts[:-1])
    target_name = parts[-1]
    with open_confined(root, parent_rel, directory=True) as parent:
        temp_name = f".pc-probe-{uuid4().hex}.tmp"
        with _nt_open_relative(parent, temp_name, directory=False, create=True) as temp:
            try:
                _write_all(temp, data)
                _rename_relative(temp, parent, target_name, replace=replace)
            except Exception:
                _mark_delete(temp)
                raise
        with _nt_open_relative(parent, target_name, directory=False) as result:
            if is_reparse(result):
                raise NativeProbeError("published target became a reparse point")
            result_path = final_path(result)
            result_identity = identity(result)
        with _open_root(root) as root_handle:
            root_path = final_path(root_handle).rstrip("\\").casefold() + "\\"
        if not result_path.casefold().startswith(root_path):
            raise NativeProbeError("published target escaped root")
        if not result_identity.file_id:
            raise NativeProbeError("missing final file identity")
    return hashlib.sha256(data).hexdigest()
