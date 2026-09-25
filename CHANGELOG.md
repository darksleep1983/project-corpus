# Changelog

[Русская версия](CHANGELOG.ru.md)

## Unreleased

## 2.2.0 — 2026-09-25

- Added optional, policy-scoped, rebuildable Context Intelligence index without source text, external database, LLM, network, or new dependencies.
- Added deterministic authority-aware retrieval, explicit temporal supersession, bounded Context Bundle/Receipt v1, evidence-bound candidates, Memory Doctor, and CorpusEval.
- Added `context` CLI namespace and capability-gated, read-only stdio MCP context tools. Protocol remains 2.0 and manual corpora remain valid.

## 2.1.0

- Added optional local, read-only source-aware discovery: deterministic search, timestamp-backed timelines and safe artifact show/read through the Runtime CLI and stdio MCP.
- Discovery views are explicitly non-authoritative; they do not create an index, alter Protocol V2, or add network, database or write dependencies.

## 2.0.1 — 2026-09-17

- Improved post-v2.0.0 README onboarding with a visual project-state flow, a
  60-second manual V2 quick start, and clearer optional Runtime setup.
- Prepared public OSS productization assets: an English-first documentation
  site, real-world V2 examples, issue forms, package-readiness metadata, and
  owner-gated Pages, PyPI, release, and MCP-distribution plans.

## 2.0.0 — 2026-09-17

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
