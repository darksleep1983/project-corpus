# Connect Claude Desktop

Claude Desktop now supports one-click Desktop Extensions, but this repository does
not yet ship an `.mcpb` extension package. The transparent first-preview route is
a local stdio configuration.

After installation, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\print_client_config.py claude-desktop
```

It prints a ready JSON block with absolute paths. In Claude Desktop:

1. Open **Settings → Developer → Edit Config**.
2. Add the printed `project-corpus` entry under `mcpServers`.
3. Save the file and restart Claude Desktop.
4. Open the connector list and confirm that the Project Corpus tools appear.

On Windows, the configuration file is normally under
`%APPDATA%\Claude\claude_desktop_config.json`. Keep the generated absolute paths;
relative paths are not reliable for a server launched by the desktop app.

When a signed or reviewed `.mcpb` package exists, you may install it from
**Settings → Extensions** instead. Until then, prefer the inspectable JSON route.

Official references:

- https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop
- https://modelcontextprotocol.io/docs/develop/connect-local-servers
