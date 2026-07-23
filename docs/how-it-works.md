# How it works — without the jargon

Project Corpus has two parts.

## 1. The Corpus

The Corpus is a folder with a small number of Markdown files.

- `AGENTS.md` contains the operating rules.
- `PROJECT_ROADMAP_CURRENT.md` says what the active project is and what happens next.
- the handoff files preserve continuity between chats;
- `Tasks/` contains exact work orders;
- `Report/` contains evidence of completed work.

The files are readable by people. You can open them in any text editor.

## 2. The MCP server

The MCP server is the controlled doorway between the AI client and the Corpus.

It does not give the AI unrestricted access to your computer. It is configured for one exact Corpus folder and enforces which files can be changed.

When the AI updates a permitted file, the server checks the current SHA-256, creates a backup, writes atomically, reads the result back, and returns a receipt.

## Why seven current files?

They separate different kinds of information so a new chat can recover quickly without treating every old task or report as current truth.

## What happens in a new chat?

```text
health check
→ read AGENTS.md
→ read the current files
→ identify the active project
→ load only relevant Tasks and Reports
→ continue from the exact next action
```

## What happens when there is no project?

The Corpus says `NO_ACTIVE_PROJECT`. You describe a new project in normal language, and the current files are initialized for that project.
