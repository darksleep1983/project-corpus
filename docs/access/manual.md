# Manual-session mode

[Русская версия](manual.ru.md)

Use `MANUAL_SESSION` with any AI chat when you do not want to configure local
folder access or MCP.

## At the start of a new session

Upload these seven current files:

```text
AGENTS.md
OPERATOR_PROFILE.md
PROJECT_ROADMAP_CURRENT.md
CORPUS_ACCESS_CURRENT.md
LOADER_PROMPT_CURRENT.md
SESSION_HANDOFF_CURRENT.md
SESSION_HANDOFF_FULL_CURRENT.md
```

Then upload only the Tasks and Reports relevant to the request. Paste the manual
section from `PROJECT_INSTRUCTION_TEMPLATE.md`.

Ask the AI to read `AGENTS.md` first, read every supplied authority file
completely, and issue a loading receipt before starting the main work.

Avoid ambiguous duplicates. If a platform keeps two uploaded files with the same
canonical name, remove the old one or clearly select the current version.

## At the end of the session

Use this request:

> Synchronize Project Corpus for manual mode. Do not rewrite AGENTS.md or
> OPERATOR_PROFILE.md. Return only current files whose content actually changed,
> plus new or changed Task/Report files. Include a change list, old and new
> SHA-256 where computable, and the exact next action. Do not claim that the
> files were saved on my computer.

Then:

1. save a backup of every local file you will replace;
2. check that each returned filename is canonical;
3. replace only the listed files;
4. reopen them and confirm that they contain the expected result;
5. keep only one current version of each canonical filename.

## What manual mode cannot prove

The AI sees uploaded snapshots, not the live files on your computer. It cannot
prove that you saved a replacement, that a process is running, or that an
external system is healthy unless a separate current tool check exists.
