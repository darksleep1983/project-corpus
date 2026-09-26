# Use Project Corpus with Claude Desktop

[Русская версия](claude-desktop.ru.md)

## New projects: start with V2

Follow the [V2 Quick Start](../quickstart.md). In a manual session, provide
`AGENTS.md`, `.project-corpus/state/PROJECT.md`, and
`.project-corpus/state/STATUS.md`, plus only the active Task and Reports needed
for the work.

## Existing V1 projects

V1 uses seven current files. Attach them to a new project or conversation, add
only relevant Tasks and Reports, and use the manual instruction template. At the
end, save the returned replacement files yourself.

## Your own MCP

Project Corpus Runtime includes a local stdio MCP adapter; see the
[adapter guide](../runtime/stdio-mcp.md). This repository does not ship a
Claude Desktop-specific extension or `.mcpb` bundle. You can also use a reviewed
extension or your own packaged server after checking its permissions and
file-root configuration.

In Claude Desktop, connected tools can be inspected from the Connectors menu or
developer settings. Exact availability may depend on plan and organization
policy.

Official guides:

- <https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop>
- <https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp>

Do not expose an unauthenticated local endpoint to the public internet.
