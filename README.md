# Project Corpus

[Русская версия](README.ru.md)

[Language policy](docs/languages.md)

> Give your AI a stable, local memory for a long-running project.

Project Corpus keeps the important parts of a project in a small set of Markdown files: the goal, current state, decisions, tasks, reports, and the exact next step. An MCP server lets compatible AI clients read those files and update them under a strict write policy.

You do not need to understand MCP internals to use it.

## What problem does it solve?

Chats end. Context gets lost. A new model or a new session may not know:

- what the project is;
- what has already been decided;
- which task is active;
- what was actually verified;
- what the AI is allowed to change;
- what should happen next.

Project Corpus keeps that state outside the chat, on your own computer.

## The simple version

```text
Install Project Corpus
→ choose a folder
→ connect your AI client
→ describe your project in normal language
→ continue in new chats without rebuilding the context from scratch
```

## What is included?

```text
project-corpus/
├── template/          Clean reusable project memory
├── src/               MCP server
├── scripts/           Setup, start, validation, client helpers
├── docs/              Plain-language guides
├── examples/          Small sanitized example
└── tests/             Write-policy and setup tests
```

The initialized corpus contains:

```text
AGENTS.md
OPERATOR_PROFILE.md
PROJECT_ROADMAP_CURRENT.md
MCP_CONNECTION_CURRENT.md
LOADER_PROMPT_CURRENT.md
SESSION_HANDOFF_CURRENT.md
SESSION_HANDOFF_FULL_CURRENT.md
Tasks/
Report/
```

## Five-minute start

### Windows

Requirements: Python 3.11 or newer.

Open PowerShell in the repository folder:

```powershell
.\install.ps1 -ProjectHome "D:\AI\MyProject" -Language en
.\start.ps1
```

### macOS or Linux

```bash
./install.sh "$HOME/AI/MyProject" --language en
./start.sh
```

The installer creates:

```text
<ProjectHome>/Corpus
<ProjectHome>/mcp-state
```

Choose `en` or `ru` at installation. It creates a matching Corpus and a local
configuration file in the repository. No project secrets are required.

## Choose your AI client

- [ChatGPT](docs/clients/chatgpt.md)
- [Claude Code](docs/clients/claude-code.md)
- [Claude Desktop](docs/clients/claude-desktop.md)
- [Any other MCP client](docs/clients/generic-mcp-client.md)

More: [how it works](docs/how-it-works.md), [FAQ](docs/faq.md),
[security model](docs/security.md), and [uninstalling](docs/uninstall.md).

After connection, use the short project instruction from:

```text
PROJECT_INSTRUCTION_TEMPLATE.md
```

Then start with something ordinary, for example:

> Start a new project. I want to build a local photo organizer. The working folder is D:\AI\PhotoOrganizer. First, help me define the architecture. Do not install or delete anything yet.

## What the server protects

The server is restricted to one configured Corpus root. It provides:

- full-file reads and SHA-256;
- separate create and update operations;
- stale-write protection through `expected_sha256`;
- backups before updates;
- atomic replacement;
- readback verification;
- audit receipts;
- protected protocol files;
- no arbitrary filesystem access outside the Corpus root.

Read [How it works](docs/how-it-works.md) for the plain-language explanation.

## Important limits

- This is a project memory and controlled file workflow, not a general computer-control agent.
- A saved report is not proof that a service or application is currently running.
- Do not store passwords, tokens, cookies, or API keys in the Corpus.
- Keep the HTTP server on loopback unless you place it behind a trusted authenticated tunnel or gateway.
- Connect only MCP servers whose code and permissions you trust.

## Current status

`v0.1.0` is a private preview, not a production-ready release. The setup scripts,
write-policy core, and both MCP transports are tested. Client interfaces and
availability can change, so each client guide links to the official documentation.

## Feedback

Use [GitHub Issues](https://github.com/darksleep1983/project-corpus/issues) for
bug reports, setup questions, and improvement ideas. Search existing issues
first and do not post secrets or private Corpus contents.

## Support the project

Project Corpus is free and MIT-licensed. Voluntary support is available through
USDT on TON; see the [support page and wallet address](SUPPORT.md). A donation
is not a purchase and does not provide additional rights or guarantees.

## License

MIT. See [LICENSE](LICENSE).
