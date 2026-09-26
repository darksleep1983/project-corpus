# V1 project instruction template

This template targets the original V1 seven-file layout. For a new project, use
the [V2 Quick Start](docs/quickstart.md).

Use this common instruction in every mode:

```text
This AI project uses Project Corpus, a seven-file Markdown authority set for one
active project.

At the beginning of a new session, obtain the seven exact current files through
the selected access mode. Fully read AGENTS.md first, then follow its loading
order and rules. Do not replace the Corpus with chat memory or files from another
project. Separate saved statements from fresh live evidence.

Before strong decisions, provide a loading receipt and a short semantic summary:
files received, complete-read status, roles, relationships, authority center,
gaps, and readiness.

During ordinary work, never rewrite AGENTS.md or OPERATOR_PROFILE.md. Update only
factually changed mutable current files and relevant Task/Report artifacts.
```

Then add one mode-specific block.

## Direct folder

```text
Mode: DIRECT_FOLDER.
Use only the explicitly granted Corpus/project filesystem boundary. Confirm the
exact folder and actual read/write permissions. Before writes, reread the current
file and preserve a backup or version-control checkpoint. Read changed files
back and report before/after hashes when available.
```

## Your own MCP

```text
Mode: OWNER_MCP.
Use only the configured trusted MCP tools for this Corpus. Verify the exact root
and available capabilities with the server's real tools. Do not assume a
universal health command or claim backups, atomic writes, hashes, or receipts
unless the server actually provides and verifies them.
```

## Manual session

```text
Mode: MANUAL_SESSION.
Treat uploaded files as snapshots. Confirm that all seven canonical current files
are present and that duplicate names are not ambiguous. At synchronization,
return only current files whose content changed plus new or changed Task/Report
files, a change list, old/new SHA-256 when computable, and the exact next action.
Do not claim that anything was saved on my computer.
```
