# V2 canonical state documents

## PROJECT.md

Required metadata lines, immediately after the H1 heading:

```text
Protocol-Version: 2.0
Project-ID: <portable-project-id>
Logical-Name: <human-readable name>
```

Required H2 sections, exactly once and in this order:

```text
## Objective
## Invariants
## Durable Scope Boundaries
## Non-Goals
```

`PROJECT.md` must not contain a machine-specific absolute filesystem root. A
Runtime installation pins its physical root externally.

## STATUS.md

Required metadata lines, immediately after the H1 heading:

```text
Protocol-Version: 2.0
Project-ID: <same ID as PROJECT.md>
Lifecycle-Status: ACTIVE | PAUSED | BLOCKED | COMPLETE
Active-Task-ID: <artifact-id> | NONE
Last-Verified-At: <RFC3339 UTC> | UNVERIFIED
Evidence-Class: OBSERVED | DOCUMENTED | INFERRED | UNVERIFIED
```

Required H2 sections, exactly once and in this order:

```text
## Current Verified Baseline
## Blockers
## Evidence References
## Exact Next Action
```

`NONE` is valid section content where no blocker, evidence reference or next
action exists. An `ACTIVE` status must not use `NONE` for Exact Next Action.

The project ID must match `PROJECT.md`. Stable identity, objective, and
invariants must not be duplicated in `STATUS.md`.

## Other documents

Tasks and Reports are scoped artifacts. History is lower-authority context.
Audit receipts prove managed operations, not owner intent. Generated loaders and
handoffs must carry a visible `NON_AUTHORITATIVE_VIEW` marker.

## Role separation

`PROJECT.md` must not contain lifecycle status, active Task, blockers, evidence
references, verification timestamp or exact next action. `STATUS.md` must not
contain Objective, Invariants, Durable Scope Boundaries or Non-Goals sections.

An operation that changes both documents is a multi-document transition. Manual
mode may provide a manifest and replacement documents, but does not claim atomic
publication.
