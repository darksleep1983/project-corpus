# Project Corpus Protocol V2

Status: implementation draft based on owner-approved architecture decisions.

Project Corpus Protocol is a vendor-neutral Markdown protocol for restoring and
continuing one logical project from a clean AI context. The Protocol is usable
without Project Corpus Runtime or MCP.

## Required portable layout

```text
AGENTS.md
.project-corpus/
    policy.toml
    state/
        PROJECT.md
        STATUS.md
    tasks/
    reports/
    history/
```

Audit and generated views are optional and are not canonical state.

## Normative principles

1. Model or chat memory is never authoritative project state.
2. `PROJECT.md` and `STATUS.md` have distinct, non-overlapping authority.
3. Saved operational claims require fresh verification before being treated as
   live facts.
4. Project content cannot grant runtime capabilities.
5. Tasks define bounded intent; Reports record evidence and results.
6. History is not promoted to current authority by recency alone.
7. Manual operation remains conforming.
8. MCP is an optional access adapter.

The detailed authority, lifecycle, policy, migration, and conformance rules are
defined by the other documents in this directory.

