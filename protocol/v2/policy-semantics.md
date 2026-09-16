# V2 policy semantics

The portable project policy is declarative and cannot grant authority by itself.
Runtime evaluates it under an external owner-approved capability ceiling.

## Required properties

- deny by default;
- relative path scopes only;
- separate read, update, create, and delete scopes;
- protected and immutable paths;
- expected-hash requirements;
- backup, verification, audit, and filesystem requirements;
- no execution or network authority in V2.0;
- policy changes never apply silently to managed writes.

Effective capabilities are the intersection of runtime hard limits, external
owner trust, project policy, and the current session subset. A project policy
digest mismatch produces `POLICY_DRIFT` and suspends mutations.

