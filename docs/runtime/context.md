# Context Intelligence (optional Runtime, 2.2.0)

[Русская версия](context.ru.md)

Project Corpus Protocol remains **2.0**. The portable Markdown layout and manual workflow do not need Runtime, SQLite, an LLM, or network access. Context Intelligence is a local, rebuildable, non-authoritative Runtime view for any AI consumer. No external database or third-party dependency is required. Future optional adapters may integrate Graphiti, Cognee, or other systems; none is used by the core.

## Sources and boundaries

The first provider reads only policy-scoped Markdown in `state/`, `tasks/`, `reports/`, and `history/`, using the native confined backend. It does not crawl code or docs. Both canonical state files must be in read scope. The explicit SQLite index path must be a `.sqlite3` file directly inside the project's `.project-corpus/cache/`; it is never read from policy and never grants a capability. The index contains project ID, source paths and SHA-256 hashes, type, authority class, timestamp, temporal class, and line/section-line provenance. It stores **no source text**. Deleting it leaves the Corpus intact; `build` recreates it. Query/bundle refuse stale source hashes until a rebuild. SQLite FTS5 is not required.

The provider limits one file to the existing Runtime 8 MiB read ceiling, the scoped snapshot to 2,048 sources/64 MiB and 50,000 nonblank lines, and the persisted index to 128 MiB. A larger corpus fails with a bounded error. Keep `.project-corpus/cache/` out of Git: it is a disposable, non-authoritative derived view. The index writer uses confined native staging/publication and refuses link or reparse paths.

```text
project-corpus context build ROOT --index ROOT/.project-corpus/cache/context.sqlite3
project-corpus context query ROOT "query" --index ROOT/.project-corpus/cache/context.sqlite3 [--limit N]
project-corpus context bundle ROOT "query" --index ROOT/.project-corpus/cache/context.sqlite3 [--max-tokens N]
project-corpus context doctor ROOT --index ROOT/.project-corpus/cache/context.sqlite3
project-corpus context eval ROOT --index ROOT/.project-corpus/cache/context.sqlite3 --dataset ROOT/eval.json
project-corpus context candidate-validate ROOT --input ROOT/candidate.json
```

Commands return JSON; invalid input, stale index, path escape, and policy denial have stable error codes and exit `2`. `doctor` and `eval` return `ok: false` in JSON for diagnostic/evaluation findings. Dataset/candidate JSON inputs must be regular files inside the project root, at most 1 MiB. No context command modifies PROJECT or STATUS.

## Retrieval and temporal meaning

Ranking is deterministic: token and phrase overlap, canonical/active/cited/scoped authority, current versus historical penalty, explicit source timestamp, exact project ID, and section provenance. Exact and near-duplicate results are suppressed. A result is a pointer, never a canonical conclusion: `non_authoritative=true` and `freshness_requirement=READ_PRIMARY_SOURCE_BEFORE_AUTHORITY_CLAIM` require primary-source readback.

The non-normative, optional line `Supersedes: .project-corpus/reports/old.md` on a scoped Task, Report, or History artifact marks that exact policy-visible source `superseded`. A relation cannot supersede PROJECT, STATUS, or the active Task. Invalid or absent links never imply a replacement. Old sources remain searchable. Without a link, older uncited Reports and inactive Tasks are historical; cited Reports are scoped. Current status comes only from STATUS, and durable identity only from PROJECT. This syntax does not change Protocol V2 required metadata or older corpora.

## Bundle, receipt, and candidate v1

`compile_bundle()` emits JSON-compatible `schema_version=1`, `project_id`, `query`, `created_at`, `index_schema_version`, `source_snapshot_digest` and `source_count` for the complete scoped corpus, bounded `selected_source_snapshot`, `mandatory_reads`, `budget`, `items`, `serialized_bytes`, `non_authoritative=true`, and `bundle_sha256`. It never embeds the complete path/hash map. Each item has ID, excerpt, path, line span, source SHA-256, authority and temporal class, freshness requirement, score, and selection reasons. PROJECT, STATUS, and the active Task receive bounded structural summaries; `mandatory_reads` gives their primary path/hash and the sections requiring full readback. At low budgets, summaries shorten while mandatory read requirements remain explicit. `max_tokens` estimates **excerpt text** as ceil(UTF-8 bytes/4), not whole-JSON tokens; the complete serialized envelope has a separate 65,536-byte ceiling and exact byte count. The deterministic hash excludes only `created_at` and the hash field itself. Any scoped source change changes the full digest and bundle hash after rebuild.

`make_receipt(bundle, consumer)` verifies the bundle hash and returns receipt `schema_version=1`, project ID, bundle hash, delivered item IDs, consumer ID, timestamp, source snapshot digest, and non-authoritative flag. The caller records actual delivery; the helper cannot prove that an external agent consumed it.

`validate_candidate(corpus, candidate)` accepts only candidate `schema_version=1`, ID, project ID, kind, statement, source refs with exact path/hash/line, UTC creation time, and `status=candidate`. Kinds: `semantic_fact`, `episodic_evidence`, `procedural_knowledge`, `environment_gotcha`, `premise`, `resource_reference`. It validates evidence and serializable content but never promotes or writes canonical state. Promotion remains an explicit supervisor/owner action.

Memory Doctor checks index schema/staleness, missing sources, provenance, duplicates, orphaned/invalid/cyclic supersession links, project mismatch, oversized STATUS, English/Russian volatile claims without freshness labels, full and selected Bundle snapshot staleness, and optional candidate evidence. It does not repair anything. CorpusEval v1 accepts `{"schema_version":"1","cases":[...]}` with each case's query, expected retrieval top source/top-k paths, source-specific temporal/authority expectations, expected/forbidden bundle paths or classes, optional must-contain/must-not-contain strings, budget, project isolation and expected snapshot digest. Retrieval and Bundle checks are separate; isolation must be tested with foreign or policy-denied fixtures. It reports recall, contamination, source-specific correctness, budget, staleness and repeatability without an LLM judge.

`forbidden_scope_paths` checks that foreign or policy-denied fixture sources never enter the collected snapshot or either output. Cases without an explicit scope assertion report isolation as untested.

The optional stdio MCP exposes `corpus.context_query`, `corpus.context_bundle`, `corpus.context_doctor`, and `corpus.candidate_validate` only when `corpus.context` is present in Runtime hard limits, external trust grant, project policy, and session subset. MCP builds an ephemeral in-memory view from current scoped sources; tool arguments contain no index or arbitrary path. Its doctor therefore checks current sources, while CLI doctor additionally compares a persisted index. Existing tools keep their contracts.
