# Implementation Plan: Tags

**Branch**: `008-tags` | **Date**: 2026-07-20 | **Spec**: `specs/008-tags/spec.md`

**Input**: Feature specification from `/specs/008-tags/spec.md`

## Summary

Add reusable free-form tags as a second classification dimension next to controlled categories. Introduce `tags` and `document_source_tags`, normalize tag identity with trim/lowercase/accent-insensitive keys, expose tag CRUD and autocomplete, allow source association through ingestion and patch flows, and support tag filters in search, answer and MCP without reprocessing embeddings when only tags change.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy async, Pydantic v2, FastMCP, PostgreSQL + pgvector

**Storage**: PostgreSQL with pgvector; add relational `tags` and `document_source_tags` tables with unique constraints and lookup indexes.

**Testing**: `.venv/bin/python -m pytest`

**Target Platform**: Linux web service with MCP server.

**Project Type**: Backend API + MCP tool integration.

**Performance Goals**: Preserve typical search under 500ms; tag autocomplete and tag-filtered list/search responses under 1 second for representative local data.

**Constraints**: Keep routes thin, put tag business rules in `backend/app/services/tags.py`, put persistence helpers in `backend/app/repositories/tags.py`, avoid embedding regeneration for metadata-only tag changes, update `doc/API.md`.

**Scale/Scope**: Existing `/api/v1/knowledge/*` API, MCP knowledge tools, source listing/detail, text/upload ingestion, source patch, search and answer.

## Constitution Check

- Code Quality: Pass. Tag rules live in services/repositories, while FastAPI and MCP layers only validate and forward requests.
- Testing Standards: Pass. Unit and integration tests cover normalization, association, filtering, source patch behavior and MCP/API contracts.
- Performance: Pass with gate. Tag filters use indexed association tables and deduplicate source/chunk rows before final limits.
- Documentation: Pass. API and MCP contract documentation must explain categories versus tags and filter semantics.

## Project Structure

### Documentation (this feature)

```text
specs/008-tags/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- knowledge-tags.md
`-- tasks.md
```

### Source Code (repository root)

```text
backend/app/
|-- api/routes/
|   `-- knowledge.py
|-- db/
|   |-- init.py
|   `-- models.py
|-- repositories/
|   |-- chunks.py
|   |-- sources.py
|   `-- tags.py
|-- schemas/
|   `-- knowledge.py
`-- services/
    |-- ingestion.py
    |-- search.py
    |-- sources.py
    `-- tags.py

mcp_server/
|-- server.py
`-- tools/knowledge.py

tests/
|-- test_knowledge_api_integration.py
|-- test_knowledge_service.py
`-- test_mcp_knowledge.py

doc/API.md
```

**Structure Decision**: Reuse the existing knowledge route and MCP tool files. Add tag-specific service/repository modules because tag normalization, autocomplete, conflict handling and in-use checks are distinct enough from category code.

## Implementation Details

### Database and Normalization

- Add `Tag` SQLAlchemy model with `id`, `name`, `slug` or `normalized_name`, and `created_at`.
- Add `document_source_tags` association table with composite primary key `(document_source_id, tag_id)` and `ON DELETE CASCADE` from source.
- Add unique constraint on `tags.normalized_name`.
- Add indexes for autocomplete/lookup:
  - unique B-tree on normalized name.
  - B-tree or pattern index suitable for prefix autocomplete if evaluation shows the default index is insufficient.
- Implement normalization in `backend/app/services/tags.py`:
  - trim whitespace.
  - lowercase.
  - collapse internal whitespace if desired by research decision.
  - remove accents with standard-library `unicodedata`.
- Keep display `name` as normalized ASCII in v1 unless a separate display name is chosen in `research.md`.

### Service and Repository Design

- Mirror category patterns for `TagNotFoundError`, `TagConflictError` and `TagInUseError`.
- Implement `get_tags(session, tag_ids)` preserving request order and reporting the first missing id.
- Implement `create_tag`, `update_tag`, `delete_tag`, `list_tags` and `autocomplete_tags`.
- For name-based association, implement an explicit `get_or_create_tags_by_name()` helper so ingestion code never performs ad hoc normalization.
- Extend source serialization in `backend/app/repositories/sources.py` to include sorted tags.
- Extend `build_chunk_read()` in `backend/app/repositories/chunks.py` so search/answer chunks include tags.

### API Contract

- Add Pydantic schemas:
  - `TagRead`, `TagWrite`.
  - reusable `validate_tag_id_list()`.
  - optional `tag_ids` on source patch, search and answer payloads.
  - optional `tag_ids` or `tag_names` on ingestion payloads after choosing one primary contract.
- Add endpoints under `/api/v1/knowledge/tags`:
  - `GET /tags`
  - `GET /tags/autocomplete?q=...&limit=...`
  - `POST /tags`
  - `PATCH /tags/{tag_id}`
  - `DELETE /tags/{tag_id}`
- Keep error mapping parallel to categories:
  - missing tag -> `404`.
  - duplicate tag -> `409`.
  - tag in use on delete -> `409`.
- Document whether tags are optional on ingestion and how clients should create/reuse tags before assigning them.

### Ingestion and Source Patch

- Extend `ingest_plain_text()` and `ingest_uploaded_file()` to accept optional tag ids or names.
- Persist source-tag associations without changing content hash behavior.
- Extend `update_source()` so metadata-only tag changes do not rebuild chunks or embeddings.
- If content changes and tags also change, update both associations and regenerated chunks in one transaction.
- Return tags in `KnowledgeUploadResponse`, `KnowledgeSourceRead` and `KnowledgeSourceDetail`.

### Search, Answer and MCP

- Extend `search_knowledge()` and `answer_knowledge()` with `tag_ids: list[int] | None`.
- Validate tag ids before embedding generation and before repository search, matching category behavior.
- Apply category and tag filters as AND dimensions:
  - category filter: source must match any requested category.
  - tag filter: source must match any requested tag for MVP.
  - combined: source must satisfy both filters when both are present.
- Deduplicate chunks by chunk id/source join shape when multiple tags match.
- Add optional future `tag_match_mode: "any" | "all"` only if the real case for ALL is confirmed.
- Extend MCP models/tools with tags in source/hit/read responses and tag filter inputs.

### Documentation and Observability

- Update `doc/API.md` for new endpoints, source/chunk fields and search/answer request fields.
- Add contract notes in `specs/008-tags/contracts/knowledge-tags.md`.
- Log non-sensitive tag filter counts where search already logs candidate counts; do not log arbitrary tag names by default.

## Data Model / API Implications

- Database gains `tags` and `document_source_tags`.
- Source and chunk responses gain `tags: list[TagRead]`.
- Search and answer requests gain optional `tag_ids`.
- Ingestion and source patch requests gain optional tag association fields.
- MCP knowledge source/hit models gain tags and search accepts tag filters.
- API docs must clearly state that categories are controlled broad subjects and tags are reusable granular markers.

## Test Strategy

- Unit test tag normalization, conflict detection, missing-id validation and in-use delete checks.
- Service tests for creating sources with tags, reusing duplicate-equivalent tags and updating only tags without embedding calls.
- Repository/service tests for tag-filtered search, category+tag combination and duplicate chunk prevention.
- API integration tests for tag CRUD, autocomplete, ingestion/patch contracts and search/answer filters.
- MCP tests for tag fields in source/search responses and optional tag filters.
- Documentation quickstart smoke test with the new endpoints.

## Risk Notes

- Free-form tags can become noisy quickly; autocomplete and normalization must be present in the same release as tag assignment.
- Accent-insensitive keys may surprise users if display names are normalized to ASCII. Preserve original display labels later if users need accents visually.
- Name-based upsert is ergonomic but can hide typos. ID-based association is safer for API contracts; name-based association can be limited to explicit ingest convenience.
- ALL tag filtering may add complexity to SQL and tests. Keep it out of MVP until a concrete case proves ANY is insufficient.
- Source patch must carefully distinguish metadata-only changes from content changes to avoid unnecessary embedding cost.

## Complexity Tracking

No constitution violations identified.
