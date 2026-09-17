# Release Git-history security gate

P10 is mandatory before any release candidate or visibility change:

```text
project-corpus security scan-history REPOSITORY_ROOT
```

The command is read-only. Exit code `0` means complete local coverage with no
findings. Exit code `3` means findings exist or the repository is shallow.
Output is JSON and never includes matched secret values.

## Coverage

The scanner enumerates every object physically available through the local Git
object database, not only objects reachable from the checked-out branch. It:

- lists every available local and remote-tracking ref and tag;
- maps every object reachable from all available refs;
- scans raw blobs, trees, commits and tag/metadata objects;
- scans the rendered binary patch for every available commit object;
- therefore includes deleted historical files whose blobs remain available;
- includes dangling and unreachable objects when they remain in the local
  object database;
- scans the current working tree as an additional pre-release check.

The patterns cover common credentials, access tokens, private-key headers,
credential-bearing URLs, private-network URLs and machine/user paths. Findings
contain only rule/category, object ID/type and path when Git can supply one.
They require owner review; matched values must never be copied into a report or
public issue.

## Required preparation and limitation

The operator must fetch every branch, tag and other ref that the Git server is
willing to transfer before running the gate. A shallow repository fails
coverage. The scanner accurately reports only the refs and objects present in
the local clone. It cannot claim to inspect server-side GitHub objects that are
not exposed by refs or object transfer, and it does not fetch or mutate remote
state itself.
