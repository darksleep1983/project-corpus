# MCP

MCP is optional. The Markdown Protocol works without an MCP server.

The optional Runtime offers a deliberately small local stdio adapter. It
provides scoped reads and stats, non-authoritative discovery and Context
Intelligence, plus managed state updates, Task/Report creation, and audit
receipt reads only when all authority inputs allow the operation. It has no
HTTP listener, remote transport, arbitrary tool dispatch, shell execution, or
trust-management tool.

For operation and limits, see [local stdio MCP](runtime/stdio-mcp.md). The
maintainer-only [MCP discovery plan](distribution/MCP_DISCOVERY_PLAN.md) tracks
possible public directory submissions; no directory eligibility is implied.
