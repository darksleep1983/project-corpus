# ADR 0001: Protocol and runtime are independent

Status: accepted by the owner

## Decision

Project Corpus Protocol is the normative, Markdown-first contract for project
authority, continuity, evidence, and migration. It requires no installation,
does not depend on an AI vendor, and remains usable through manual file exchange.

Project Corpus Runtime is an optional reference implementation. It may provide a
CLI, validation, policy enforcement, filesystem transactions, audit and recovery,
and a local stdio MCP adapter. Runtime behavior does not silently define or amend
the Protocol.

Protocol and Runtime use independent versions. Runtime conformance is established
by tests against published Protocol fixtures.

## Consequences

- A project remains recoverable without Runtime.
- Runtime-specific metadata is never portable project authority.
- A Runtime change that alters Protocol semantics requires an explicit Protocol
  revision and compatibility analysis.
- HTTP MCP, execution, Git mutation, orchestration, distributed locking, and a
  multi-project runtime are outside the initial V2.0 scope.

