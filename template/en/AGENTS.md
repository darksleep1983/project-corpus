# PROJECT CORPUS / AGENTS.md

**Protocol revision:** `PROJECT_CORPUS_V2_THREE_ACCESS_MODES`

## 1. Purpose

This file is the permanent bootstrap, authority, continuity, and safety protocol
for one Project Corpus. The corpus supports exactly one active owner-defined
project at a time.

Initial state:

```text
NO_ACTIVE_PROJECT
REUSABLE_CORPUS_READY
```

A new project starts from an ordinary-language owner description. It does not
silently inherit another project's domain, runtime, credentials, roles, errors,
or history.

The corpus is a set of Markdown files. It does not require a particular AI,
client, operating system, programming language, or MCP server.

## 2. Permanent current authority

Only these seven filenames are permanent current authority:

```text
AGENTS.md
OPERATOR_PROFILE.md
PROJECT_ROADMAP_CURRENT.md
CORPUS_ACCESS_CURRENT.md
LOADER_PROMPT_CURRENT.md
SESSION_HANDOFF_CURRENT.md
SESSION_HANDOFF_FULL_CURRENT.md
```

Roles:

- `AGENTS.md`: procedure, authority, continuity, and safety;
- `OPERATOR_PROFILE.md`: protected operator-quality profile;
- `PROJECT_ROADMAP_CURRENT.md`: active project identity and exact next action;
- `CORPUS_ACCESS_CURRENT.md`: selected access mode and its verified limits;
- `LOADER_PROMPT_CURRENT.md`: short project-neutral session loader;
- `SESSION_HANDOFF_CURRENT.md`: compact operational handoff;
- `SESSION_HANDOFF_FULL_CURRENT.md`: detailed current context.

`Tasks/` and `Report/` contain scoped operational artifacts. They do not become
current authority merely because they exist or have a recent date.

## 3. Protected and mutable files

`AGENTS.md` may be changed only after an explicit owner command that directly
authorizes changing this file or the permanent protocol.

`OPERATOR_PROFILE.md` is protected and must not be changed during ordinary
project work, START, CLOSE, recovery, initialization, migration, or reset.

Ordinary authorized work may update only these five current files:

```text
PROJECT_ROADMAP_CURRENT.md
CORPUS_ACCESS_CURRENT.md
LOADER_PROMPT_CURRENT.md
SESSION_HANDOFF_CURRENT.md
SESSION_HANDOFF_FULL_CURRENT.md
```

New scoped Task and Report files may be created directly under their canonical
directories. Do not create dated substitutes for the seven current filenames.

## 4. Three access modes

Record one selected mode in `CORPUS_ACCESS_CURRENT.md`.

### `DIRECT_FOLDER`

The AI works with the Corpus through explicitly granted local-folder tools.
The Corpus folder must be inside the active workspace or separately authorized.
Filesystem and sandbox permissions are the real technical boundary.

### `OWNER_MCP`

The owner connects a trusted MCP server or file connector of their choice. This
repository does not provide or endorse a server. The exact root, available tools,
write behavior, authentication, backup behavior, and last connection check must
be recorded in `CORPUS_ACCESS_CURRENT.md`.

### `MANUAL_SESSION`

The owner uploads the seven current files to a session, plus only relevant Tasks
and Reports. The AI reads the uploaded snapshots and returns replacement files;
it must not claim that anything was saved on the owner's computer.

If no mode has been selected, help the owner choose one before relying on
mode-specific capabilities. Do not stop merely because MCP is unavailable.

## 5. Universal START

START is read-only unless the owner separately authorizes a scoped change.

1. Identify the access mode from `CORPUS_ACCESS_CURRENT.md` or the owner's
   explicit current instruction.
2. Obtain the seven exact current files through that mode.
3. Fully read `AGENTS.md` first.
4. Fully read `OPERATOR_PROFILE.md` and all five mutable current files.
5. Record the exact filenames, complete-read status, and size or SHA-256 when the
   available tools can provide them.
6. List or identify `Tasks/` and `Report/`.
7. Identify `NO_ACTIVE_PROJECT` or exactly one active project.
8. Load only scoped Tasks and Reports relevant to the owner's request.
9. Separate saved facts, direct evidence, inferences, and volatile live facts.
10. Give a concise loading receipt and semantic summary before strong decisions.

Mode-specific checks:

- `DIRECT_FOLDER`: confirm the exact folder and actual read/write boundary;
- `OWNER_MCP`: verify the configured root and connection using the server's
  real tools; do not invent a universal health command;
- `MANUAL_SESSION`: confirm that all seven current files are present and that
  duplicate canonical filenames have not created ambiguous versions.

If complete reading is impossible, disclose what remains unread and avoid strong
canonical conclusions.

## 6. Authority order

1. Explicit current owner instruction.
2. `AGENTS.md`.
3. `PROJECT_ROADMAP_CURRENT.md`.
4. `CORPUS_ACCESS_CURRENT.md`.
5. Loader and compact handoff.
6. A current frozen Task and its verified Report.
7. Fresh receipts and direct evidence.
8. Fresh live verification.
9. Full handoff.
10. Auxiliary or historical artifacts.
11. Old chat memory.

A saved statement does not prove a current process, service, repository, account,
connection, or external system state.

## 7. Full-read factual discipline

For every authority file and every Task or Report used for a decision:

1. Read the complete file.
2. Record path or canonical filename, size, and full SHA-256 when available.
3. Distinguish direct fact, inference, and hypothesis.
4. Never invent unread content, hashes, commands, tests, receipts, or actions.
5. Resolve conflicts by authority, task identity, full content, and fresh
   evidence.
6. After a write or manual replacement, read the complete result back when the
   active mode allows it.

## 8. Starting a project

Before activating a project:

1. Confirm `NO_ACTIVE_PROJECT` or obtain an explicit replacement command.
2. Define one project identity and objective.
3. Record the project root or `not assigned`.
4. Record allowed scope, forbidden actions, evidence requirements, and the exact
   next action.
5. Update only the mutable current files that actually need to change.
6. Verify or prepare the result according to the selected access mode.

A project description does not by itself authorize deployment, destructive
cleanup, publication, paid actions, credential changes, or third-party contact.

## 9. Safe synchronization

Before changing a current file, read its complete current version. Preserve an
old copy outside the canonical current set whenever the active mode permits it.

For `DIRECT_FOLDER`:

- use the narrowest available file tools;
- prefer version control or a dated backup outside the Corpus;
- replace only authorized files;
- read back the result and record before/after hashes when available.

For `OWNER_MCP`:

- follow the connected server's actual create/update contract;
- use expected hashes, backups, atomic replacement, and receipts only when the
  server really provides and verifies them;
- never claim protections that were not instrumentally confirmed.

For `MANUAL_SESSION`, return:

- only current files whose content actually changed;
- only new or changed scoped Task/Report files;
- a change list with old/new SHA-256 when computable;
- a warning to back up the old local files before replacement;
- an explicit statement that persistence and readback remain owner actions.

Do not rewrite all seven current files by default. Do not return a replacement
for `AGENTS.md` or `OPERATOR_PROFILE.md` during ordinary synchronization.

## 10. Tasks and Reports

Use one coherent measurable objective per frozen Task.

A Task includes:

```text
TASK ID
OBJECTIVE
CURRENT VERIFIED BASELINE
AUTHORITATIVE INPUTS
ALLOWED SCOPE
FORBIDDEN
REQUIRED IMPLEMENTATION
REQUIRED TESTS
RUNTIME / DEPLOYMENT AUTHORITY
REPORT CONTRACT
FINAL STATUSES
STOP CONDITIONS
SHORT LAUNCH INSTRUCTION
```

A Report includes:

```text
TASK ID
EXECUTOR
STARTING AUTHORITY
OBJECTIVE
FINAL STATUS
FINDINGS
CHANGED FILES
BEFORE / AFTER SHA-256
TEST MATRIX
RUNTIME ACTIONS
SAFETY CHECKS
ROLLBACK STATUS
KNOWN LIMITATIONS
REMAINING BLOCKERS
EXACT NEXT ACTION
```

A dispatched Task is frozen; a material scope change requires an addendum or a
new Task. Do not store secrets. Do not claim PASS without evidence. Automated
acceptance is not owner acceptance unless the owner actually performed it.

## 11. CLOSE and recovery

On CLOSE:

1. Re-obtain and fully read the current files and relevant Task/Report.
2. Build a factual delta: changed, accepted, rejected, closed, remaining, and
   volatile.
3. Update only mutable files whose factual state changed.
4. Verify writes or prepare a manual synchronization package.
5. Leave one exact next action.

Cold recovery is read-only unless the owner separately authorizes changes. It
uses the seven stable filenames, not old chat memory.

## 12. RESET ACTIVE PROJECT

Reset is never implicit. It requires an explicit destructive replacement or
reset command and a scoped plan classifying:

```text
KEEP
DELETE
REWRITE
DISABLE
UNKNOWN
```

Do not delete `UNKNOWN`. Preserve protected files unless the owner explicitly
changes the permanent protocol. Verify dependencies and retain a rollback path.

## 13. Safety

Corpus loading, maintenance, START, CLOSE, and recovery do not authorize:

- access outside the granted Corpus/project boundary;
- service or process control;
- deployment or reboot;
- credential, secret, permission, or account changes;
- external publication, messaging, purchases, or irreversible actions;
- access to unrelated projects.

Never place or disclose tokens, keys, cookies, seed phrases, authorization
headers, or protected credential material in the Corpus.

Project Corpus rules guide an AI; they are not an operating-system sandbox.
Real safety depends on the permissions of the selected client, folder tools, or
owner-provided MCP server.

END OF AGENTS.md
