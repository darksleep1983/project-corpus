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

| Gate | Windows NTFS | Ubuntu ext4 | macOS APFS |
|---|---|---|---|
| P1 Windows confinement | PASS | N/A | N/A |
| P2 Windows publish | PASS with documented limitations | N/A | N/A |
| P3 Linux confinement | N/A | PASS | N/A |
| P4 macOS confinement | N/A | N/A | PASS |
| P5 durability semantics | PASS, scoped below | PASS | PASS |
| P6 managed-writer concurrency | PASS | PASS | PASS |
| P7 recovery state model | PASS | PASS | PASS |
| P8 backend choice | PASS | PASS | PASS |

P1-P8 are closed for the named platform/filesystem combinations. This permits
production implementation to begin; that implementation must independently pass
the same and stronger tests before it can claim the guarantee level.

## Windows evidence

Tested locally on the `D:` NTFS volume and on GitHub-hosted Windows NTFS. The
tests establish only the following:

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

GitHub-hosted Ubuntu ext4 passed both Linux resolution paths: restrictive
`openat2` and a forced descriptor-walk fallback. Adversarial tests repeatedly exchange an
in-root directory with a symlink to an outside directory and assert that a
successful read can return only in-root bytes.

GitHub-hosted macOS 26.6.2 APFS passed the descriptor walk, the same escape test,
and case plus composed/decomposed Unicode collision fixtures. V2 uses NFC
portable names and rejects collisions by NFC-plus-casefold key even on a
case-sensitive filesystem.

POSIX publication flushes the staged file before same-directory publication and
then fsyncs the opened parent directory. A PASS reports only the actual CI
filesystem; it is not evidence for NFS, SMB, FUSE or other mounts.

Cross-platform evidence: GitHub Actions run `35121332371`, six successful jobs
covering Python 3.11 and 3.12 on each platform.

## Recovery evidence

The prototype transaction state model injects a crash after each recorded phase:
`STAGED`, `BACKED_UP`, `PUBLISHED`, `VERIFIED` and `AUDITED`.

- pre-publication phases deterministically roll back to old content;
- post-publication phases deterministically finish verification/audit;
- unexpected target content returns `NEEDS_OWNER` without overwriting it.

The production journal must reproduce these semantics through the confined
backend. This model test alone is not a production crash-durability claim.
