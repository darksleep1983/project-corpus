# V2 canonical state documents

## PROJECT.md

Required fields or sections:

```text
Protocol version
Project ID
Logical project name
Objective
Invariants
Durable scope boundaries
Non-goals
```

`PROJECT.md` must not contain a machine-specific absolute filesystem root. A
Runtime installation pins its physical root externally.

## STATUS.md

Required fields or sections:

```text
Project ID
Lifecycle status
Active Task ID or NONE
Current verified baseline
Blockers
Evidence references
Exact next action
Last verified timestamp and evidence class
```

The project ID must match `PROJECT.md`. Stable identity, objective, and
invariants must not be duplicated in `STATUS.md`.

## Other documents

Tasks and Reports are scoped artifacts. History is lower-authority context.
Audit receipts prove managed operations, not owner intent. Generated loaders and
handoffs must carry a visible `NON_AUTHORITATIVE_VIEW` marker.

