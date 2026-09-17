from __future__ import annotations

import ctypes
import errno
import hashlib
import os
from pathlib import Path
import platform
import stat as stat_module
import unicodedata
from uuid import uuid4

from .base import BackendError, NativePathBackend, PathStat, StagedWrite
from .common import validate_relative_path


class _PosixStage:
    def __init__(
        self,
        parent_fd: int,
        file_fd: int,
        temp_name: str,
        target_name: str,
        parent_parts: tuple[str, ...],
    ):
        self.parent_fd = parent_fd
        self.file_fd = file_fd
        self.temp_name = temp_name
        self.target_name = target_name
        self.parent_parts = parent_parts


def _linux_filesystem(fd: int) -> str:
    class StatFs(ctypes.Structure):
        _fields_ = [
            ("f_type", ctypes.c_long), ("f_bsize", ctypes.c_long),
            ("f_blocks", ctypes.c_ulong), ("f_bfree", ctypes.c_ulong),
            ("f_bavail", ctypes.c_ulong), ("f_files", ctypes.c_ulong),
            ("f_ffree", ctypes.c_ulong), ("f_fsid", ctypes.c_int * 2),
            ("f_namelen", ctypes.c_long), ("f_frsize", ctypes.c_long),
            ("f_flags", ctypes.c_long), ("f_spare", ctypes.c_long * 4),
        ]

    info = StatFs()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.fstatfs(fd, ctypes.byref(info)) != 0:
        code = ctypes.get_errno()
        raise BackendError("FILESYSTEM_QUERY", os.strerror(code))
    names = {0xEF53: "ext4"}
    return names.get(info.f_type & 0xFFFFFFFF, f"linux-magic-{info.f_type & 0xFFFFFFFF:x}")


def _darwin_filesystem(fd: int) -> str:
    class Fsid(ctypes.Structure):
        _fields_ = [("val", ctypes.c_int32 * 2)]

    class StatFs(ctypes.Structure):
        _fields_ = [
            ("f_bsize", ctypes.c_uint32), ("f_iosize", ctypes.c_int32),
            ("f_blocks", ctypes.c_uint64), ("f_bfree", ctypes.c_uint64),
            ("f_bavail", ctypes.c_uint64), ("f_files", ctypes.c_uint64),
            ("f_ffree", ctypes.c_uint64), ("f_fsid", Fsid),
            ("f_owner", ctypes.c_uint32), ("f_type", ctypes.c_uint32),
            ("f_flags", ctypes.c_uint32), ("f_fssubtype", ctypes.c_uint32),
            ("f_fstypename", ctypes.c_char * 16),
            ("f_mntonname", ctypes.c_char * 1024),
            ("f_mntfromname", ctypes.c_char * 1024),
            ("f_reserved", ctypes.c_uint32 * 8),
        ]

    info = StatFs()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.fstatfs(fd, ctypes.byref(info)) != 0:
        code = ctypes.get_errno()
        raise BackendError("FILESYSTEM_QUERY", os.strerror(code))
    return bytes(info.f_fstypename).split(b"\0", 1)[0].decode("ascii").casefold()


class PosixNativeBackend(NativePathBackend):
    QUALIFIED = frozenset({"ext4", "apfs"})

    def __init__(self, root: Path, *, require_qualified: bool = True):
        self.root = root.absolute()
        flags = (
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
            getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            self._root_fd = os.open(self.root, flags)
        except OSError as exc:
            raise BackendError("ROOT_OPEN", str(exc)) from exc
        root_stat = os.fstat(self._root_fd)
        if not stat_module.S_ISDIR(root_stat.st_mode):
            self.close()
            raise BackendError("ROOT_NOT_DIRECTORY", str(root))
        system = platform.system()
        self.filesystem = (
            _linux_filesystem(self._root_fd) if system == "Linux"
            else _darwin_filesystem(self._root_fd) if system == "Darwin"
            else "unsupported-posix"
        )
        self.root_identity = f"posix:{root_stat.st_dev:x}:{root_stat.st_ino:x}"
        self.durability_level = "file-and-parent-fsync"
        if require_qualified and self.filesystem not in self.QUALIFIED:
            self.close()
            raise BackendError("FILESYSTEM_UNQUALIFIED", self.filesystem)

    def close(self) -> None:
        fd = getattr(self, "_root_fd", -1)
        if fd >= 0:
            os.close(fd)
            self._root_fd = -1

    def _openat2(self, relative: str, flags: int) -> int:
        class OpenHow(ctypes.Structure):
            _fields_ = [
                ("flags", ctypes.c_ulonglong), ("mode", ctypes.c_ulonglong),
                ("resolve", ctypes.c_ulonglong),
            ]

        how = OpenHow(
            flags | getattr(os, "O_CLOEXEC", 0), 0,
            0x01 | 0x02 | 0x04 | 0x08,
        )
        libc = ctypes.CDLL(None, use_errno=True)
        fd = libc.syscall(
            437, self._root_fd, relative.encode(), ctypes.byref(how), ctypes.sizeof(how)
        )
        if fd < 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code), relative)
        return fd

    def _open_components(self, parts: tuple[str, ...], final_flags: int) -> int:
        current = os.dup(self._root_fd)
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
            return os.open(
                parts[-1], final_flags | getattr(os, "O_NOFOLLOW", 0) |
                getattr(os, "O_CLOEXEC", 0), dir_fd=current,
            )
        finally:
            os.close(current)

    def _open_read(self, relative: str) -> int:
        parts = validate_relative_path(relative, windows=False)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            if platform.system() == "Linux":
                try:
                    fd = self._openat2("/".join(parts), flags)
                except OSError as exc:
                    if exc.errno not in {errno.ENOSYS, errno.EINVAL}:
                        raise
                    fd = self._open_components(parts, flags)
            else:
                fd = self._open_components(parts, flags)
        except OSError as exc:
            raise BackendError("PATH_OPEN", str(exc)) from exc
        mode = os.fstat(fd).st_mode
        if not stat_module.S_ISREG(mode):
            os.close(fd)
            raise BackendError("NOT_REGULAR_FILE", relative)
        return fd

    def read_bytes(self, relative: str, *, max_bytes: int | None = None) -> bytes:
        fd = self._open_read(relative)
        chunks: list[bytes] = []
        total = 0
        try:
            while True:
                block = os.read(fd, 1024 * 1024)
                if not block:
                    return b"".join(chunks)
                total += len(block)
                if max_bytes is not None and total > max_bytes:
                    raise BackendError("READ_LIMIT", relative)
                chunks.append(block)
        finally:
            os.close(fd)

    def stat(self, relative: str) -> PathStat:
        fd = self._open_read(relative)
        try:
            info = os.fstat(fd)
            digest = hashlib.sha256()
            size = 0
            while True:
                block = os.read(fd, 1024 * 1024)
                if not block:
                    break
                size += len(block)
                digest.update(block)
        finally:
            os.close(fd)
        return PathStat(
            relative, size, digest.hexdigest(),
            f"posix:{info.st_dev:x}:{info.st_ino:x}",
        )

    def _open_parent(self, parts: tuple[str, ...]) -> int:
        current = os.dup(self._root_fd)
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
            return current
        except Exception:
            os.close(current)
            raise

    @staticmethod
    def _reject_collision(parent_fd: int, target: str) -> None:
        key = unicodedata.normalize("NFC", target).casefold()
        for existing in os.listdir(parent_fd):
            if existing != target and unicodedata.normalize("NFC", existing).casefold() == key:
                raise BackendError("PORTABLE_NAME_COLLISION", target)

    def stage_bytes(self, relative: str, content: bytes) -> StagedWrite:
        parts = validate_relative_path(relative, windows=False)
        parent_fd = self._open_parent(parts)
        file_fd = -1
        temp_name = f".pc-stage-{uuid4().hex}.tmp"
        try:
            self._reject_collision(parent_fd, parts[-1])
            file_fd = os.open(
                temp_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) |
                getattr(os, "O_CLOEXEC", 0),
                0o600, dir_fd=parent_fd,
            )
            view = memoryview(content)
            while view:
                view = view[os.write(file_fd, view):]
            os.fsync(file_fd)
            return StagedWrite(
                relative, hashlib.sha256(content).hexdigest(),
                _PosixStage(
                    parent_fd, file_fd, temp_name, parts[-1], parts[:-1]
                ),
            )
        except Exception:
            if file_fd >= 0:
                os.close(file_fd)
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            os.close(parent_fd)
            raise

    def publish(self, staged: StagedWrite, *, replace: bool) -> PathStat:
        data = staged.platform_data
        if not isinstance(data, _PosixStage) or staged.published:
            raise BackendError("STAGE_STATE", staged.relative_path)
        try:
            current_parent = self._open_parent(
                data.parent_parts + (data.target_name,)
            )
        except OSError as exc:
            raise BackendError(
                "PARENT_IDENTITY_CHANGED", staged.relative_path
            ) from exc
        try:
            opened = os.fstat(data.parent_fd)
            current = os.fstat(current_parent)
            if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
                raise BackendError(
                    "PARENT_IDENTITY_CHANGED", staged.relative_path
                )
        finally:
            os.close(current_parent)
        if replace:
            os.replace(
                data.temp_name, data.target_name,
                src_dir_fd=data.parent_fd, dst_dir_fd=data.parent_fd,
            )
        else:
            os.link(
                data.temp_name, data.target_name,
                src_dir_fd=data.parent_fd, dst_dir_fd=data.parent_fd,
                follow_symlinks=False,
            )
            os.unlink(data.temp_name, dir_fd=data.parent_fd)
        os.fsync(data.parent_fd)
        os.close(data.file_fd)
        os.close(data.parent_fd)
        data.file_fd = -1
        data.parent_fd = -1
        staged.published = True
        return self.stat(staged.relative_path)

    def discard(self, staged: StagedWrite) -> None:
        data = staged.platform_data
        if not isinstance(data, _PosixStage) or staged.published:
            return
        if data.file_fd >= 0:
            os.close(data.file_fd)
            data.file_fd = -1
        try:
            os.unlink(data.temp_name, dir_fd=data.parent_fd)
        except FileNotFoundError:
            pass
        if data.parent_fd >= 0:
            os.close(data.parent_fd)
            data.parent_fd = -1
