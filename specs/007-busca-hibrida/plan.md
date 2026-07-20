# Implementation Plan: Busca Hibrida

**Branch**: `007-busca-hibrida` | **Date**: 2026-07-20 | **Spec**: `specs/007-busca-hibrida/spec.md`

**Input**: Feature specification from `/specs/007-busca-hibrida/spec.md`

## Summary

Add hybrid retrieval for knowledge search by combining the existing pgvector semantic ranking with PostgreSQL full-text search over chunk content. Retrieve vector and text candidates independently, apply category filters before each candidate limit, deduplicate by chunk id, fuse ranks with Reciprocal Rank Fusion, and optionally expose diagnostic match reasons while preserving the default API/MCP contract.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, FastMCP, PostgreSQL full-text search, pgvector

**Storage**: PostgreSQL with pgvector; add `tsvector` support and GIN index for `knowledge_chunks.content`.

**Testing**: `.venv/bin/python -m pytest`; Plano 12 evaluation runner once available.

**Target Platform**: Linux web service with MCP server.

**Project Type**: Backend API + MCP tool integration.

**Performance Goals**: Keep typical search within 500ms; text search must use GIN index and vector search must preserve the existing indexed pgvector path when available.

**Constraints**: Keep routes thin, business behavior in `backend/app/services`, persistence queries in `backend/app/repositories`, update `doc/API.md`, avoid logging query text by default.

**Scale/Scope**: Existing `/api/v1/knowledge/search`, `/api/v1/knowledge/answer` and MCP `search` flows. No mandatory frontend change.

## Constitution Check

- Code Quality: Pass. Search orchestration stays in `backend/app/services/search.py`; SQL details stay in `backend/app/repositories/chunks.py`; API/MCP layers only pass options through.
- Testing Standards: Pass. Unit and integration tests cover repository ranking, service fusion, API forwarding and MCP compatibility.
- Performance: Pass with gate. Plan requires GIN index and execution-plan validation for text search plus unchanged pgvector candidate path.
- Documentation: Pass. API docs and Spec Kit contract document optional diagnostics and hybrid behavior.

## Project Structure

### Documentation (this feature)

```text
specs/007-busca-hibrida/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- hybrid-search.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- db/
|   |-- init.py
|   `-- models.py
|-- repositories/
|   `-- chunks.py
|-- schemas/
|   `-- knowledge.py
|-- api/routes/
|   `-- knowledge.py
`-- services/
    `-- search.py

mcp_server/
|-- server.py
`-- tools/knowledge.py

tests/
|-- test_knowledge_api_integration.py
|-- test_knowledge_service.py
`-- test_mcp_knowledge.py

doc/API.md
plan/12-avaliacao-rag.md
```

**Structure Decision**: Use the existing backend repository/service split. No new route module or standalone search subsystem is needed for v1.

## Implementation Details

### Database and Indexing

- Add a `search_vector` `tsvector` representation for `knowledge_chunks.content`.
- Prefer a generated column when compatible with the supported PostgreSQL version; otherwise maintain the column idempotently in `backend/app/db/init.py`.
- Create `CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_search_vector ON knowledge_chunks USING GIN (search_vector)`.
- Use `to_tsvector('simple', content)` initially because the feature explicitly needs codes, numbers, tickers and exact-ish tokens. Record a follow-up decision if Portuguese stemming materially improves evaluation results.
- Ensure existing rows are backfilled during init/migration.

### Repository Query Design

- Keep `search_similar_chunks()` or introduce a vector-specific helper returning ranked candidates with raw distance.
- Add `search_text_chunks()` in `backend/app/repositories/chunks.py` using `websearch_to_tsquery` or `plainto_tsquery` with the selected configuration.
- Apply category filters in both vector and text statements before candidate `limit`.
- Fetch an expanded candidate count internally, such as `max(limit * 4, 20)`, so fusion has enough candidates before the final `limit`.
- Reuse the existing `build_chunk_read()` path so citation metadata, public source ids and URI sanitization remain consistent.

### Fusion and Filtering

- Implement a small internal `HybridSearchCandidate` structure in `backend/app/services/search.py`.
- Compute RRF as `sum(1 / (k + rank))` across available retrieval paths, with `k=60` as the standard default unless evaluation recommends a different constant.
- Deduplicate by `chunk.id`; preserve vector score as the public `score` when available so `min_score` remains comparable to existing behavior.
- Apply `min_score` to the vector score for candidates that have vector matches. Text-only candidates should not be discarded solely because they lack vector score; document their public `score` as `None` or a non-probabilistic fused score only after contract review.
- Sort by fused rank, then prefer candidates that matched both paths, then vector score, then text rank as deterministic tie breakers.

### API, RAG and MCP Flow

- Keep `search_knowledge()` as the single orchestration point used by API search, API answer and MCP search.
- Add optional request fields only if diagnostics or mode selection are needed:
  - `include_match_reasons: bool = False`
  - optional future `search_mode: "hybrid" | "vector"` if rollback/calibration needs a public switch.
- Preserve default response shape for clients that do not request diagnostics.
- When diagnostics are enabled, expose concise match reasons per result rather than raw query text or internal SQL details.
- `answer_knowledge()` should use the same hybrid retrieval path so RAG context benefits from exact-term recall.

### Observability

- Log non-sensitive counts: vector candidate count, text candidate count, fused count, final count, threshold source and whether diagnostics were requested.
- Do not log the raw query text by default.
- Add a manual SQL check in `quickstart.md` for `EXPLAIN` plans using GIN.

## Data Model / API Implications

- Database gains `knowledge_chunks.search_vector` and `ix_knowledge_chunks_search_vector`.
- Existing search responses remain compatible by default.
- Optional diagnostics may add `match_reasons` to each result only when explicitly requested.
- API request bodies for `/knowledge/search` and `/knowledge/answer`, plus MCP search, may gain `include_match_reasons`.
- `doc/API.md` must document hybrid ranking and clarify that public `score` remains a similarity signal, not a direct hybrid probability.

## Test Strategy

- Unit test RRF fusion ordering, deduplication and tie-breaking in `tests/test_knowledge_service.py`.
- Unit or repository test text candidate retrieval for exact identifiers, tickers and error messages.
- Regression test semantic paraphrase results still pass through the vector candidate path.
- API integration tests verify default response compatibility and optional diagnostic forwarding.
- MCP tests verify default compatibility and optional diagnostic exposure if added to MCP.
- Database validation checks that the text search plan uses the GIN index.
- Plano 12 evaluation compares hybrid candidate against vector-only baseline before acceptance.

## Risk Notes

- `simple` configuration may reduce Portuguese stemming quality; `portuguese` may damage code-like tokens. The implementation must keep this as an evaluation-backed decision.
- Applying `min_score` to hybrid results is subtle because RRF is not comparable to cosine similarity. Preserve vector score semantics and document text-only behavior.
- Text-only matches can improve exact recall but may introduce false positives for very common terms; candidate limits and RRF tie-breakers need calibration.
- Idempotent schema updates in `init_db()` are acceptable in this repo, but a future migration tool may be preferable as schema complexity grows.
- Plano 12 is listed as a release gate even though the current roadmap places evaluation after hybrid search; at minimum create enough local fixtures to compare vector-only and hybrid behavior.

## Complexity Tracking

No constitution violations identified.
