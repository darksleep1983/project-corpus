# Use Project Corpus with another AI client

[Русская версия](other-clients.ru.md)

Choose the narrowest mode your client supports:

1. `DIRECT_FOLDER` if it can access an explicitly granted local folder;
2. `OWNER_MCP` if you already have a trusted file-capable MCP server;
3. `MANUAL_SESSION` if it can only receive attached or pasted files.

The client must be able to read all seven current files completely. For
automatic synchronization, it must also be able to write or return replacement
files. Record only capabilities you have actually tested in
`CORPUS_ACCESS_CURRENT.md`.

If the client has its own persistent-instruction file, keep that file short and
make it point to `AGENTS.md`. Do not maintain two independent copies of the
protocol.

Never assume that the words “filesystem access” or “MCP support” imply safe path
restriction, backups, atomic writes, or readback verification.
