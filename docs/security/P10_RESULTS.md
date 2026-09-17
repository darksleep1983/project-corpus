# P10 release-history scan evidence

Status: scanner PASS; repository release gate `OWNER_REVIEW_REQUIRED`

## Evidence provenance

- Implementation qualification target:
  `e862e44d4abf62a5a8b92fb202d5f779c539d234`.
- P10 scanned HEAD: `e862e44d4abf62a5a8b92fb202d5f779c539d234`.
- P10 counts: 620 objects, 40 commits, 13 findings.
- P10 result: release `NO-GO / OWNER_REVIEW_REQUIRED`.
- Evidence-sync branch HEAD:
  `fda4370bfc90cd7f02768a8bd6960ebbcb820041`.
- Post-sync CI: GitHub Actions run `35233928484`, 6/6 jobs PASS,
  93 tests PASS.

The controlled P10 scan was run from the repository root at commit
`e862e44d4abf62a5a8b92fb202d5f779c539d234`. This commit is the implementation
qualification target; it is not described as the current branch HEAD. The clone
was complete rather than shallow. The exact refs present and scanned were:

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

GitHub Actions run `35207733720` qualified the scanned implementation target.
The later evidence-sync commit `fda4370bfc90cd7f02768a8bd6960ebbcb820041`
changed only this evidence documentation, the implementation report and the
integrity manifest. It did not change implementation and was not included in
the recorded P10 scan. Post-sync GitHub Actions run `35233928484` passed 6/6
Windows/Ubuntu/macOS and Python 3.11/3.12 jobs and 93 tests.

CI unit tests create an isolated complete repository and prove coverage of
deleted committed content, commit patches and a locally available unreachable
object, as well as output redaction and the failing release-gate exit code. A
normal shallow CI checkout is not treated as full-project history evidence.

## Future release attestation rule

The final release P10 scan must run on the frozen release-candidate HEAD after
all repository commits are complete. Its release attestation must be stored
outside commit history, for example as a CI or release artifact. This prevents
an evidence commit from changing the scanned HEAD and creating a
self-invalidating evidence-commit loop.

This record covers only objects and refs transferred into the local object
database. It makes no claim about server-side GitHub objects unavailable through
refs or object transfer.
