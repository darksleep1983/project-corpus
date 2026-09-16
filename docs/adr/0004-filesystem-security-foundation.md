# ADR 0004: Native path backend is required

Status: accepted; P1-P8 passed for NTFS, ext4 and APFS

## Decision

Security-sensitive filesystem operations require platform-native, handle-based
path resolution and publication. `pathlib.resolve()` and ordinary path-based
open/replace sequences are not a sufficient confinement boundary.

Python may remain the orchestration language, but the path backend must call the
relevant native primitives. The prototype phase must decide whether maintained
Python bindings are adequate or a compiled helper or extension is required.

The prototype gates selected Python orchestration with explicit native bindings:
Windows NT handles through `ctypes`, Linux `openat2` plus a descriptor-walk
fallback, and a descriptor walk on macOS. This is not a portable Python-only
path implementation.

Production implementation is now permitted, but it cannot inherit prototype
claims automatically. The production backend and transaction engine must pass
their own negative, failure, concurrency and recovery suites.

Unsupported or network filesystems fail closed for managed mutations by default.
