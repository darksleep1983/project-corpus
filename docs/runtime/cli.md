# Reference CLI

Status: controlled adapter qualified on the listed local filesystems

The CLI is an optional Runtime adapter. The Markdown Protocol remains usable
without installing it. Commands return JSON and use exit code `2` for a
fail-closed validation, authority, confinement or transaction error.

## Diagnostic commands

```text
project-corpus doctor PROJECT_ROOT [--trust OWNER_GRANT]
project-corpus validate PROJECT_ROOT
project-corpus search PROJECT_ROOT QUERY [--type state|task|report|history] [--limit 1..100]
project-corpus timeline PROJECT_ROOT SELECTOR
project-corpus show PROJECT_ROOT ARTIFACT_PATH
project-corpus migration plan V1_ROOT --project-id ID --logical-name NAME
project-corpus migration authorize V1_ROOT --destination NEW_V2_ROOT \
  --authorization OWNER_FILE --project-id ID --logical-name NAME
project-corpus migration apply V1_ROOT --authorization OWNER_FILE \
  --trust NEW_TRUST_GRANT [--allow CAPABILITY ...]
```

`plan` does not mutate the project. `authorize` writes only external owner
configuration and provisions its external lock state. `apply` creates a
separate, previously absent V2 destination with create-only directory
publication; neither command changes V1. `validate` is direct-folder
observation and does not claim Runtime enforcement.

`search`, `timeline` and `show` are likewise direct-folder, read-only
observations: like `validate` and `doctor`, they do not require an owner trust
grant. Their boundary is OS ACLs, V2 conformance, policy `read_scopes` and
native backend confinement. Controlled writes and stdio MCP authority remain
external-owner-trust-gated; direct-folder discovery does not broaden that
capability boundary.

The optional [`context` namespace](context.md) builds a non-authoritative,
rebuildable SQLite provenance index and provides query, bundle, doctor, eval,
and candidate validation. It never writes canonical project state.

## Owner trust and Runtime state

```text
project-corpus trust create PROJECT_ROOT --trust GRANT --allow CAPABILITY ...
project-corpus trust approve-policy --trust GRANT
project-corpus runtime init --trust GRANT
```

`trust create` requires every capability ceiling entry explicitly. It records
the physical root, native root identity, filesystem and current policy digest
outside the project. `approve-policy` is the explicit owner action that accepts
a changed portable policy digest; project content cannot invoke it through a
controlled mutation.

`runtime init` provisions the single-project journal, backup and lock root next
to the external grant. Controlled commands derive this path internally. There
is no project-policy field or mutation/MCP argument that can redirect it.
The grant and Runtime state trees must be disjoint from the project tree.
Initialization verifies the pinned root identity, filesystem, protocol version,
project identity and policy digest before creating Runtime state.

## Controlled operations

```text
project-corpus read --trust GRANT --path RELATIVE_PATH
project-corpus stat --trust GRANT --path RELATIVE_PATH
project-corpus state update --trust GRANT --input FILE --expected-sha256 SHA256
project-corpus task create --trust GRANT --input FILE --id ARTIFACT_ID
project-corpus report create --trust GRANT --input FILE --id ARTIFACT_ID
project-corpus audit-read --trust GRANT --transaction-id ID
project-corpus runtime recover --trust GRANT
project-corpus mcp --trust GRANT --allow mcp.stdio [--allow CAPABILITY ...]
```

Read and stat evaluate the same four-way authority intersection and portable
read scopes. Mutations never accept an arbitrary target for state, Task or
Report operations: the adapter maps each command to its fixed capability and
managed path class, then delegates to the transaction engine. Create uses the
explicit `ABSENT` state internally; STATUS update requires a caller-supplied
current SHA-256.

The CLI contains no Git commit/push, HTTP MCP, shell execution, sandbox,
orchestration, distributed locking or multi-project server operation.
The `mcp` command starts the optional local stdio adapter documented in
[`stdio-mcp.md`](stdio-mcp.md); it adds no capabilities beyond the explicit
client subset.

## Qualification evidence

GitHub Actions run `35182881428` passed all six jobs on 2026-09-17:

- Windows local NTFS, Python 3.11 and 3.12;
- Ubuntu local ext4, Python 3.11 and 3.12;
- macOS local APFS, Python 3.11 and 3.12.

The matrix executed 78 tests, including negative authority, scope, stale-policy,
embedded-grant, unprovisioned-state, CRLF and transaction failure cases. This
evidence does not qualify network, FUSE, removable or other filesystems and
does not extend the transaction durability claims in
[`platform-guarantees.md`](../security/platform-guarantees.md).
