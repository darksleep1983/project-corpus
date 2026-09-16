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

At this milestone the loader is a read-only compatibility component. Controlled
CLI use will route reads through the production confined path backend after that
backend is implemented. Direct use on a folder has the direct-folder guarantee
level, not the controlled-runtime guarantee level.
