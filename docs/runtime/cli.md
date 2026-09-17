# Reference CLI

Status: controlled adapter under platform qualification

The CLI is an optional Runtime adapter. The Markdown Protocol remains usable
without installing it. Commands return JSON and use exit code `2` for a
fail-closed validation, authority, confinement or transaction error.

## Diagnostic commands

```text
project-corpus doctor PROJECT_ROOT [--trust OWNER_GRANT]
project-corpus validate PROJECT_ROOT
project-corpus migration plan V1_ROOT --project-id ID --logical-name NAME
```

These commands do not mutate the project. `validate` is direct-folder
observation; it does not claim Runtime enforcement.

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
```

Read and stat evaluate the same four-way authority intersection and portable
read scopes. Mutations never accept an arbitrary target for state, Task or
Report operations: the adapter maps each command to its fixed capability and
managed path class, then delegates to the transaction engine. Create uses the
explicit `ABSENT` state internally; STATUS update requires a caller-supplied
current SHA-256.

The CLI contains no Git commit/push, HTTP MCP, shell execution, sandbox,
orchestration, distributed locking or multi-project server operation.
