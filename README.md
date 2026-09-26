# Project Corpus

[Русская версия](README.ru.md)

[![CI](https://github.com/darksleep1983/project-corpus/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/darksleep1983/project-corpus/actions/workflows/test.yml)
[![Docs build](https://github.com/darksleep1983/project-corpus/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/darksleep1983/project-corpus/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-66d9c2)](LICENSE)
[![Release](https://img.shields.io/github/v/release/darksleep1983/project-corpus?display_name=tag&sort=semver)](https://github.com/darksleep1983/project-corpus/releases)
[![PyPI](https://img.shields.io/pypi/v/project-corpus)](https://pypi.org/project/project-corpus/)
[![Protocol 2.0](https://img.shields.io/badge/Protocol-2.0-66d9c2)](protocol/v2/README.md)

**Durable project identity, continuity and authority for AI-assisted work.**

AI sessions and models change. A project's understanding of itself, its current
state, and the evidence behind that state should outlast them. Project Corpus is
a vendor-neutral, Markdown-first protocol that gives this information a clear,
project-owned home. It defines what is canonical, what is current, what has
been verified, what comes next, and which rules govern change.

The protocol is useful on its own. The optional Python Runtime adds local
validation, controlled operations, audit and recovery, CLI tools, and stdio MCP.

## Start in three steps

1. Download or clone this repository. Copy
   [`templates/v2/minimal/`](templates/v2/minimal/) into the root of the
   project you want to carry across AI sessions:

   ```sh
   cp -R templates/v2/minimal/. /path/to/your-project/
   ```

   PowerShell:

   ```powershell
   Copy-Item -Force .\templates\v2\minimal\AGENTS.md C:\path\to\your-project\
   Copy-Item -Recurse -Force .\templates\v2\minimal\.project-corpus C:\path\to\your-project\
   ```

2. Fill in `.project-corpus/state/PROJECT.md` with the project's durable
   identity. Use the same project ID in `.project-corpus/state/STATUS.md` and
   `.project-corpus/policy.toml`; record the verified current state, blockers,
   evidence, and exact next action in STATUS.
3. Give your AI client access to the project folder, or upload `AGENTS.md`,
   `PROJECT.md`, and `STATUS.md` with the relevant active Task and Reports. Ask
   it to follow `AGENTS.md`, read the canonical state, report what is current,
   and continue from the exact next action.

The [Quick Start](docs/quickstart.md) includes a ready-to-use loading prompt.

## How it works

Each project owns a small set of canonical Markdown records:

- `PROJECT.md` describes durable identity, purpose, and boundaries.
- `STATUS.md` records the verified current state and next action.
- `AGENTS.md` defines local workflow and authority rules.
- Tasks bound requested work; Reports record what was done and the evidence.

At the start of a session, the AI reads those sources and checks mutable facts
against the live project. This helps prevent old chat context, saved summaries,
or one AI executor from being mistaken for current project authority.

## Protocol and optional Runtime

| Project Corpus Protocol | Optional Project Corpus Runtime |
| --- | --- |
| Markdown-first, vendor-neutral, and usable manually | Local Python implementation for added enforcement |
| No installation, database, or MCP required | Validation, controlled CLI, and local stdio MCP |
| Project files remain the portable authority | External owner trust, policy enforcement, transactions, audit, and recovery |

The Runtime implements the Protocol; it does not define or silently change its
semantics. Technical guarantees apply only to documented controlled modes and
qualified local filesystems. See [Protocol vs Runtime](docs/concepts/protocol-vs-runtime.md)
and the [security model](docs/security.md).

Install the optional Runtime from PyPI:

```sh
pip install project-corpus
project-corpus validate /path/to/your-project
project-corpus doctor /path/to/your-project
```

Runtime 2.2.0 also includes optional [Context Intelligence](docs/runtime/context.md):
a rebuildable, policy-scoped index and bounded, source-backed context for any AI
consumer. Its results are non-authoritative; canonical Markdown remains the
source of truth.

## Relationship to higher-level systems

Lifecycle, recovery, and orchestration architectures can use Project Corpus as
a durable project-state foundation while keeping their own contracts and
verification responsibilities. Living Software Organism (LSO) is one such
higher-level architecture and reference direction. Project Corpus is not LSO;
it is independently useful and does not require LSO, a Runtime, MCP, a database, or a
specific AI vendor. This describes an architectural relationship; it does not
claim that a public LSO package or repository is available.

## Existing V1 projects

The original V1 workflow and templates remain supported. The optional Runtime
can plan a V1 migration read-only and create a separate V2 destination without
rewriting V1 files. See the [V1 compatibility overview](docs/how-it-works.md),
[direct-folder](docs/access/direct-folder.md), [manual-session](docs/access/manual.md),
and [your-own-MCP](docs/access/own-mcp.md) guides, plus the
[migration guide](docs/migration/v1-read-only-planner.md).

## Documentation

- [Quick Start](docs/quickstart.md)
- [How it works](docs/how-it-works.md)
- [FAQ](docs/faq.md)
- [Runtime and CLI](docs/runtime.md)
- [Local stdio MCP](docs/runtime/stdio-mcp.md)
- [Examples](docs/examples.md)
- [Security](docs/security.md)
- [Russian README](README.ru.md)

## Project details

Project Corpus Protocol is version 2.0. The optional Python Runtime is version
2.2.0, supports Python 3.11+, and has no third-party runtime dependencies.
Release history is in the [changelog](CHANGELOG.md). Questions and bug reports
belong in [GitHub Issues](https://github.com/darksleep1983/project-corpus/issues);
do not post private Corpus contents or secrets.

Project Corpus is free under the MIT license. Optional donations are described
on the [support page](SUPPORT.md); they provide no additional rights or guarantees.

## License

MIT. See [LICENSE](LICENSE).
