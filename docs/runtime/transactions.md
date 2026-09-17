# Controlled filesystem transactions

Status: implementation under platform qualification

The transaction engine is a Runtime component, not part of the Markdown
Protocol definition. It composes the native path backend with current external
trust, portable project policy and a session capability subset.

## Trust split

The project contains the optional, non-authoritative audit receipt. The active
journal and exact pre-update backup live in a separate single-project Runtime
state root provisioned by the owner. Project content cannot select that root,
rewrite the journal or convert an audit receipt into authority.

The external Runtime root must already contain regular marker files at:

```text
journal/.keep
backups/.keep
locks/.keep
```

It must be outside the project tree and on a filesystem qualified by the same
native backend. Controlled adapters derive this path from owner configuration;
it is never accepted from a project file, prompt or MCP argument.

## Update lifecycle

1. Acquire the local single-project writer lock.
2. Recover or block on the previous active journal.
3. Reload policy and recompute effective authority.
4. Validate capability, target scope, content schema and expected hash.
5. Record `PREPARED`; stage and flush bytes; verify replacement metadata.
6. Record `STAGED`; create and verify the external backup; record `BACKED_UP`.
7. Recheck target hash and identity; publish atomically; record `PUBLISHED`.
8. Fully read back content and metadata; record `VERIFIED`.
9. Create and read back a content-free project audit receipt; record `AUDITED`.
10. Record `COMPLETE` and clean deterministic orphan stages.

Create operations use the explicit expected state `ABSENT`, never an omitted
hash. Updates require a lowercase SHA-256. Create and update capabilities are
separate; delete is not implemented in V2.0.

## Recovery

If the target still has the old expected state, recovery removes the known
staged object and records `ROLLED_BACK`. If the target has the verified new
hash, recovery verifies backup/metadata, finishes audit and records `COMPLETE`.
Any third state, missing backup, metadata mismatch or conflicting audit records
`NEEDS_OWNER` without overwriting the target.

The lock is local inter-process serialization. No distributed-locking claim is
made, and an out-of-band writer is not treated as a cooperating transaction.
