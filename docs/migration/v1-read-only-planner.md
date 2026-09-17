# V1 read-only migration planner

The compatibility loader reads the seven V1 current files completely, records
their SHA-256 digests, and indexes Task/Report artifacts. The planner does not
write the source or a destination.

The proposed V2 tree contains:

- a derived `PROJECT.md` and `STATUS.md`;
- a deny-by-default `READ_ONLY` project policy request;
- exact byte-preserving copies of every V1 current file and artifact under
  `.project-corpus/history/v1-source/`;
- a receipt containing relative paths and hashes, not file contents or a
  machine-specific source root.

A V1 absolute project root is never copied into `PROJECT.md`. The planner may
hold it transiently as an untrusted suggestion for a separate external owner
trust approval. The public plan receipt reveals only whether such a suggestion
exists.

Conflicting V1 status markers produce
`V1_STATUS_CONFLICT_OWNER_REVIEW_REQUIRED`; the planner does not silently choose
an active operational state. Missing canonical files and case-colliding names
fail the read.

Direct planning remains a read-only compatibility operation with the
direct-folder guarantee level. Controlled `migration authorize` and
`migration apply` route all V1 reads through the qualified native backend.

## Controlled apply

Apply is deliberately separate from planning and never targets the V1 source:

1. `migration authorize` reads V1 through confinement, pins its complete source
   manifest, the deterministic plan digest, a separate absent destination name,
   the destination-parent identity and filesystem in an external owner file.
2. `migration apply` re-reads V1, requires both digests to match, stages a full
   V2 directory as a sibling, verifies every expected entry and byte, and uses
   create-only native directory publication.
3. A pre-existing destination is never replaced. An interrupted staging pass is
   resumable from the pinned authorization; a completed exact destination is
   idempotently verified.
4. The migration audit receipt is included before publication. Only after the
   published tree validates does Runtime create the external trust grant with
   the owner's explicitly requested post-migration capability ceiling.

The external migration authorization is the bootstrap control-plane policy for
an absent project; project content cannot create or modify it. After publication,
ordinary four-way project authority applies. The V1 source is not modified or
deleted, and cleanup remains a separate owner decision.
