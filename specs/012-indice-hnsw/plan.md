# Implementation Plan: Indice Vetorial HNSW

**Branch**: `012-indice-hnsw` | **Date**: 2026-07-21 | **Spec**: `specs/012-indice-hnsw/spec.md`

**Input**: Feature specification from `/specs/012-indice-hnsw/spec.md`

## Summary

Add an operationally measured HNSW rollout for pgvector search. Introduce idempotent HNSW index creation for `knowledge_chunks.embedding` with `vector_cosine_ops`, benchmark exact versus indexed vector search, validate `EXPLAIN (ANALYZE, BUFFERS)` plans, preserve category/tag/project filters, and document memory/build/maintenance cost plus rollback. The existing API/MCP search contract remains unchanged; the feature is delivered through database init helpers, service-level measurement utilities, CLI/runbook tasks and tests.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, PostgreSQL + pgvector, argparse-based CLI

**Storage**: PostgreSQL with pgvector; add HNSW index on `knowledge_chunks.embedding` and supporting operational metadata/reporting without changing search response data.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux backend service and local/operator CLI.

**Project Type**: Backend API/services plus console script/runbook; no frontend required.

**Performance Goals**: Keep typical vector/hybrid search under 500ms and demonstrate measurable p95 latency improvement on a corpus large enough to justify approximate search.

**Constraints**: Keep routes unchanged/thin; SQL helpers in `backend/app/repositories`; orchestration in `backend/app/services`; never choose HNSW parameters without measured evidence; update `doc/OPERATIONS.md` and `doc/API.md` only where behavior/runbook changes are public or operational.

**Scale/Scope**: Existing `search_similar_chunks()` path, active compatible embedding batches, filters by categories/tags/projects, reindex/ingestion write paths, local operator workflow.

## Constitution Check

- Code Quality: Pass. HNSW DDL and SQL plan helpers stay out of route code; benchmark orchestration lives in services/CLI.
- Testing Standards: Pass with gate. Search performance and filter correctness are critical paths and require pytest coverage plus manual/DB-backed validation.
- Performance: Pass with gate. The feature is accepted only after baseline, HNSW validation, recall comparison and insertion/reindex impact are measured.
- Documentation: Pass. Rollback, memory/build cost and operational caveats must be documented.
- UX: N/A for frontend. Operator CLI/runbook output must be concrete and sanitized.

## Project Structure

### Documentation (this feature)

```text
specs/012-indice-hnsw/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- hnsw-operations.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- cli/
|   `-- hnsw.py
|-- db/
|   `-- init.py
|-- repositories/
|   `-- vector_index.py
`-- services/
    `-- vector_index.py

tests/
|-- test_vector_index_operations.py
|-- test_knowledge_service.py
`-- test_reindex_operations.py

doc/
|-- API.md
`-- OPERATIONS.md

pyproject.toml
```

**Structure Decision**: Add a small `repositories/vector_index.py` for DDL, `EXPLAIN` and pgvector metadata queries, plus `services/vector_index.py` for benchmark/report decisions. Add `backend/app/cli/hnsw.py` as the operator surface. Keep `search_similar_chunks()` behavior compatible and update it only if exact-search forcing or query-plan test hooks need shared query construction.

## Implementation Details

### Database and Indexing

- Use one canonical index name: `ix_knowledge_chunks_embedding_hnsw_cosine`.
- Create with pgvector cosine semantics:
  - `CREATE INDEX ... ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)`
  - Include `IF NOT EXISTS` for idempotent local/dev usage.
  - Use `CONCURRENTLY` only in operator CLI/runbook outside transactional `engine.begin()`; do not put concurrent creation inside `init_db()`.
- Add a guarded helper in `backend/app/db/init.py` or `repositories/vector_index.py` that can verify pgvector supports HNSW before attempting creation.
- Always run `ANALYZE knowledge_chunks` after index creation before plan validation.
- Do not add HNSW automatically for row counts below a threshold such as 10,000 chunks unless the operator explicitly overrides.

### Exact vs HNSW Measurement

- Add repository functions that build the same vector-search SQL shape as `search_similar_chunks()`:
  - compatible `EmbeddingBatch.config_hash`;
  - `KnowledgeChunk.embedding_status == 'embedded'`;
  - optional category/tag/project filters;
  - distance ordering with cosine distance;
  - deterministic limit.
- For exact baseline, disable index usage locally for the measurement session or execute before index creation. Prefer a transaction/session-local setting documented in quickstart.
- For HNSW measurement, run the normal query after index creation and `ANALYZE`.
- Capture `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` where possible so tests/services can parse whether the index name appears in the plan.

### Parameter Calibration

- Start with pgvector defaults for build/query parameters unless baseline proves insufficient.
- Allow CLI options for session-local query parameter experiments, e.g. `--hnsw-ef-search`, without baking arbitrary values into global startup.
- Record chosen parameters and rationale in the report. If no parameter improves latency/recall tradeoff, keep defaults.
- Document that build parameters such as `m` and `ef_construction` affect index creation and may require index rebuild.

### Filters and Existing Search

- Preserve category, tag and project filters exactly as current `backend/app/repositories/chunks.py` semantics.
- Benchmark must include:
  - unfiltered vector query;
  - category-filtered query;
  - project-filtered query;
  - optionally combined filters when fixture data exists.
- If filtered queries do not use HNSW, report it as a measured caveat rather than changing API behavior.

### CLI and Reports

- Add `backend/app/cli/hnsw.py` with subcommands:
  - `baseline`: run exact/current measurement and save a JSON report.
  - `create`: create HNSW index when supported and threshold allows it.
  - `validate`: run `ANALYZE`, explain representative queries and compare recall/latency.
  - `drop`: print or execute rollback with explicit confirmation flag.
- Add a console script in `pyproject.toml`, e.g. `knowledge-hnsw = "backend.app.cli.hnsw:main"`.
- Report fields should include timestamp, pgvector version, row counts, active embedding identity/config hash, query specs, exact ids, hnsw ids, recall@k, latency p50/p95, explain plan summary, index size and acceptance decision.

### Documentation

- Update `doc/OPERATIONS.md` with:
  - preconditions from `plan/11-indice-hnsw.md`;
  - baseline command;
  - index creation command;
  - validation command;
  - recall threshold decision point;
  - memory/build/write cost notes;
  - rollback command.
- Update `doc/API.md` only to note search performance/indexing behavior if already documenting search operations; no request/response contract changes are expected.

## Data Model / API Implications

- Database gains one optional HNSW index on `knowledge_chunks.embedding`; no table columns are required.
- Optional operational report JSON is a file artifact, not persisted in the application database for MVP.
- Search API, answer API and MCP search retain their existing request/response contracts.
- CLI becomes the primary public operator interface for HNSW lifecycle and validation.

## Test Strategy

- Unit tests for report decision logic: accept/reject based on latency gain, recall threshold, row-count threshold and plan-index detection.
- Repository/SQL construction tests ensuring category/tag/project filters remain present for explained vector queries.
- DB integration test, when PostgreSQL + pgvector is available, proving HNSW index creation is idempotent and `ANALYZE` runs.
- Service tests comparing exact ids vs approximate ids with deterministic fixtures or mocked repository output.
- Regression tests for `search_knowledge()` to ensure result shape and filter semantics do not change.
- Reindex/insertion impact test can be a service-level benchmark stub plus manual quickstart step if CI cannot run a large corpus.

## Risk Notes

- HNSW may not help small corpora; the implementation must allow exact search to remain the accepted path.
- PostgreSQL planner may choose sequential/exact plans for selective filters; acceptance should reflect measured behavior per filter type.
- `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block, so startup init and operator commands need separate paths.
- HNSW consumes memory and slows writes/reindexing; this is an operational tradeoff that must be measured before production rollout.
- pgvector version differences can break DDL syntax or parameter support; feature must detect/report capabilities.

## Complexity Tracking

No constitution violations identified. The extra CLI/reporting layer is justified because the source plan explicitly requires measured calibration, recall comparison and rollback documentation.
