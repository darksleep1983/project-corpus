# V2 lifecycle

## Cold start

1. Identify manual, unmanaged direct-folder, controlled CLI, or controlled stdio
   MCP access.
2. Read AGENTS, PROJECT, STATUS, and the portable project policy completely.
3. Confirm that project IDs agree and required sections are present.
4. Load only the active or owner-relevant Tasks and Reports.
5. Separate canonical state, evidence, live facts, history, and inference.
6. Issue a loading receipt and continue from the exact next action.

## Synchronization

Only factual changes are carried forward. PROJECT changes are rare and require
explicit owner authority. STATUS changes require the current expected hash when
performed by Runtime. Manual synchronization returns replacement files and never
claims local persistence.

## Close

Re-read current authority, compute the factual delta, update only affected
documents, record evidence references, and leave exactly one next action.

## Reset

Reset is explicit and destructive. Unknown state is preserved. V1 migration and
V2 reset never delete source files implicitly.

