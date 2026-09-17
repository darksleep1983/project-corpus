# P10 release-history scan evidence

Status: scanner PASS; repository release gate `OWNER_REVIEW_REQUIRED`

The controlled scan was run from the repository root after commit `517a3fd`.
The clone was complete rather than shallow and contained the local and
remote-tracking `main` and `v2/implementation` refs. The scanner inspected 605
locally available objects, all reachable in this object database, 39 commit
patches, deleted historical content and the working tree. No locally available
dangling object existed in this particular scan; the automated negative test
independently proves that such objects are enumerated when present.

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

GitHub Actions run `35207189523` passed the scanner and full test suite on all
six Windows/Ubuntu/macOS and Python 3.11/3.12 jobs. CI unit tests create an
isolated complete repository and prove coverage of deleted committed content,
commit patches and a locally available unreachable object, as well as output
redaction and the failing release-gate exit code. A normal shallow CI checkout
is not treated as full-project history evidence.

This record covers only objects and refs transferred into the local object
database. It makes no claim about server-side GitHub objects unavailable through
refs or object transfer.
