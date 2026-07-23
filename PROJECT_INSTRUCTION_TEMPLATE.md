This AI project works with a local Project Corpus through its connected MCP server.

At the beginning of every new chat:

1. Call `corpus_health`.
2. Verify that `status=ok`, the exact `corpusRoot` matches this project, and the server/write-policy versions satisfy `AGENTS.md`.
3. Fully read `AGENTS.md`.
4. Follow its loading order and all of its rules.

Use only `corpus_*` tools for the Corpus. Do not replace the Corpus with chat memory, another MCP server, or files from another project.

If the MCP server is unavailable or the root does not match, stop and report:

`CORPUS_MCP_NOT_CONNECTED`

Follow the create/update, SHA-256, backup, readback, and audit-receipt rules defined in `AGENTS.md`.

Do not treat saved files or Reports as proof of current live state without a fresh instrumental check.
