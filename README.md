# Project Corpus

[Русская версия](README.ru.md)

**Persistent project state and authority for AI agents.**

Project Corpus is a Markdown-first, vendor-neutral protocol that lets ChatGPT,
Codex, Claude, and other AI agents resume a project from clean context without
relying on chat memory.

It defines what the project is, which state is current, which rules are
authoritative, what has been verified, what comes next, and which authority may
change that state.

The [Protocol](protocol/v2/README.md) works with plain Markdown and requires no
Runtime, database, or MCP server. It can be used manually and is independent of
any AI vendor.

An [optional reference Runtime](docs/runtime/cli.md) adds declarative policy
enforcement, expected-hash filesystem transactions, audit/recovery, CLI
tooling, and local stdio MCP. Runtime behavior does not define or silently
amend the Protocol. Its enforced guarantees apply only in controlled modes on
the qualified local filesystems listed in the
[platform matrix](docs/security/platform-guarantees.md).

> A memory bank tells an agent what it remembers. Project Corpus defines what
> the project currently considers authoritative.

## Why Project Corpus?

AI sessions are disposable. Projects are not. Typical memory files help an
agent recall information; Project Corpus also separates and defines:

- canonical project identity;
- current operational state;
- authority boundaries and change permissions;
- cited evidence versus saved claims that need re-verification;
- the exact next action;
- controlled state changes when the optional Runtime is used.

## Protocol and Runtime

| Project Corpus Protocol | Project Corpus Runtime |
| --- | --- |
| Markdown-first and vendor-neutral | Optional reference implementation |
| No installation or database | CLI and validation |
| Manual workflow supported | Policy enforcement and external owner trust |
| MCP optional | Verified transactions, audit/recovery, local stdio MCP |

The Protocol is the product contract. The Runtime is an optional enforcement
layer for users who need stronger technical controls.

## The idea in one minute

```text
copy a clean Corpus template
→ choose how your AI can access it
→ describe the project in normal language
→ keep the current files synchronized
→ continue in a new session from the exact next action
```

The maintained V1 Corpus template contains:

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
