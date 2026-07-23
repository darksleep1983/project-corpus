# How it works — without the jargon

[Русская версия](how-it-works.ru.md)

Project Corpus separates project memory from any single chat or AI client.

## The seven current files

- `AGENTS.md` contains the operating rules.
- `OPERATOR_PROFILE.md` defines the quality standard.
- `PROJECT_ROADMAP_CURRENT.md` says what the project is and what happens next.
- `CORPUS_ACCESS_CURRENT.md` records how the AI receives and synchronizes files.
- `LOADER_PROMPT_CURRENT.md` is the short startup sequence.
- the two handoff files preserve compact and detailed continuity.

`Tasks/` contains exact work orders. `Report/` records what was actually done and
verified.

## Three doors to the same Corpus

```text
local folder tools ─┐
your own MCP ───────┼→ the same seven current files
manual uploads ─────┘
```

The access method changes, but the authority order and file roles do not.

## In a new session

```text
identify access mode
→ obtain the seven current files
→ read AGENTS.md first
→ read the remaining current files
→ load only relevant Tasks and Reports
→ issue a loading receipt
→ continue from the exact next action
```

## At synchronization

Only factual changes are carried forward. `AGENTS.md` and
`OPERATOR_PROFILE.md` stay protected during ordinary work. Direct-folder or MCP
tools may write files if authorized; in manual mode the AI returns replacement
files and the owner saves them.

The files are the memory. MCP is only one optional way to reach them.
