from __future__ import annotations

from pathlib import PurePosixPath
import re
import unicodedata


class PrototypePathError(ValueError):
    pass


WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
    "COM¹", "COM²", "COM³", "LPT¹", "LPT²", "LPT³",
}


def validate_relative_path(value: str, *, windows: bool) -> tuple[str, ...]:
    """Validate the portable relative-path grammar used by the probes.

    This is lexical validation only.  It must always be followed by native,
    handle-based filesystem resolution.
    """
    if not value or value != value.strip():
        raise PrototypePathError("path must be non-empty and trimmed")
    if "\x00" in value or any(ord(ch) < 32 for ch in value):
        raise PrototypePathError("control characters are forbidden")
    if "\\" in value:
        if not windows:
            raise PrototypePathError("backslash is not portable")
        value = value.replace("\\", "/")
    if value.startswith(("/", "//")):
        raise PrototypePathError("absolute or UNC path is forbidden")
    if windows and (":" in value or value.startswith(("\\\\?\\", "\\\\.\\"))):
        raise PrototypePathError("drive, device, extended, and ADS paths are forbidden")
    if re.match(r"^[A-Za-z]:", value):
        raise PrototypePathError("drive path is forbidden")

    path = PurePosixPath(value)
    parts = value.split("/")
    if path.is_absolute() or any(part in {"", ".", ".."} for part in parts):
        raise PrototypePathError("empty, dot, and traversal components are forbidden")

    normalized: list[str] = []
    for part in parts:
        if windows:
            if part.endswith((" ", ".")):
                raise PrototypePathError("Windows trailing space or dot is forbidden")
            if any(ch in '<>:"/\\|?*' for ch in part):
                raise PrototypePathError("Windows reserved character is forbidden")
            stem = part.split(".", 1)[0].upper()
            if stem in WINDOWS_RESERVED:
                raise PrototypePathError("Windows device name is forbidden")
        # NFC is the portable spelling.  Native lookup still detects actual
        # filesystem collisions rather than trusting Unicode strings alone.
        nfc = unicodedata.normalize("NFC", part)
        if nfc != part:
            raise PrototypePathError("path must use NFC spelling")
        normalized.append(part)
    return tuple(normalized)

