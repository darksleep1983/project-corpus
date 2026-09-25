# Use Project Corpus with Codex

[Русская версия](codex.ru.md)

## Recommended: direct folder

Put the Corpus inside the trusted project workspace or open the Corpus as a
local folder. Start Codex from the folder hierarchy that contains `AGENTS.md`.
Codex discovers `AGENTS.md` from the project root down to the current working
directory.

If the Corpus is outside the active workspace, grant that exact folder access
instead of widening access to an entire drive. Use the project's instruction
template to make the loading and synchronization steps explicit.

Official guides:

- <https://developers.openai.com/codex/agent-configuration/agents-md>
- <https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex>

## Built-in V2 Runtime MCP

The optional V2 Runtime includes a local stdio MCP adapter. For example, after
configuring an external owner trust grant and project policy for the exact V2
Corpus root, register a read-only capability subset:

```bash
codex mcp add project-corpus -- project-corpus mcp --trust OWNER_GRANT --allow mcp.stdio --allow corpus.read --allow corpus.stat
```

The trust grant must allow the `stdio-mcp` transport and each requested
capability. See the [stdio MCP guide](../runtime/stdio-mcp.md). This adapter is
separate from the V1 `OWNER_MCP` access mode.

## V1 OWNER_MCP or third-party MCP

Codex stores MCP settings in `config.toml`. The ChatGPT desktop app, Codex CLI,
and IDE extension share this configuration. Add only a server you trust and
configure that server to expose the exact Corpus root.

CLI pattern for a local stdio server:

```bash
codex mcp add <server-name> -- <server-command> [args...]
```

Then verify it with:

```bash
codex mcp list
```

Official guide: <https://developers.openai.com/codex/mcp>

For a third-party server, replace `<server-command>` with that server's actual
command. Its capabilities are independent of the built-in V2 adapter.
