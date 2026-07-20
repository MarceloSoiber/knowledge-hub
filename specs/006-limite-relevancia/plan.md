# Implementation Plan: Limite Minimo de Relevancia

**Branch**: `006-limite-relevancia` | **Date**: 2026-07-17 | **Spec**: `specs/006-limite-relevancia/spec.md`

**Input**: Feature specification from `/specs/006-limite-relevancia/spec.md`

## Summary

Add a configurable minimum relevance threshold to semantic search so weak matches are filtered before they reach API, RAG answer generation or MCP clients. Use a global `SEARCH_MIN_SCORE` default for safe behavior and an optional validated request-level `min_score` override for controlled calibration.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, FastMCP, pgvector

**Storage**: PostgreSQL with pgvector; no schema migration expected.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux web service with MCP server.

**Project Type**: Backend API + MCP tool integration.

**Performance Goals**: Keep typical semantic search within the existing 500ms target; filtering happens in memory over the already limited result set.

**Constraints**: Keep API routes thin, keep business behavior in `backend/app/services`, update `doc/API.md`, do not log sensitive query text by default.

**Scale/Scope**: Existing `/knowledge/search`, `/knowledge/answer` and MCP `search_knowledge` flows; no new persistence model.

## Constitution Check

- Code Quality: Pass. Threshold resolution and filtering live in services/repositories instead of routes.
- Testing Standards: Pass. Unit, API validation and MCP tests cover filtering, empty results and invalid limits.
- Performance: Pass. Filtering is a cheap post-processing step over search candidates.
- Documentation: Pass. API docs and Spec Kit contract document default threshold and calibration rules.

## Project Structure

### Documentation (this feature)

```text
specs/006-limite-relevancia/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- relevance-threshold.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- core/settings.py
|-- repositories/chunks.py
|-- schemas/knowledge.py
|-- api/routes/knowledge.py
`-- services/
    |-- rag.py
    `-- search.py

mcp_server/
|-- server.py
`-- tools/knowledge.py

tests/
|-- test_knowledge_api_integration.py
|-- test_knowledge_service.py
`-- test_mcp_knowledge.py

doc/API.md
```

**Structure Decision**: Use the existing backend service, schema and MCP modules. No database model or migration is needed because the feature derives from existing search scores.

## Implementation Details

### Threshold Configuration

- Add `search_min_score: float = Field(default=0.35, ge=0.0, le=1.0)` to `backend/app/core/settings.py`.
- Environment variable maps to `SEARCH_MIN_SCORE` through Pydantic settings.
- Reject non-finite values during request validation and service filtering; `NaN` or infinite scores must never pass the threshold.
- Document the default as conservative, not universal; recalibrate when domains or embedding models change.

### Search Flow

- Extend `KnowledgeSearchRequest` with optional `min_score: float | None = Field(default=None, ge=0.0, le=1.0)`.
- Extend `search_knowledge()` to accept `min_score`.
- Resolve effective threshold as request `min_score` when present, otherwise `get_settings().search_min_score`.
- Compute scores as today in `backend/app/repositories/chunks.py`, then remove results whose score is missing, invalid or lower than the effective threshold.
- Keep filtering in `backend/app/services/search.py` so API search, API answer and MCP use the same policy.
- Consider fetching up to the requested limit only for v1; if calibration shows too many false negatives due to top-N truncation, add a later candidate expansion parameter.

### Answer Flow

- Extend `KnowledgeAnswerRequest` with optional `min_score` so `/answer` uses the same threshold behavior as `/search`.
- When filtering yields no sources, keep `sources=[]` and rely on the existing RAG instruction to declare absence of information.
- Add a narrow test to confirm `answer_knowledge()` calls the answer client with zero sources when all results are filtered.

### MCP Flow

- Extend `mcp_server/tools/knowledge.py::search_knowledge()` with optional `min_score`.
- Extend the registered FastMCP wrapper in `mcp_server/server.py::search()` so external MCP clients can pass `min_score`.
- Validate `min_score` with typed annotations/Pydantic bounds before calling the backend search service.
- Return the same result contract as API search.

### Observability

- Add non-sensitive structured logging around search filtering:
  - effective threshold
  - raw result count
  - filtered result count
  - minimum and maximum score among raw candidates when available
- Do not log the query string by default.

## Data Model / API Implications

- No database schema changes.
- API request bodies for `/api/v1/knowledge/search` and `/api/v1/knowledge/answer` gain optional `min_score`.
- API responses remain unchanged; fewer or zero results may be returned.
- MCP search gains optional `min_score`.

## Test Strategy

- Unit test score filtering in `tests/test_knowledge_service.py`.
- Unit test that score equal to threshold is retained and score below threshold is removed.
- Unit test empty filtered results in `answer_knowledge()`.
- API integration tests verify valid `min_score` forwarding for search and answer, plus invalid `min_score` validation errors.
- MCP tests verify `min_score` forwarding from tool helper and registered server wrapper, plus invalid values where local validation applies.
- Documentation check by updating `doc/API.md` examples and parameter tables.

## Risk Notes

- The initial default may be too strict or too permissive for some domains; this is expected and requires calibration.
- `1 - cosine_distance` is not a probability, so user-facing documentation must avoid probability language.
- Filtering after the current `limit` can return fewer than requested even if additional lower-ranked candidates would pass only in unusual ordering cases; acceptable for v1 because ordering is already by cosine distance.
- Lowering `min_score` per request can increase false positives; bounds and documentation make that explicit.

## Complexity Tracking

No constitution violations identified.
