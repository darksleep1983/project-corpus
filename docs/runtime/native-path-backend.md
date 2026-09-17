# Native path backend

Status: production component; platform qualification is test-gated

The Runtime uses an explicit native path backend for all controlled reads and
for the filesystem primitives that a later transaction layer will compose.
Portable `Path.resolve()` checks are not a security boundary.

## Contract

The backend:

- opens a previously owner-pinned root and records its filesystem identity;
- accepts only normalized relative managed paths;
- rejects traversal, absolute paths, device syntax, ADS syntax and portable
  name ambiguity before mutation;
- opens every path component relative to an already-open directory;
- rejects symlinks, junctions, reparse points and non-regular final objects;
- stages bytes in the target directory, flushes the staged file and publishes
  by same-directory native rename/link semantics;
- supports create-if-absent separately from replacement;
- returns content hash and file identity from native handles;
- fails managed mutation closed on a filesystem not explicitly qualified.

The backend does **not** grant authority, select a policy, implement optimistic
concurrency, create backups, write a journal or emit audit receipts. Those are
transaction-layer responsibilities. Calling this low-level component directly
is therefore not a controlled CLI/MCP mutation.

## Platform implementations

- Windows uses handle-relative NT opens and renames, rejects reparse points,
  checks final handle paths and supports only qualified local NTFS. Open
  directory handles prevent the tested parent move during publication.
- Linux uses restrictive `openat2` resolution when available and a
  descriptor-relative no-follow walk as the tested fallback. It supports only
  qualified local ext4.
- macOS uses a descriptor-relative no-follow walk and supports only qualified
  local APFS.

POSIX publication reopens the parent from the pinned root and compares native
directory identity immediately before publish. A changed or detached parent
fails closed. The Runtime does not claim protection from another process with
the same OS account deliberately and continuously rearranging directory
topology; that actor already has the project's operating-system authority.
Static malicious repository paths and symlink substitutions remain in scope.

## Durability boundary

On ext4 and APFS, staged file data and the opened parent directory are fsynced.
On NTFS, staged file data is flushed and namespace replacement is atomic in the
tested cases; directory-flush-equivalent sudden-power-loss durability is not
claimed. See [platform guarantees](../security/platform-guarantees.md).

Production guarantee activation requires the backend suite to pass on the
corresponding operating system and filesystem. Prototype results alone do not
activate this component's guarantees.
