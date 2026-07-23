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

## Your own MCP

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

Project Corpus does not supply the `<server-command>`.
