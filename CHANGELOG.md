# Changelog

[Русская версия](CHANGELOG.ru.md)

## Unreleased

- Added the independent Markdown-first Project Corpus Protocol V2 with
  role-separated canonical state and explicit conformance rules.
- Added the optional Python 3.11+ reference Runtime with external owner trust,
  native confined transactions, audit/recovery, CLI and local stdio MCP.
- Added read-only planning and controlled create-only V1-to-V2 migration; V1
  templates remain unchanged and usable.
- Added the mandatory redacted full-local-history release security gate.
- Excluded Git commit/push, HTTP/remote MCP, arbitrary shell execution,
  sandboxing, orchestration, distributed locking and multi-project operation.
- Reframed Project Corpus as a Markdown protocol rather than a bundled server.
- Added three equal access modes: direct folder, owner-provided MCP, and manual
  session uploads.
- Replaced `MCP_CONNECTION_CURRENT.md` with neutral
  `CORPUS_ACCESS_CURRENT.md`.
- Added paired access guides and Codex client guides.
- Removed the embedded MCP runtime, transports, ports, installers, package
  metadata, and required user-side Python dependency.
- Preserved English/Russian parity, protected-file rules, GitHub Issues
  feedback, and voluntary USDT-on-TON support.
- Prepared public-facing status and vulnerability-reporting guidance.

## 0.1.0 — historical server preview

- Initial combined protocol and bundled MCP-server preview.
