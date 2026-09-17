# ADR 0002: Two canonical state documents

Status: accepted by the owner

## Decision

V2 uses two canonical Markdown state documents with non-overlapping roles:

- `PROJECT.md` stores the project ID and logical identity, objective, invariants,
  and durable scope boundaries.
- `STATUS.md` stores operational status, active Task reference, blockers,
  evidence references, and the exact next action.

`PROJECT.md` never stores a machine-specific absolute filesystem root. Physical
root identity belongs to the external owner trust grant maintained by Runtime.

Tasks, Reports, history, audit records, loaders, and handoff views do not become
canonical current state. Generated views must identify themselves as
non-authoritative.

## Rejected alternatives

A single `current.md` was rejected because unrelated stable and operational
changes would share one conflict surface. Machine-readable canonical state was
rejected because it would make tooling necessary for the manual Markdown
workflow.

