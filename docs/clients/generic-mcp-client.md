# Connect another MCP client

Project Corpus supports two transports:

## Streamable HTTP

Start the server:

```bash
./start.sh
```

Endpoint:

```text
http://127.0.0.1:8334/mcp
```

Configure your client with that URL.

## stdio

Run:

```bash
project-corpus-mcp --transport stdio \
  --corpus-root /absolute/path/to/Corpus \
  --mcp-root /absolute/path/to/mcp-state
```

Use the absolute executable path and absolute folder paths in clients that launch MCP servers as subprocesses.

Official protocol documentation: https://modelcontextprotocol.io/docs/
