# FAQ

[Русская версия](faq.ru.md)

## Is this just another memory bank?

No. A memory bank helps an agent remember information. Project Corpus also
defines canonical identity, current operational state, evidence, exact next
action, and authority boundaries.

## Do I need MCP?

No. Use a direct local folder or manual file uploads. MCP is optional.

## What is Context Intelligence?

An optional 2.2.0 Runtime feature that builds a disposable index from scoped
Markdown, retrieves source-backed context by authority and time, and assembles
bounded Context Bundles for any AI agent.

## Is a Context Bundle authoritative?

No. It is a non-authoritative guide to relevant sources. Read the canonical
Markdown files before making an authority or current-state claim.

## Does it require an LLM, vector DB, or external database?

No. The local index is rebuildable; no LLM, vector database, external database,
or network is required.

## Do I need Python or an installer?

No for the Markdown Protocol. Copy the V2 template and start working manually.
Python 3.11+ is needed only for the optional local Runtime.

## Can I use it with ChatGPT, Codex, or Claude?

Yes. Any client that can read Markdown can use manual mode. Clients with local
file tools can use direct-folder mode.

## Can the Runtime access my whole disk?

Not by project content alone. Controlled Runtime operations are bounded by its
hard limits, an external owner trust grant that pins one physical root, project
policy, and the client capability subset. Direct-folder mode remains governed by
the permissions you give the AI client.

## Is it a sandbox?

No. The Markdown Protocol is not a security sandbox. The optional Runtime
provides scoped guarantees only in documented controlled modes on qualified
local filesystems. It does not make a third-party client or MCP host safe.

## Does it work on network drives?

Do not assume so. Network, FUSE, removable, and other unqualified filesystems
are outside the Runtime's measured guarantees and controlled mutation fails
closed when the filesystem is unqualified.

## Can multiple agents edit at once?

Use one authoritative writer at a time. The Runtime has local writer controls
for its supported single-project mode; it does not provide distributed locking
or multi-project coordination.

## Why `PROJECT.md` and `STATUS.md`?

Stable identity and operational state change at different rates. Separate
canonical documents make authority clearer and reduce unnecessary conflicts.

## Why not a database?

Markdown remains inspectable, portable, vendor-neutral, and usable without an
installation. A database may be used by another tool, but it is not required to
use this Protocol.

## Does it send my whole project to the internet?

Project Corpus itself sends nothing. A cloud AI receives what you upload or what
a connected tool reads for it. Review the client's data policy and share only
what is needed.

## Can I keep two projects in one Corpus?

No. Use a separate Corpus for each active project.

## Can I rename the files?

You can, but every protocol reference and client instruction must change
together. The default names are designed as one set.

## Why Tasks and Reports?

A Task defines what is allowed and required. A Report records what was actually
done and verified. Keeping them separate prevents a plan from being mistaken for
evidence.

## Does manual mode update my local files?

No. The AI returns replacement files. You back up and save them yourself.

## Can I migrate V1?

Yes. The Runtime provides read-only migration planning and separate controlled,
create-only V2 publication. V1 templates remain unchanged; see the migration
guide before authorizing an apply step.

## Is PyPI available?

Yes. The optional Runtime can be installed from PyPI with `pip install project-corpus`.
