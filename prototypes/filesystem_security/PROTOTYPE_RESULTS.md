# Filesystem prototype results

Status: pre-production evidence record

This record describes the evidence used to cross the filesystem prototype
boundary. It does not turn the code in this directory into a supported Runtime
API.

## Backend decision

Result: `NATIVE_PATH_BACKEND_REQUIRED`.

Selected implementation technology for V2.0: Python orchestration with a small,
explicit native binding layer:

- Windows: `ctypes` bindings to handle-relative NT open, rename, disposition,
  identity and Win32 metadata/flush APIs;
- Linux: `openat2` with restrictive resolution flags, with a descriptor-relative
  component-walk fallback;
- macOS: descriptor-relative component walk with no-follow behavior;
- all platforms: native inter-process file locking plus required expected hashes
  for managed writers.

A compiled helper is not currently required by measured evidence. Portable
Python path APIs alone are insufficient. Missing native APIs or an unqualified
filesystem must fail managed mutation closed.

## Gate matrix

| Gate | Windows local NTFS | Linux CI filesystem | macOS CI filesystem |
|---|---|---|---|
| P1 Windows confinement | PASS | N/A | N/A |
| P2 Windows publish | PASS with documented limitations | N/A | N/A |
| P3 Linux confinement | N/A | PENDING | N/A |
| P4 macOS confinement | N/A | N/A | PENDING |
| P5 durability semantics | PASS, scoped below | PENDING | PENDING |
| P6 managed-writer concurrency | PASS | PENDING | PENDING |
| P7 recovery state model | PASS | PENDING | PENDING |
| P8 backend choice | PASS, conditional on P3/P4 evidence | PENDING | PENDING |

Production mutation implementation remains blocked until the pending cells have
passed on the branch CI matrix.

## Windows evidence

Tested locally on the `D:` NTFS volume. The tests establish only the following:

- drive, UNC, device, extended, ADS, traversal, reserved-name and ambiguous
  trailing-character inputs are rejected lexically;
- every managed component is opened relative to an already-open directory
  handle, with reparse-point following disabled;
- directory junction and final symlink fixtures are rejected;
- case-variant create collides rather than creating a second managed object;
- final path and file identity are read from the opened handle;
- publish flushes the staged file, then renames by handle relative to the opened
  parent;
- replace changes file identity;
- a named stream attached to the old target does not survive replacement;
- the default inherited owner/group/DACL descriptor was equal before and after
  the tested replacement;
- a target held without delete sharing causes publish to fail, leaves the old
  bytes intact and removes the staged object;
- two managed writers starting from the same expected hash serialize; exactly
  one publishes and the other returns stale.

The prototype does **not** establish preservation of a custom ACL. Replacement
publishes the staged object, so production must either set and verify the
intended security descriptor or reject targets whose metadata policy cannot be
preserved. It likewise does not preserve old alternate data streams; V2 managed
documents forbid ADS.

`FlushFileBuffers` succeeded for staged files. A directory-handle flush on the
tested NTFS volume returned access denied. Consequently V2 may claim atomic
namespace replacement on qualified local NTFS, but not POSIX-equivalent durable
directory commit after sudden power loss.

## POSIX evidence requirements

The CI tests must prove both Linux resolution paths: restrictive `openat2` and a
forced descriptor-walk fallback. Adversarial tests repeatedly exchange an
in-root directory with a symlink to an outside directory and assert that a
successful read can return only in-root bytes.

On macOS, the descriptor walk must reject the same escape and the fixture suite
must exercise case and composed/decomposed Unicode collisions. V2 uses NFC
portable names and rejects collisions by NFC-plus-casefold key even on a
case-sensitive filesystem.

POSIX publication flushes the staged file before same-directory publication and
then fsyncs the opened parent directory. A PASS reports only the actual CI
filesystem; it is not evidence for NFS, SMB, FUSE or other mounts.

## Recovery evidence

The prototype transaction state model injects a crash after each recorded phase:
`STAGED`, `BACKED_UP`, `PUBLISHED`, `VERIFIED` and `AUDITED`.

- pre-publication phases deterministically roll back to old content;
- post-publication phases deterministically finish verification/audit;
- unexpected target content returns `NEEDS_OWNER` without overwriting it.

The production journal must reproduce these semantics through the confined
backend. This model test alone is not a production crash-durability claim.
