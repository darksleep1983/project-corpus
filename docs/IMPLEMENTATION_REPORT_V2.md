# Project Corpus V2 implementation report

Status: implementation complete for owner review; not merged; not released

## Branch and commits

Implementation branch: `v2/implementation`

Final qualification evidence was captured at branch HEAD
`e862e44d4abf62a5a8b92fb202d5f779c539d234`.

The branch was built as independently tested logical commits. The sequence is
recorded by `git log main..v2/implementation`; its milestone heads are:

- `d76d3fa` protocol and architecture boundaries;
- `f89c986` through `8379eb7` filesystem prototypes and frozen guarantees;
- `5994eb2` protocol templates and conformance fixtures;
- `9d8685e` read-only V1 migration planner;
- `f7beace` external trust and four-way policy intersection;
- `3e0e30a` read-only validator/doctor;
- `6181dd1` through `5b978af` production native path backend hardening;
- `1a62d6b` through `e035b94` journaled transaction/recovery engine;
- `9f474af` through `fc91ee2` controlled CLI and qualification evidence;
- `8f265a1` through `d80dd90` P9 and native create-only directory publication;
- `4ae16b4` controlled, non-destructive V1 migration;
- `7297103` and `3725bea` optional stdio MCP and qualification evidence;
- `517a3fd` full-local-history release security gate;
- `e862e44` finalized V2 documentation and this implementation report.

No commit on this branch merges to `main`, creates a release, pushes project
data, or adds Runtime Git commit/push behavior.

## Repository delta and implemented architecture

The V1 `template/en` and `template/ru` trees remain unchanged. V2 adds these
separate layers:

```text
protocol/v2/                 normative Markdown-first Protocol
templates/v2/                non-authoritative examples and artifact templates
src/project_corpus/          optional reference Runtime
  platform/                  native confined path backends
prototypes/filesystem_security/
                             pre-production P1-P9 evidence
tests/                       conformance, negative and failure tests
docs/adr/                    accepted architecture decisions
docs/runtime/                Runtime behavior and adapter contracts
docs/security/               guarantee matrix and release gate
docs/migration/              V1 compatibility/migration contract
```

Protocol is usable manually, requires no installation and remains independent
of Runtime behavior. Canonical state uses role-separated Markdown documents.
`PROJECT.md` carries logical project identity only. The machine-specific root,
root identity, filesystem and approved policy digest are pinned exclusively in
external owner configuration.

Effective Runtime authority is the intersection of Runtime hard limits,
external owner trust, portable project policy and the session/client subset.
Project content, prompts and adapter arguments cannot raise that ceiling.

The optional Runtime provides validation, doctor, external trust provisioning,
confined read/stat, expected-hash transactions, journal/audit/recovery,
controlled non-destructive migration, CLI, and local stdio MCP. It deliberately
does not provide Git commit/push, HTTP/remote MCP, arbitrary shell execution, an
execution sandbox, orchestration, distributed locking or multi-project service.

## Prototype gates P1-P10

| Gate | Result | Evidence/constraint |
|---|---|---|
| P1 Windows confinement | PASS | Handle-relative NT opens; reparse/junction and final-link escape rejected on NTFS. |
| P2 Windows publication | PASS, scoped | Handle-relative atomic namespace replacement; custom metadata fails closed; no directory-flush power-loss claim. |
| P3 Linux confinement | PASS | Restrictive `openat2` and descriptor-walk fallback passed on ext4. |
| P4 macOS confinement | PASS | Descriptor-relative no-follow walk passed on APFS. |
| P5 durability | PASS, scoped | File flush on NTFS; file and parent-directory fsync on ext4/APFS; no hardware/power-loss claim beyond tested contracts. |
| P6 concurrency | PASS | Managed writers serialize and stale expected hashes reject. |
| P7 recovery | PASS | Every recorded phase recovers deterministically; unexpected content requires owner action. |
| P8 backend decision | PASS | `NATIVE_PATH_BACKEND_REQUIRED`; Python orchestration plus explicit native bindings is sufficient on qualified targets. |
| P9 directory publication | PASS | Fully staged absent V2 tree publishes create-only; existing destinations are never replaced. |
| P10 release scan | Scanner PASS; release NO-GO | Full local object database/history scanner works and redacts values; current history has owner-review findings. |

P1-P8 passed before production mutation work began. P9 was introduced and
passed before migration directory publication was implemented. Production
backends then passed independent tests rather than inheriting prototype claims.

## Test matrix

All listed GitHub Actions runs completed successfully in six jobs: Windows
local NTFS, Ubuntu local ext4 and macOS local APFS, each on Python 3.11 and
3.12.

| Run | Milestone |
|---|---|
| `35121332371` | P1-P8 prototypes |
| `35180605924` | production native path backend |
| `35182044031` | transaction, concurrency, recovery and audit |
| `35182881428` | controlled CLI |
| `35183223557` | P9 prototype |
| `35183457729` | production directory publication |
| `35205827671` | controlled V1 migration |
| `35206204618` | stdio MCP |
| `35207733720` | final `e862e44` qualification, P10 scanner and complete 93-test suite |

The final local suite also passes 93 tests on Windows; five POSIX-only probes
are correctly skipped there. Wheel construction for `2.0.0.dev0` succeeds.

## Platform guarantee levels

- Markdown/manual: protocol-readable; no Runtime enforcement.
- Direct folder: observable but not enforced; out-of-band writes can bypass
  policy and transactions.
- Controlled CLI: Runtime-enforced only with a valid external grant and on a
  specifically qualified local filesystem.
- Controlled stdio MCP: the same core guarantee, narrowed again by the client
  subset; transport grants nothing.
- Network, removable, FUSE and unknown filesystems: mutation-unqualified and
  fail closed.

Only local NTFS, ext4 and APFS have the evidence stated in the platform matrix.
No other platform/filesystem security claim is made.

## Migration verification

V1 loading and planning are read-only. Controlled migration pins the complete
source manifest and plan digest in an external authorization, rereads through
the native backend, stages and verifies a separate tree, then publishes only to
an absent destination. Source drift, symlinked canonical files, destination
races and embedded authority fail closed. The source V1 tree is neither edited
nor deleted, and exact V1 template compatibility is continuously tested.

## Security findings and release-gate status

The final scanner implementation covers every object present in the local Git
object database, all available refs, deleted historical files, commits,
rendered binary patches, blobs/trees/tags and metadata, plus locally available
unreachable objects. Output contains locations and classifications but never
matched values.

The recorded P10 run scanned final qualification HEAD `e862e44`, all 620
locally available objects and all 40 locally available commit objects/rendered
patches in the available non-shallow clone. It found 13 redacted location-level
findings: 6 `personal_infrastructure`, 7 `private_url`, and 0 credential, token
or private-key findings. Details without values and the exact five refs are in
[`security/P10_RESULTS.md`](security/P10_RESULTS.md). The scanner cannot inspect
server-side objects GitHub did not transfer.

Release gate: `NO-GO`. No history rewrite or exception has been assumed.

## Deviations and known limitations

There is no silent reduction of the accepted guarantee. Measured evidence led
to `NATIVE_PATH_BACKEND_REQUIRED`, implemented as Python orchestration with
native system calls rather than a compiled helper. P9 was added as an explicit
gate when migration revealed a dependency on create-only directory publication.

Known limitations are: NTFS parent-directory flush is not qualified; custom or
non-equivalent metadata fails closed; distributed/out-of-band writers are not
serialized; unsupported filesystems cannot mutate; stdio is the only MCP
transport; and P10 can see only the transferred local object database.

## Exact remaining work and readiness

Implementation scope authorized for V2.0 is complete. Remaining owner/release
work is:

1. review the redacted P10 locations and choose remediation or a formal release
   exception policy;
2. rerun P10 after that decision until the release gate is explicitly closed;
3. review this branch and decide whether to merge it;
4. only after merge and a clean release gate, choose release metadata/version
   and publish V2 separately.

Merge readiness: `GO FOR OWNER REVIEW`, not an authorization to merge.

Release readiness: `NO-GO` pending P10 owner decision and a subsequent clean or
explicitly approved gate. No release has been created.
