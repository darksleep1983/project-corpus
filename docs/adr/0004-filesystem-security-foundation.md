# ADR 0004: Native path backend is required

Status: accepted architecture; production backend blocked on prototype evidence

## Decision

Security-sensitive filesystem operations require platform-native, handle-based
path resolution and publication. `pathlib.resolve()` and ordinary path-based
open/replace sequences are not a sufficient confinement boundary.

Python may remain the orchestration language, but the path backend must call the
relevant native primitives. The prototype phase must decide whether maintained
Python bindings are adequate or a compiled helper or extension is required.

Production mutations remain prohibited until the Windows, Linux, and macOS
prototype gates, durability analysis, concurrency tests, recovery tests, and
backend-choice gate pass.

Unsupported or network filesystems fail closed for managed mutations by default.

