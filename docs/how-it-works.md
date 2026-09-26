# How Project Corpus works

[Русская версия](how-it-works.ru.md)

Project Corpus keeps a project's working identity and continuity in files the
project owns. AI clients and sessions can change while those records stay with
the project.

## The V2 project record

- `AGENTS.md` defines the project's local workflow and authority rules.
- `.project-corpus/state/PROJECT.md` records durable identity, purpose, and
  boundaries.
- `.project-corpus/state/STATUS.md` records the verified current state,
  blockers, evidence references, and exact next action.
- `.project-corpus/tasks/` contains bounded work requests.
- `.project-corpus/reports/` records completed work and evidence.

At a new session, follow `AGENTS.md`, read canonical identity and current state,
and load only the active Task and relevant evidence. Check facts that can change
against the live project. A Task describes authorized work; a Report describes
what was observed. Neither replaces canonical state.

## One protocol, several ways to use it

```text
local project folder ──┐
manual file upload ────┼──> the same project-owned Markdown records
local stdio MCP ───────┘
```

The Markdown Protocol works manually without installing the Runtime. The
optional local Runtime adds validation and controlled operations for clients
that need them. MCP is one access method; it is not the source of authority.

## V1 compatibility

Existing V1 projects keep their original seven-file layout and supported access
guides. Those filenames belong to V1; new projects should start with the
[V2 minimal template](https://github.com/darksleep1983/project-corpus/tree/main/templates/v2/minimal)
and
[Quick Start](quickstart.md). The optional Runtime can plan migration read-only
and publish a separate V2 destination without rewriting V1 files. See the
[direct-folder](access/direct-folder.md), [manual-session](access/manual.md),
and [your-own-MCP](access/own-mcp.md) access guides and the
[migration guide](migration/v1-read-only-planner.md).
