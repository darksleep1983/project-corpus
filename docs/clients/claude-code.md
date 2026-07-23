# Connect Claude Code

For a local Project Corpus, use the stdio route first. Claude Code launches the
server as a local subprocess, so you do not need to keep an HTTP server running.

1. Install Project Corpus.
2. Print the ready command:

```powershell
.\.venv\Scripts\python.exe .\scripts\print_client_config.py claude-code
```

3. Run the printed command in a terminal. It adds `project-corpus` as a local
   stdio MCP server in your Claude Code user scope.
4. In Claude Code, run `/mcp` and confirm that `project-corpus` is connected.
5. Put `PROJECT_INSTRUCTION_TEMPLATE.md` into your project instructions, or give
   Claude the same instruction at the beginning of work.

## Optional: local Streamable HTTP

If you deliberately want a separately running server, start it with
`.\start.ps1`, then add it with:

```bash
claude mcp add --transport http project-corpus http://127.0.0.1:8334/mcp
```

Use HTTP for a remote server only when it has appropriate authentication. In
JSON configuration, the transport type must be `http` or `streamable-http`; a
URL without a type is not a valid configuration.

Official reference: https://code.claude.com/docs/en/mcp
