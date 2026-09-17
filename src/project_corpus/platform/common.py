from __future__ import annotations

from pathlib import PurePosixPath
import re
import unicodedata


class PathValidationError(ValueError):
    pass


WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
    "COM¹", "COM²", "COM³", "LPT¹", "LPT²", "LPT³",
}


def validate_relative_path(value: str, *, windows: bool) -> tuple[str, ...]:
    if not value or value != value.strip():
        raise PathValidationError("path must be non-empty and trimmed")
    if "\x00" in value or any(ord(char) < 32 for char in value):
        raise PathValidationError("control characters are forbidden")
    if "\\" in value:
        if not windows:
            raise PathValidationError("backslash is not portable")
        value = value.replace("\\", "/")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise PathValidationError("absolute, drive, UNC or device path is forbidden")
    if windows and ":" in value:
        raise PathValidationError("drive and ADS syntax is forbidden")
    parts = value.split("/")
    if PurePosixPath(value).is_absolute() or any(
        part in {"", ".", ".."} for part in parts
    ):
        raise PathValidationError("empty, dot and traversal components are forbidden")
    for part in parts:
        if unicodedata.normalize("NFC", part) != part:
            raise PathValidationError("path must use NFC spelling")
        if windows:
            if part.endswith((" ", ".")):
                raise PathValidationError("trailing space or dot is forbidden")
            if any(char in '<>:"/\\|?*' for char in part):
                raise PathValidationError("reserved character is forbidden")
            if part.split(".", 1)[0].upper() in WINDOWS_RESERVED:
                raise PathValidationError("reserved device name is forbidden")
    return tuple(parts)
