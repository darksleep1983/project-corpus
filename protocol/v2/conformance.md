# V2 conformance

## Protocol conformance

A project is Protocol-conforming when its required Markdown documents are
complete, roles do not overlap, project IDs agree, and the manual cold-start and
synchronization procedures can be followed without Runtime.

The fixtures under `tests/fixtures/protocol_v2/` are published examples of these
rules. `expected.json` lists the exact conformance outcome for each fixture.
Passing a fixture suite does not authorize a Runtime capability.

Minimum validator error codes:

- `MISSING_REQUIRED_PATH`
- `MISSING_METADATA`
- `INVALID_METADATA`
- `MISSING_SECTION`
- `DUPLICATE_SECTION`
- `SECTION_ORDER`
- `PROJECT_ID_MISMATCH`
- `ROLE_OVERLAP`
- `PROJECT_ABSOLUTE_ROOT`
- `GENERATED_VIEW_UNMARKED`

## Runtime conformance

A Runtime implementation must:

- implement a published Protocol version rather than define it implicitly;
- prevent project content from expanding effective authority;
- fail closed when the trusted policy digest or root identity changes;
- state its exact platform and filesystem guarantees;
- require expected hashes for managed updates;
- verify successful mutations and provide deterministic recovery semantics;
- omit HTTP/remote MCP, Git mutation, execution, orchestration, distributed
  locking, and multi-project operation from initial V2.0.

Claims that are not exercised on the corresponding platform and filesystem are
non-conforming.
