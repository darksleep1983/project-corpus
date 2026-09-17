# Project Corpus

[Русская версия](README.ru.md)

> A small, readable project memory that survives new AI chats.

Chats end. Models change. A new session may not know what the project is, what
has already been decided, what was actually verified, or what should happen
next.

Project Corpus keeps that state in a compact set of ordinary Markdown files on
your computer. There is no application to install and no required Python
runtime. MCP is optional.

## Project Corpus V2

Project Corpus V2 adds the Markdown-first, vendor-neutral
[Project Corpus Protocol V2](protocol/v2/README.md) while keeping the existing
V1 templates and workflow intact. Protocol V2 remains usable manually with no
installation.

An [optional reference Runtime](docs/runtime/cli.md) for Python 3.11+ implements
validation, externally granted policy enforcement, native confined filesystem
transactions, audit/recovery, non-destructive V1 migration, a local CLI, and a
local stdio MCP adapter. Runtime behavior does not define or silently amend the
Protocol. The exact guarantee levels and qualified local filesystems are listed
in the [platform matrix](docs/security/platform-guarantees.md).

## The idea in one minute

```text
copy a clean Corpus template
→ choose how your AI can access it
→ describe the project in normal language
→ keep the current files synchronized
→ continue in a new session from the exact next action
```

The Corpus contains:

```text
AGENTS.md
OPERATOR_PROFILE.md
PROJECT_ROADMAP_CURRENT.md
CORPUS_ACCESS_CURRENT.md
LOADER_PROMPT_CURRENT.md
SESSION_HANDOFF_CURRENT.md
SESSION_HANDOFF_FULL_CURRENT.md
Tasks/
Report/
```

`AGENTS.md` defines the rules. The roadmap and handoffs preserve current state.
`Tasks/` contains scoped work orders; `Report/` contains evidence of completed
work.

## Choose one access mode

| Mode | Best for | What happens |
| --- | --- | --- |
| Direct folder | Codex, Claude Code, ChatGPT Work, and other local agents | Give the client access only to the Corpus folder and let it read or update the files directly. |
| Your own MCP | Clients that support an MCP server or file connector | Connect a trusted server of your choice, restrict it to the Corpus root, and record its real capabilities. |
| Manual session | Any AI chat, with no setup | Upload the seven current files at the start; at the end, save only the replacement files the AI returns. |

The three modes use the same protocol. An unavailable MCP server is not a
blocker: switch to direct-folder or manual access.

Read the detailed guides:

- [Direct folder](docs/access/direct-folder.md)
- [Your own MCP](docs/access/own-mcp.md)
- [Manual sessions](docs/access/manual.md)

## Five-minute start

1. Download or clone this repository.
2. Copy one language folder to a safe location and name it `Corpus`:
   - `template/en` for English;
   - `template/ru` for Russian.
3. Open `CORPUS_ACCESS_CURRENT.md` and choose an access mode.
4. Give your AI the matching text from
   [`PROJECT_INSTRUCTION_TEMPLATE.md`](PROJECT_INSTRUCTION_TEMPLATE.md).
5. Say what you want to build in normal language.

Example:

> Start a new project. I want to build a local photo organizer. First help me
> define the architecture. Do not install, delete, publish, or contact anyone.

## Client guides

- [ChatGPT](docs/clients/chatgpt.md)
- [Codex](docs/clients/codex.md)
- [Claude Code](docs/clients/claude-code.md)
- [Claude Desktop](docs/clients/claude-desktop.md)
- [Other AI clients](docs/clients/other-clients.md)

Client interfaces and plan availability can change. Each guide keeps volatile
client setup separate from the stable Corpus protocol and links to official
documentation.

## Manual mode really works

If you do not want to configure local folders or MCP:

1. upload the seven current files in a new session;
2. upload only the Tasks and Reports relevant to the request;
3. ask the AI to read `AGENTS.md` first and issue a loading receipt;
4. work normally;
5. ask for a manual synchronization package;
6. back up the old local files and save the returned replacements.

Ordinary synchronization must not rewrite `AGENTS.md` or
`OPERATOR_PROFILE.md`. The AI should return only files that actually changed and
must not claim that it saved them on your computer.

## Important limits

- Project Corpus is a documentation protocol, not a security sandbox.
- Real access is controlled by your AI client, filesystem permissions, or your
  chosen MCP server.
- V1 direct-folder and manual workflows do not gain Runtime enforcement.
- The optional V2 Runtime provides local CLI and stdio MCP only; it does not
  provide HTTP/remote MCP or audit third-party servers.
- A saved Report is not proof that a service or external system is currently
  healthy.
- Do not store passwords, tokens, cookies, seed phrases, or API keys in the
  Corpus.
- Keep one active project per Corpus.

More: [how it works](docs/how-it-works.md), [FAQ](docs/faq.md),
[security model](docs/security.md), [languages](docs/languages.md), and
[moving or removing a Corpus](docs/uninstall.md).

## Current status

Project Corpus V2 is the current open-source generation. The bilingual
templates, three access modes, documentation links, repository integrity and
optional Runtime are checked automatically. Release changes are recorded in
the [changelog](CHANGELOG.md).

## Feedback

Use [GitHub Issues](https://github.com/darksleep1983/project-corpus/issues) for
bugs, setup questions, and improvement ideas. Do not post secrets or private
Corpus contents.

## Support the project

Project Corpus is free and MIT-licensed. Voluntary support is available through
USDT on TON; see the [support page and wallet address](SUPPORT.md). A donation is
not a purchase and does not provide additional rights or guarantees.

## License

MIT. See [LICENSE](LICENSE).
