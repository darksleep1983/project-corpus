# Local stdio MCP adapter

Status: optional Runtime adapter qualified on the listed local filesystems

The adapter exposes a deliberately small tool set over newline-delimited UTF-8
JSON-RPC on stdin/stdout. It implements the MCP `initialize`, `ping`,
`tools/list` and `tools/call` flow for protocol revisions `2024-11-05`,
`2025-06-18` and `2025-11-25`. It has no HTTP listener, authentication server,
network discovery, sampling, prompts, resources or arbitrary tool dispatch.

Start it with an external trust grant and an explicit client capability subset:

```text
project-corpus mcp --trust OWNER_GRANT \
  --allow mcp.stdio --allow corpus.read --allow corpus.stat
```

Both the external grant and project policy must permit `mcp.stdio`; the grant
must also list the `stdio-mcp` transport. Each exposed operation separately
requires its own capability in all four authority inputs. Removing a capability
from the command cannot be compensated for by project content or an MCP
argument.

## Tools

- `corpus.read` — scoped UTF-8 read with stat/hash evidence;
- `corpus.stat` — scoped size, hash and native identity;
- `state.update` — fixed STATUS target with required expected SHA-256;
- `task.create` — create-only conforming Task at its ID-derived path;
- `report.create` — create-only conforming Report at its ID-derived path;
- `audit.read` — one transaction receipt by a 32-hex identifier.

Tool schemas reject unknown arguments. Mutation tools call the same transaction,
locking, verification, audit and recovery engine as controlled CLI. There is no
tool for trust creation/approval, migration authorization/apply, Git commit or
push, shell execution, HTTP transport, sandbox control or arbitrary path write.

Tool execution failures are returned as MCP tool results with `isError: true`;
protocol and lifecycle failures use JSON-RPC errors. Stdout contains protocol
messages only. Project Corpus does not claim that a third-party MCP host safely
handles or displays tool results; its guarantee ends at the local stdio adapter
and the verified filesystem operation.

## Qualification evidence

GitHub Actions run `35206204618` passed 90 tests in all six Windows/Ubuntu/macOS
and Python 3.11/3.12 jobs. The adapter suite covers lifecycle framing, strict
arguments, scoped reads, capability/transport denial and a mutation through the
production transaction engine. The run qualifies only local stdio on the
platform/filesystem combinations listed in `platform-guarantees.md`; it is not
evidence for HTTP, remote clients or network filesystems.
