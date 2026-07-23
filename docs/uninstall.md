# Move or remove a Corpus

[Русская версия](uninstall.ru.md)

There is no application, service, virtual environment, or runtime to uninstall.

## Move it

1. Stop active work and make a complete backup.
2. Move the whole Corpus folder, including `Tasks/` and `Report/`.
3. Update the exact location in `CORPUS_ACCESS_CURRENT.md`.
4. Update any local client or owner-MCP configuration.
5. Start a new session and perform the complete loading check.

## Remove it

A Corpus contains project state. Back it up first, then delete the whole Corpus
folder only when you intentionally want to remove that state.

For manual mode, also remove old uploaded copies from the AI project if you no
longer want them stored there. For your-own-MCP mode, remove the server
configuration separately according to that server and client's documentation.
