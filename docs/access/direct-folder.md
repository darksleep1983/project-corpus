# V1 direct-folder mode

[Русская версия](direct-folder.ru.md)

Use `DIRECT_FOLDER` when an AI client can read local files and, if you allow it,
write inside a selected workspace.

This guide describes the original V1 template. For a new V2 Corpus, follow the
[V2 Quick Start](../quickstart.md).

## Set it up

1. Copy `template/en` or `template/ru` to a safe folder named `Corpus`.
2. Put the Corpus inside the project workspace, or grant the client access to
   that one folder explicitly.
3. In `CORPUS_ACCESS_CURRENT.md`, record:
   - `Mode: DIRECT_FOLDER`;
   - the exact folder path;
   - whether writes are allowed;
   - the backup method;
   - the last time access was actually checked.
4. Give the client the matching project instruction template.

Do not grant access to an entire home drive merely to reach one Corpus folder.

## Start a session

Ask the AI to:

1. read `AGENTS.md` completely;
2. read the other six current files;
3. list `Tasks/` and `Report/`;
4. load only relevant scoped files;
5. issue a loading receipt and semantic summary.

## End a session

Ask for Corpus synchronization. The AI should:

- reread current files before changing them;
- preserve a backup or use version control;
- change only factually affected mutable current files;
- leave `AGENTS.md` and `OPERATOR_PROFILE.md` unchanged during ordinary work;
- read the changed files back and report before/after hashes when available.

The protocol guides the AI, but filesystem permissions and the client's sandbox
are the real technical boundary.
