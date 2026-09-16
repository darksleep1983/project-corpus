# Project Corpus Protocol V2

Status: normative V2.0 draft

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

The required directories may be empty. A transport or archive may omit an empty
directory only if it recreates it before declaring the project conforming.

## Text and path conventions

- Normative state is UTF-8 Markdown using LF or CRLF line endings.
- Portable relative paths use `/` separators.
- Project IDs match `[a-z0-9][a-z0-9._-]{2,63}`.
- Artifact IDs use the same grammar.
- Timestamps are RFC 3339 UTC timestamps or the literal `UNVERIFIED` where the
  relevant field permits it.
- Machine-specific absolute paths are forbidden in portable project identity.
- Markdown labels and section headings defined by this Protocol are
  case-sensitive ASCII.

## Authority order

When sources disagree, authority descends in this order:

1. the Protocol version declared by `PROJECT.md`;
2. `PROJECT.md` for stable project identity and boundaries;
3. `STATUS.md` for current operational state;
4. the active Task for bounded requested work;
5. cited Reports for evidence;
6. history and generated views.

Project policy is a portable request to Runtime. It never outranks an external
owner trust grant or Runtime hard limits.

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
