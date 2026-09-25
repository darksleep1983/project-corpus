# Runtime

The Project Corpus Runtime is an optional local reference implementation. It is
useful when a project needs technical enforcement beyond a manual or
direct-folder workflow.

It validates Protocol conformance; evaluates external owner trust and portable
policy; confines managed reads and writes; uses expected hashes, journal,
backup, readback, audit receipts, and recovery; and exposes controlled CLI and
local stdio MCP adapters.

Version 2.2.0 also provides optional, non-authoritative
[Context Intelligence](runtime/context.md) for bounded retrieval and context
bundles. The Protocol remains 2.0 and does not require an index.

It does not provide HTTP/remote MCP, arbitrary shell execution, an execution
sandbox, Git commit/push, distributed locking, or multi-project operation.

Start with [CLI](runtime/cli.md), then read [transactions](runtime/transactions.md),
[stdio MCP](runtime/stdio-mcp.md), and the [platform guarantees](security/platform-guarantees.md).
