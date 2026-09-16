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

## Project policy shape

The portable TOML policy uses these tables:

```toml
policy_version = "2.0"
project_id = "example-project"
profile = "READ_ONLY"

[capabilities]
allow = ["corpus.read", "corpus.stat", "corpus.validate"]

[scopes]
read = [".project-corpus/state/**"]
write = []

[requirements]
expected_hash = true
verified_readback = true
audit_receipt = true
```

Unknown keys are rejected. Paths are portable relative patterns; absolute,
drive, UNC, device, ADS and traversal syntax is invalid. The policy cannot name
a physical project root.
