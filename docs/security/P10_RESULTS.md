# P10 release-history scan evidence

Status: scanner PASS; repository release gate `OWNER_REVIEW_REQUIRED`

The final controlled scan was run from the repository root at branch
`v2/implementation`, HEAD
`e862e44d4abf62a5a8b92fb202d5f779c539d234`. The clone was complete rather
than shallow. The exact refs present and scanned were:

- `refs/heads/main`;
- `refs/heads/v2/implementation`;
- `refs/remotes/origin/HEAD`;
- `refs/remotes/origin/main`;
- `refs/remotes/origin/v2/implementation`.

The scanner inspected 620 locally available objects, all 620 reachable in this
object database, 40 locally available commit objects/rendered patches, deleted
historical content and 159 working-tree files. The local object database
contained 0 dangling/unreachable objects at scan time. The automated negative
test independently proves that such objects are enumerated when present.

The scan returned 13 redacted location-level findings:

- 6 `personal_infrastructure` findings: a generic POSIX user-path example and
  the intentional Windows absolute-root rejection fixture, each represented in
  object/patch/working-tree contexts;
- 7 `private_url` findings: historical private-network/loopback MCP references
  represented in commit patches and deleted or historical blobs;
- 0 credential, token, private-key or embedded-URL-credential findings.

Matched values are intentionally absent from this record. Findings are not
silently exempted because fixtures and historical documentation still require
an owner release decision. The Runtime does not rewrite Git history. Release is
therefore `NO-GO` until the owner chooses remediation or explicitly defines and
approves a release-exception policy, after which P10 must be run again.

GitHub Actions run `35207733720` qualified that exact HEAD and passed the full
93-test suite on all six Windows/Ubuntu/macOS and Python 3.11/3.12 jobs. CI unit
tests create an isolated complete repository and prove coverage of deleted
committed content, commit patches and a locally available unreachable object,
as well as output redaction and the failing release-gate exit code. A normal
shallow CI checkout is not treated as full-project history evidence.

This record covers only objects and refs transferred into the local object
database. It makes no claim about server-side GitHub objects unavailable through
refs or object transfer.
