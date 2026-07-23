# Use Project Corpus with Claude Desktop

[Русская версия](claude-desktop.ru.md)

## Easiest: manual mode

Attach the seven current files to a new project or conversation, add only
relevant Tasks and Reports, and use the manual instruction template. At the end,
save the returned replacement files yourself.

## Your own MCP

Claude Desktop supports desktop extensions and organization-managed connectors.
Use a reviewed extension or your own packaged server only after checking its
permissions and file-root configuration. This repository does not ship an
`.mcpb` package or local server.

In Claude Desktop, connected tools can be inspected from the Connectors menu or
developer settings. Exact availability may depend on plan and organization
policy.

Official guides:

- <https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop>
- <https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp>

Do not expose an unauthenticated local endpoint to the public internet.
