# V2 guarantee levels and platform matrix

Status: normative Runtime guarantee contract

The word "safe" is intentionally not used as a single undifferentiated claim.
Runtime reports a mode and a guarantee level.

## Interaction levels

### Markdown/manual mode: protocol-readable

- The Protocol, canonical roles and conflict rules are available without
  installation.
- No filesystem confinement, policy enforcement, expected-hash check,
  transaction, audit or recovery guarantee is provided by Project Corpus.
- The human operator owns validation and conflict resolution.

### Direct-folder mode: observable, not enforced

- A client may read or edit project files using its own filesystem access.
- Runtime can later detect schema errors, hash drift and policy inconsistency.
- Runtime cannot prevent an out-of-band editor from bypassing project policy,
  racing a managed writer or partially writing a file.
- Direct-folder access never inherits the controlled CLI/MCP guarantee level.

### Controlled CLI: runtime-enforced

After the production engine passes its conformance suite, a supported local
filesystem receives:

- authority bounded by runtime hard limits, external owner trust grant, project
  policy and the command's requested capability subset;
- native handle/descriptor-relative root confinement;
- deny-by-default path and object-type checks;
- expected-hash conflict rejection and managed-writer serialization;
- journaled publication, full readback, hash verification, audit and deterministic
  recovery.

These guarantees cover cooperating managed writers. An out-of-band writer is
detected where identity/hash checks observe it; distributed serializability is
not claimed.

### Controlled stdio MCP: runtime-enforced through an adapter

- Uses the same core, policy evaluator and transaction engine as controlled CLI.
- The MCP client capability subset can only narrow effective authority.
- Project content and MCP arguments cannot raise the capability ceiling.
- MCP transport adds no filesystem authority and cannot mutate owner trust.
- Initial V2 supports local stdio only; HTTP/remote MCP is outside scope.

### Unsupported or network filesystem: mutation-unqualified

- Read-only inspection and validation may be available with an explicit warning.
- Managed mutations fail closed unless that exact filesystem class is separately
  qualified.
- SMB, NFS, FUSE, removable media and unknown filesystem types have no V2.0
  atomicity, locking or durability claim.

## Qualified platform/filesystem combinations

| Platform/filesystem | Confinement | Publication | Durability claim |
|---|---|---|---|
| Windows local NTFS | Handle-relative NT open; reparse points rejected; final handle identity/path checked | Same-directory handle-relative rename; expected-hash serialization; full readback | Staged file flush is tested. Atomic namespace replacement is claimed. Directory-flush/power-loss durability is not claimed. |
| Linux local ext4 | `openat2` restrictive resolution, with tested descriptor-walk fallback | Same-directory replace or create-if-absent; expected-hash serialization; full readback | Staged file and opened parent directory fsync complete in tests; hardware/power-loss behavior beyond OS contracts is not claimed. |
| macOS local APFS | Descriptor-relative component walk with `O_NOFOLLOW`; portable case/Unicode collision rejection | Same-directory replace or create-if-absent; expected-hash serialization; full readback | Staged file and opened parent directory fsync complete in tests; hardware/power-loss behavior beyond OS contracts is not claimed. |

Filesystem qualification is exact. For example, successful Windows NTFS tests do
not qualify exFAT or SMB, and successful Linux ext4 tests do not qualify NFS.

## Replacement metadata

On tested NTFS, replacement creates a new file identity, removes alternate data
streams attached to the old target and retained an equal default inherited
owner/group/DACL descriptor. Custom ACL preservation was not proven. The
production backend therefore compares owner/group/DACL before replacement and
rejects a non-equivalent descriptor rather than silently discarding it.

On POSIX, the production backend preserves ordinary mode bits and requires
owner, group, ACL and extended attributes to match the staged object's inherited
metadata. Special mode bits and non-equivalent custom metadata fail closed.

V2 managed-document paths forbid ADS. Audit receipts must record the active
guarantee level and filesystem qualification without recording secret content.

## Evidence

- Prototype implementation and adversarial fixtures live under
  `prototypes/filesystem_security/`.
- GitHub Actions run `35121332371` passed all six OS/Python jobs and recorded
  NTFS, ext4 and APFS as the backing filesystems.
- GitHub Actions run `35180605924` passed the production native path backend
  suite in all six OS/Python jobs. This qualifies the confinement/publication
  primitive, not the transaction engine.
- Controlled mutation guarantees activate only after the production
  transaction, concurrency, recovery, policy and audit suites pass; prototype
  and backend success are gates, not certification of unimplemented layers.
