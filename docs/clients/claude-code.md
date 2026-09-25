# Use Project Corpus with Claude Code

[Русская версия](claude-code.ru.md)

## Recommended: direct folder

Put the Corpus inside the project workspace or grant it as an additional working
directory. Claude Code reads `CLAUDE.md`, not `AGENTS.md`, so use one of these
approaches:

1. paste `PROJECT_INSTRUCTION_TEMPLATE.md` at the start of work; or
2. add a short project `CLAUDE.md` that tells Claude to fully read and follow
   `Corpus/AGENTS.md` before project work.

Do not duplicate the whole protocol inside `CLAUDE.md`; keep one authority copy
in the Corpus.

Official memory guide:
<https://docs.anthropic.com/en/docs/claude-code/memory>

## Built-in V2 Runtime MCP

The optional V2 Runtime includes a local stdio MCP adapter. After configuring
an external owner trust grant and project policy for the exact V2 Corpus root,
add a read-only capability subset, for example:

```bash
claude mcp add --transport stdio project-corpus -- project-corpus mcp --trust OWNER_GRANT --allow mcp.stdio --allow corpus.read --allow corpus.stat
```

The trust grant must allow the `stdio-mcp` transport and each requested
capability. See the [stdio MCP guide](../runtime/stdio-mcp.md). This adapter is
separate from the V1 `OWNER_MCP` access mode.

## V1 OWNER_MCP or third-party MCP

Add a trusted remote or local MCP server using the server's real command or URL.
For a local stdio server, the general syntax is:

```bash
claude mcp add --transport stdio <name> -- <command> [args...]
```

Run `/mcp` inside Claude Code to inspect the connection. Restrict the server to
the exact Corpus root and record its actual capabilities in
`CORPUS_ACCESS_CURRENT.md`.

Official MCP guide:
<https://docs.anthropic.com/en/docs/claude-code/mcp>

For a third-party server, use that server's real command or URL. Its
capabilities are independent of the built-in V2 adapter.
