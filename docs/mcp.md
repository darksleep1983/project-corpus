# MCP

MCP is optional. The Markdown Protocol works without an MCP server.

The optional Runtime offers a deliberately small local stdio adapter. It exposes
scoped reads, stats, managed state updates, Task/Report creation, and audit
receipt reads only when all authority inputs allow the operation. It has no
HTTP listener, remote transport, arbitrary tool dispatch, shell execution, or
trust-management tool.

For operation and limits, see [local stdio MCP](runtime/stdio-mcp.md). For a
future public listing, see the maintainer-only
[MCP discovery plan](distribution/MCP_DISCOVERY_PLAN.md).
