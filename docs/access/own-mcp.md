# Use your own MCP

[Русская версия](own-mcp.ru.md)

Project Corpus does not ship an MCP server. Use `OWNER_MCP` only when you have
chosen and reviewed a server or file connector that you trust.

## Minimum requirements

Configure the server for one exact Corpus root. Prefer a server that can:

- list and fully read files;
- expose file metadata or SHA-256;
- limit writes to known current files and direct `Tasks/` or `Report/` children;
- protect against path traversal and stale writes;
- back up old content;
- verify writes by readback;
- return an audit receipt.

These protections are recommendations, not features of this repository. Record
only capabilities you have actually verified.

## Connect it

1. Follow your server's own installation and security documentation.
2. Restrict its filesystem root to the selected Corpus.
3. Follow the official MCP setup for your AI client.
4. Record the server name, transport, exact root, tool names, authentication,
   write behavior, backup behavior, and verification timestamp in
   `CORPUS_ACCESS_CURRENT.md`.
5. In a new session, verify the connection using the server's real tools.

There is no universal `corpus_health` command. A server may expose a different
health check or none at all.

## Safe first check

Confirm that the connection can list the Corpus root and fully read `AGENTS.md`.
Confirm that unrelated paths are outside the granted scope. Test writes only in
a disposable Corpus or an explicitly approved scoped Task.

Never expose a local unauthenticated server to the public internet merely to
connect a cloud client.

Protocol reference: <https://modelcontextprotocol.io/docs/>
