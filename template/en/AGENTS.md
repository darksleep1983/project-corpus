# PROJECT CORPUS / AGENTS.md

**Protocol revision:** `PROJECT_CORPUS_V1_WRITE_POLICY_V1`

## 1. Purpose

This file is the permanent bootstrap, authority, continuity, and safety protocol
for:

```text
{{CORPUS_ROOT}}
```

The corpus supports exactly one active owner-defined project at a time.

Empty state:

```text
NO_ACTIVE_PROJECT
REUSABLE_CORPUS_READY
```

A new project starts from an ordinary-language owner description. It does not
silently inherit a previous project's domain, runtime, credentials, roles,
errors, or history.

## 2. Permanent current authority

Only these seven filenames are permanent current authority:

```text
AGENTS.md
OPERATOR_PROFILE.md
PROJECT_ROADMAP_CURRENT.md
MCP_CONNECTION_CURRENT.md
LOADER_PROMPT_CURRENT.md
SESSION_HANDOFF_CURRENT.md
SESSION_HANDOFF_FULL_CURRENT.md
```

`Tasks/` and `Report/` contain scoped artifacts and are not permanent current
authority.

## 3. Protected and mutable files

`AGENTS.md` may be updated only after an explicit owner command changing this
file or the permanent corpus protocol. The MCP update requires:

```text
operation=update
authorization=EXPLICIT_OWNER_PROTOCOL_CHANGE
expected_sha256=<current full SHA-256>
```

`OPERATOR_PROFILE.md` is hard-denied for ordinary writes.

Ordinary authorized work may update only:

```text
PROJECT_ROADMAP_CURRENT.md
MCP_CONNECTION_CURRENT.md
LOADER_PROMPT_CURRENT.md
SESSION_HANDOFF_CURRENT.md
SESSION_HANDOFF_FULL_CURRENT.md
```

## 4. MCP baseline

Required health:

```text
status=ok
corpusRoot={{CORPUS_ROOT}}
serverVersion>=0.1.0
writePolicyVersion>=1.0
```

Write Policy requires create/update separation, exact expected SHA-256 for
updates, verified backup, atomic publication, full readback, and audit receipt.

Backups remain outside the corpus under:

```text
{{MCP_ROOT}}/backups/current
{{MCP_ROOT}}/backups/tasks
{{MCP_ROOT}}/backups/report
```

## 5. Authority order

1. Explicit current owner instruction.
2. `AGENTS.md`.
3. `PROJECT_ROADMAP_CURRENT.md`.
4. `MCP_CONNECTION_CURRENT.md`.
5. Loader and compact handoff.
6. Current frozen Task and verified Report.
7. Fresh receipts and direct evidence.
8. Fresh runtime verification.
9. Full handoff.
10. Auxiliary or historical artifacts.
11. Old chat memory.

## 6. Full-read discipline

Read every authority file and every Task/Report used for a decision completely.
Record exact path, size, and full SHA-256. Distinguish fact, inference, and
hypothesis. Do not invent unread content, commands, tests, hashes, receipts, or
external actions. After create/update, perform full readback.

Saved state and live runtime state are different evidence classes.

## 7. START

START is read-only unless the owner separately authorizes a scoped write or
implementation.

1. Call `corpus_health`.
2. Verify root and minimum versions.
3. List the corpus root.
4. Fully read all seven current files.
5. Record size, SHA-256, and complete-read proof.
6. List `Tasks/` and `Report/` as scoped artifacts.
7. Identify `NO_ACTIVE_PROJECT` or one active project.
8. Load only relevant Tasks/Reports.
9. Separate saved facts from volatile live facts.

## 8. Starting a project

Before activating a project:

1. Confirm `NO_ACTIVE_PROJECT` or obtain an explicit replacement command.
2. Define one project identity and objective.
3. Record project root or `not assigned`.
4. Record scope, safety boundaries, evidence requirements, and exact next action.
5. Update the five mutable current files consistently through the MCP.
6. Fully read back every update.

A project description does not automatically authorize deployment, destructive
cleanup, publication, paid actions, credential changes, or third-party contact.

## 9. Tasks and Reports

New Task/Report files are Markdown directly under their canonical directory.
A dispatched Task is frozen; material changes require an addendum or new Task.
Do not store secrets. Do not claim PASS without evidence.

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

## 10. CLOSE and recovery

On CLOSE, verify health, fully read current files and relevant Task/Report,
build a factual delta, update only changed mutable files, and verify every
write. Cold recovery is read-only and relies on the seven stable filenames,
not old chat memory.

## 11. RESET ACTIVE PROJECT

Reset is never implicit. It requires an explicit destructive replacement or
reset command and a scoped Work Order classifying:

```text
KEEP
DELETE
REWRITE
DISABLE
UNKNOWN
```

Do not delete `UNKNOWN`. Verify dependencies and health after every destructive
phase. Remove secrets without reading or disclosing their values. Return the
current files to `NO_ACTIVE_PROJECT` only after verified cleanup.

## 12. Safety

Corpus maintenance does not itself authorize changes outside the corpus,
service control, deployment, reboot, credential or ACL changes, external
publication, messaging, purchases, or access to unrelated projects.

Never disclose tokens, keys, cookies, authorization headers, or protected
credential material.

END OF AGENTS.md
