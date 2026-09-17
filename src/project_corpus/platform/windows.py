from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
from pathlib import Path
import unicodedata
from uuid import uuid4

from .base import BackendError, NativePathBackend, PathStat, StagedWrite
from .common import validate_relative_path


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll")

INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
SHARE_ALL = 0x1 | 0x2 | 0x4
DUPLICATE_SAME_ACCESS = 0x2
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
FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
FILE_ID_INFO_CLASS = 18
FILE_NAMES_INFORMATION_CLASS = 12
FILE_RENAME_INFORMATION = 10
FILE_DISPOSITION_INFORMATION = 13
STATUS_NO_MORE_FILES = 0x80000006


class UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]


class OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.ULONG), ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.POINTER(UNICODE_STRING)),
        ("Attributes", wintypes.ULONG), ("SecurityDescriptor", wintypes.LPVOID),
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
kernel32.ReadFile.argtypes = [
    wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
]
kernel32.ReadFile.restype = wintypes.BOOL
kernel32.WriteFile.argtypes = [
    wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
]
kernel32.WriteFile.restype = wintypes.BOOL
kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
kernel32.FlushFileBuffers.restype = wintypes.BOOL
kernel32.GetFileSizeEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_longlong)]
kernel32.GetFileSizeEx.restype = wintypes.BOOL
kernel32.GetVolumeInformationByHandleW.argtypes = [
    wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD,
]
kernel32.GetVolumeInformationByHandleW.restype = wintypes.BOOL
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.DuplicateHandle.argtypes = [
    wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE,
    ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, wintypes.BOOL,
    wintypes.DWORD,
]
kernel32.DuplicateHandle.restype = wintypes.BOOL
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
ntdll.NtQueryDirectoryFile.argtypes = [
    wintypes.HANDLE, wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.POINTER(IO_STATUS_BLOCK), ctypes.c_void_p, wintypes.ULONG,
    ctypes.c_int, wintypes.BOOLEAN, ctypes.POINTER(UNICODE_STRING),
    wintypes.BOOLEAN,
]
ntdll.NtQueryDirectoryFile.restype = ctypes.c_long
ntdll.RtlNtStatusToDosError.argtypes = [ctypes.c_long]
ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG


class _Handle:
    def __init__(self, value: int):
        self.value = value

    def close(self) -> None:
        if self.value not in (None, 0, INVALID_HANDLE_VALUE):
            kernel32.CloseHandle(self.value)
            self.value = 0


class _WindowsStage:
    def __init__(self, parent: _Handle, file: _Handle, target_name: str):
        self.parent = parent
        self.file = file
        self.target_name = target_name


def _last_error(code: str) -> BackendError:
    return BackendError(code, str(ctypes.WinError(ctypes.get_last_error())))


def _nt_error(code: str, status: int) -> BackendError:
    winerror = ntdll.RtlNtStatusToDosError(status)
    return BackendError(code, f"WinError {winerror}")


def _is_reparse(handle: _Handle) -> bool:
    info = FILE_ATTRIBUTE_TAG_INFO()
    if not kernel32.GetFileInformationByHandleEx(
        handle.value, FILE_ATTRIBUTE_TAG_INFO_CLASS,
        ctypes.byref(info), ctypes.sizeof(info),
    ):
        raise _last_error("REPARSE_QUERY")
    return bool(info.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)


def _identity(handle: _Handle) -> str:
    info = FILE_ID_INFO()
    if not kernel32.GetFileInformationByHandleEx(
        handle.value, FILE_ID_INFO_CLASS, ctypes.byref(info), ctypes.sizeof(info)
    ):
        raise _last_error("IDENTITY_QUERY")
    return f"windows:{info.VolumeSerialNumber:x}:{bytes(info.FileId.Identifier).hex()}"


def _final_path(handle: _Handle) -> str:
    size = kernel32.GetFinalPathNameByHandleW(handle.value, None, 0, 0)
    if not size:
        raise _last_error("FINAL_PATH_QUERY")
    buffer = ctypes.create_unicode_buffer(size + 1)
    written = kernel32.GetFinalPathNameByHandleW(handle.value, buffer, len(buffer), 0)
    if not written or written >= len(buffer):
        raise _last_error("FINAL_PATH_QUERY")
    return buffer.value


def _duplicate(handle: _Handle) -> _Handle:
    process = kernel32.GetCurrentProcess()
    output = wintypes.HANDLE()
    if not kernel32.DuplicateHandle(
        process, handle.value, process, ctypes.byref(output), 0, False,
        DUPLICATE_SAME_ACCESS,
    ):
        raise _last_error("HANDLE_DUPLICATE")
    return _Handle(output.value)


def _nt_open(parent: _Handle, name: str, *, directory: bool, create: bool = False) -> _Handle:
    buffer = ctypes.create_unicode_buffer(name)
    length = len(name.encode("utf-16-le"))
    unicode_name = UNICODE_STRING(length, length, ctypes.cast(buffer, wintypes.LPWSTR))
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
        access |= GENERIC_READ
        options |= FILE_NON_DIRECTORY_FILE
        if create:
            access |= GENERIC_WRITE | DELETE
    status = ntdll.NtCreateFile(
        ctypes.byref(output), access, ctypes.byref(attrs), ctypes.byref(iosb),
        None, FILE_ATTRIBUTE_NORMAL, SHARE_ALL, FILE_CREATE if create else FILE_OPEN,
        options, None, 0,
    )
    if status < 0:
        raise _nt_error("PATH_OPEN", status)
    result = _Handle(output.value)
    if _is_reparse(result):
        result.close()
        raise BackendError("REPARSE_FORBIDDEN", name)
    return result


def _read_all(handle: _Handle, max_bytes: int | None = None) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        buffer = ctypes.create_string_buffer(1024 * 1024)
        read = wintypes.DWORD()
        if not kernel32.ReadFile(
            handle.value, buffer, len(buffer), ctypes.byref(read), None
        ):
            raise _last_error("READ")
        if not read.value:
            return b"".join(chunks)
        total += read.value
        if max_bytes is not None and total > max_bytes:
            raise BackendError("READ_LIMIT", str(max_bytes))
        chunks.append(buffer.raw[:read.value])


def _write_all(handle: _Handle, content: bytes) -> None:
    view = memoryview(content)
    while view:
        written = wintypes.DWORD()
        buffer = (ctypes.c_char * len(view)).from_buffer_copy(view)
        if not kernel32.WriteFile(
            handle.value, buffer, len(view), ctypes.byref(written), None
        ):
            raise _last_error("WRITE")
        if not written.value:
            raise BackendError("WRITE", "zero-length progress")
        view = view[written.value:]
    if not kernel32.FlushFileBuffers(handle.value):
        raise _last_error("FILE_FLUSH")


def _list_names(directory: _Handle) -> tuple[str, ...]:
    result: list[str] = []
    restart = True
    while True:
        buffer = ctypes.create_string_buffer(64 * 1024)
        iosb = IO_STATUS_BLOCK()
        status = ntdll.NtQueryDirectoryFile(
            directory.value, None, None, None, ctypes.byref(iosb), buffer,
            len(buffer), FILE_NAMES_INFORMATION_CLASS, False, None, restart,
        )
        restart = False
        unsigned = status & 0xFFFFFFFF
        if unsigned == STATUS_NO_MORE_FILES:
            break
        if status < 0:
            raise _nt_error("DIRECTORY_ENUMERATION", status)
        offset = 0
        limit = iosb.Information
        while offset + 12 <= limit:
            next_offset = int.from_bytes(buffer.raw[offset:offset + 4], "little")
            name_length = int.from_bytes(buffer.raw[offset + 8:offset + 12], "little")
            name = buffer.raw[offset + 12:offset + 12 + name_length].decode("utf-16-le")
            result.append(name)
            if not next_offset:
                break
            offset += next_offset
    return tuple(result)


def _rename(handle: _Handle, parent: _Handle, name: str, replace: bool) -> None:
    class RenameInfo(ctypes.Structure):
        _fields_ = [
            ("ReplaceIfExists", wintypes.BOOLEAN), ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * len(name)),
        ]

    info = RenameInfo()
    info.ReplaceIfExists = 1 if replace else 0
    info.RootDirectory = parent.value
    info.FileNameLength = len(name.encode("utf-16-le"))
    info.FileName = name
    size = RenameInfo.FileName.offset + info.FileNameLength
    iosb = IO_STATUS_BLOCK()
    status = ntdll.NtSetInformationFile(
        handle.value, ctypes.byref(iosb), ctypes.byref(info), size,
        FILE_RENAME_INFORMATION,
    )
    if status < 0:
        raise _nt_error("PUBLISH", status)


def _mark_delete(handle: _Handle) -> None:
    class DispositionInfo(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

    info = DispositionInfo(1)
    iosb = IO_STATUS_BLOCK()
    status = ntdll.NtSetInformationFile(
        handle.value, ctypes.byref(iosb), ctypes.byref(info), ctypes.sizeof(info),
        FILE_DISPOSITION_INFORMATION,
    )
    if status < 0:
        raise _nt_error("STAGE_CLEANUP", status)


class WindowsNativeBackend(NativePathBackend):
    QUALIFIED = frozenset({"ntfs"})

    def __init__(self, root: Path, *, require_qualified: bool = True):
        self.root = root.absolute()
        value = kernel32.CreateFileW(
            str(self.root), FILE_READ_ATTRIBUTES | FILE_LIST_DIRECTORY | SYNCHRONIZE,
            SHARE_ALL, None, OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None,
        )
        if value == INVALID_HANDLE_VALUE:
            raise _last_error("ROOT_OPEN")
        self._root = _Handle(value)
        if _is_reparse(self._root):
            self.close()
            raise BackendError("ROOT_REPARSE_FORBIDDEN", str(root))
        fs_name = ctypes.create_unicode_buffer(64)
        serial = wintypes.DWORD()
        max_component = wintypes.DWORD()
        flags = wintypes.DWORD()
        if not kernel32.GetVolumeInformationByHandleW(
            self._root.value, None, 0, ctypes.byref(serial),
            ctypes.byref(max_component), ctypes.byref(flags), fs_name, len(fs_name),
        ):
            self.close()
            raise _last_error("FILESYSTEM_QUERY")
        self.filesystem = fs_name.value.casefold()
        self.root_identity = _identity(self._root)
        self._root_final = _final_path(self._root).rstrip("\\")
        self.durability_level = "file-flush-atomic-namespace-no-directory-flush"
        if require_qualified and self.filesystem not in self.QUALIFIED:
            self.close()
            raise BackendError("FILESYSTEM_UNQUALIFIED", self.filesystem)

    def close(self) -> None:
        root = getattr(self, "_root", None)
        if root is not None:
            root.close()

    def _open(self, relative: str, *, directory: bool = False) -> _Handle:
        parts = validate_relative_path(relative, windows=True)
        current = _Handle(self._root.value)
        owns_current = False
        try:
            for index, part in enumerate(parts):
                next_handle = _nt_open(
                    current, part, directory=directory or index < len(parts) - 1
                )
                if owns_current:
                    current.close()
                current = next_handle
                owns_current = True
            return current
        except Exception:
            if owns_current:
                current.close()
            raise

    def _verify_final(self, handle: _Handle) -> None:
        actual = _final_path(handle).rstrip("\\").casefold()
        root = self._root_final.casefold()
        if actual != root and not actual.startswith(root + "\\"):
            raise BackendError("ROOT_ESCAPE", "final handle path is outside pinned root")

    def read_bytes(self, relative: str, *, max_bytes: int | None = None) -> bytes:
        handle = self._open(relative)
        try:
            self._verify_final(handle)
            return _read_all(handle, max_bytes)
        finally:
            handle.close()

    def stat(self, relative: str) -> PathStat:
        handle = self._open(relative)
        try:
            self._verify_final(handle)
            content = _read_all(handle)
            size = ctypes.c_longlong()
            if not kernel32.GetFileSizeEx(handle.value, ctypes.byref(size)):
                raise _last_error("SIZE_QUERY")
            return PathStat(
                relative, size.value, hashlib.sha256(content).hexdigest(),
                _identity(handle),
            )
        finally:
            handle.close()

    def stage_bytes(self, relative: str, content: bytes) -> StagedWrite:
        parts = validate_relative_path(relative, windows=True)
        parent = (
            self._open("/".join(parts[:-1]), directory=True)
            if len(parts) > 1 else _duplicate(self._root)
        )
        try:
            key = unicodedata.normalize("NFC", parts[-1]).casefold()
            for existing in _list_names(parent):
                if existing != parts[-1] and unicodedata.normalize("NFC", existing).casefold() == key:
                    raise BackendError("PORTABLE_NAME_COLLISION", parts[-1])
            temp = _nt_open(parent, f".pc-stage-{uuid4().hex}.tmp", directory=False, create=True)
            try:
                _write_all(temp, content)
                return StagedWrite(
                    relative, hashlib.sha256(content).hexdigest(),
                    _WindowsStage(parent, temp, parts[-1]),
                )
            except Exception:
                _mark_delete(temp)
                temp.close()
                raise
        except Exception:
            parent.close()
            raise

    def publish(self, staged: StagedWrite, *, replace: bool) -> PathStat:
        data = staged.platform_data
        if not isinstance(data, _WindowsStage) or staged.published:
            raise BackendError("STAGE_STATE", staged.relative_path)
        self._verify_final(data.parent)
        _rename(data.file, data.parent, data.target_name, replace)
        data.file.close()
        data.parent.close()
        staged.published = True
        return self.stat(staged.relative_path)

    def discard(self, staged: StagedWrite) -> None:
        data = staged.platform_data
        if not isinstance(data, _WindowsStage) or staged.published:
            return
        try:
            _mark_delete(data.file)
        finally:
            data.file.close()
            data.parent.close()
